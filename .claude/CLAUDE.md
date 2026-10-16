# CLAUDE.md — cse310_MCQM
(전역 ~/.claude/CLAUDE.md의 규칙에 더해 적용. 아래는 전역 규칙의 예외 또는 추가)

## 프로젝트
- 명세: docs/PROJECT_SPEC.md (작업 전 해당 절 재확인)
- 진행 기록: docs/PROGRESS.md (마일스톤마다 완료/미완료/검증 결과 갱신)
- 계약: docs/SCHEMA.md + docs/schema/sample.jsonl (변경 규칙은 SCHEMA.md). 명령 모음: docs/COMMANDS.md
- 인계판: docs/HANDOFF.md (Claude↔Codex 작업 큐·모델/effort 추천. 아래 협업 프로토콜 필수)
- 기반: vcaml/ (submodule, 브랜치 mcqm. upstream noise-lab/vcaml — 원본에 LICENSE 없음). 직접 수정이 필요하면 먼저 제안
- 솔로 프로젝트 자료(읽기 전용, 수정 금지)와 개인 경로는 CLAUDE.local.md (각자 작성, git 제외)
- 명령은 OS 중립으로: `uv run ...`, `npm --prefix dashboard ...`. 항상 repo 루트에서 실행 (vcaml data_root가 실행 위치 기준)

## 소유권 (소유자만 수정, 상대는 PR 리뷰)
| 경로 | 소유 |
|---|---|
| vcaml/, pyproject.toml, uv.lock, server/, capture/, scripts/, tests/, overlay/ (Flutter, v6 보관: 개발 중단) | Sungmin (Windows) |
| dashboard/ | Web (팀원, Mac). v6: 웹 대시보드가 최종 화면, 네이티브 앱 없음 |
| docs/SCHEMA.md, docs/schema/, docs/PROGRESS.md, docs/PROJECT_SPEC.md, README.md, .claude/CLAUDE.md, .gitignore | 공동 — 둘 다 승인 |
- 브랜치: main은 PR로만. 작업은 `ml/<주제>`, `web/<주제>`, `docs/<주제>`. 짧게 유지, squash merge
- **data/in_lab_data, data/real_world_data는 솔로 자료로의 junction이다. 안에서 파일을 지우거나 쓰지 말 것. 링크 제거는 `cmd /c rmdir`만**

## 전역 규칙의 예외
- 웹 조회 사전 승인 불필요 범위: github.com/noise-lab/vcaml, w3c.github.io/webrtc-stats,
  PCAPdroid/scrcpy/gnirehtet/Clumsy 공식 repo·문서, scikit-learn/FastAPI/Vite/Chart.js 공식 문서,
  www.itu.int (G.1070 등 QoE 표준), pub.dev (Flutter 패키지) — 2026-10-13 승인.
  그 외 사이트와 모든 커넥터는 전역 규칙대로 먼저 묻기

## 추가 규칙
- 설명은 한국어, 코드·명령어·기술 용어는 영어
- 확인하지 않은 것은 "미확인"으로 표기하고 질문
- Kakao/Zoom 결과는 validated:false, "모델 추정값"으로 표기 (정답 없음)
- 내 폰·노트북 자신의 트래픽만 캡처. 타인 트래픽·Wi-Fi 스니핑 코드 금지
- make 불가 시 Makefile 타겟을 uv 명령으로 번역해 docs/COMMANDS.md에 기록
- 시스템 변경(드라이버, 핫스팟, 방화벽)은 되돌리는 방법도 함께 기록
- pcap·모델 등 대용량 데이터는 data/ 에 두고 git과 qmd 인덱스에서 제외
## Claude ↔ Codex 협업 프로토콜 (두 AI 모두 따름, 상세표는 docs/HANDOFF.md)
- **시작**: docs/HANDOFF.md의 "현재 상태"와 내 몫 항목만 읽는다. 전체 문서를 훑지 않는다 (토큰 절약)
- **끝**: HANDOFF.md를 갱신한다: 항목 상태, 기록 한 줄(한 일 / **다음 담당 + 모델·effort 추천 + 이유** / 남은 위험). 마일스톤·수치는 PROGRESS.md, 실험·결정 이력은 PROJECT_LOG.md. 문서를 남기지 않은 작업은 끝난 것이 아니다
- **인계 추천**: 다음 작업을 HANDOFF의 역할표로 분류해 담당(Claude/Codex)과 모델·effort를 제안한다. 표와 다르게 추천하면 이유를 적는다. 모델·effort 선택은 사용자가 실행 전에 확정한다
- **분업**: 설계·판단·문서·실험 해석 = Claude, 범위가 명확한 구현·리팩터링·테스트 = Codex. 리뷰는 작성자의 반대편 AI가 한다
- **충돌 방지**: 한 항목(T번호)은 한 작업자만 수정한다. 상대가 진행 중(🟡)인 항목·파일은 건드리지 않는다. 필요하면 HANDOFF에 요청을 적는다
- **질문·제안**: 걸림돌, 모호한 점, 더 효율적인 방법이 보이면 HANDOFF "사용자에게" 란에 적고 응답 끝에서 한 번에 묶어 묻는다(최대 3개, 각 질문에 권장안 포함). 답이 결과를 바꾸지 않는 질문은 하지 말고 기본값으로 진행 후 알린다
- **모르면 추측하지 않는다**: 상대 AI가 한 일은 HANDOFF·git diff로 확인하고, 없으면 "미확인"으로 적는다
