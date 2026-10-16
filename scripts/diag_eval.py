"""W3 진단 평가. 실행: uv run python scripts/diag_eval.py [--no-device].

log.csv는 docs/design/w3_collection.md 형식, 패킷·OS는 data/pilot,
dump는 data/w3. 같은 조건의 통화를 ID 순으로 dev/test에 번갈아 배정한다.
"""
import argparse
import ast
import csv
import json
import math
import statistics
import sys
import tempfile
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from capture.tshark_live import FIELDS, parse  # noqa: E402
from server.diagnosis import CAUSES, Diagnoser  # noqa: E402
from server.features import RtpSeqLoss, WindowFeatures  # noqa: E402

LABELS = ["none", "loss", "bandwidth", "device_cpu"]


def condition_label(cond):
    if cond == "N0":
        return "none"
    if cond in ("C2", "C2L"):
        return "device_cpu"
    if cond in ("L3", "L5", "L10"):
        return "loss"
    if cond in ("B1000", "B300"):
        return "bandwidth"
    raise ValueError(f"unknown condition: {cond}")


def window_label(ts, call):
    t0, on, off = (float(call[k]) for k in ("t0", "impair_on", "impair_off"))
    if not all(math.isfinite(t) for t in (t0, on, off)) or not t0 <= on < off <= t0 + 380:
        raise ValueError(f"invalid interval for call {call['call_id']}")
    label = condition_label(call["cond"])
    if label == "none":
        return "none" if t0 + 150 <= ts <= t0 + 380 else None
    if t0 + 150 <= ts < min(t0 + 210, on) or off + 30 <= ts <= t0 + 380:
        return "none"
    return label if on + 3 <= ts <= off else None


def load_os(path):
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not {"ts", "call_core_pct"}.issubset(reader.fieldnames or []):
            return [], []  # 과거 기록을 전체 CPU%로 대체하지 않는다.
        rows = [(float(r["ts"]), {"call_core_pct": float(r["call_core_pct"])}) for r in reader]
    if any(not math.isfinite(ts) or not math.isfinite(d["call_core_pct"])
           or not 0 <= d["call_core_pct"] <= 100 for ts, d in rows):
        raise ValueError(f"invalid OS sample: {path}")
    rows.sort(key=lambda r: r[0])
    return [r[0] for r in rows], [r[1] for r in rows]


def run_call(path, os_path, *, no_device=False, dst=None):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError(f"packet CSV must contain the 14 tshark fields: {path}")
        packets = []
        sizes = Counter()
        for row in reader:
            fields = [row[k] or "" for k in FIELDS]
            packet = parse(fields)
            if packet is not None and packet[3] == 17:
                packets.append((packet, row))
                sizes[packet[2]] += packet[4]
    dst = dst or max(sizes, key=sizes.get, default=None)
    times, devices = ([], []) if no_device else load_os(os_path)
    wf, diag, seq = WindowFeatures(dst_ip=dst), Diagnoser(), RtpSeqLoss()
    flows = Counter()
    out = []

    def emit(w):
        et = int(w["et"].iloc[0])
        i = bisect_right(times, et) - 1
        device = devices[i] if i >= 0 and et - times[i] <= 2 else None
        flow = max(flows, key=flows.get, default=None)
        cause, conf = diag.update(w.iloc[0], seq_loss=seq.take(), device=device, flow=flow)
        out.append({"et": et, "pred": cause, "confidence": conf, "ready": bool(diag.last_signals)})
        flows.clear()

    for packet, raw in packets:
        if packet[2] != dst or packet[4] <= wf.video_thresh:
            continue
        w = wf.push(*packet)
        if w is not None:
            emit(w)  # 경계를 연 패킷은 다음 창의 RTP·flow 집계에 넣는다.
        src, port = raw["ip.src"], raw["udp.srcport"]
        if src and port and "," not in src and "," not in port:
            flows[(src, int(port))] += packet[4]
        ssrc, number = raw["rtp.ssrc"], raw["rtp.seq"]
        if ssrc and number:
            seq.push((src, port, ssrc.split(",")[0]), int(number.split(",")[0]))
    if (w := wf.flush()) is not None:
        emit(w)
    return out


def effects(path, epochs, call):
    """선택된 PC의 decode/frame, 송신 fps, freeze 증분. 자료가 없으면 평가 불가(None)."""
    if not path.exists():
        return {}
    from vcaml.io.webrtc_reader import WebRTCReader

    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    best, best_n = None, -1
    with tempfile.TemporaryDirectory() as td:
        for conn in raw["PeerConnections"].values():
            p = Path(td) / "pc.json"
            p.write_text(json.dumps({"PeerConnections": {"pc": conn}}), encoding="utf-8")
            truth = WebRTCReader(str(p), "in_lab_data").get_webrtc()
            if truth.empty or "framesReceivedPerSecond" not in truth:
                continue
            n = int(((truth["framesReceivedPerSecond"] > 0) & truth.ts.isin(epochs)).sum())
            if n > best_n:
                best, best_n = conn["stats"], n
    if best is None or best_n <= 0:
        return {}
    reader = WebRTCReader(str(path), "in_lab_data")
    inbound = reader._getMostActiveStreamId(best, reader._getActiveStreamIds(best, "IT01V"))

    def series(key, cumulative=False):
        if key not in best:
            return pd.Series(dtype=float)
        s = best[key]
        frame = reader._parseStatSeries(key, s["startTime"], s["endTime"], ast.literal_eval(s["values"]))
        result = frame.set_index("ts").iloc[:, 0].astype(float)
        return result.diff().clip(lower=0) if cumulative else result

    prefix = f"IT01V{inbound}-"
    decoded = series(prefix + "framesDecoded", True)
    decode = series(prefix + "totalDecodeTime", True) / decoded.where(decoded > 0)
    freeze = series(prefix + "freezeCount", True)
    sent = [series(k) for k in best if k.startswith("OT01V") and k.endswith("-framesPerSecond")]
    sent = pd.concat(sent, axis=1).sum(axis=1, min_count=1) if sent else pd.Series(dtype=float)
    start = float(call["t0"]) + 150
    end = min(float(call["t0"]) + 210, float(call["impair_on"]))
    baseline_decode = decode[(decode.index >= start) & (decode.index < end)].median()
    baseline_sent = sent[(sent.index >= start) & (sent.index < end)].median()
    result = {}
    for et in epochs:
        checks = []
        d, fps, fr = decode.get(et), sent.get(et), freeze.get(et)
        if pd.notna(d) and pd.notna(baseline_decode) and baseline_decode > 0:
            checks.append(d >= 2 * baseline_decode)
        if pd.notna(fps) and pd.notna(baseline_sent) and baseline_sent > 0:
            checks.append(fps <= 0.8 * baseline_sent)
        if pd.notna(fr):
            checks.append(fr > 0)
        result[et] = any(checks) if checks else None
    return result


def summarize(rows):
    scored = [r for r in rows if r["truth"] is not None]
    cm = {c: {p: 0 for p in CAUSES} for c in LABELS}
    for r in scored:
        cm[r["truth"]][r["pred"]] += 1
    precision, recall = {}, {}
    for c in LABELS:
        tp = cm[c][c]
        predicted, actual = sum(cm[t][c] for t in LABELS), sum(cm[c].values())
        precision[c] = tp / predicted if predicted else None
        recall[c] = tp / actual if actual else None
    latencies = defaultdict(list)
    calls = defaultdict(list)
    for r in rows:
        if r["target"] != "none" and r["on"] <= r["et"] <= r["off"]:
            calls[r["call_id"]].append(r)
    detected = Counter()
    for group in calls.values():
        hits = [r["et"] - r["on"] for r in group if r["ready"] and r["pred"] == r["target"]]
        if hits:
            detected[group[0]["target"]] += 1
            latencies[group[0]["target"]].append(min(hits))
    cpu_effect = [r for r in scored if r["truth"] == "device_cpu" and r["effect"] is True]
    normal = [r for r in scored if r["truth"] == "none"]
    return {"windows_scored": len(scored), "confusion_matrix": cm,
            "precision": precision, "recall": recall,
            "none_false_positive_rate": sum(r["pred"] != "none" for r in normal) / len(normal) if normal else None,
            "latency_median_s": {c: statistics.median(latencies[c]) if latencies[c] else None
                                 for c in LABELS if c != "none"},
            "detected_calls": dict(detected), "effect_cpu_windows": len(cpu_effect),
            "effect_cpu_recall": sum(r["pred"] == "device_cpu" for r in cpu_effect) / len(cpu_effect) if cpu_effect else None}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", type=Path, default=Path("data/w3/log.csv"))
    ap.add_argument("--packets-dir", type=Path, default=Path("data/pilot"))
    ap.add_argument("--dump-dir", type=Path, default=Path("data/w3"))
    ap.add_argument("--out", type=Path, default=Path("data/diag/w3"))
    ap.add_argument("--split", choices=("dev", "test"), default="test")
    ap.add_argument("--no-device", action="store_true")
    ap.add_argument("--dst")
    args = ap.parse_args(argv)
    with args.log.open(newline="", encoding="utf-8-sig") as f:
        calls = [r for r in csv.DictReader(f) if r["status"] in ("ok", "no_truth")]
    calls.sort(key=lambda r: int(r["call_id"]))
    if len({int(r["call_id"]) for r in calls}) != len(calls):
        raise ValueError("duplicate call_id in log")
    counts, rows, selected = Counter(), [], []
    for call in calls:
        condition_label(call["cond"])
        split = "dev" if counts[call["cond"]] % 2 == 0 else "test"
        counts[call["cond"]] += 1
        if split != args.split:
            continue
        stem = f"w3_{int(call['call_id']):02d}"
        windows = run_call(args.packets_dir / f"{stem}_pkts.csv", args.packets_dir / f"{stem}_os.csv",
                           no_device=args.no_device, dst=args.dst)
        effect = effects(args.dump_dir / f"{stem}_dump.json", [r["et"] for r in windows], call)
        for row in windows:
            rows.append(dict(row, call_id=call["call_id"], cond=call["cond"],
                             truth=window_label(row["et"], call), target=condition_label(call["cond"]),
                             on=float(call["impair_on"]), off=float(call["impair_off"]),
                             effect=effect.get(row["et"])))
        selected.append(call["call_id"])
    report = dict(summarize(rows), split=args.split, no_device=args.no_device, calls=selected)
    args.out.mkdir(parents=True, exist_ok=True)
    name = f"{args.split}_{'packet_only' if args.no_device else 'device'}"
    (args.out / f"{name}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    pd.DataFrame(rows).to_csv(args.out / f"{name}_windows.csv", index=False)
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return report


if __name__ == "__main__":
    main()
