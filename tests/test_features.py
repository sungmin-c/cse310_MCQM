"""server/features.py 스트리밍 결과가 vcaml 배치(ip-udp-ml 경로)와 같은지 검사한다.

in-lab 데이터(data/in_lab_data, 솔로 자료 junction)가 없으면 데이터 의존 테스트는 skip된다.
"""
import glob
import os
from pathlib import Path

import pandas as pd
import pytest

from server.features import WindowFeatures, stream_csv
from vcaml.config import project_config
from vcaml.feature_extraction import FeatureExtractor
from vcaml.pipeline.net_utils import readIpUdpFile, renameNetColumns

DATA = Path(__file__).parents[1] / "data" / "in_lab_data"
N_PER_VCA = 5


def batch_features(csv, vca):
    """vcaml IP_UDP_ML._loadAndPrepareFile + extract_features와 같은 경로."""
    df = readIpUdpFile(csv)
    dst = df["ip.dst"].iloc[0]
    df = renameNetColumns(df).sort_values("time_normed")[["length", "time", "time_normed"]]
    fe = FeatureExtractor(["LSTATS", "TSTATS"], project_config, vca, "in_lab_data")
    return fe.extract_features(df), dst


def sample_files():
    if not DATA.exists():
        return []
    out = []
    dirs = sorted(os.listdir(DATA))
    for vca in ("meet", "teams", "webex"):
        picked = 0
        for d in dirs:
            if f"_{vca}_" not in d:
                continue
            csvs = glob.glob(str(DATA / d / "*.csv"))
            if csvs and readIpUdpFile(csvs[0]) is not None:
                out.append((vca, csvs[0]))
                picked += 1
            if picked == N_PER_VCA:
                break
    return out


@pytest.mark.parametrize("vca,csv", sample_files() or [pytest.param(None, None, marks=pytest.mark.skip("no in-lab data"))])
def test_streaming_equals_vcaml_batch(vca, csv):
    batch, dst = batch_features(csv, vca)
    stream = stream_csv(csv, vca=vca, dst_ip=dst)
    assert len(stream) == len(batch)
    pd.testing.assert_frame_equal(
        stream[sorted(stream.columns)].reset_index(drop=True),
        batch[sorted(batch.columns)].reset_index(drop=True),
        check_dtype=False, rtol=1e-9, atol=1e-9)


def test_window_boundary_rule():
    """경계 규칙 단위 테스트 (데이터 불필요): 시작+1s '초과' 패킷이 새 윈도우를 연다."""
    wf = WindowFeatures(dst_ip="A")
    pkt = lambda t: wf.push(1000.0 + t, t, "A", 17, 1000)
    assert pkt(0.5) is None
    assert pkt(1.0) is None
    assert pkt(1.5) is None          # 1.5 - 0.5 = 1.0 → 초과 아님, 같은 윈도우
    w = pkt(1.6)                     # 1.1 > 1.0 → 첫 윈도우 닫힘
    assert w is not None and w["l_num_pkts"].iloc[0] == 3 and w["et"].iloc[0] == 1001
    assert w["t_max"].iloc[0] == pytest.approx(500.0)   # 첫 IAT = 캡처 시작부터 0.5s
    last = wf.flush()
    assert last["l_num_pkts"].iloc[0] == 1
    assert last["t_mean"].iloc[0] == pytest.approx(100.0)  # 직전 패킷(1.5)과의 간격


def test_filters_drop_non_video_packets():
    wf = WindowFeatures(dst_ip="A")
    assert wf.push(1.0, 0.1, "A", 6, 1000) is None       # TCP
    assert wf.push(1.0, 0.2, "B", 17, 1000) is None      # 다른 dst
    assert wf.push(1.0, 0.3, "A", 17, 306) is None       # 306 이하 = 영상 아님
    assert wf.flush() is None
