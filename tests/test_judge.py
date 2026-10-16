"""judge 설계의 경계·단조성·상태 전이와 기존 tick 계약 재생을 검증한다."""
import json

import pytest

from server.dummy_stream import tick
from server.judge import JudgeState, judge
from test_schema_contract import check


BASE = dict(fps=30.0, bitrate=1000.0, frameHeight=720.0, frame_jitter=10.0)
METRICS = tuple(BASE)
SEVERITY = {"good": 0, "fair": 1, "poor": 2}


@pytest.mark.parametrize("fps, expected", [
    (30, "good"), (24, "good"), (23.9, "fair"),
    (15, "fair"), (14.9, "poor"), (0, "poor"),
])
def test_fps_boundaries(fps, expected):
    result = judge({"fps": fps}, "meet", JudgeState())
    assert result["fps"] == result["overall"] == expected


@pytest.mark.parametrize("jitter, expected", [
    (0, "good"), (29.9, "good"), (30, "fair"),
    (59.9, "fair"), (60, "poor"), (100, "poor"),
])
def test_jitter_boundaries(jitter, expected):
    result = judge({"frame_jitter": jitter}, "meet", JudgeState())
    assert result["frame_jitter"] == result["overall"] == expected


@pytest.mark.parametrize("metric", ["bitrate", "frameHeight"])
@pytest.mark.parametrize("value, expected", [
    (1000, "good"), (800, "good"), (799, "fair"),
    (500, "fair"), (499, "poor"), (0, "poor"),
])
def test_relative_boundaries(metric, value, expected):
    state = JudgeState(baseline={metric: 1000.0})
    result = judge({metric: value}, "meet", state)
    assert result[metric] == result["overall"] == expected


@pytest.mark.parametrize("metric", METRICS)
def test_worsening_sweep_never_improves(metric):
    state = JudgeState(baseline={"bitrate": 1000.0, "frameHeight": 1000.0})
    values = range(1201) if metric == "frame_jitter" else range(1000, -1, -1)
    previous = -1
    for value in values:
        value = value / 10 if metric in ("fps", "frame_jitter") else value
        result = judge({metric: value}, "meet", state)
        severity = SEVERITY[result[metric]]
        assert severity >= previous, (metric, value, result)
        assert result["overall"] == result[metric]
        previous = severity


@pytest.mark.parametrize("metric, poor_value", [
    ("fps", 10), ("bitrate", 100), ("frameHeight", 180), ("frame_jitter", 80),
])
def test_deterioration_is_immediate_and_recovery_takes_two_ticks(metric, poor_value):
    state = JudgeState(base_len=1)
    assert judge(BASE, "meet", state)[metric] == "good"
    result = judge(dict(BASE, **{metric: poor_value}), "meet", state)
    assert result[metric] == result["overall"] == "poor"
    assert judge(BASE, "meet", state)[metric] == "poor"
    assert judge(BASE, "meet", state)[metric] == "good"
    assert state.recent[metric].maxlen == 2
    assert list(state.recent[metric]) == ["good", "good"]


def test_recovery_requires_the_same_new_raw_grade():
    state = JudgeState()
    for fps, expected in [(10, "poor"), (20, "poor"), (30, "poor"),
                          (20, "poor"), (20, "fair"), (30, "fair"), (30, "good")]:
        assert judge({"fps": fps}, "meet", state)["fps"] == expected


def test_invalid_tick_interrupts_recovery_without_showing_stale_grades():
    state = JudgeState()
    judge({"fps": 10}, "meet", state)
    assert judge({"fps": 30}, "meet", state)["fps"] == "poor"
    assert judge({}, "meet", state)["fps"] == "unknown"
    assert judge({"fps": 20}, "meet", state)["fps"] == "fair"


def test_without_baseline_relative_grades_are_unknown_and_overall_uses_other_metrics():
    result = judge(BASE, "meet", JudgeState())
    assert result == dict(fps="good", bitrate="unknown", frameHeight="unknown",
                          frame_jitter="good", overall="good", validated=True)
    result = judge({"bitrate": 1000}, "meet", JudgeState())
    assert result["bitrate"] == result["overall"] == "unknown"


def test_baseline_is_initial_median_and_does_not_follow_degradation():
    state = JudgeState(base_len=3)
    for value in (1000, 10000):
        result = judge(dict(BASE, bitrate=value, frameHeight=value / 10), "meet", state)
        assert result["bitrate"] == result["frameHeight"] == "unknown"
    result = judge(dict(BASE, bitrate=2000, frameHeight=200), "meet", state)
    assert state.baseline == {"bitrate": 2000, "frameHeight": 200}
    assert result["bitrate"] == result["frameHeight"] == "good"
    for _ in range(30):
        result = judge(dict(BASE, bitrate=100, frameHeight=10), "meet", state)
        assert result["bitrate"] == result["frameHeight"] == "poor"
    assert state.baseline == {"bitrate": 2000, "frameHeight": 200}
    assert state._samples == {"bitrate": [], "frameHeight": []}


@pytest.mark.parametrize("changes", [
    {"fps": 23.9}, {"fps": 10}, {"frame_jitter": 30}, {"frame_jitter": 60},
])
def test_unhealthy_absolute_metrics_do_not_enter_baseline(changes):
    state = JudgeState(base_len=2)
    for _ in range(3):
        judge(dict(BASE, **changes), "meet", state)
    assert state.baseline == {}
    assert judge(BASE, "meet", state)["bitrate"] == "unknown"
    result = judge(BASE, "meet", state)
    assert result["bitrate"] == result["frameHeight"] == "good"


@pytest.mark.parametrize("value", [None, float("nan"), -1.0, float("inf"), -float("inf"), 0])
def test_baseline_excludes_invalid_and_zero_values(value):
    state = JudgeState(base_len=2)
    judge(BASE, "meet", state)
    judge(dict(BASE, bitrate=value, frameHeight=value), "meet", state)
    assert state.baseline == {}
    result = judge(BASE, "meet", state)
    assert result["bitrate"] == result["frameHeight"] == "good"


def test_relative_baselines_are_independent_and_allow_missing_absolute_metrics():
    state = JudgeState(base_len=2)
    for _ in range(2):
        result = judge({"bitrate": 1000}, "meet", state)
    assert state.baseline == {"bitrate": 1000}
    assert result["bitrate"] == "good" and result["frameHeight"] == "unknown"
    for _ in range(2):
        result = judge({"frameHeight": 720}, "meet", state)
    assert state.baseline == {"bitrate": 1000, "frameHeight": 720}
    assert result["frameHeight"] == "good" and result["bitrate"] == "unknown"


@pytest.mark.parametrize("value", [None, float("nan"), -1.0, float("inf"), -float("inf")])
def test_invalid_inputs_are_unknown_even_after_valid_ticks(value):
    state = JudgeState(base_len=1)
    judge(BASE, "meet", state)
    result = judge(dict.fromkeys(METRICS, value), "meet", state)
    assert all(result[metric] == "unknown" for metric in METRICS)
    assert result["overall"] == "unknown"


@pytest.mark.parametrize("vca, validated", [
    ("meet", True), ("zoom", False), ("kakao", False),
    ("kakao_video", False), ("kakao_voice", False),
])
def test_validated_is_meet_only(vca, validated):
    assert judge(BASE, vca, JudgeState())["validated"] is validated


def test_sessions_and_returned_snapshots_are_independent():
    first, second = JudgeState(base_len=1), JudgeState(base_len=1)
    est = dict(BASE)
    snapshot = judge(est, "meet", first)
    judge(dict(BASE, fps=10), "meet", first)
    assert est == BASE
    assert snapshot["fps"] == "good"
    assert second.baseline == {}
    assert all(not recent for recent in second.recent.values())
    assert all(grade == "unknown" for grade in second.grades.values())
    assert judge(BASE, "zoom", second)["overall"] == "good"


@pytest.mark.parametrize("base_len", [0, -1])
def test_baseline_length_must_be_positive(base_len):
    with pytest.raises(ValueError, match="base_len"):
        JudgeState(base_len=base_len)


@pytest.mark.parametrize("app", ["meet", "kakao_video", "kakao_voice", "zoom"])
@pytest.mark.parametrize("mode", ["replay", "live", "whatif"])
def test_synthetic_stream_replay_preserves_current_schema(app, mode):
    state = JudgeState()
    overall = set()
    for i in range(120):
        msg = json.loads(json.dumps(tick(i, app, mode, now=float(i))))
        est = msg["est"]
        result = judge({
            "fps": est["fps"],
            "bitrate": None if est["bitrate_kbps"] is None else est["bitrate_kbps"] * 1000,
            "frameHeight": est["height"],
            "frame_jitter": est["frame_jitter_ms"],
        }, app, state)
        assert set(result) == {*METRICS, "overall", "validated"}
        assert all(result[key] in {*SEVERITY, "unknown"} for key in (*METRICS, "overall"))
        assert result["validated"] is (app == "meet")
        known = [result[metric] for metric in METRICS if result[metric] != "unknown"]
        assert result["overall"] == max(known, key=SEVERITY.__getitem__, default="unknown")
        overall.add(result["overall"])
        # judgement는 미승인 v1.2 초안이므로 기존 tick에 추가하지 않고 현 계약을 검증한다.
        check(msg)
    assert {"good", "fair" if app == "kakao_voice" else "poor"} <= overall
