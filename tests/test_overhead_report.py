"""합성 csv로 단계 집계·통과 판정·RSS 기울기를 검증한다 (실측 데이터·psutil 불필요)."""
import pandas as pd

from scripts import overhead_report as r


def make():
    # 끔 60초 + 켬 60초. 켬 단계 앞 15초는 버려지므로 거기에 이상값(99%)을 넣어 두었다.
    phase = pd.DataFrame({"ts": [0, 60, 120, 121], "phase": ["off", "on", "end", "end"]})
    ts = list(range(121))
    mem = pd.DataFrame({"ts": ts, "monitor_cpu_pct": [0.0] * 60 + [99.0] * 15 + [2.0] * 46,
                        "monitor_rss_mb": [0.0] * 60 + [100 + 0.5 * (t - 60) for t in range(60, 121)]})
    dump = pd.DataFrame({"ts": ts, "dec_fps": 28.0, "freeze": 0.0, "decode_ms": 6.0,
                         "send_fps": [29.0] * 60 + [27.5] * 61})
    return phase, {"mem": mem, "dump": dump}


def test_aggregate_skips_warmup_and_compares_with_off():
    phase, tables = make()
    means, _ = r.aggregate(phase, tables, skip=15)
    assert means.loc["on", "monitor_cpu_pct"] == 2.0          # 앞 15초(99%)는 제외
    ok = {label: res for label, _, res in r.verdicts(means)}
    assert ok["on: 모니터 CPU% < 5"] is True
    assert ok["on: Δ수신 fps < 1"] is True
    assert ok["on: Δ송신 fps < 1"] is False                  # 29 → 27.5
    assert ok["on: ΔPages/s ≤ 0"] is None                     # perf 자료 없음은 판정 불가


def test_rss_slope_flags_leak():
    phase, tables = make()
    slope = r.rss_slope_mb_per_min(tables["mem"], phase, skip=15)
    assert abs(slope - 30.0) < 0.5                            # 초당 0.5MB = 30MB/분
