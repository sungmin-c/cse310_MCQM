"""추정값의 품질 등급. 임계값은 [가정]이며 W3 실측 후 THRESHOLDS에서 보정한다.

[가정] base_len 기본값은 20이다. 사용 가능한 fps/jitter가 모두 good인 1초 행에서
지표별 유효 양수 값 base_len개를 모아 중앙값을 고정한다. 없는 절대 지표는 수집을
막지 않으며, 기준선이 완성되는 행부터 상대 판정한다. 0은 기준선에서 제외한다.
[가정] unknown은 즉시 반영하고 연속 회복을 끊는다. 다음 유효 판정은 즉시 표시한다.
[가정] 경계 일반 규칙보다 명시 구간을 우선한다: jitter=30ms는 fair, 60ms는 poor.
[가정] 정답 유무를 받지 않으므로 validated는 Meet만 True인 앱 수준 표시다.
실제 tick의 truth 기반 validated를 대체하지 않는다.
"""
import math
from collections import deque
from dataclasses import dataclass, field
from statistics import median


THRESHOLDS = {
    "fps": {"good": 24.0, "fair": 15.0},
    "frame_jitter": {"good": 30.0, "fair": 60.0},
    "relative": {"good": 0.8, "fair": 0.5},
    "base_len": 20,
    "recovery_ticks": 2,
}
METRICS = ("fps", "bitrate", "frameHeight", "frame_jitter")
RELATIVE_METRICS = ("bitrate", "frameHeight")
SEVERITY = {"good": 0, "fair": 1, "poor": 2}


@dataclass
class JudgeState:
    """통화 세션마다 새로 만든다. recent에는 지표별 최근 raw 등급을 보관한다."""

    base_len: int = THRESHOLDS["base_len"]
    baseline: dict[str, float] = field(default_factory=dict)
    recent: dict[str, deque[str]] = field(default_factory=lambda: {
        metric: deque(maxlen=THRESHOLDS["recovery_ticks"]) for metric in METRICS
    })
    grades: dict[str, str] = field(default_factory=lambda: {
        metric: "unknown" for metric in METRICS
    })
    _samples: dict[str, list[float]] = field(default_factory=lambda: {
        metric: [] for metric in RELATIVE_METRICS
    }, repr=False)

    def __post_init__(self):
        if self.base_len < 1:
            raise ValueError("base_len must be positive")


def _valid(value):
    return value is not None and math.isfinite(value) and value >= 0


def _stabilize(metric, raw, state):
    recent = state.recent[metric]
    recent.append(raw)
    previous = state.grades[metric]
    if (raw == "unknown" or previous == "unknown"
            or SEVERITY[raw] >= SEVERITY[previous]
            or (len(recent) == recent.maxlen and all(g == raw for g in recent))):
        state.grades[metric] = raw
    return state.grades[metric]


def judge(est: dict, vca: str, state: JudgeState) -> dict:
    """fps, bitrate(bps), frameHeight(px), frame_jitter(ms)의 등급과 overall을 반환한다."""
    values = {metric: est.get(metric) for metric in METRICS}
    raw = {metric: "unknown" for metric in METRICS}

    fps = values["fps"]
    if _valid(fps):
        limits = THRESHOLDS["fps"]
        raw["fps"] = "good" if fps >= limits["good"] else "fair" if fps >= limits["fair"] else "poor"
    jitter = values["frame_jitter"]
    if _valid(jitter):
        limits = THRESHOLDS["frame_jitter"]
        # jitter는 설계의 명시 구간을 따른다: 30ms는 fair, 60ms는 poor.
        raw["frame_jitter"] = "good" if jitter < limits["good"] else "fair" if jitter < limits["fair"] else "poor"

    healthy = all(raw[metric] in ("good", "unknown") for metric in ("fps", "frame_jitter"))
    for metric in RELATIVE_METRICS:
        value = values[metric]
        if not _valid(value):
            continue
        if metric not in state.baseline and healthy and value > 0:
            samples = state._samples[metric]
            samples.append(value)
            if len(samples) == state.base_len:
                state.baseline[metric] = median(samples)
                samples.clear()
        baseline = state.baseline.get(metric)
        if baseline is not None and _valid(baseline) and baseline > 0:
            ratio = value / baseline
            limits = THRESHOLDS["relative"]
            raw[metric] = "good" if ratio >= limits["good"] else "fair" if ratio >= limits["fair"] else "poor"

    result = {metric: _stabilize(metric, raw[metric], state) for metric in METRICS}
    result["overall"] = max((g for g in result.values() if g != "unknown"),
                            key=SEVERITY.__getitem__, default="unknown")
    result["validated"] = vca == "meet"
    return result
