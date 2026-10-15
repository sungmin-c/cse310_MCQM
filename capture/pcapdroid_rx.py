"""PCAPdroid UDP exporter 수신기 — pcap 파일로 저장하고 전송 품질(M0-5)을 잰다.

PCAPdroid v2.0.2 UDP exporter 형식 (공식 tools/udp_receiver.py, UDPDumper.java로 확인):
  첫 데이터그램 = pcap 전역 헤더 24바이트, 이후 데이터그램 1개 = pcap 레코드 1개(16바이트 레코드 헤더 + 패킷).
  extensions(구 trailer)가 꺼져 있으면 linktype = RAW(101).

기록: <out>.pcap (그대로 저장), <out>.csv (데이터그램마다 수신 시각·패킷 시각·길이·프로토콜), <out>.json (요약)
지연: 패킷 시각(폰 시계)과 수신 시각(노트북 시계)의 차이. 시계 차이는 --clock-offset(adb로 잰 폰−노트북, 초)으로 보정.
     보정이 없으면 '최소 지연 대비 추가 지연'만 의미가 있다.

실행: uv run python capture/pcapdroid_rx.py --port 1234 --duration 660 --out data/m0/udp_run1
수신률 측정: --duration 3600 --end-after-idle 15 (폰에서 정지하면 15초 뒤 종료, 앱의 패킷 수와 비교)
"""
import argparse
import csv
import json
import socket
import struct
import time
from pathlib import Path

import numpy as np

PCAP_MAGIC_LE = bytes.fromhex("d4c3b2a1")


def ip_proto(pkt):
    """RAW IP 패킷의 (버전, 프로토콜). IPv6는 next header."""
    if not pkt:
        return None, None
    v = pkt[0] >> 4
    if v == 4 and len(pkt) >= 20:
        return 4, pkt[9]
    if v == 6 and len(pkt) >= 40:
        return 6, pkt[6]
    return v, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=1234)
    ap.add_argument("--duration", type=float, default=660.0, help="초. 첫 데이터 수신 후부터 셈")
    ap.add_argument("--idle-timeout", type=float, default=900.0, help="아무것도 안 오면 종료(초)")
    ap.add_argument("--end-after-idle", type=float, default=None,
                    help="데이터를 받은 뒤 이만큼(초) 조용하면 종료 → 폰에서 캡처를 정지한 시점까지 전부 셈")
    ap.add_argument("--clock-offset", type=float, default=None, help="폰 시계 − 노트북 시계 (초)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
    sock.bind(("0.0.0.0", a.port))
    sock.settimeout(1.0)
    print(f"listening UDP {a.port} → {out}.pcap", flush=True)

    rows, linktype, header_seen, malformed = [], None, False, 0
    t_first = t_last_report = None
    t_start = time.time()
    with open(f"{out}.pcap", "wb") as fp:
        while True:
            now = time.time()
            if t_first is None and now - t_start > a.idle_timeout:
                print("IDLE TIMEOUT: no data received", flush=True)
                break
            if t_first is not None and now - t_first > a.duration:
                break
            if a.end_after_idle and rows and now - rows[-1][0] > a.end_after_idle:
                print(f"END: idle {a.end_after_idle:.0f}s after last record", flush=True)
                break
            try:
                data, addr = sock.recvfrom(65535)
            except socket.timeout:
                continue
            t = time.time()
            if t_first is None:
                t_first = t_last_report = t
                print(f"FIRST DATA from {addr[0]}:{addr[1]} ({len(data)} B)", flush=True)
            if len(data) == 24 and data.startswith(PCAP_MAGIC_LE):
                if not header_seen:
                    fp.write(data)
                    header_seen = True
                    linktype = struct.unpack("<I", data[20:24])[0]
                    print(f"PCAP HEADER linktype={linktype}", flush=True)
                continue
            if not header_seen:                      # 헤더를 놓쳤으면 RAW로 가정하고 만든다
                fp.write(PCAP_MAGIC_LE + bytes.fromhex("020004000000000000000000ffff000065000000"))
                header_seen, linktype = True, None
            if len(data) < 16:
                malformed += 1
                continue
            ts_s, ts_us, incl, orig = struct.unpack("<IIII", data[:16])
            if len(data) != 16 + incl:
                malformed += 1
                continue
            fp.write(data)
            ver, proto = ip_proto(data[16:])
            rows.append((t, ts_s + ts_us / 1e6, incl, orig, ver, proto))
            if t - t_last_report >= 10:
                t_last_report = t
                print(f"PROGRESS {t - t_first:5.0f}s records={len(rows)}", flush=True)

    with open(f"{out}.csv", "w", newline="") as fc:
        w = csv.writer(fc)
        w.writerow(["arrival_epoch", "pkt_epoch", "incl_len", "orig_len", "ip_ver", "ip_proto"])
        w.writerows(rows)

    summary = {"port": a.port, "header_seen": header_seen, "linktype": linktype,
               "records": len(rows), "malformed": malformed}
    if rows:
        arr = np.array([r[0] for r in rows])
        pkt = np.array([r[1] for r in rows])
        # 지연 = 수신(노트북 시계) − 패킷 시각을 노트북 시계로 환산(pkt − offset) = arr − pkt + offset
        lat = arr - pkt + (a.clock_offset if a.clock_offset is not None else 0.0)
        gaps = np.diff(arr) if len(arr) > 1 else np.array([0.0])
        reorder = int((np.diff(pkt) < 0).sum()) if len(pkt) > 1 else 0
        protos = {}
        for r in rows:
            protos[str(r[5])] = protos.get(str(r[5]), 0) + 1
        summary.update({
            "duration_s": round(float(arr[-1] - arr[0]), 1),
            "bytes": int(sum(r[2] for r in rows)),
            "truncated_records": int(sum(r[2] < r[3] for r in rows)),
            "out_of_order_records": reorder,
            "max_arrival_gap_s": round(float(gaps.max()), 3),
            "clock_offset_s": a.clock_offset,
            "latency_ms": {k: round(float(np.percentile(lat, q)) * 1000, 1)
                           for k, q in (("p05", 5), ("p50", 50), ("p95", 95), ("p99", 99))},
            "latency_above_min_ms_p95": round(float(np.percentile(lat - lat.min(), 95)) * 1000, 1),
            "ip_proto_counts": protos,
        })
    Path(f"{out}.json").write_text(json.dumps(summary, indent=1))
    print("DONE " + json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
