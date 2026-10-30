"""합성 csv로 단계 집계·통과 판정·RSS 기울기를 검증한다 (실측 데이터·psutil 불필요)."""
from datetime import datetime

import pandas as pd
import pytest

from scripts import overhead_report as r


def make():
    # 끔 60초 + 켬 60초. 켬 단계 앞 15초는 버려지므로 거기에 이상값(99%)을 넣어 두었다.
    phase = pd.DataFrame({"ts": [0, 60, 120, 121], "phase": ["off", "on", "end", "end"]})
    ts = list(range(121))
    mem = pd.DataFrame({"ts": ts, "monitor_cpu_pct": [0.0] * 60 + [99.0] * 15 + [2.0] * 46,
                        "monitor_rss_mb": [0.0] * 60 + [100 + 0.5 * (t - 60) for t in range(60, 121)]})
    dump = pd.DataFrame({"ts": ts, "dec_fps": 28.0, "freeze": 0.0, "decode_ms": 6.0,
                         "send_fps": [29.0] * 60 + [27.5] * 61})
    return phase, {"mem": mem, "dump": dump}


def test_aggregate_skips_warmup_and_compares_with_off():
    phase, tables = make()
    means, _ = r.aggregate(phase, tables, skip=15)
    assert means.loc["on", "monitor_cpu_pct"] == 2.0          # 앞 15초(99%)는 제외
    ok = {label: res for label, _, res in r.verdicts(means)}
    assert ok["on: 모니터 CPU% < 5"] is True
    assert ok["on: Δ수신 fps < 1"] is True
    assert ok["on: Δ송신 fps < 1"] is False                  # 29 → 27.5
    assert ok["on: ΔPages/s ≤ 0"] is None                     # perf 자료 없음은 판정 불가


def test_rss_slope_flags_leak():
    phase, tables = make()
    slope = r.rss_slope_mb_per_min(tables["mem"], phase, skip=15)
    assert abs(slope - 30.0) < 0.5                            # 초당 0.5MB = 30MB/분


@pytest.mark.parametrize("ts", [[16], []])
def test_empty_phase_keeps_columns_and_displays_dash(ts):
    phase = pd.DataFrame({"ts": [0, 60, 120], "phase": ["off", "on", "end"]})
    mem = pd.DataFrame({"ts": ts, "monitor_cpu_pct": [2.0] * len(ts)})
    means, _ = r.aggregate(phase, {"mem": mem})
    assert pd.isna(means.loc["on", "monitor_cpu_pct"])
    assert "모니터 CPU%" in r.markdown(means)
    assert "| on | – |" in r.markdown(means)
    if not ts:
        assert "| off | – |" in r.markdown(means)
    assert all(ok is None for _, _, ok in r.verdicts(means))


def test_perf_table_reads_typeperf_csv_and_sums_gpu(tmp_path):
    path = tmp_path / "perf.csv"
    path.write_text(
        '"(PDH-CSV 4.0)","\\\\HOST\\Memory\\Pages/sec",'
        '"\\\\HOST\\GPU Engine(pid_1_engtype_3D)\\Utilization Percentage",'
        '"\\\\HOST\\GPU Engine(pid_2_engtype_3D)\\Utilization Percentage"\n'
        '"10/31/2026 14:00:01.123","3.0","1.5","2.5"\n'
        '"10/31/2026 14:00:02.123"," "," "," "\n'
        '"10/31/2026 14:00:03.123","1.0"," ","3.0"\n',
        encoding="utf-8",
    )
    table = r.perf_table(path)
    assert list(table.columns) == ["ts", "pages_sec", "gpu_pct"]
    assert table.loc[0, "ts"] == pytest.approx(datetime(2026, 10, 31, 14, 0, 1, 123000).timestamp(), rel=0, abs=1e-6)
    assert table.loc[0, "pages_sec"] == 3.0
    assert table.loc[0, "gpu_pct"] == 4.0
    assert table.loc[1, ["pages_sec", "gpu_pct"]].isna().all()
    assert table.loc[2, "gpu_pct"] == 3.0


@pytest.mark.parametrize("missing", [("os",), ("mem",), ("os", "mem")])
def test_missing_required_csv_exits_with_filenames(tmp_path, monkeypatch, capsys, missing):
    for kind in ("os", "mem"):
        if kind not in missing:
            (tmp_path / f"trial_{kind}.csv").write_text("ts\n", encoding="utf-8")
    monkeypatch.setattr(r, "OUT", tmp_path)
    monkeypatch.setattr("sys.argv", ["overhead_report.py", "--name", "trial"])
    with pytest.raises(SystemExit) as exc:
        r.main()
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert "필수 파일이 없습니다" in error
    assert all(f"trial_{kind}.csv" in error for kind in missing)
    assert "Traceback" not in error


def test_main_runs_without_dump(tmp_path, monkeypatch, capsys):
    pd.DataFrame({"ts": [0, 60, 120], "phase": ["off", "on", "end"]}).to_csv(
        tmp_path / "trial_phase.csv", index=False)
    pd.DataFrame({"ts": [16, 76], "cpu_pct": [20, 21]}).to_csv(tmp_path / "trial_os.csv", index=False)
    pd.DataFrame({"ts": [16, 76], "monitor_cpu_pct": [0, 2], "monitor_rss_mb": [0, 100]}).to_csv(
        tmp_path / "trial_mem.csv", index=False)
    monkeypatch.setattr(r, "OUT", tmp_path)
    monkeypatch.setattr("sys.argv", ["overhead_report.py", "--name", "trial"])
    r.main()
    output = capsys.readouterr().out
    assert "| on | 2.00 | 21.00 | 100.00 |" in output
    assert "PASS  on: 모니터 CPU% < 5" in output
    assert "수신 fps" not in output.split("통과 기준")[0]
    assert "----  on: Δ수신 fps < 1  (자료 없음)" in output
