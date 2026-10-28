# AGENTS.md — cse310_MCQM (Claude·Codex 공통. .claude/CLAUDE.md가 이 파일을 import한다 — 규칙은 여기서만 고친다)

## 목표
Windows 노트북의 화상통화(Meet → Teams, 둘 다 Chrome 웹. Zoom은 v8에서 제외) 패킷으로 fps·bitrate·해상도를 실시간 추정하고, 품질 저하 원인(네트워크 vs 기기 CPU)을 진단하고, 안내한 조치 뒤 회복을 판정한다. 최종 화면은 웹 대시보드 + 미니 위젯(대시보드의 Document PiP).

## 읽을 곳 (필요한 절만)
명세 docs/PROJECT_SPEC.md · 일정·결과 docs/PROGRESS.md · 이력 docs/PROJECT_LOG.md · 계약 docs/SCHEMA.md + docs/schema/sample.jsonl · 명령 docs/COMMANDS.md · **인계판 docs/HANDOFF.md** · 개인 경로 CLAUDE.local.md(git 제외, 읽기 전용 참고)

## 실행
- 항상 repo 루트에서 `uv run ...` (PowerShell). 테스트 `uv run pytest tests/ -q`
- worktree에서는 `UV_PROJECT_ENVIRONMENT=<루트>\.venv`와 `--no-sync`로 루트 환경을 공유한다
- 끝나면 `변경 / 테스트 / 남은 것` 3줄. 확인 못 한 것은 "미확인"

## 자율 범위 (이 안에서는 묻지 말고 진행한다)
- **허용**: 읽기, 편집, 테스트, worktree·브랜치 생성, `ml/*` `docs/*` 브랜치에 commit·push, draft PR 생성, 웹 조회(조사·결과물 목적)
- **공동 승인 파일**(SCHEMA.md, docs/schema/, PROGRESS.md, PROJECT_SPEC.md, README.md, AGENTS.md, .claude/CLAUDE.md, .gitignore): 브랜치에서 수정하고 PR 본문에 "공동 승인 필요"를 적는다. 승인은 팀원의 PR 리뷰다
- **사람만**: main 병합, force push, 삭제·`reset --hard`·`git clean`, 새 의존성(pyproject.toml·uv.lock), SCHEMA 확정, 시스템 변경(드라이버·핫스팟·방화벽), 실측(캡처·통화·부하)
- **수정 금지**: dashboard/(팀원 소유, 제안만), overlay/(중단·보관), vcaml/(submodule, 필요하면 먼저 제안)
- 막히면 멈추지 말고 HANDOFF "사용자에게"에 적고 다음 일로 넘어간다
- 브랜치 `ml/<주제>` `web/<주제>` `docs/<주제>`. main 직접 커밋 금지

## 절대 금지
- **data/in_lab_data, data/real_world_data는 솔로 자료 junction.** 안에서 쓰기·삭제 금지, 링크 제거는 `cmd /c rmdir`만. `Remove-Item -Recurse` 금지. 솔로 프로젝트 폴더는 읽기 전용
- 내 폰·노트북 자신의 트래픽만 캡처. 타인 트래픽·Wi-Fi 스니핑 코드 금지
- pcap·모델 등 대용량은 data/에 두고 git 제외. 시스템 변경 코드는 되돌리는 방법을 docs/COMMANDS.md에 같이 기록

## 도메인
- 정답 경로 확인(T9) 전 Teams 결과는 `validated:false`, "모델 추정값". 조치는 안내만, 앱이 직접 실행하지 않는다. 스키마는 docs/SCHEMA.md가 계약(필드 변경 전 확인)
- Meet는 통화 중 PeerConnection을 갈아탄다 → 정답은 fps>0이 가장 많은 PC를 고른다 (scripts/pilot_live.py `compare`)
- vcaml 모델은 우리 환경에서 오차가 크다(P1 fps MAE 9.09). 성능 주장은 측정값과 함께

## 코드
- 주변 스타일 따름, 요청 없는 추상화·의존성 금지, 가장 짧은 변경. 비자명한 로직엔 작은 테스트 하나
- 설명·보고는 한국어, 코드·명령어·용어는 영어

## 리뷰 모드 (요청 시)
수정하지 말고 발견만: 심각도 순, `파일:줄 — 문제 — 실패 상황`. 우선순위 ①정확성(스키마·시간 정렬·단위·PC 갈아타기) ②데이터 안전 ③캡처 윤리 ④Windows 경로·인코딩 ⑤테스트 공백. 취향·사소한 네이밍 제외, 불확실하면 "미확인"

## Claude ↔ Codex 협업 (표·큐는 docs/HANDOFF.md)
- 시작: HANDOFF "현재 상태"와 내 몫만 읽는다. 끝: HANDOFF 갱신(상태 / 한 일 / 다음 담당+모델·effort+이유 / 위험). 수치는 PROGRESS, 실험·결정은 PROJECT_LOG
- 분업: 설계·판단·문서·해석 = Claude, 범위 명확한 구현·테스트 = Codex. 리뷰는 반대편 AI
- 한 T항목은 한 작업자만. 상대가 🟡인 항목·파일은 건드리지 않는다
- **Codex 기본값: gpt-6-luna · medium · Fast** (모델·effort 추천 불필요, 그대로 진행). 같은 작업이 2회 실패(리뷰 FIX 2회·테스트 2회 실패)하면 gpt-6.1-sol · high로 올리고 HANDOFF 기록에 이유를 한 줄 남긴다. Claude는 전역 규칙대로 HANDOFF 표를 따른다
- 질문은 최대 3개를 권장안과 함께 응답 끝에서 한 번에. 결과를 바꾸지 않는 질문은 하지 말고 기본값으로 진행 후 알린다
