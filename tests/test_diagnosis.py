"""server/diagnosis.py 규칙 단위 테스트 (데이터 불필요) + RtpSeqLoss."""
import pytest

from server.diagnosis import CAUSES, Diagnoser
from server.features import RtpSeqLoss

BASE = dict(l_num_bytes=20000, l_num_pkts=30, t_q1=20.0, t_q2=33.0, t_std=10.0, t_max=60.0)


def warm(d, n=12):
    for _ in range(n):
        d.update(BASE)


def run(d, f, n=3, **kw):
    out = None
    for _ in range(n):
        out = d.update(f, **kw)
    return out


def test_warmup_returns_none():
    d = Diagnoser()
    assert all(d.update(BASE)[0] == "none" for _ in range(10))


def test_steady_call_is_none():
    d = Diagnoser()
    warm(d)
    assert run(d, BASE)[0] == "none"


def test_bandwidth_signature():
    d = Diagnoser()
    warm(d)
    cause, conf = run(d, dict(BASE, l_num_bytes=9000, l_num_pkts=15, t_q1=45.0, t_q2=60.0))
    assert cause == "bandwidth" and 0 < conf <= 1


def test_jitter_signature():
    d = Diagnoser()
    warm(d)
    cause, _ = run(d, dict(BASE, t_q1=2.0, t_q2=20.0, t_std=25.0, t_max=150.0))
    assert cause == "delay_jitter"


def test_loss_from_rtp_sequence_gaps():
    d = Diagnoser()
    warm(d)
    assert run(d, BASE, seq_loss=0.05)[0] == "loss"
    d2 = Diagnoser()
    warm(d2)
    assert run(d2, BASE, seq_loss=0.0)[0] == "none"


def test_loss_from_ipudp_when_no_rtp():
    d = Diagnoser()
    warm(d)
    assert run(d, dict(BASE, l_num_bytes=17000, l_num_pkts=25))[0] == "loss"


def test_weak_wifi_has_priority():
    d = Diagnoser()
    warm(d)
    assert run(d, BASE, rssi_dbm=-82)[0] == "weak_wifi"
    d2 = Diagnoser()
    warm(d2)
    assert run(d2, BASE, rssi_dbm=-60)[0] == "none"


def test_single_spike_is_suppressed_by_vote():
    d = Diagnoser()
    warm(d)
    spike = dict(BASE, l_num_bytes=9000, t_q1=45.0)
    assert d.update(spike)[0] == "none"      # 1/3 표 → none
    assert d.update(BASE)[0] == "none"


def test_impaired_windows_do_not_poison_baseline():
    d = Diagnoser()
    warm(d)
    bw = dict(BASE, l_num_bytes=9000, l_num_pkts=15, t_q1=45.0)
    for _ in range(30):                       # 기준선 길이(20)보다 오래 손상
        cause, _ = d.update(bw)
    assert cause == "bandwidth"


def test_bitrate_rampup_updates_baseline():
    """Teams처럼 영상 시작 후 비트레이트가 몇 배로 오르는 것은 저하가 아니다 → 기준선이 따라가야 한다."""
    d = Diagnoser()
    warm(d)
    high = dict(BASE, l_num_bytes=80000, l_num_pkts=120)
    for _ in range(25):
        d.update(high)
    # 이제 기준선이 high → 20% 감소는 bandwidth/loss 신호가 아니어야 하고, 원래 BASE로 떨어지면 감지돼야 함
    assert d.update(dict(high, l_num_bytes=76000))[0] == "none"
    assert run(d, dict(BASE, t_q1=45.0))[0] == "bandwidth"


def test_jitter_ratio_rule_for_small_q1_apps():
    """q1이 원래 1ms 남짓인 앱: q1이 0으로 붕괴 + 최대 간격 크게 증가 → 지터."""
    base = dict(BASE, t_q1=1.3, t_q2=1.4, t_std=8.0, t_max=44.0)
    d = Diagnoser()
    for _ in range(12):
        d.update(base)
    assert run(d, dict(base, t_q1=0.0, t_q2=0.0, t_max=120.0))[0] == "delay_jitter"
    d2 = Diagnoser()
    for _ in range(12):
        d2.update(base)
    assert run(d2, dict(base, t_q1=0.0, t_q2=0.0, t_max=55.0))[0] == "none"   # 몰림만으론 지터 아님


def test_outputs_are_schema_values():
    d = Diagnoser()
    warm(d)
    cause, conf = d.update(BASE)
    assert cause in CAUSES and 0 <= conf <= 1


def test_rtp_seq_loss_counts_gaps_and_wraps():
    s = RtpSeqLoss()
    for q in [1, 2, 3, 5, 6, 10]:             # 빠진 것: 4, 7, 8, 9 → 4 / (6+4)
        s.push("A", q)
    assert s.take() == pytest.approx(0.4)
    for q in [65534, 65535, 0, 1]:            # 순번 한 바퀴 → 빈칸 아님
        s.push("B", q)
    assert s.take() == pytest.approx(0.0)
    s.push("A", 9)                            # 뒤바뀐(이전) 순번은 무시
    assert s.take() is None


@pytest.mark.parametrize("device", [None, {}, {"cpu_pct": 100}, {"call_core_pct": None}])
def test_missing_core_util_never_reports_device_cpu(device):
    d = Diagnoser()
    warm(d)
    assert run(d, BASE, device=device)[0] == "none"
    assert d.last_signals["call_core_pct"] is None


@pytest.mark.parametrize("util, expected", [(84.9, "none"), (85.0, "device_cpu"), (95, "device_cpu"), (150, "device_cpu")])
def test_device_cpu_threshold_and_confidence(util, expected):
    d = Diagnoser()
    warm(d)
    cause, conf = run(d, BASE, device={"call_core_pct": util})
    assert cause == expected and cause in CAUSES and 0 < conf <= 1
    assert d.last_signals["call_core_pct"] == util


@pytest.mark.parametrize("features, seq_loss, expected", [
    (dict(BASE, l_num_bytes=9000, t_q1=45.0), None, "bandwidth"),
    (BASE, 0.05, "loss"),
    (dict(BASE, t_q1=2.0, t_std=25.0, t_max=150.0), None, "delay_jitter"),
    (dict(BASE, t_std=20.0, t_max=100.0), None, "delay_jitter"),
    (dict(BASE, l_num_bytes=17000, l_num_pkts=25), None, "device_cpu"),
    (BASE, 0.0, "device_cpu"),
])
def test_device_cpu_rule_priority(features, seq_loss, expected):
    d = Diagnoser()
    warm(d)
    assert run(d, features, seq_loss=seq_loss, device={"call_core_pct": 95})[0] == expected


def test_single_device_cpu_spike_is_suppressed():
    d = Diagnoser()
    warm(d)
    assert d.update(BASE, device={"call_core_pct": 95})[0] == "none"
    assert d.update(BASE)[0] == "none"


def test_healthy_cpu_windows_update_baseline():
    d = Diagnoser()
    warm(d)
    high = dict(BASE, l_num_bytes=80000, l_num_pkts=120)
    run(d, high, n=25, device={"call_core_pct": 95})
    assert d.update(high)[0] == "none"
    assert d.last_signals["r_bytes"] == 1.0
    assert d.last_signals["r_pkts"] == 1.0


@pytest.mark.parametrize("device", [None, {}, {"cpu_pct": 100}, {"call_core_pct": None}])
def test_missing_core_util_suppresses_stale_cpu_votes(device):
    d = Diagnoser()
    warm(d)
    assert run(d, BASE, device={"call_core_pct": 95})[0] == "device_cpu"
    assert d.update(BASE, device=device)[0] == "none"


def test_flow_change_restarts_skip_warmup_and_votes():
    d = Diagnoser()
    run(d, BASE, n=12, flow=("A", 1000))
    assert run(d, BASE, flow=("A", 1000), seq_loss=0.05)[0] == "loss"
    other = dict(BASE, l_num_bytes=48000, l_num_pkts=72, t_q1=8.0, t_std=25.0, t_max=120.0)
    d.update(other, flow=("B", 2000))
    assert d.update(other, flow=("B", 2000)) == ("none", 0.0)
    assert d._base == [] and not d._recent and d.last_signals == {}
    assert d._seen == 1
    for _ in range(d.skip_first + d.warmup - 1):
        assert d.update(other, flow=("B", 2000)) == ("none", 0.0)
    assert run(d, other, n=5, flow=("B", 2000))[0] == "none"
    assert d.last_signals["r_bytes"] == 1.0


def test_single_flow_spike_keeps_baseline():
    d = Diagnoser()
    run(d, BASE, n=12, flow=("A", 1000))
    d.update(BASE, flow=("B", 2000))
    d.update(BASE, flow=("A", 1000))
    assert d._seen == 14 and len(d._base) >= d.warmup
    assert d._flow == ("A", 1000)


def test_missing_flow_breaks_consecutive_change_detection():
    d = Diagnoser()
    run(d, BASE, n=12, flow=("A", 1000))
    d.update(BASE, flow=("B", 2000))
    d.update(BASE, flow=None)
    d.update(BASE, flow=("B", 2000))
    assert d._seen == 15 and d._flow == ("A", 1000)
    assert d.update(BASE, flow=("B", 2000)) == ("none", 0.0)
    assert d._flow == ("B", 2000)


def test_distinct_flow_candidates_do_not_reset_baseline():
    d = Diagnoser()
    run(d, BASE, n=12, flow=("A", 1000))
    d.update(BASE, flow=("B", 2000))
    d.update(BASE, flow=("C", 3000))
    assert d._seen == 14 and d._flow == ("A", 1000)
