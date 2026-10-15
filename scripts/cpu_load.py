"""W1 파일럿 P2 — 노트북 CPU에 단계별 부하를 건다 (busy loop, 설치 불필요).

단계마다 코어 수만큼 프로세스를 띄워 100 ms 주기 중 level%만큼 계산하고 나머지는 쉰다.
단계 시작 시각을 data/pilot/<name>_load.csv (ts, level)에 적는다 → pilot_live 결과와 초 단위로 맞춘다.

--pin N: 저사양 노트북 흉내. chrome.exe와 부하 프로세스를 코어 0..N-1에만 묶는다 (psutil affinity).
  단계마다 다시 걸고(새로 뜬 Chrome 프로세스 포함), 끝나면 원래 affinity로 되돌린다.
  되돌리기가 안 됐으면(강제 종료 등): Chrome을 완전히 껐다 켜면 원래대로 돌아간다.

실행 (repo 루트, pilot_live capture와 동시에):
  uv run python scripts/cpu_load.py --name p2_meet1 --levels 0,50,80,100 --step 60
  uv run --with psutil python scripts/cpu_load.py --name p2_meet2 --pin 2 --workers 4
멈추기: Ctrl+C (부하 프로세스도 함께 끝난다)
"""
import argparse
import csv
import multiprocessing as mp
import os
import time
from pathlib import Path

PERIOD = 0.1


def burn(level):
    busy = PERIOD * level / 100
    while True:
        t = time.perf_counter()
        while time.perf_counter() - t < busy:
            pass
        if busy < PERIOD:
            time.sleep(PERIOD - busy)


def pin_chrome(ps, cores):
    """Chrome 프로세스 전부를 cores에 묶고 개수를 돌려준다. 묶인 뒤 새로 뜬 자식은 묶인 affinity를 물려받으므로
    '원래 값'을 저장해 되돌리면 안 된다 → 복원은 항상 전체 코어로 한다."""
    n = 0
    for p in ps.process_iter(["name"]):
        if (p.info["name"] or "").lower() == "chrome.exe":
            try:
                p.cpu_affinity(cores)
                n += 1
            except ps.Error:
                pass
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--levels", default="0,50,80,100", help="단계별 부하 %%, 쉼표 구분")
    ap.add_argument("--step", type=int, default=60, help="단계당 초")
    ap.add_argument("--workers", type=int, default=os.cpu_count(), help="부하 프로세스 수 (기본: 논리 코어 수)")
    ap.add_argument("--pin", type=int, default=0, help="Chrome·부하를 코어 0..N-1에 묶음 (0이면 끔)")
    a = ap.parse_args()
    ps = None
    cores = list(range(a.pin))
    if a.pin:
        import psutil as ps

    out = Path("data/pilot")
    out.mkdir(parents=True, exist_ok=True)
    procs = []
    with open(out / f"{a.name}_load.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "level"])
        try:
            for level in (int(x) for x in a.levels.split(",")):
                for p in procs:
                    p.terminate()
                procs = [mp.Process(target=burn, args=(level,), daemon=True) for _ in range(a.workers if level else 0)]
                for p in procs:
                    p.start()
                if a.pin:
                    pin_chrome(ps, cores)
                    for p in procs:
                        ps.Process(p.pid).cpu_affinity(cores)
                w.writerow([round(time.time(), 3), level])
                f.flush()
                print(f"{time.strftime('%H:%M:%S')} 부하 {level}% × {len(procs)}개 프로세스, {a.step}초", flush=True)
                time.sleep(a.step)
        except KeyboardInterrupt:
            pass
        finally:
            for p in procs:
                p.terminate()
            if a.pin:
                n = pin_chrome(ps, list(range(os.cpu_count())))
                print(f"Chrome affinity 복원(전체 코어): {n}개 프로세스", flush=True)
            w.writerow([round(time.time(), 3), 0])
            print("부하 끝", flush=True)


if __name__ == "__main__":
    main()
