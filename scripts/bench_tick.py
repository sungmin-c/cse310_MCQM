"""1 tick(1초 윈도우) 처리 시간 측정 — 지표 4개 모델 동시 추론 + 진단, What-if 경로 포함 (M0-2 확장).

tick 비용 = 그 윈도우에 속한 패킷 push 시간 합 + feature 계산 + 모델 4개 predict + 진단
           (What-if는 여기에 그 1초 분량의 손상 적용 시간을 더함)

실행: uv run --with psutil python scripts/bench_tick.py [--calls 10] [--models data/models]
모델: data/models/meet_{fps,bitrate,frame_jitter,frameHeight}_cv1.pkl (솔로 MLflow fold-1에서 복사)
"""
import argparse
import json
import pickle
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from diag_synth import clean_calls, load_packets  # noqa: E402
from server.diagnosis import Diagnoser  # noqa: E402
from server.features import WindowFeatures  # noqa: E402
from server.impair import Impairer, ImpairParams  # noqa: E402

METRICS = ["fps", "bitrate", "frame_jitter", "frameHeight"]


def load_models(folder):
    proc = psutil.Process()
    rss0 = proc.memory_info().rss
    t0 = time.perf_counter()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        models = {}
        for m in METRICS:
            with open(Path(folder) / f"meet_{m}_cv1.pkl", "rb") as f:
                obj = pickle.load(f)
            models[m] = (obj.estimator, list(obj.featureMatrix.columns))
    return models, {
        "load_s": round(time.perf_counter() - t0, 2),
        "rss_mb_added": round((proc.memory_info().rss - rss0) / 2**20),
        "warnings": sorted({str(x.message)[:100] for x in w}),
    }


def run(calls, models, whatif=None):
    costs, preds = [], []
    for ci, csv in enumerate(calls):
        dst, epoch, rel, size, _, _ = load_packets(csv)
        wf, dg = WindowFeatures(vca="meet", dst_ip=dst), Diagnoser()
        imp = Impairer(ImpairParams(**whatif), seed=ci) if whatif else None
        acc = 0.0

        def close(w):
            t = time.perf_counter()
            row = {m: float(est.predict(w[cols])[0]) for m, (est, cols) in models.items()}
            dg.update(w.iloc[0])
            return row, time.perf_counter() - t

        # 1초씩 잘라 넣는다 (What-if면 그 1초에 손상 적용)
        edges = np.arange(rel[0], rel[-1] + 1.0, 1.0)
        for a, b in zip(edges[:-1], edges[1:]):
            i, j = np.searchsorted(rel, [a, b])
            t = time.perf_counter()
            if imp is not None:
                k, tn = imp.apply(rel[i:j], size[i:j])
                k = k + i
                pk = zip(epoch[k] + (tn - rel[k]), tn, size[k])
            else:
                pk = zip(epoch[i:j], rel[i:j], size[i:j])
            acc += time.perf_counter() - t
            for e, r, s in pk:
                t = time.perf_counter()
                w = wf.push(e, r, dst, 17, s)
                acc += time.perf_counter() - t
                if w is not None:
                    row, dt = close(w)
                    costs.append((acc + dt) * 1000)
                    preds.append(row)
                    acc = 0.0
    c = np.array(costs)
    suspended = int((c > 60_000).sum())   # 노트북 절전(Modern Standby)이 끼면 tick 하나가 몇 시간이 된다
    c = c[c <= 60_000]
    return {"ticks": len(c), "excluded_suspend": suspended, "p50_ms": round(float(np.percentile(c, 50)), 1),
            "p95_ms": round(float(np.percentile(c, 95)), 1), "max_ms": round(float(c.max()), 1),
            "pred_median": {m: round(float(np.median([p[m] for p in preds])), 1) for m in METRICS}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", type=int, default=10)
    ap.add_argument("--models", default="data/models")
    ap.add_argument("--out", default="data/bench/bench_tick.json")
    a = ap.parse_args()

    models, load = load_models(a.models)
    calls = clean_calls("meet")[1::2][:a.calls]          # diag_synth test 분할과 같은 통화
    res = {"load": load, "calls": len(calls),
           "live_replay": run(calls, models),
           "whatif": run(calls, models, whatif=dict(loss_pct=5, burst_len=2, delay_ms=100,
                                                     jitter_ms=30, bw_kbps=120)),
           "rss_mb_total": round(psutil.Process().memory_info().rss / 2**20)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
