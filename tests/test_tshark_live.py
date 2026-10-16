"""tshark 실행·data/ 접근 없이 합성 라인으로 실시간 추정 경로를 검증한다."""
import csv
import io
from types import SimpleNamespace

import pandas as pd
import pytest

from capture.tshark_live import FIELDS, METRICS, parse, process_lines
from capture import tshark_live


def packet(rel=0.5, *, dst="A", proto="17", ulen="1000"):
    return [str(rel), str(1000 + rel), "sender", dst, proto, "1028",
            "5000", "5001", ulen, "123", "456", "1", "96", "0"]


def line(rel=0.5, **kwargs):
    return "\t".join(packet(rel, **kwargs)) + "\n"


class FakeModel:
    def __init__(self, value, columns):
        self.value = value
        self.columns = columns
        self.calls = []

    def predict(self, frame):
        assert list(frame.columns) == self.columns
        self.calls.append(frame.copy())
        return [self.value]


def fake_models(columns):
    return {metric: (FakeModel(i + 0.12345, columns), columns)
            for i, metric in enumerate(METRICS)}


@pytest.mark.parametrize("field,value", [(4, ""), (4, "17,17"), (3, ""), (3, "A,B")])
def test_parse_rejects_missing_or_multiple_proto_and_dst(field, value):
    fields = packet()
    fields[field] = value
    assert parse(fields) is None


@pytest.mark.parametrize("ulen,expected", [("1000", 1000.0), ("", 0.0), ("1000,900", 0.0)])
def test_parse_converts_fields_and_udp_length(ulen, expected):
    assert parse(packet(1.25, ulen=ulen)) == (1001.25, 1.25, "A", 17, expected)


def test_process_lines_filters_packets_and_flushes_partial_window():
    models = fake_models(["l_num_pkts", "et"])
    emitted = []
    output = io.StringIO(newline="")
    lines = ["too\tshort\n", line(dst=""), line(proto="17,17"),
             line(proto="6"), line(dst="B"), line(ulen=""),
             line(ulen="1000,900"), line(ulen="306"),
             line(0.5), line(1.0), line(1.5), line(1.6)]

    process_lines(iter(lines), models, emitted.append, dst_ip="A",
                  packet_writer=csv.writer(output))

    # 경계는 첫 패킷 + 1초를 초과할 때 닫히고, 마지막 1개도 종료 때 추정한다.
    assert [(row["et"], row["n_pkts"]) for row in emitted] == [(1001, 3), (1001, 1)]
    for row in emitted:
        assert set(row) == {"et", "n_pkts", "tick_ms", *METRICS}
        assert type(row["et"]) is int and type(row["n_pkts"]) is int
        assert isinstance(row["tick_ms"], float) and row["tick_ms"] >= 0
        for i, metric in enumerate(METRICS):
            assert type(row[metric]) is float
            assert row[metric] == i + 0.12345  # 콜백은 CSV용 반올림 전 값을 받는다.
    for model, _ in models.values():
        assert [frame["l_num_pkts"].iloc[0] for frame in model.calls] == [3, 1]

    # 충분한 필드가 있으면 parse/영상 필터 전에 원래 패킷을 그대로 기록한다.
    recorded = list(csv.reader(io.StringIO(output.getvalue())))
    assert recorded == [entry.rstrip("\n").split("\t") for entry in lines[1:]]
    assert all(len(row) == len(FIELDS) for row in recorded)


class FakeWindow:
    def __init__(self, final=None):
        self.final = final
        self.packets = []
        self.flush_calls = 0

    def push(self, *parsed):
        self.packets.append(parsed)
        return None

    def flush(self):
        self.flush_calls += 1
        return self.final


def test_process_lines_empty_stream_flushes_once_without_predictions():
    wf = FakeWindow()
    models = fake_models(["et"])
    emitted = []

    process_lines([], models, emitted.append, window_features=wf)

    assert wf.flush_calls == 1
    assert wf.packets == [] and emitted == []
    assert all(model.calls == [] for model, _ in models.values())


def test_process_lines_keyboard_interrupt_flushes_once_with_ordered_features():
    # 모델 학습 때의 열 순서는 feature 표의 저장 순서와 다를 수 있다.
    final = pd.DataFrame([{"first": 1.0, "et": 1000.9, "l_num_pkts": 1, "second": 2.0}])
    wf = FakeWindow(final)
    models = fake_models(["second", "first"])
    emitted = []

    def interrupted():
        yield line()
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        process_lines(interrupted(), models, emitted.append, window_features=wf)

    assert wf.flush_calls == 1
    assert wf.packets == [parse(packet())]
    assert len(emitted) == 1 and emitted[0]["et"] == 1000
    for model, _ in models.values():
        assert len(model.calls) == 1
        assert model.calls[0].iloc[0].tolist() == [2.0, 1.0]


def test_capture_preserves_csv_format_and_tshark_arguments(tmp_path, monkeypatch):
    class FakeProcess:
        stdout = io.StringIO(line(0.5) + line(1.6))

        def __init__(self):
            self.terminated = 0

        def terminate(self):
            self.terminated += 1

    process = FakeProcess()
    launches = []

    def popen(argv, **kwargs):
        launches.append((argv, kwargs))
        return process

    models = fake_models(["l_num_pkts"])
    ticks = iter([0.0, 0.001234, 1.0, 1.002345])
    monkeypatch.setattr(tshark_live, "OUT", tmp_path)
    monkeypatch.setattr(tshark_live, "load_models", lambda: models)
    monkeypatch.setattr(tshark_live, "tshark_path", lambda: "fake-tshark")
    monkeypatch.setattr(tshark_live.subprocess, "Popen", popen)
    monkeypatch.setattr(tshark_live, "time", SimpleNamespace(
        perf_counter=lambda: next(ticks), strftime=tshark_live.time.strftime))

    tshark_live.capture(SimpleNamespace(name="sample", iface="test-iface", duration=2,
                                       dst="A", no_os=True))

    header = ["frame.time_relative", "frame.time_epoch", "ip.src", "ip.dst", "ip.proto", "ip.len",
              "udp.srcport", "udp.dstport", "udp.length", "rtp.ssrc", "rtp.timestamp", "rtp.seq",
              "rtp.p_type", "rtp.marker"]
    with (tmp_path / "sample_pkts.csv").open(newline="") as f:
        assert list(csv.reader(f)) == [header, packet(0.5), packet(1.6)]
    with (tmp_path / "sample_est.csv").open(newline="") as f:
        assert list(csv.reader(f)) == [
            ["et", "n_pkts", "fps", "bitrate", "frame_jitter", "frameHeight", "tick_ms"],
            ["1001", "1", "0.12", "1.12", "2.12", "3.12", "1.2"],
            ["1001", "1", "0.12", "1.12", "2.12", "3.12", "2.3"],
        ]
    expected_argv = ["fake-tshark", "-i", "test-iface", "-p", "-f", "udp", "-l", "-n",
                     "-d", "udp.port==1024-49152,rtp", "--enable-heuristic", "rtp_udp",
                     "-T", "fields", "-E", "separator=/t"]
    for field in header:
        expected_argv += ["-e", field]
    expected_argv += ["-a", "duration:2"]
    assert launches == [(expected_argv, {"stdout": tshark_live.subprocess.PIPE,
                                        "stderr": tshark_live.subprocess.DEVNULL, "text": True})]
    assert process.terminated == 1
    assert {path.name for path in tmp_path.iterdir()} == {"sample_pkts.csv", "sample_est.csv"}
