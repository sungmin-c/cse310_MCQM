"""실측 자료 없이 W3 라벨·분리·OS 정렬·평가 CLI를 확인한다."""
import csv
import json
from datetime import datetime, timezone

import pytest

from capture.tshark_live import FIELDS
from scripts import diag_eval


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)


@pytest.mark.parametrize("ts,expected", [
    (149, None), (150, "none"), (209, "none"), (210, None),
    (212, None), (213, "device_cpu"), (300, "device_cpu"),
    (301, None), (329, None), (330, "none"), (381, None),
])
def test_label_boundaries(ts, expected):
    call = dict(call_id="01", cond="C2", t0="0", impair_on="210", impair_off="300")
    assert diag_eval.window_label(ts, call) == expected
    if ts >= 150 and ts <= 380:
        assert diag_eval.window_label(ts, dict(call, cond="N0")) == "none"


def test_cli_synthetic_cpu_and_packet_only(tmp_path, capsys):
    log = tmp_path / "log.csv"
    write_csv(log, ["call_id", "cond", "t0", "impair_on", "impair_off", "status"],
              [("01", "C2", 1000, 1170, 1200, "ok"), ("02", "C2", 2000, 2170, 2200, "no_truth")])
    for call_id, t0 in [("01", 1000), ("02", 2000)]:
        packets = []
        for i in range(1500, 2200):
            rel = i / 10
            packets.append([rel, t0 + rel, "sender", "receiver", 17, 1028,
                            5000, 5001, 1000, "123", 100, i, 96, 0])
        write_csv(tmp_path / f"w3_{call_id}_pkts.csv", FIELDS, packets)
        write_csv(tmp_path / f"w3_{call_id}_os.csv", ["ts", "cpu_pct", "call_core_pct"],
                  [(t0 + t, 25, 95 if 170 <= t <= 200 else 20) for t in range(150, 221)])
    args = ["--log", str(log), "--packets-dir", str(tmp_path), "--dump-dir", str(tmp_path),
            "--out", str(tmp_path / "out")]
    report = diag_eval.main(args)
    assert report["calls"] == ["02"] and report["windows_scored"] > 20
    assert report["recall"]["device_cpu"] == 1
    assert report["precision"]["device_cpu"] == 1
    assert report["effect_cpu_recall"] is None
    packet_only = diag_eval.main(args + ["--no-device"])
    assert packet_only["calls"] == report["calls"]
    assert packet_only["windows_scored"] == report["windows_scored"]
    assert packet_only["recall"]["device_cpu"] == 0
    assert packet_only["confusion_matrix"]["device_cpu"]["none"] > 0
    assert json.loads((tmp_path / "out/test_device.json").read_text())["calls"] == ["02"]
    assert (tmp_path / "out/test_packet_only_windows.csv").exists()
    capsys.readouterr()


def test_os_freshness_and_missing_column(tmp_path, monkeypatch):
    path, os_path = tmp_path / "pkts.csv", tmp_path / "os.csv"
    packets = [[i / 10, 1000 + i / 10, "sender", "receiver", 17, 1028,
                5000, 5001, 1000, "123", 100, i, 96, 0] for i in range(45)]
    write_csv(path, FIELDS, packets)
    write_csv(os_path, ["ts", "call_core_pct"], [(1001, 95), (1004, 20)])
    seen = []

    class SpyDiagnoser:
        last_signals = {"ready": True}

        def update(self, features, **kwargs):
            seen.append(kwargs)
            return "none", 1.0

    monkeypatch.setattr(diag_eval, "Diagnoser", SpyDiagnoser)
    windows = diag_eval.run_call(path, os_path)
    for w, item in zip(windows, seen):
        if w["et"] < 1004:
            assert item["device"] == ({"call_core_pct": 95.0} if 0 <= w["et"] - 1001 <= 2 else None)
        else:
            assert item["device"] == {"call_core_pct": 20.0}
        assert item["flow"] == ("sender", 5000)
        assert item["seq_loss"] == 0
    write_csv(os_path, ["ts", "cpu_pct"], [(1001, 95)])
    seen.clear()
    diag_eval.run_call(path, os_path)
    assert all(r["device"] is None for r in seen)


def test_effects_selects_active_pc_and_uses_deltas(tmp_path):
    def stat(values):
        return {"startTime": datetime.fromtimestamp(1000, timezone.utc).isoformat(),
                "endTime": datetime.fromtimestamp(1004, timezone.utc).isoformat(),
                "values": str(values)}

    active = {"IT01V1-framesPerSecond": stat([30, 30, 30, 30]),
              "IT01V1-[framesReceived/s]": stat([30, 30, 30, 30]),
              "IT01V1-framesDecoded": stat([0, 30, 60, 90]),
              "IT01V1-totalDecodeTime": stat([0, 0.03, 0.06, 0.15]),
              "IT01V1-freezeCount": stat([0, 0, 0, 1]),
              "OT01V2-framesPerSecond": stat([30, 30, 30, 10])}
    inactive = dict(active, **{"IT01V1-[framesReceived/s]": stat([0, 0, 0, 0])})
    dump = tmp_path / "dump.json"
    dump.write_text(json.dumps({"PeerConnections": {"old": {"stats": inactive},
                                                    "current": {"stats": active}}}), encoding="utf-8")
    call = dict(call_id="01", cond="C2", t0="850", impair_on="1003", impair_off="1010")
    result = diag_eval.effects(dump, [1001, 1002, 1003, 1005], call)
    assert result == {1001: False, 1002: False, 1003: True, 1005: None}


def test_summary_counts_legacy_causes_as_false_positives_and_missed_calls():
    rows = [dict(et=150, truth="none", pred="weak_wifi", ready=True,
                 call_id="01", target="loss", on=210, off=300, effect=None),
            dict(et=213, truth="loss", pred="delay_jitter", ready=True,
                 call_id="01", target="loss", on=210, off=300, effect=None)]
    report = diag_eval.summarize(rows)
    assert report["none_false_positive_rate"] == 1
    assert report["recall"]["loss"] == 0
    assert report["latency_median_s"]["loss"] is None


def test_rewarmup_windows_still_count_as_false_negatives():
    report = diag_eval.summarize([dict(et=213, truth="device_cpu", pred="none", ready=False,
                                      call_id="01", target="device_cpu", on=210, off=300, effect=None)])
    assert report["windows_scored"] == 1
    assert report["recall"]["device_cpu"] == 0
