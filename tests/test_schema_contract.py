"""docs/SCHEMA.md 계약 테스트: 서버가 만드는 메시지가 docs/schema/sample.jsonl과 같은 모양인지 검사한다.

sample.jsonl을 바꾸면 이 테스트와 dashboard 쪽 Vitest가 함께 깨진다 — 의도된 동작이다.
"""
import json
from pathlib import Path

from server.dummy_stream import tick

SAMPLE = [
    json.loads(line)
    for line in (Path(__file__).parents[1] / "docs/schema/sample.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]


def kind(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    return type(v).__name__


def leaves(obj, prefix=""):
    """{'est.fps': 'number', 'truth': 'null', ...}"""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out.update(leaves(v, f"{prefix}{k}."))
        return out
    return {prefix[:-1]: kind(obj)}


ALLOWED = {}  # path -> sample에 나온 타입들
for _m in SAMPLE:
    for _p, _t in leaves(_m).items():
        ALLOWED.setdefault(_p, set()).add(_t)


def check(msg):
    ref = SAMPLE[0]
    assert msg.keys() == ref.keys()
    assert msg["est"].keys() == ref["est"].keys()
    assert msg["impair"].keys() == ref["impair"].keys()
    if msg["truth"] is not None:
        assert msg["truth"].keys() == ref["est"].keys()
    for path, t in leaves(msg).items():
        assert t in ALLOWED.get(path, ()), f"{path}: {t} not in {ALLOWED.get(path)}"
    assert msg["mode"] in {"live", "replay", "whatif"}
    assert msg["verdict"] in {"passed", "failed"}
    assert 0 <= msg["qoe"] <= 100
    assert msg["validated"] == (msg["truth"] is not None)


def test_sample_is_consistent():
    for m in SAMPLE:
        check(m)


def test_dummy_ticks_match_sample():
    for app in ("meet", "kakao_video", "kakao_voice", "zoom"):
        for mode in ("replay", "live", "whatif"):
            for i in range(60):
                check(json.loads(json.dumps(tick(i, app, mode, now=0.0))))


def test_dummy_cycle_has_both_verdicts():
    verdicts = {tick(i)["verdict"] for i in range(60)}
    assert verdicts == {"passed", "failed"}
