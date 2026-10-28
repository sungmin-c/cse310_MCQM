# T9a — `--app teams` 추가 (서버 · 더미 스트림 · 문서)

배경: SPEC v8로 측정 앱이 Meet + Teams(Chrome 웹 클라이언트)가 됐다. 서버 `--app`은 아직 `meet|zoom`이고 `teams`가 없다.
Teams 정답 경로는 T9 파일럿 전이라 미확인이므로 `teams`는 `meet`처럼 정답 검증된 앱으로 취급하지 않는다.

## 할 일
1. `server/app.py` `--app` choices에 `teams`를 추가한다. `zoom`은 **지우지 않는다**(SCHEMA·계약 테스트를 팀원과 공유하므로 이 작업에서 건드리지 않음).
2. `server/dummy_stream.py` `--app` choices와 docstring에 `teams`를 추가한다.
3. `judge.py` 등에서 앱 이름으로 분기하는 곳을 확인해, `teams`가 `meet`과 같은 모델·임계값 경로를 타되 `validated`(정답 검증 여부)는 `meet`만 true인 기존 규칙을 따르는지 보인다. 분기가 문자열 비교면 최소 수정으로 맞춘다. 필요 없으면 바꾸지 않는다.
4. 문서 한 줄씩: `docs/COMMANDS.md`의 WS 설명(앱 `meet`, `--app zoom`은 모델 추정값 문구)과 `docs/design/ws_protocol.md`의 `--app` 줄·`app` 필드 설명에 teams를 반영한다. 문구는 "teams는 meet 모델을 그대로 쓴 추정값, 정답 검증은 T9 이후 [가정]"으로 한다.
5. 테스트 추가(`tests/test_ws.py` 또는 가까운 기존 파일): `parse_args(["--live", "--app", "teams"])`가 통과하고, teams로 만든 tick의 `app == "teams"`, `validated`는 live에서 false.

## 하지 말 것
- `SCHEMA.md`, `tests/test_schema_contract.py`의 앱 목록, `dashboard/`, `vcaml/` 수정, 새 의존성, push.
- 기존 `meet` 동작 변경. `--snaplen`, `--every` 옵션 건드리기.

## 완료 기준
- `uv run --no-sync pytest tests/ -q` 전부 통과(현재 201개 + 새 테스트).
- `python -m server.app --live --app teams --help` 대신 `parse_args` 테스트로 확인(실제 캡처 실행 금지).
- 변경 파일 목록과, 3번에서 분기를 바꿨는지 여부를 보고에 적는다.
