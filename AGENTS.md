# AGENTS.md — cse310_MCQM
(전역 ~/.codex/AGENTS.md에 더해 적용. 충돌하면 이 파일이 우선. Claude Code용은 .claude/CLAUDE.md — 규칙을 바꾸면 양쪽을 같이 고친다)

## 목표 (한 줄)
Windows 노트북의 화상통화(Meet/Zoom) 패킷으로 fps·bitrate·해상도를 실시간 추정하고, 품질 저하 원인이 네트워크인지 기기(CPU)인지 진단한다. 최종 화면은 웹 대시보드.

## 읽을 곳 (필요한 절만)
- 명세: docs/PROJECT_SPEC.md / 일정·결과·결정: docs/PROGRESS.md / 이력: docs/PROJECT_LOG.md
- 계약: docs/SCHEMA.md + docs/schema/sample.jsonl (필드 변경은 SCHEMA.md 규칙 따름)
- 명령: docs/COMMANDS.md (새 명령은 여기에 추가)
- 인계판: docs/HANDOFF.md (Claude↔Codex 작업 큐·모델/effort 추천)
- 개인 경로·솔로 자료: CLAUDE.local.md (git 제외, 있으면 읽기 전용 참고. 없으면 묻기)

## 실행 규칙
- 명령은 OS 중립: `uv run ...`, `npm --prefix dashboard ...`. **항상 repo 루트에서 실행** (vcaml data_root가 실행 위치 기준)
- 셸은 PowerShell. 테스트: `uv run pytest tests/`
- 실행 전 모델과 effort를 추천.
- 작업 끝나면 `변경 / 테스트 / 남은 것` 3줄로 보고. 확인 못 한 것은 "미확인"으로 쓴다

## 소유권
| 경로 | 규칙 |
|---|---|
| vcaml/, pyproject.toml, uv.lock, server/, capture/, scripts/, tests/ | 이 작업의 기본 수정 범위 (Sungmin 소유) |
| overlay/ | 개발 중단(보관). 건드리지 말 것 |
| dashboard/ | 팀원 소유. 수정 금지, 필요하면 제안만 |
| docs/SCHEMA.md, docs/schema/, docs/PROGRESS.md, docs/PROJECT_SPEC.md, README.md, .claude/CLAUDE.md, AGENTS.md, .gitignore | 공동 승인. 수정하면 무엇을 왜 바꿨는지 먼저 알릴 것 |
- vcaml/은 submodule(upstream 원본에 LICENSE 없음). 직접 수정이 필요하면 **먼저 제안**
- 브랜치: main에 직접 커밋 금지. `ml/<주제>`, `web/<주제>`, `docs/<주제>`. 커밋·푸시는 요청받았을 때만

## 절대 금지
- **data/in_lab_data, data/real_world_data는 솔로 자료로 가는 junction이다. 안에서 쓰기·삭제 금지.** 링크 제거는 `cmd /c rmdir`만. `Remove-Item -Recurse` 금지
- 솔로 프로젝트 폴더(CLAUDE.local.md의 경로)는 읽기 전용
- 내 폰·노트북 자신의 트래픽만 캡처. 타인 트래픽·Wi-Fi 스니핑 코드 금지
- pcap·모델 등 대용량은 data/에 두고 git에 올리지 않음
- 드라이버·핫스팟·방화벽 등 시스템 변경 코드는 되돌리는 방법을 docs/COMMANDS.md나 주석에 같이 기록. 실행 전 확인 요청
- 결과물과 조사를 위한 웹 조회는 전면 허용.

## 도메인 주의
- Kakao/Zoom 결과는 `validated:false`, "모델 추정값"으로 표기 (정답 없음)
- Meet는 통화 중 PeerConnection을 갈아탄다. 정답 파싱은 vcaml `WebRTCReader`(첫 PC만) 대신 캡처 구간에 fps>0이 가장 많은 PC를 고른다 (scripts/pilot_live.py `compare` 참고)
- 기존 vcaml 모델은 우리 Windows 실환경에서 오차가 크다(P1: fps MAE 9.09). 모델 성능 주장은 측정값과 함께 쓴다
- 출력 스키마는 docs/SCHEMA.md가 계약이다. 필드 추가·이름 변경 전에 확인

## 코드 스타일
- 주변 코드 스타일과 주석 밀도를 맞춘다. 요청받지 않은 추상화·의존성 추가 금지, 가장 짧은 변경 우선
- 새 의존성은 `pyproject.toml` 변경이 필요하므로 먼저 알린다
- 비자명한 로직엔 작은 테스트 하나를 tests/에 남긴다
- 설명·보고는 한국어, 코드·명령어·기술 용어는 영어

## 코드 리뷰 모드 (리뷰를 요청받았을 때)
- 수정하지 말고 **발견만** 보고한다. 심각도 순, 항목당 `파일:줄 — 문제 — 실패하는 입력/상황`
- 우선순위: ① 정확성(스키마 계약 위반, 시간 정렬·단위 오류, PC 갈아타기 처리) ② 데이터 안전(junction·data/ 쓰기, 시스템 변경) ③ 캡처 윤리 ④ Windows/PowerShell 경로·인코딩 ⑤ 테스트 공백
- 스타일 취향, 사소한 네이밍은 보고하지 않는다. 확신 없으면 "미확인"으로 표시

## 큰 변경은 계획 먼저
스키마, 의존성, 대량 파일 이동·삭제, 시스템 변경은 계획을 먼저 보이고 승인을 기다린다.

## Claude ↔ Codex 협업 프로토콜 (두 AI 모두 따름, 상세표는 docs/HANDOFF.md)
- **시작**: docs/HANDOFF.md의 "현재 상태"와 내 몫 항목만 읽는다. 전체 문서를 훑지 않는다 (토큰 절약)
- **끝**: HANDOFF.md를 갱신한다: 항목 상태, 기록 한 줄(한 일 / **다음 담당 + 모델·effort 추천 + 이유** / 남은 위험). 마일스톤·수치는 PROGRESS.md, 실험·결정 이력은 PROJECT_LOG.md. 문서를 남기지 않은 작업은 끝난 것이 아니다
- **인계 추천**: 다음 작업을 HANDOFF의 역할표로 분류해 담당(Claude/Codex)과 모델·effort를 제안한다. 표와 다르게 추천하면 이유를 적는다. 모델·effort 선택은 사용자가 실행 전에 확정한다
- **분업**: 설계·판단·문서·실험 해석 = Claude, 범위가 명확한 구현·리팩터링·테스트 = Codex. 리뷰는 작성자의 반대편 AI가 한다
- **충돌 방지**: 한 항목(T번호)은 한 작업자만 수정한다. 상대가 진행 중(🟡)인 항목·파일은 건드리지 않는다. 필요하면 HANDOFF에 요청을 적는다
- **질문·제안**: 걸림돌, 모호한 점, 더 효율적인 방법이 보이면 HANDOFF "사용자에게" 란에 적고 응답 끝에서 한 번에 묶어 묻는다(최대 3개, 각 질문에 권장안 포함). 답이 결과를 바꾸지 않는 질문은 하지 말고 기본값으로 진행 후 알린다
- **모르면 추측하지 않는다**: 상대 AI가 한 일은 HANDOFF·git diff로 확인하고, 없으면 "미확인"으로 적는다
