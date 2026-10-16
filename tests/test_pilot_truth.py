"""compare와 WS Replay의 공통 PeerConnection 선택 규칙."""
import json

import pandas as pd

from scripts.pilot_live import select_truth
from vcaml.io import webrtc_reader


def test_select_truth_counts_active_seconds_inside_capture(tmp_path, monkeypatch):
    frames = {
        "old": [(90, 30), (91, 30), (100, 0), (101, 0)],
        "duplicate": [(100, 30), (100, 30), (100, 30)],
        "new/pc": [(100, 25), (101, 25), (102, 0)],
    }
    dump = tmp_path / "dump.json"
    dump.write_text(json.dumps({"PeerConnections": {pc: {} for pc in frames}}), encoding="utf-8")

    class Reader:
        def __init__(self, path, dataset):
            self.path = path
            assert dataset == "in_lab_data"

        def get_webrtc(self):
            with open(self.path, encoding="utf-8") as f:
                pc = next(iter(json.load(f)["PeerConnections"]))
            return pd.DataFrame(frames[pc], columns=["ts", "framesReceivedPerSecond"])

    monkeypatch.setattr(webrtc_reader, "WebRTCReader", Reader)
    truth = select_truth(dump, [100, 101, 102])
    assert truth["framesReceivedPerSecond"].tolist() == [25, 25, 0]
    assert truth["ts"].tolist() == [100, 101, 102]


def test_select_truth_empty_dump_returns_empty_frame(tmp_path):
    dump = tmp_path / "empty.json"
    dump.write_text('{"PeerConnections": {}}', encoding="utf-8")
    assert select_truth(dump, [100]).empty
