"""P5 E4 — 시스템 가용 RAM을 목표(--avail-mb)까지 줄이고 유지한다. Ctrl+C로 해제.

가용이 목표보다 크면 64 MB씩 잡고, 목표보다 작으면 64 MB씩 놓는다 (2초마다). 통화·모니터를 켜기 전에 먼저 실행한다.
실행: uv run --with psutil python scripts/mem_hog.py --avail-mb 500
"""
import argparse
import time

CHUNK = 64 * 2**20


def main():
    import psutil
    ap = argparse.ArgumentParser()
    ap.add_argument("--avail-mb", type=int, required=True)
    ap.add_argument("--tol-mb", type=int, default=100, help="이 폭 안이면 가만히 둔다")
    a = ap.parse_args()
    held = []
    try:
        while True:
            avail = psutil.virtual_memory().available / 2**20
            if avail > a.avail_mb + a.tol_mb:
                held.append(bytearray(b"\x01") * CHUNK)   # 0이 아닌 값으로 채워 실제로 물리 메모리를 쓴다
            elif avail < a.avail_mb - a.tol_mb and held:
                held.pop()
            print(f"{time.strftime('%H:%M:%S')} 가용 {avail:6.0f} MB  점유 {len(held) * 64} MB", flush=True)
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    print("해제")


if __name__ == "__main__":
    main()
