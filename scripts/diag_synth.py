"""원인 진단 합성 실험 — 깨끗한 in-lab 통화에 손상을 주입하고 진단 규칙을 평가한다 (실험 ③의 사전 연습).

절차
1. 깨끗한 통화 선택: 폴더명 <처리량kbps>_<처리량변동>_<지연ms>_<지연변동>_<손실%>_<길이s>_<번호>
   [가정] 형식은 vcaml run_calls.py에서 추정. 처리량 ≥ 3000, 지연 ≤ 60, 지연변동 ≤ 15, 손실 0.
2. 통화마다 '영상 시작 + ONSET_S'초부터 끝까지 한 가지 손상(server/impair.py)을 넣는다. 그 전은 정상(none).
   in-lab 캡처는 영상이 녹화 시작 약 24초 뒤부터 흐르므로(확인됨) 영상 시작 시점을 기준으로 한다.
3. 스트리밍 feature(server/features.py) → 진단(server/diagnosis.py) → 윈도우별 정답 라벨과 비교.
4. 통화를 짝/홀로 나눠 dev(규칙 조정용) / test(보고용)로 쓴다.

실행: uv run python scripts/diag_synth.py [--vca meet] [--split test] [--rtp] [--out data/diag/]
재채점: uv run python scripts/diag_synth.py --rescore data/diag/test/windows_meet_test_rtp.csv [--rtp] --out <폴더>
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.diagnosis import CAUSES, Diagnoser  # noqa: E402
from server.features import RtpSeqLoss, WindowFeatures  # noqa: E402
from server.impair import Impairer, ImpairParams  # noqa: E402
from vcaml.pipeline.net_utils import readIpUdpFile  # noqa: E402

DATA = Path("data/in_lab_data")
ONSET_S = 12.0     # 손상 시작 = 영상 시작 + 12초 (진단기 기준선 2+8윈도우 확보 후)
SETTLE_S = 2.0     # 손상 직후 과도 구간은 채점에서 제외
MIN_IMPAIRED_S = 10.0  # 손상 구간이 이보다 짧은 통화는 제외

# (라벨, 이름, 파라미터). bandwidth는 통화 기준 비트레이트 대비 비율로 지정 → 실제로 병목이 되게.
CONDITIONS = [
    ("none", "none", {}),
    ("loss", "loss2", dict(loss_pct=2)),
    ("loss", "loss5", dict(loss_pct=5)),
    ("loss", "loss10", dict(loss_pct=10)),
    ("loss", "loss5_burst3", dict(loss_pct=5, burst_len=3)),
    ("delay_jitter", "jit20", dict(delay_ms=100, jitter_ms=20)),
    ("delay_jitter", "jit40", dict(delay_ms=100, jitter_ms=40)),
    ("delay_jitter", "jit80", dict(delay_ms=150, jitter_ms=80)),
    ("bandwidth", "bw60", dict(bw_frac=0.6)),
    ("bandwidth", "bw40", dict(bw_frac=0.4)),
    ("bandwidth", "bw25", dict(bw_frac=0.25)),
]
# 수동 확인용: 지터 없는 고정 지연은 수신 측 trace만으로는 보이지 않는다 (진단 대상 아님, 별도 보고)
DELAY_ONLY = ("delay_jitter", "delay200_only", dict(delay_ms=200))


def clean_calls(vca):
    out = []
    for d in sorted(os.listdir(DATA)):
        p = d.split("_")
        if p[1] != vca:
            continue
        thr, _tj, lat, lj, loss, _dur, _num = map(int, p[2:9])
        if thr >= 3000 and lat <= 60 and lj <= 15 and loss == 0:
            csvs = list((DATA / d).glob("*.csv"))
            if csvs and readIpUdpFile(str(csvs[0])) is not None:
                out.append(str(csvs[0]))
    return out


def _first_int(v):
    if isinstance(v, float) and np.isnan(v):
        return None
    return int(float(str(v).split(",")[0]))


def load_packets(csv):
    """수신 dst로 가는 UDP 패킷 전부(음성 포함) — 손상은 영상 필터 전에 건다."""
    dst = readIpUdpFile(csv)["ip.dst"].iloc[0]
    df = pd.read_csv(csv, usecols=["frame.time_relative", "frame.time_epoch", "ip.dst",
                                   "ip.proto", "udp.length", "rtp.ssrc", "rtp.seq"])
    proto = df["ip.proto"].astype(str)
    df = df[~df["ip.proto"].isna() & ~proto.str.contains(",")]
    df = df[(df["ip.proto"].astype(float).astype(int) == 17) & (df["ip.dst"] == dst)]
    ssrc = [None if isinstance(v, float) else str(v).split(",")[0] for v in df["rtp.ssrc"]]
    seq = [_first_int(v) for v in df["rtp.seq"]]
    return (dst, df["frame.time_epoch"].to_numpy(float), df["frame.time_relative"].to_numpy(float),
            df["udp.length"].fillna(0).to_numpy(float), np.array(ssrc, dtype=object), np.array(seq, dtype=object))


def media_start(rel, size, thresh=306, min_pps=10):
    """영상 패킷이 처음으로 초당 min_pps개 이상 흐른 1초 구간의 시작 시각."""
    v = rel[size > thresh]
    for i, t in enumerate(v):
        if np.searchsorted(v, t + 1.0) - i >= min_pps:
            return t
    return None


def run_call(csv, vca, params, seed, use_rtp=False):
    dst, epoch, rel, size, ssrc, seq = load_packets(csv)
    ms = media_start(rel, size)
    if ms is None or rel[-1] - (ms + ONSET_S) < MIN_IMPAIRED_S:
        return None, None
    t0 = ms + ONSET_S
    cut = np.searchsorted(rel, t0)
    params = dict(params)
    if "bw_frac" in params:
        # 기준 비트레이트 = 영상 시작 ~ 손상 직전의 평균 수신 속도 (음성 포함)
        a = np.searchsorted(rel, ms)
        base_kbps = size[a:cut].sum() * 8 / (t0 - ms) / 1000
        params["bw_kbps"] = base_kbps * params.pop("bw_frac")
    idx, t_new = Impairer(ImpairParams(**params), seed=seed).apply(rel[cut:], size[cut:])
    idx = idx + cut
    rel2 = np.concatenate([rel[:cut], t_new])
    epoch2 = np.concatenate([epoch[:cut], epoch[idx] + (t_new - rel[idx])])
    size2 = np.concatenate([size[:cut], size[idx]])
    ssrc2 = np.concatenate([ssrc[:cut], ssrc[idx]])
    seq2 = np.concatenate([seq[:cut], seq[idx]])

    wf = WindowFeatures(vca=vca, dst_ip=dst)
    diag = Diagnoser()
    sl = RtpSeqLoss()
    epoch_t0 = epoch[0] + (t0 - rel[0])
    out = []

    def judge(w):
        loss = sl.take()
        cause, conf = diag.update(w.iloc[0], seq_loss=loss if use_rtp else None)
        out.append((w, cause, conf, dict(diag.last_signals, seq_loss_obs=loss)))
        diag.last_signals = {}

    for e, r, s, ss, sq in zip(epoch2, rel2, size2, ssrc2, seq2):
        w = wf.push(e, r, dst, 17, s)
        if w is not None:
            judge(w)              # 이 패킷은 다음 윈도우 소속 → 순번 집계는 판정 뒤에
        sl.push(ss, sq)
    last = wf.flush()
    if last is not None:
        judge(last)
    rows = []
    for w, cause, conf, sig in out:
        et = float(w["et"].iloc[0])
        rows.append({"et_rel": et - epoch_t0, "pred": cause, "conf": conf, **sig,
                     **{k: float(w[k].iloc[0]) for k in ("l_num_bytes", "l_num_pkts", "t_q1", "t_q2", "t_std", "t_max")}})
    return pd.DataFrame(rows), params.get("bw_kbps")


def summarize(res, vca, split, mode, n_calls, out_dir):
    # 진단기가 실제로 판정한 윈도우만 채점 (기준선 준비 전 윈도우는 제외 → 'none' 부풀림 방지)
    scored = res[(res["truth"] != "skip") & (res["cond"] != DELAY_ONLY[1]) & res["r_bytes"].notna()]
    cm = pd.crosstab(scored["truth"], scored["pred"]).reindex(index=CAUSES, columns=CAUSES, fill_value=0)
    cm = cm.loc[[c for c in CAUSES if c != "weak_wifi"], [c for c in CAUSES if c != "weak_wifi"]]
    prec = {c: cm.at[c, c] / cm[c].sum() if cm[c].sum() else float("nan") for c in cm.columns}
    rec = {c: cm.at[c, c] / cm.loc[c].sum() if cm.loc[c].sum() else float("nan") for c in cm.index}
    acc = np.trace(cm.values) / cm.values.sum()

    imp = res[(res["et_rel"] > 0) & (res["cond"] != "none")]
    per_cond = (res[res["truth"] == res["cond_label"]].groupby("cond")
                .apply(lambda g: (g["pred"] == g["cond_label"]).mean(), include_groups=False))
    # 판정 지연: 손상 시작 후 처음으로 맞힌 윈도우까지 걸린 시간(초)
    lat = (imp[imp["pred"] == imp["cond_label"]].groupby(["cond", "call"])["et_rel"].min()
           .groupby("cond").median())
    delay_only = res[(res["cond"] == DELAY_ONLY[1]) & (res["et_rel"] > SETTLE_S)]

    summary = {
        "vca": vca, "split": split, "mode": mode, "calls": n_calls, "windows_scored": int(len(scored)),
        "accuracy": round(float(acc), 3),
        "precision": {k: round(float(v), 3) for k, v in prec.items()},
        "recall": {k: round(float(v), 3) for k, v in rec.items()},
        "recall_by_condition": {k: round(float(v), 3) for k, v in per_cond.items()},
        "median_detect_s": {k: round(float(v), 1) for k, v in lat.items()},
        "delay_only_pred_share": delay_only["pred"].value_counts(normalize=True).round(3).to_dict(),
        "confusion_matrix": cm.to_dict(orient="index"),
    }
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / f"summary_{vca}_{split}_{mode}.json").write_text(json.dumps(summary, indent=1))
    print(cm.to_string())
    print(json.dumps({k: v for k, v in summary.items() if k != "confusion_matrix"}, indent=1))
    return summary


def rescore(csv, use_rtp, out_dir):
    """저장된 윈도우 feature로 진단만 다시 돌린다 (손상·feature 재계산 없음 → 규칙 조정이 빠름)."""
    res = pd.read_csv(csv)
    vca, split = Path(csv).stem.split("_")[1:3]
    if "seq_loss_obs" not in res:          # 옛 형식: --rtp로 만든 CSV에만 seq_loss가 있다
        res["seq_loss_obs"] = res.get("seq_loss")
    sig_cols = [c for c in res.columns if c.startswith(("r_", "d_")) or c == "seq_loss"]
    res = res.drop(columns=sig_cols)
    rows = []
    for _, g in res.sort_values(["call", "cond", "et_rel"]).groupby(["call", "cond"], sort=False):
        d = Diagnoser()
        for i, r in g.iterrows():
            sl = r["seq_loss_obs"] if use_rtp and pd.notna(r.get("seq_loss_obs")) else None
            cause, conf = d.update(r, seq_loss=sl)
            rows.append({"_i": i, "pred": cause, "conf": conf, **d.last_signals})
            d.last_signals = {}
    new = pd.DataFrame(rows).set_index("_i")
    res = res.drop(columns=["pred", "conf"]).join(new)
    mode = "rtp" if use_rtp else "ipudp"
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    res.to_csv(Path(out_dir) / f"windows_{vca}_{split}_{mode}.csv", index=False)
    return summarize(res, vca, split, mode, res["call"].nunique(), out_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vca", default="meet")
    ap.add_argument("--split", default="test", choices=["dev", "test", "all"])
    ap.add_argument("--out", default="data/diag")
    ap.add_argument("--rtp", action="store_true", help="RTP 순번 손실률을 진단 신호로 사용")
    ap.add_argument("--rescore", help="저장된 windows_*.csv로 진단만 다시 채점")
    a = ap.parse_args()
    if a.rescore:
        rescore(a.rescore, a.rtp, a.out)
        return

    calls = clean_calls(a.vca)
    if a.split != "all":
        calls = calls[(0 if a.split == "dev" else 1)::2]
    mode = "rtp" if a.rtp else "ipudp"
    print(f"{a.vca}: {len(calls)} clean calls ({a.split}, {mode})", flush=True)

    recs = []
    for ci, csv in enumerate(calls):
        for label, name, params in CONDITIONS + [DELAY_ONLY]:
            df, bw = run_call(csv, a.vca, params, seed=ci, use_rtp=a.rtp)
            if df is None:
                break
            df["call"], df["cond"], df["cond_label"], df["bw_kbps"] = ci, name, label, bw
            recs.append(df)
    res = pd.concat(recs, ignore_index=True)
    print(f"usable calls: {res['call'].nunique()}", flush=True)
    res["truth"] = np.where(res["et_rel"] <= 0, "none",
                            np.where(res["et_rel"] > SETTLE_S, res["cond_label"], "skip"))
    Path(a.out).mkdir(parents=True, exist_ok=True)
    res.to_csv(Path(a.out) / f"windows_{a.vca}_{a.split}_{mode}.csv", index=False)

    summarize(res, a.vca, a.split, mode, len(calls), a.out)

if __name__ == "__main__":
    main()
