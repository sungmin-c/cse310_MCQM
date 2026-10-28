"""P5 집계 — overhead_ab.py 산출물을 단계별 평균과 "끔 대비 차이"로 요약하고 통과 기준(overhead_weekend.md §3)을 판정한다.

입력 (data/pilot/): <name>_phase.csv, <name>_os.csv, <name>_mem.csv, 선택: <name>_perf.csv(typeperf), --dump(webrtc-internals)
각 단계는 앞 --skip초(Chrome 적응)와 마지막 1초를 버리고, 같은 이름의 단계끼리 평균한다.
실행: uv run --with psutil python scripts/overhead_report.py --name p5_e1 --dump <dump.json>
"""
import argparse
import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
OUT = Path("data/pilot")
# 표에 보일 열과 제목. 없는 열은 건너뛴다
COLS = {"monitor_cpu_pct": "모니터 CPU%", "cpu_pct": "총 CPU%", "call_proc_cpu_pct": "Chrome CPU%",
        "avail_mb": "가용 MB", "monitor_rss_mb": "모니터 RSS MB", "pages_sec": "Pages/s", "gpu_pct": "GPU%",
        "dec_fps": "수신 fps", "decode_ms": "디코드 ms", "freeze": "freeze/s", "send_fps": "송신 fps",
        "send_kbps": "송신 kbps"}


def intervals(phase):
    """phase.csv(ts, phase) → [(단계, 시작, 끝)]. warm·end는 뺀다."""
    t, names = phase["ts"].tolist(), phase["phase"].tolist()
    return [(names[i], t[i], t[i + 1]) for i in range(len(t) - 1) if names[i] not in ("warm", "end")]


def aggregate(phase, tables, skip=15):
    """tables: {이름: ts 열이 있는 DataFrame}. 반환: (단계별 평균 표, 구간별 평균 표)."""
    per = []
    for name, start, end in intervals(phase):
        row = {"phase": name}
        for df in tables.values():
            win = df[(df["ts"] >= start + skip) & (df["ts"] < end - 1)]
            for c in df.columns:
                if c != "ts":
                    row[c] = win[c].mean()
        per.append(row)
    frame = pd.DataFrame(per)
    return frame.groupby("phase", sort=False).mean(numeric_only=True), frame


def rss_slope_mb_per_min(mem, phase, skip=15):
    """가장 긴 단계 안에서 모니터 RSS의 선형 기울기 (E6 누수 판정). 모니터가 안 떠 있던 초(0)는 뺀다."""
    wins = [mem[(mem["ts"] >= s + skip) & (mem["ts"] < e - 1) & (mem["monitor_rss_mb"] > 0)]
            for _, s, e in intervals(phase)]
    win = max((w for w in wins if len(w) >= 10), key=len, default=None)
    if win is None:
        return None
    return float(np.polyfit(win["ts"].to_numpy(), win["monitor_rss_mb"].to_numpy(), 1)[0]) * 60


def verdicts(means, off="off"):
    """통과 기준 §3. 반환: [(항목, 값, 통과 True/False, 자료 없으면 None)]."""
    if off not in means.index:
        return [("끔 단계 없음", None, None)]
    base, out = means.loc[off], []
    for phase in [p for p in means.index if p != off]:
        m = means.loc[phase]

        def diff(c):
            ok = c in m and c in base and pd.notna(m[c]) and pd.notna(base[c])
            return m[c] - base[c] if ok else None

        dec = diff("decode_ms")
        rel = dec / base["decode_ms"] if dec is not None and base.get("decode_ms") else None
        checks = [("모니터 CPU% < 5", m.get("monitor_cpu_pct"), lambda v: v < 5),
                  ("Δ수신 fps < 1", diff("dec_fps"), lambda v: abs(v) < 1),
                  ("Δ송신 fps < 1", diff("send_fps"), lambda v: abs(v) < 1),
                  ("Δfreeze/s ≤ 0", diff("freeze"), lambda v: v <= 0),
                  ("ΔPages/s ≤ 0", diff("pages_sec"), lambda v: v <= 0),
                  ("Δ디코드 < 10%", rel, lambda v: v < 0.10)]
        for label, v, ok in checks:
            out.append((f"{phase}: {label}", v, None if v is None or pd.isna(v) else bool(ok(v))))
    return out


def perf_table(path):
    """typeperf csv → ts, pages_sec, gpu_pct. 시각은 로컬 시간."""
    raw = pd.read_csv(path)
    raw.columns = [c.strip() for c in raw.columns]
    ts = pd.to_datetime(raw.iloc[:, 0], format="mixed").map(lambda t: t.to_pydatetime().timestamp())
    num = raw.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    out = pd.DataFrame({"ts": ts})
    pages = [c for c in num if "Pages/sec" in c]
    gpu = [c for c in num if "GPU Engine" in c]
    if pages:
        out["pages_sec"] = num[pages].sum(axis=1, min_count=1)
    if gpu:
        out["gpu_pct"] = num[gpu].sum(axis=1, min_count=1)
    return out


def dump_table(path):
    """webrtc-internals dump → 초 단위 ts, dec_fps, decode_ms, freeze, send_fps, send_kbps (inbound 영상이 가장 긴 PC)."""
    from vcaml.io.webrtc_reader import WebRTCReader

    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    reader = WebRTCReader(str(path), "in_lab_data")

    def count(stats, key):
        return len(ast.literal_eval(stats[key]["values"]))

    best, best_key, best_n = None, None, -1
    for conn in raw["PeerConnections"].values():
        for key in conn["stats"]:
            if key.startswith("IT01V") and key.endswith("-framesDecoded") and count(conn["stats"], key) > best_n:
                best, best_key, best_n = conn["stats"], key, count(conn["stats"], key)
    if best is None:
        sys.exit("dump에 IT01V(inbound video) 통계가 없다")

    def series(key, cumulative=False):
        s = best[key]
        frame = reader._parseStatSeries(key, s["startTime"], s["endTime"], ast.literal_eval(s["values"]))
        r = frame.set_index("ts").iloc[:, 0].astype(float)
        return r.diff().clip(lower=0) if cumulative else r

    prefix = best_key[: -len("framesDecoded")]
    decoded = series(best_key, True)
    out = pd.DataFrame({"dec_fps": decoded,
                        "decode_ms": series(prefix + "totalDecodeTime", True) / decoded.where(decoded > 0) * 1000,
                        "freeze": series(prefix + "freezeCount", True)})
    for col, suffix, scale in (("send_fps", "-[framesSent/s]", 1), ("send_kbps", "-[bytesSent_in_bits/s]", 1000)):
        parts = [series(k) for k in best if k.startswith("OT01V") and k.endswith(suffix)]
        if parts:
            out[col] = pd.concat(parts, axis=1).sum(axis=1, min_count=1) / scale
    out.index.name = "ts"
    return out.reset_index()


def markdown(means):
    cols = [c for c in COLS if c in means.columns]
    lines = ["| 단계 | " + " | ".join(COLS[c] for c in cols) + " |", "|---|" + "---|" * len(cols)]
    for phase, row in means.iterrows():
        lines.append(f"| {phase} | " + " | ".join("–" if pd.isna(row[c]) else f"{row[c]:.2f}" for c in cols) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--dump")
    ap.add_argument("--skip", type=int, default=15)
    a = ap.parse_args()
    missing = [OUT / f"{a.name}_{k}.csv" for k in ("os", "mem") if not (OUT / f"{a.name}_{k}.csv").is_file()]
    if missing:
        ap.error("필수 파일이 없습니다: " + ", ".join(str(p) for p in missing))
    phase = pd.read_csv(OUT / f"{a.name}_phase.csv")
    tables = {k: pd.read_csv(OUT / f"{a.name}_{k}.csv") for k in ("os", "mem")}
    if (OUT / f"{a.name}_perf.csv").exists():
        tables["perf"] = perf_table(OUT / f"{a.name}_perf.csv")
    if a.dump:
        tables["dump"] = dump_table(a.dump)
    means, _ = aggregate(phase, tables, a.skip)
    print(markdown(means))
    print("\n통과 기준 (overhead_weekend.md §3):")
    for label, v, ok in verdicts(means):
        shown = "자료 없음" if v is None or pd.isna(v) else round(float(v), 3)
        print(f"  {'PASS' if ok else 'FAIL' if ok is False else '----'}  {label}  ({shown})")
    slope = rss_slope_mb_per_min(tables["mem"], phase, a.skip)
    if slope is not None:
        print(f"  {'PASS' if slope < 1 else 'FAIL'}  모니터 RSS 기울기 < 1 MB/분  ({slope:.2f}, 가장 긴 단계 기준)")


if __name__ == "__main__":
    main()
