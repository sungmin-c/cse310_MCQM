"""W1 파일럿 P3 (H1) — 모니터가 통화를 망치는가. 모니터 끔/켬을 번갈아 돌리고 단계 시각을 기록한다.

순서: warm(끔, Meet 연결 전환 대기) → off, on, off, on, off, on (각 --step초).
  on  단계: `pilot_live.py capture --duration step --name <name>_onK` (tshark + 모델 + psutil)
  전체 구간: psutil 1 Hz 기록 → data/pilot/<name>_os.csv (총 CPU, Chrome CPU)
  단계 시각: data/pilot/<name>_phase.csv (ts, phase)
통화 쪽 영향(수신·디코드·freeze·송신 fps)은 끝난 뒤 webrtc-internals dump로 단계별 비교한다.

실행 (repo 루트):
  uv run --with psutil python scripts/overhead_ab.py --name p3_meet1 --dst 172.30.1.51
"""
import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_live import OUT, OsSampler  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--dst", required=True, help="노트북 IP")
    ap.add_argument("--iface", default="Wi-Fi")
    ap.add_argument("--step", type=int, default=50, help="단계당 초")
    ap.add_argument("--warm", type=int, default=150, help="시작 전 대기 초 (Meet PeerConnection 전환)")
    ap.add_argument("--pairs", type=int, default=3)
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    samp = OsSampler(OUT / f"{a.name}_os.csv", [])
    samp.start()
    phases = [("warm", a.warm)] + [(p, a.step) for _ in range(a.pairs) for p in ("off", "on")]
    k = 0
    with open(OUT / f"{a.name}_phase.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "phase"])
        try:
            for phase, sec in phases:
                w.writerow([round(time.time(), 3), phase])
                f.flush()
                print(f"{time.strftime('%H:%M:%S')} {phase} {sec}초", flush=True)
                if phase == "on":
                    k += 1
                    subprocess.run([sys.executable, str(Path(__file__).parent / "pilot_live.py"), "capture",
                                    "--name", f"{a.name}_on{k}", "--iface", a.iface, "--dst", a.dst,
                                    "--duration", str(sec)], stdout=subprocess.DEVNULL)
                else:
                    time.sleep(sec)
        except KeyboardInterrupt:
            pass
        finally:
            w.writerow([round(time.time(), 3), "end"])
            samp.stop.set()
            samp.join(2)
            print("끝", flush=True)


if __name__ == "__main__":
    main()
