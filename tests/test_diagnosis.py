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
