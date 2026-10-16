# T3b — server/judge.py 구현
`docs/design/judge.md`를 그대로 구현한다 (설계가 계약. 모호하면 [가정]으로 표시하고 가장 단순한 쪽 선택).
요구
1. `server/judge.py`: `JudgeState`(dataclass), `judge(est, vca, state)`. 임계값은 모듈 상단 상수 하나로 모아 W3 보정이 쉽게.
2. `tests/test_judge.py`: 설계 문서 "테스트 표" 전 항목. 단조성은 값 스윕 루프로.
3. 순수 Python(+numpy 가능), 새 의존성 금지. `server/features.py`·`diagnosis.py`·SCHEMA는 수정하지 말 것.
4. 마지막 항목(합성 스트림 재생 → SCHEMA 계약 통과)은 `docs/SCHEMA.md`와 `tests/test_schema_contract.py`를 읽고 judgement 필드 추가가 필요한지 판단만 하고, **필요하면 수정하지 말고 보고에 적는다** (SCHEMA는 공동 승인 파일).
5. `uv run --no-sync pytest tests/ -q` 전체 통과 (기준 43 passed).
완료 기준 = 위 1~5. dashboard/·vcaml/ 변경 없음.
