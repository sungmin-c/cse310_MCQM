# CLAUDE.md — cse310_MCQM
(전역 ~/.claude/CLAUDE.md의 규칙에 더해 적용. 아래는 전역 규칙의 예외 또는 추가)

## 프로젝트
- 명세: docs/PROJECT_SPEC.md (작업 전 해당 절 재확인)
- 진행 기록: docs/PROGRESS.md (마일스톤마다 완료/미완료/검증 결과 갱신)
- 계약: docs/SCHEMA.md + docs/schema/sample.jsonl (변경 규칙은 SCHEMA.md). 명령 모음: docs/COMMANDS.md
- 기반: vcaml/ (submodule, 브랜치 mcqm. upstream noise-lab/vcaml — 원본에 LICENSE 없음). 직접 수정이 필요하면 먼저 제안
- 솔로 프로젝트 자료(읽기 전용, 수정 금지)와 개인 경로는 CLAUDE.local.md (각자 작성, git 제외)
- 명령은 OS 중립으로: `uv run ...`, `npm --prefix dashboard ...`. 항상 repo 루트에서 실행 (vcaml data_root가 실행 위치 기준)

## 소유권 (소유자만 수정, 상대는 PR 리뷰)
| 경로 | 소유 |
|---|---|
| vcaml/, pyproject.toml, uv.lock, server/, capture/, scripts/, tests/, overlay/ (Flutter) | Sungmin (Windows) |
| dashboard/ | Web (팀원, Mac) |
| overlay/lib/ 버블 UI·문구 (`Bubble` 위젯, `tick.dart` 문구) | 팀원 (10/13 인계). 빌드·S20 실기기 시험·Android 네이티브는 Sungmin |
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