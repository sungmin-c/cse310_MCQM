"""server/impair.py: 손실률 통계, seed 재현성, 분할 적용 일관성, 지연·대역폭 동작, 1 tick 성능."""
import time

import numpy as np
import pytest

from server.impair import Impairer, ImpairParams, impair


def trace(n=200_000, gap=0.002, size=1000):
    return np.arange(n) * gap, np.full(n, float(size))


def test_no_params_is_identity():
    t, s = trace(1000)
    idx, out = impair(t, s)
    assert np.array_equal(idx, np.arange(1000)) and np.array_equal(out, t)


def test_bernoulli_loss_rate():
    t, s = trace()
    idx, _ = impair(t, s, loss_pct=5, seed=1)
    assert 1 - len(idx) / len(t) == pytest.approx(0.05, abs=0.003)


def test_gilbert_loss_rate_and_burst_length():
    t, s = trace()
    idx, _ = impair(t, s, loss_pct=5, burst_len=4, seed=2)
    lost = np.ones(len(t), dtype=bool)
    lost[idx] = False
    assert lost.mean() == pytest.approx(0.05, abs=0.01)
    # 연속 손실 구간 평균 길이
    edges = np.diff(np.r_[0, lost.astype(int), 0])
    runs = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
    assert runs.mean() == pytest.approx(4.0, rel=0.1)


def test_seed_reproducible_and_seed_sensitive():
    t, s = trace(5000)
    kw = dict(loss_pct=10, jitter_ms=20, delay_ms=50)
    a, b, c = impair(t, s, seed=7, **kw), impair(t, s, seed=7, **kw), impair(t, s, seed=8, **kw)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
    assert not np.array_equal(a[0], c[0])


def test_chunked_equals_whole():
    t, s = trace(20_000)
    p = ImpairParams(loss_pct=5, burst_len=3, delay_ms=80, jitter_ms=15, bw_kbps=3000)
    whole = Impairer(p, seed=3).apply(t, s)
    imp = Impairer(p, seed=3)
    parts = [imp.apply(t[i:i + 500], s[i:i + 500]) for i in range(0, len(t), 500)]
    idx = np.concatenate([pi + i for (pi, _), i in zip(parts, range(0, len(t), 500))])
    out = np.concatenate([po for _, po in parts])
    assert np.array_equal(idx, whole[0]) and np.allclose(out, whole[1])


def test_constant_delay_shifts_exactly():
    t, s = trace(1000)
    idx, out = impair(t, s, delay_ms=120)
    assert np.allclose(out - t[idx], 0.120)


def test_jitter_is_fifo_and_has_expected_spread():
    t, s = trace(5000, gap=1.0)          # 간격이 지터보다 훨씬 커서 FIFO가 거의 개입하지 않음
    idx, out = impair(t, s, delay_ms=100, jitter_ms=20, seed=4)
    assert np.all(np.diff(out) >= 0)
    extra = out - t[idx]
    assert extra.mean() == pytest.approx(0.100, abs=0.002)
    assert extra.std() == pytest.approx(0.020, abs=0.002)


def test_bandwidth_caps_throughput_and_queue():
    t, s = trace(50_000, gap=0.002, size=1000)   # 제공 부하 4 Mbps
    idx, out = impair(t, s, bw_kbps=2000)          # 병목 2 Mbps
    dur = out[-1] - out[0]
    kbps = s[idx].sum() * 8 / dur / 1000
    assert kbps == pytest.approx(2000, rel=0.03)
    assert (out - t[idx]).max() <= 0.200 + 1e-9    # 대기 한도
    assert 1 - len(idx) / len(t) == pytest.approx(0.5, abs=0.03)


def test_bandwidth_under_capacity_no_drop():
    t, s = trace(10_000, gap=0.01, size=1000)     # 0.8 Mbps
    idx, out = impair(t, s, bw_kbps=2000)
    assert len(idx) == len(t) and (out - t).max() < 0.005


def test_one_tick_is_fast():
    t, s = trace(1000, gap=0.001)                  # 1초 분량 1000패킷 (영상통화보다 많게)
    imp = Impairer(ImpairParams(loss_pct=5, burst_len=3, delay_ms=100, jitter_ms=30, bw_kbps=1000), seed=0)
    t0 = time.perf_counter()
    imp.apply(t, s)
    assert time.perf_counter() - t0 < 0.05
