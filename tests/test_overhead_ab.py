"""단계 생성과 CLI 검증만 확인한다 (프로세스·샘플러 실행 없음)."""
import pytest

from scripts import overhead_ab as a


def test_build_phases_rotates_widget_pairs():
    phases = a.build_phases(["off", "widget"], pairs=3, step=60, warm=150)
    assert phases == [("warm", 150), ("off", 60), ("widget", 60),
                      ("widget", 60), ("off", 60), ("off", 60), ("widget", 60)]
    assert len(phases) == 7
    assert sum(sec for _, sec in phases) == 510


def test_default_phases_keep_existing_order(monkeypatch):
    monkeypatch.setattr(a.os, "cpu_count", lambda: 4)
    args = a.parse_args(["--name", "test", "--dst", "127.0.0.1"])
    assert a.build_phases(args.modes, args.pairs, args.step, args.warm) == [
        ("warm", 150), ("off", 50), ("on", 50),
        ("on", 50), ("off", 50), ("off", 50), ("on", 50)]


def test_build_phases_rotates_each_start_and_keeps_input():
    modes = ["off", "capture", "server", "widget"]
    phases = a.build_phases(modes, pairs=3, step=25, warm=0)
    assert phases == [("warm", 0)] + [(mode, 25) for mode in [
        "off", "capture", "server", "widget", "capture", "server", "widget", "off",
        "server", "widget", "off", "capture"]]
    assert modes == ["off", "capture", "server", "widget"]


@pytest.mark.parametrize("option,value,message", [
    ("--modes", "off,unknown", "--modes는"),
    ("--modes", "off,", "--modes는"),
    ("--modes", "", "--modes는"),
    ("--pin-monitor", "4", "--pin-monitor는"),
    ("--pin-monitor", "5", "--pin-monitor는"),
    ("--pin-monitor", "-1", "--pin-monitor는"),
    ("--pairs", "0", "--pairs와 --step은"),
    ("--pairs", "-1", "--pairs와 --step은"),
    ("--step", "0", "--pairs와 --step은"),
    ("--step", "-1", "--pairs와 --step은"),
])
def test_parse_args_rejects_invalid_input(monkeypatch, capsys, option, value, message):
    monkeypatch.setattr(a.os, "cpu_count", lambda: 4)
    with pytest.raises(SystemExit) as exc:
        a.parse_args(["--name", "test", "--dst", "127.0.0.1", option, value])
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert message in error.splitlines()[-1]
    assert "Traceback" not in error


def test_parse_args_accepts_all_modes_and_minimum_durations(monkeypatch):
    monkeypatch.setattr(a.os, "cpu_count", lambda: 4)
    args = a.parse_args(["--name", "test", "--dst", "127.0.0.1",
                         "--modes", "off,on,capture,server,widget,os",
                         "--pin-monitor", "3", "--pairs", "1", "--step", "1"])
    assert args.modes == ["off", "on", "capture", "server", "widget", "os"]
    assert (args.pin_monitor, args.pairs, args.step) == (3, 1, 1)
