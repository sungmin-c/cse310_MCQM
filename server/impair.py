"""What-if 손상 주입 — 녹화된 수신 trace(패킷 시각·크기)에 손실·대역폭·지연·지터를 적용한다.

trace 기반 에뮬레이션이다. 송신 측 혼잡 제어 반응(앱이 화질을 낮추는 것)은 반영하지 않는다.

적용 순서 (실제 경로를 흉내):
  1. 손실      Bernoulli(burst_len<=1) 또는 Gilbert 2-상태(burst_len>1, Bad 상태에서만 손실)
  2. 대역폭    토큰 버킷 + FIFO 대기열. 대기가 max_queue_ms를 넘을 패킷은 버림(tail drop)
  3. 지연·지터 extra = delay + N(0, jitter), 0 미만은 0. **FIFO: 순서 뒤바뀜 없음**
               (출력 시각 = max(t + extra, 직전 출력 시각)).
               [가정] 영상통화 경로에서 재정렬은 드물다고 보고 FIFO로 단순화한다.

Impairer는 상태(손실 상태, 토큰, 대기열 끝, 난수열)를 유지하므로 1초 tick마다 나눠 호출해도
한 번에 호출한 것과 결과가 같다 (What-if 실시간 재생용). 손실·지터 난수열을 분리해 이를 보장한다.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class ImpairParams:
    loss_pct: float = 0.0        # 0–100
    burst_len: float = 1.0       # 평균 연속 손실 길이(패킷). 1 이하 = Bernoulli
    delay_ms: float = 0.0
    jitter_ms: float = 0.0       # 추가 지연의 표준편차
    bw_kbps: float | None = None  # None = 제한 없음
    burst_bytes: float | None = None  # 토큰 버킷 깊이. None = max(1500, 10ms 분량)
    max_queue_ms: float = 200.0  # [가정] 병목 대기열 한도 200ms


class Impairer:
    def __init__(self, params: ImpairParams, seed: int = 0):
        self.p = params
        ss = np.random.SeedSequence(seed)
        self._rng_loss, self._rng_jit = (np.random.default_rng(s) for s in ss.spawn(2))
        self._bad = False            # Gilbert 상태
        self._tokens = None          # 토큰 버킷 (첫 패킷에서 가득 채움)
        self._t_tok = None
        self._q_end = -np.inf        # 대역폭 대기열 마지막 출발 시각
        self._out_end = -np.inf      # 최종 출력 마지막 시각 (FIFO)

    def apply(self, t, size):
        """t: 수신 시각(초, 오름차순), size: 바이트. 반환 (살아남은 원래 인덱스, 새 시각)."""
        t = np.asarray(t, dtype=float)
        size = np.asarray(size, dtype=float)
        idx = np.flatnonzero(~self._loss_mask(len(t)))
        idx, dep = self._bandwidth(idx, t, size)
        return idx, self._delay(dep)

    # ------------------------------------------------------------------ steps

    def _loss_mask(self, n):
        p = self.p.loss_pct / 100.0
        u = self._rng_loss.random(n)
        if p <= 0:
            return np.zeros(n, dtype=bool)
        if self.p.burst_len <= 1:
            return u < p
        # Gilbert: r = P(Bad→Good) = 1/burst, q = P(Good→Bad) → 정상상태 손실률 q/(q+r) = p
        r = 1.0 / self.p.burst_len
        q = min(1.0, p * r / (1.0 - p)) if p < 1 else 1.0
        lost = np.empty(n, dtype=bool)
        bad = self._bad
        for i in range(n):
            bad = (u[i] >= r) if bad else (u[i] < q)
            lost[i] = bad
        self._bad = bad
        return lost

    def _bandwidth(self, idx, t, size):
        if not self.p.bw_kbps:
            return idx, t[idx]
        rate = self.p.bw_kbps * 1000.0 / 8.0                      # bytes/s
        depth = self.p.burst_bytes or max(1500.0, rate * 0.010)
        max_q = self.p.max_queue_ms / 1000.0
        keep, dep_out = [], []
        for i in idx:
            ti, si = t[i], size[i]
            cap = max(depth, si)
            if self._tokens is None:
                self._tokens, self._t_tok = cap, ti
            ready = max(ti, self._q_end)
            tok = min(cap, self._tokens + (ready - self._t_tok) * rate)
            dep = ready if tok >= si else ready + (si - tok) / rate
            if dep - ti > max_q:
                continue                                           # 대기열 넘침 → 버림
            self._tokens, self._t_tok = (tok - si, ready) if tok >= si else (0.0, dep)
            self._q_end = dep
            keep.append(i)
            dep_out.append(dep)
        return np.asarray(keep, dtype=int), np.asarray(dep_out, dtype=float)

    def _delay(self, dep):
        if len(dep) == 0:
            return dep
        extra = np.full(len(dep), self.p.delay_ms / 1000.0)
        if self.p.jitter_ms > 0:
            extra = extra + self._rng_jit.normal(0.0, self.p.jitter_ms / 1000.0, len(dep))
        out = dep + np.maximum(extra, 0.0)
        out[0] = max(out[0], self._out_end)
        out = np.maximum.accumulate(out)                           # FIFO
        self._out_end = out[-1]
        return out


def impair(t, size, seed=0, **params):
    """한 번에 적용하는 편의 함수. 예: impair(t, size, loss_pct=5, delay_ms=100)."""
    return Impairer(ImpairParams(**params), seed=seed).apply(t, size)
