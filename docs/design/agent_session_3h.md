# 3시간 병렬 세션 가이드 (2026-10-28) — 창 2개: Claude Code + Codex(GPT)

> 목적: 사용자가 자리에 없어도 3시간 동안 두 AI가 **서로 다른 파일**을 작업한다. 병합·push는 사람이 한다.
> 실측(통화·부하)은 이 세션에 없다. 세션 ②(P5 분석)는 주말 실측 뒤에 따로 한다.

## 역할 분담 (파일이 겹치지 않게)
| 창 | 도구 | 모델 · effort | 작업 | 건드리는 곳 |
|---|---|---|---|---|
| 1 | Claude Code (대화형) | **Opus 5.5 · high** | T10 조치·회복 설계 | `docs/design/recovery.md`, `docs/HANDOFF.md`, `docs/PROGRESS.md` **만** |
| 2 | PowerShell 터미널 → `run_queue.ps1` | Codex **gpt-6.1-sol · high** 구현 → Claude **Opus · high** 리뷰(자동, 읽기 전용) | T9a(`--app teams`) → T13(P5 도구 보강), 작업마다 격리 worktree | `../mcqm-wt-T9a`, `../mcqm-wt-T13` **만** (main 폴더 안 건드림) |

- 창 2의 "GPT"는 Codex를 대화로 쓰는 것이 아니라 `codex exec`가 큐 안에서 자동으로 돈다. 사람이 입력할 것은 명령 한 줄뿐이다.
- 리뷰는 `claude -p`(비대화형)가 자동 호출한다. 창 1의 Claude Code와는 별개 프로세스라 문맥을 나누지 않는다.
- T9a와 T13은 파일이 겹치지 않지만(서버·문서 vs 스크립트·테스트) RAM이 적어(여유 약 1.9GB) **순서대로** 돈다.

## 순서
### 0. 시작 전 (5분, 사용자)
1. **Chrome을 모두 닫는다**(지금 프로세스 38개). Codex·Claude 리뷰·pytest가 동시에 돌아 메모리가 모자랄 수 있다.
2. 충전기 연결. 절전은 `run_queue.ps1`이 프로세스가 도는 동안만 막는다(시스템 설정은 안 바꿈).
3. 두 도구 로그인 확인: 새 PowerShell에서 `codex --version`, `claude --version`(둘 다 설치 확인됨: 0.163.0 / 2.1.312). 로그인이 풀려 있으면 각각 한 번 실행해 로그인한다.
4. 권한 파일은 **바꾸지 않아도 된다**. `ai_loop.ps1`이 `codex exec -C <worktree> --sandbox workspace-write`로 worktree 안에서만 쓰고, 커밋은 스크립트가 한다. 단 Codex 로그에 "write denied"가 보이면 `.codex/config.toml`의 `writable_roots`에 `C:\Users\okggg\Desktop\CSE 310\mcqm-wt-T9a`, `…\mcqm-wt-T13`을 추가한다(권한 파일은 에이전트가 못 바꾸므로 사용자가 직접).

### 1. 창 2 — 큐 시작 (먼저)
repo 루트에서:
```powershell
pwsh scripts/run_queue.ps1 -MaxMinutes 180 -Rounds 2
```
- 새 작업은 180분 안에만 시작한다(진행 중인 작업은 끝까지). 라운드는 작업당 최대 2번(구현 → 리뷰 → 수정 → 리뷰).
- 중단: `Ctrl+C`. 되돌리기: `git worktree remove --force ../mcqm-wt-T9a`, `git branch -D ml/t9a-teams-app` (T13도 같은 방식).

### 2. 창 1 — Claude Code (큐가 시작된 뒤)
```text
claude --model opus --effort high
```
첫 입력:
```text
T10을 설계해줘. docs/design/recovery.md를 새로 쓴다. 코드는 쓰지 않는다.
읽을 것: docs/HANDOFF.md의 T10 항목, docs/PROJECT_SPEC.md v8 §5-1, docs/design/ws_protocol.md, docs/design/diagnosis_v1.md, docs/design/w3_collection.md의 recovery 구간(해제 후 80초), docs/SCOPE_CHANGE_v8.md.
들어갈 것: 원인별 조치 문구(loss·bandwidth·device_cpu), 회복 판정 규칙(N초 유지·T초 제한, 히스테리시스는 judge.md와 일관되게), SCHEMA 필드 제안과 "조치함" client→server 메시지 제안, 테스트 표, 팀원(Web)에게 물을 확인 질문.
규칙: 수정은 docs/design/recovery.md, docs/HANDOFF.md(T10 행·기록 한 줄), docs/PROGRESS.md(T10 관련 한 줄)만. server/, scripts/, tests/, docs/COMMANDS.md, docs/design/ws_protocol.md는 지금 Codex 큐가 다른 worktree에서 다루므로 건드리지 않는다. 임계값 같은 가정은 [가정]으로 표시하고, 회복은 "판정의 지연·정확도"로 평가한다는 SPEC 범위를 넘지 않는다. 끝나면 변경/테스트/남은 것으로 보고.
```
- T10이 끝나면(보통 30–60분) 창 1은 더 시키지 말고 대기해도 된다. 남는 시간에 큐 결과를 같이 보려면 아래 5번을 쓴다.

### 3. 진행 확인 (아무 때나, 사용자)
```powershell
Get-Content data\ai_runs\T9a\summary.txt          # 끝난 작업의 verdict
Get-ChildItem data\ai_runs\T9a                     # codex_N.md(보고), review_N.md(리뷰 VERDICT)
git worktree list
```
- `review_N.md` 첫 줄이 `VERDICT: PASS`이면 그 라운드에서 끝난다. `FIX`면 다음 라운드가 자동으로 이어진다.

### 4. 끝난 뒤 확인 (사용자, 3시간 후)
1. 창 2 맨 아래 `===== 요약 =====`에서 T9a·T13 verdict와 라운드 수.
2. 각 브랜치: `git log --oneline main..ml/t9a-teams-app`, `git diff --stat <기준브랜치> ml/t9a-teams-app`.
3. 테스트: 각 worktree에서 `$env:UV_PROJECT_ENVIRONMENT='C:\Users\okggg\Desktop\CSE 310\cse310_MCQM\.venv'; uv run --no-sync pytest tests/ -q`.
4. FIX로 끝났거나 이상하면 병합하지 말고 창 1에 `data/ai_runs/<Id>/review_*.md`를 읽게 한다.

### 5. 병합과 세션 ② 연결 (사용자 확인 후)
- 두 브랜치 모두 PASS이고 테스트가 통과하면 병합한다(순서 T9a → T13). 병합·push는 Claude도 Codex도 하지 않는다.
- T13 병합 후 `scripts/overhead_report.py`가 보강된 상태로 주말 실측(E1–E7)을 한다. 세션 ② 프롬프트는 이전 안내 그대로 쓴다(Opus · high, 실측 직후 새 세션).

## 한계 (미리 알아둘 것)
- 이 구성은 `ai_loop.ps1`(T1·T3b·T4·T8b에서 쓴 방식)을 그대로 재사용한 것으로, 이번 큐(`run_queue.ps1`)와 `-Base` 옵션은 **처음 돌려 보는 것**이다. 첫 5분(worktree 생성과 Codex 첫 응답)을 지켜보고, 막히면 `Ctrl+C` 후 알려 달라.
- Codex 호출은 사용량 한도에 걸릴 수 있다. 걸리면 로그(`data/ai_runs/<Id>/codex_N.log`)에 남고 큐는 다음 작업으로 넘어간다.
- 3시간은 상한이다. 작업이 작아서 1–2시간에 끝날 수 있다.
