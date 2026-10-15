"""원인 진단 v0 — 1초 feature를 통화 초반 기준선과 비교해 품질 저하 원인을 추정한다 (규칙 기반).

출력 cause ∈ CAUSES, confidence ∈ [0, 1]. 트래픽 기반 '추정'이며 확정 진단이 아니다.

신호 (기준선 = 정상 윈도우들의 중앙값):
  r_bytes, r_pkts  수신 바이트·영상 패킷 수 비율
  d_q1             패킷 간격(IAT) 하위 25% 값의 증가량 ms
  r_std            IAT 표준편차 비율
  d_max            최대 IAT 증가량 ms

근거 (scripts/diag_synth.py, in-lab Meet·Teams dev 각 26통화에서 관찰. 결과는 docs/PROGRESS.md):
  bandwidth     병목 대기열이 패킷을 전송 속도대로 벌려 놓는다 → d_q1 크게 증가 + 바이트 감소
  delay_jitter  지연이 들쭉날쭉하면 FIFO에서 패킷이 몰렸다 풀린다 → r_std 증가 + q1 붕괴(몰림)
                (q1이 원래 ~1ms인 Teams는 비율 r_q1과 최대 간격 증가로 본다)
  loss          패킷 수 감소 + 빈자리만큼 최대 간격 증가, 몰림은 없음
  지터 없는 고정 지연은 수신 측 trace에 흔적이 없어 진단할 수 없다 (한계로 보고).
임계값은 dev 세트에서 정했고 test 세트로만 성능을 보고한다. 저비트레이트(≈160 kbps) in-lab 데이터
기준이라 실제 폰 통화(수백 kbps~Mbps)에서 재조정이 필요하다 (M4 Clumsy 실험).
"""
from collections import Counter, deque

import numpy as np

CAUSES = ["bandwidth", "delay_jitter", "loss", "weak_wifi", "none"]


class Diagnoser:
    def __init__(self, warmup=8, skip_first=2, base_len=20, min_pkts=5, rssi_weak_dbm=-75.0, vote=3):
        self.warmup = warmup              # 기준선을 만들기 전까지는 판정하지 않음
        self.min_pkts = min_pkts          # 기준선 후보 윈도우의 최소 영상 패킷 수
        self.skip_first = skip_first      # 통화 시작 직후 램프업 윈도우는 기준선에서 제외
        self.base_len = base_len          # 기준선 = 최근 '정상' 윈도우 base_len개의 중앙값
        self.rssi_weak_dbm = rssi_weak_dbm  # [가정] SCHEMA v1.1 초안 값
        self._seen = 0
        self._base = []
        self._recent = deque(maxlen=vote)   # 최근 원시 판정 (다수결로 1초 잡음 억제)
        self.last_signals = {}

    def update(self, f, rssi_dbm=None, seq_loss=None):
        """f: feature 1행(dict-like: l_num_bytes, l_num_pkts, t_q1, t_q2, t_std, t_max …).

        rssi_dbm: 오버레이 앱이 보낸 Wi-Fi 신호 세기 (없으면 None → weak_wifi 판정 안 함)
        seq_loss: RTP 순번 기반 손실률 (RTP를 볼 수 없으면 None → IP/UDP 규칙으로 손실 추정)
        """
        self._seen += 1
        x = {k: float(f[k]) for k in ("l_num_bytes", "l_num_pkts", "t_q1", "t_q2", "t_std", "t_max")}
        if self._seen <= self.skip_first:
            return "none", 0.0
        if len(self._base) < self.warmup:
            if x["l_num_pkts"] >= self.min_pkts:     # 영상이 본격적으로 흐를 때만 기준선에 넣음
                self._base.append(x)
            return "none", 0.0
        b = {k: float(np.median([w[k] for w in self._base])) for k in x}
        s = self.last_signals = {
            "r_bytes": x["l_num_bytes"] / max(b["l_num_bytes"], 1.0),
            "r_pkts": x["l_num_pkts"] / max(b["l_num_pkts"], 1.0),
            "d_q1": x["t_q1"] - b["t_q1"],
            "r_q1": (x["t_q1"] + 0.1) / (b["t_q1"] + 0.1),
            "d_q2": x["t_q2"] - b["t_q2"],
            "r_std": x["t_std"] / max(b["t_std"], 0.1),
            "d_max": x["t_max"] - b["t_max"],
            "seq_loss": seq_loss,
        }
        raw, strength = self._rules(s, rssi_dbm)
        if raw == "none" and self._healthy(s):
            # 손상 구간이 기준선에 섞이면 비율이 1로 수렴해 진단이 꺼진다 → 정상 범위 윈도우만 반영
            self._base = (self._base + [x])[-self.base_len:]
        self._recent.append((raw, strength))
        votes = Counter(c for c, _ in self._recent)
        cause, n = votes.most_common(1)[0]
        if cause == "none" or n < 2:
            return "none", round(votes["none"] / len(self._recent), 2)
        # 신뢰도 = 다수결 비율 × 해당 원인 규칙 강도 평균
        mean_strength = np.mean([st for c, st in self._recent if c == cause])
        return cause, round(float(n / len(self._recent) * mean_strength), 2)

    @staticmethod
    def _healthy(s):
        # 비트레이트 '상승'은 정상(Teams는 영상 시작 후 수십 초 동안 4배까지 오른다) → 하한만 둔다
        ok_seq = s["seq_loss"] is None or s["seq_loss"] < 0.01
        return ok_seq and s["r_bytes"] > 0.85 and s["d_q1"] < 2.0 and s["r_std"] < 1.3 and s["d_max"] < 15

    def _rules(self, s, rssi_dbm):
        """원시 판정 (원인, 강도 0–1). 순서가 우선순위다."""
        if rssi_dbm is not None and rssi_dbm <= self.rssi_weak_dbm:
            return "weak_wifi", min(1.0, 0.5 + (self.rssi_weak_dbm - rssi_dbm) / 20)
        if (s["d_q1"] >= 5 and s["r_bytes"] <= 0.9) or s["d_q1"] >= 12:
            return "bandwidth", min(1.0, s["d_q1"] / 20)
        # 지터 = FIFO에서 패킷이 몰렸다 풀림 → 짧은 간격(q1)이 붕괴 + 간격 편차·최대 간격 증가.
        if s["r_std"] >= 1.35 and s["d_q1"] <= -3:
            return "delay_jitter", min(1.0, (s["r_std"] - 1) / 1.5)
        # q1이 원래 1ms 남짓인 앱(Teams)은 비율로 몰림을 본다. 단 송신 방식 변화(패킷 급증)로도 q1이
        # 0이 되므로(Teams dev에서 확인) 최대 간격이 크게 늘었을 때만 지터로 본다.
        if s["r_q1"] <= 0.3 and s["d_max"] >= 40:
            return "delay_jitter", min(1.0, s["d_max"] / 100)
        # 지터는 순번 빈칸을 만들지 않으므로, RTP가 보이면 빈칸 검사를 '간격 큼' 지터 규칙보다 먼저 한다
        if s["seq_loss"] is not None and s["seq_loss"] >= 0.015:
            return "loss", min(1.0, 0.5 + s["seq_loss"] * 5)
        if s["r_std"] >= 1.8 and s["d_max"] >= 30:
            return "delay_jitter", min(1.0, (s["r_std"] - 1) / 1.5)
        if s["seq_loss"] is not None:                     # RTP 순번이 보이고 빈칸이 없으면 손실 아님
            return "none", 1.0
        if s["d_q1"] > -3 and (s["r_pkts"] <= 0.9 or (s["d_max"] >= 20 and s["r_std"] >= 1.1)):
            return "loss", min(1.0, max(1 - s["r_pkts"], s["d_max"] / 60))
        return "none", 1.0
