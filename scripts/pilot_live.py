"""W1 파일럿 P1–P3 — 노트북이 받는 통화 패킷을 tshark로 실시간 읽어 1초마다 추정하고, webrtc-internals 정답과 비교한다.

capture: tshark(-i 인터페이스, UDP만) → server.features.WindowFeatures → Meet 모델 4개 → 1초마다 한 줄 출력
         + psutil 1 Hz: 전체 CPU%, 통화 프로세스(chrome/Zoom) CPU%, 모니터 자신(tshark+python) CPU%
         산출물 data/pilot/<name>_pkts.csv (vcaml 14필드 형식), _est.csv, _os.csv
캡처 구현: capture.tshark_live (라인 스트림 → 추정 콜백을 서버에서 재사용 가능).
compare: _est.csv ↔ webrtc-internals dump(vcaml WebRTCReader)를 초(et == ts)로 맞춰 MAE 등 계산 → _cmp.csv, _summary.json

실행 (repo 루트):
  uv run --with psutil python scripts/pilot_live.py ifaces
  uv run --with psutil python scripts/pilot_live.py capture --name p1_meet1 --iface Wi-Fi --duration 200
  uv run python scripts/pilot_live.py compare --name p1_meet1 --dump "%USERPROFILE%\\Downloads\\webrtc_internals_dump.txt"

내 노트북 자신의 트래픽만 캡처한다 (프로미스큐어스 모드 끔 -p).
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from capture.tshark_live import METRICS, OUT, capture, tshark_path  # noqa: E402


def compare(a):
    import numpy as np
    import pandas as pd
    from vcaml.io.webrtc_reader import WebRTCReader

    est = pd.read_csv(OUT / f"{a.name}_est.csv")
    # Meet는 통화 중 PeerConnection을 갈아탄다(P2P↔서버 [추정]). WebRTCReader는 첫 PC만 읽으므로
    # PC마다 따로 읽어 캡처 구간에서 fps > 0인 초가 가장 많은 PC를 고른다
    raw = json.load(open(a.dump, encoding="utf-8"))
    best, best_n = pd.DataFrame(), -1
    with tempfile.TemporaryDirectory() as td:
        for pc, conn in raw["PeerConnections"].items():
            p = Path(td) / f"{pc}.json"
            p.write_text(json.dumps({"PeerConnections": {pc: conn}}), encoding="utf-8")
            t = WebRTCReader(str(p), "in_lab_data").get_webrtc()
            if t.empty:
                continue
            n = int(((t["framesReceivedPerSecond"] > 0) & t["ts"].isin(est["et"])).sum())
            print(f"PC {pc}: 캡처 구간 fps>0 {n}초")
            if n > best_n:
                best, best_n = t, n
    truth = best
    if truth.empty:
        sys.exit("정답 파싱 실패: dump에 IT01V(inbound video) 통계가 없다 — Chrome 통계 ID 형식 확인 필요")
    truth = truth[["ts", *METRICS.values()]]

    def merged(lag):
        t = truth.assign(ts=truth["ts"] - lag)
        return pd.merge(est, t, left_on="et", right_on="ts").dropna(subset=["framesReceivedPerSecond"])

    # 시계가 어긋났는지 보려고 ±3초 이동해 fps MAE가 가장 작은 지점도 함께 본다
    scan = {lag: float((m["fps"] - m["framesReceivedPerSecond"]).abs().mean())
            for lag in range(-3, 4) if len(m := merged(lag))}
    if not scan:
        sys.exit(f"시각이 겹치지 않음: est {est.et.min()}–{est.et.max()}, truth {truth.ts.min()}–{truth.ts.max()}")
    m = merged(0) if 0 in scan else merged(min(scan, key=scan.get))
    err = m["fps"] - m["framesReceivedPerSecond"]
    res = {
        "n_seconds": len(m),
        "fps_mae": round(float(err.abs().mean()), 2),
        "fps_within_2": round(float((err.abs() <= 2).mean()), 3),
        "fps_truth_mean": round(float(m["framesReceivedPerSecond"].mean()), 1),
        "fps_est_mean": round(float(m["fps"].mean()), 1),
        "bitrate_mae_kbps": round(float((m["bitrate_x"] - m["bitrate_y"]).abs().mean() / 1000), 1),
        "bitrate_truth_mean_kbps": round(float(m["bitrate_y"].mean() / 1000), 1),
        "frame_jitter_mae_ms": round(float((m["frame_jitter_x"] - m["frame_jitter_y"]).abs().mean()), 1),
        "height_acc": round(float((np.abs(m["frameHeight_x"] - m["frameHeight_y"]) < 1).mean()), 3),
        "height_truth_values": sorted(m["frameHeight_y"].dropna().unique().astype(int).tolist()),
        "lag_scan_fps_mae": {k: round(v, 2) for k, v in scan.items()},
        "vcaml_paper_ref": "in-lab IP/UDP ML 평균 FPS MAE 1.50, 팀 재현 Meet 1.33",
    }
    m.to_csv(OUT / f"{a.name}_cmp.csv", index=False)
    (OUT / f"{a.name}_summary.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ifaces")
    c = sub.add_parser("capture")
    c.add_argument("--name", required=True)
    c.add_argument("--iface", default="Wi-Fi")
    c.add_argument("--duration", type=int, default=0, help="초. 0이면 Ctrl+C까지")
    c.add_argument("--dst", default=None, help="노트북 IP (없으면 UDP 바이트가 가장 많은 dst)")
    c.add_argument("--no-os", action="store_true", help="CPU 기록 끔")
    p = sub.add_parser("compare")
    p.add_argument("--name", required=True)
    p.add_argument("--dump", required=True)
    a = ap.parse_args()
    if a.cmd == "ifaces":
        subprocess.run([tshark_path(), "-D"])
    elif a.cmd == "capture":
        capture(a)
    else:
        compare(a)


if __name__ == "__main__":
    main()
