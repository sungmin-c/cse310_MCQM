# HANDOFF — Claude ↔ Codex 작업 인계판
> 두 AI가 세션 시작 때 **이 파일 상단(현재 상태 + 내 몫)만** 읽고, 세션 끝에 갱신한다. 80줄 이하 유지.
> 마일스톤·결과 수치 → PROGRESS.md / 실험·결정 이력 → PROJECT_LOG.md / 여기는 "지금 누가 무엇을" 만.
> 완료 항목은 한 줄로 줄여 PROJECT_LOG에 옮기고 여기서 지운다.

## 현재 상태 (갱신: 2026-10-16, Codex)
- 주차: W2 (10/20–10/26, Midterm 1 10/21). T1·T3b 후속 수정 커밋 완료(`19028f7`, `f2c9db6`), 문서 분리·push 진행. T4 착수 대기. 이전 세션 리뷰 루프 실행 여부 미확인
- 마지막 작업자: Codex (T1·T3b 재검증·후속 수정 커밋, 게시 재개)

## 역할과 모델/effort 추천표 (시작값. 결과가 나쁘면 한 단계 올리고 이유를 아래 기록에 남긴다)
| 작업 유형 | 담당 | 모델 · effort | 이유 |
|---|---|---|---|
| 설계, 스키마·계약, 원인진단 로직 설계, 실험 해석, 문서 | Claude | Opus 5.5 · high (가벼운 문서는 Sonnet 5.5 · medium) | 문맥·판단 비중이 큼 |
| 범위·완료 기준이 명확한 구현, 리팩터링, 테스트 작성 | Codex | gpt-6-luna · medium | 지시를 그대로 수행, 토큰 대비 효율 |
| 어려운 버그, 동시성·실시간 파이프라인 | Codex | gpt-6-luna · high | 추론 필요 |
| 단순 수정, 이름 변경, 명령 문서화 | 둘 중 지금 열린 쪽 | Sonnet 5.5 · low 또는 luna · low | 비용 최소 |
| 코드 리뷰 | **작성자와 반대편** | Codex: `codex review --uncommitted` / Claude: `/code-review` | 다른 모델이 보면 놓침이 줄어듦 |
| 실측(tshark 캡처, 통화, CPU 부하) | **사용자** | — | 장비 필요. AI는 절차·스크립트만 준비 |

## 큐 (T번호 = 작업 ID. 한 항목은 한 번에 한 작업자만 수정)
| ID | 작업 | 담당 → 모델·effort | 상태 | 읽을 것 | 완료 기준 |
|---|---|---|---|---|---|
| T1 | `scripts/pilot_live.py` capture 로직을 `capture/tshark_live.py`로 분리 (브랜치 `ml/t1-tshark-live`) | Codex sol·high + Claude 리뷰 | ✅ 리뷰 PASS 2회(2차는 미커밋 수정 기준), **커밋·push·draft PR 대기** | PROGRESS W1 결과 절, pilot_live.py, overhead_ab.py | overhead_ab·cpu_load 안 깨짐, 동작 불변, COMMANDS.md 반영, pytest 통과 |
| T2 | T1 결과 리뷰 (루프가 자동 수행, 최종 사람 확인) | Claude → Opus·high | 🟡 | T1 diff | 발견 목록 |
| T3 | `judge.py` 입출력 설계 → `docs/design/judge.md` | Claude | ✅ | — | 설계 문서 + 테스트 표 |
| T3b | `server/judge.py` 구현 (브랜치 `ml/t3b-judge`) | Codex → gpt-6.1-sol·xhigh + Claude 리뷰 루프 | ✅ 리뷰 PASS 2회(2차 미커밋 기준, 중간 지적 처리됨), **커밋·push·draft PR 대기** | docs/design/judge.md | 테스트 표 전부 통과 |
| T4 | FastAPI WS (Live·Replay) 구현 (브랜치 `ml/t4-ws` = T1+T3b 위) | Codex → sol·high | ⬜ **착수 가능** (설계 완료) | docs/design/ws_protocol.md, docs/briefs/T4.md | ws_protocol §9 |
| T5 | WS 메시지 계약 설계 → `docs/design/ws_protocol.md` | Claude | ✅ 10/16 | — | T4 브리프 |
| T6 | SCHEMA v1.2 제안 → `docs/design/schema_v1.2_proposal.md` | Claude → 팀원(Web) 확인 | ⏳ 팀원 답 대기 (Q1–Q8) | 제안 문서 §4 | 승인 후 §5 반영 PR |
| T7 | W3 수집 절차 → `docs/design/w3_collection.md` | Claude ✅ → 사용자 실측 | ⬜ S0 사전 점검부터 | 절차 문서 | 30통화 `ok` |
| T8 | diagnosis v1 (`device_cpu`) 설계 → `docs/design/diagnosis_v1.md` | Claude → Opus·high, 구현은 Codex | ⬜ | PROJECT_SPEC §1·§3-4, PROGRESS P2, server/diagnosis.py | 규칙·입력(device)·테스트 표 |

## 기록 (최신이 위. 항목당 3줄 이내: 한 일 / 다음 담당·모델·effort 추천+이유 / 남은 위험)
- 2026-10-16 Codex: 사용자 요청으로 게시 재개. 공유 .venv에서 T1 39 passed+1 skipped, T3b 104 passed+1 skipped 재확인 후 후속 수정 커밋. 다음: 문서 브랜치 분리 후 T1·T3b를 그 위로 정리·draft PR, 문서 PR 병합 후 base main 전환. 이후 T4 Codex sol·high(동시성). 위험: data 없는 테스트 skip, tshark 실측 미확인.
- 2026-10-16 15:20 Claude 루프: T1·T3b 미커밋 후속 수정 리뷰 PASS (`data/ai_runs/review_T1_2.md` 39 passed+1 skipped, `review_T3b_2.md` 104 passed+1 skipped). 대신 커밋하려 했으나 권한 분류기가 worktree 커밋·이후 git 조회를 막아 push·PR 못 함. 다음: 사용자가 커밋·push·PR(아래 "사용자에게" 1번) → T4 Codex sol·high. 위험: codex_notes에 Codex 답 기록 없음(Codex 실행 여부 미확인).
- 2026-10-16 Claude: T5 ws_protocol·T4 브리프, T6 v1.2 제안, T7 W3 절차 작성. 리뷰 지적은 `data/ai_runs/codex_notes.md` "Claude 리뷰"로 이관, 15분 리뷰 루프 시작. 다음: T4 → Codex sol·high (스레드↔asyncio 연결이 실시간 파이프라인이라 표의 "동시성" 행). 위험: T4는 pyproject 변경 금지라 WS 테스트를 ASGI 직접 호출로 함(httpx 미설치); W3 S0-1(캡처에 손실이 보이는지) 미확인.
- 2026-10-16 루프(T1): Codex 구현 → Claude PASS, pytest 39 passed+1 skipped(data 없음; 기존 43+신규 11이면 54 예상, 미확인). 다음: 사용자가 `ml/t1-tshark-live` diff 확인·병합, tshark 실측. 위험: 문서 2곳("pytest 차단" 문구)과 테스트의 전역 `time.perf_counter` 패치(tests/test_tshark_live.py:153)는 luna·low 후속 수정 필요.
- 2026-10-16 Claude: 자동 루프 도입(Codex 구현→Claude 리뷰→수정, 최대 3라운드, worktree 격리·push 없음). T3 설계 완료, T1·T3b 루프 시작. 다음: 결과는 사용자가 브랜치 diff 확인 후 병합. 위험: SCHEMA judgement 필드는 팀원 승인 전 미반영.
- 2026-10-16 Claude: 프로토콜 도입, T1–T4 시드. 다음: T1 → Codex luna·medium (범위가 명확한 리팩터링). 위험: 실제 tshark 캡처는 사용자 실측 전까지 미검증.

## 사용자에게 (걸림돌·제안·모호한 점. 답 받으면 지우고 결정은 PROGRESS "결정 사항"으로)
**다음 세션 순서 (10/16 작성. 각 단계 시작 전: 이 HANDOFF "현재 상태" + PROJECT_SPEC 해당 절 확인 → 계획 → 실행)**
- S1 [사용자] 커밋이 오면(또는 Codex가 안 하면 직접) T1·T3b 후속 수정 커밋. 리뷰한 diff hash `T1=1FA27B6632F5 T3b=061F2D996E57` (state 파일)
  `foreach($t in "T1","T3b"){ git -C "..\mcqm-wt-$t" add -A; git -C "..\mcqm-wt-$t" commit -m "fix(${t}): review round 1 follow-up" }`
- S2 [Claude] 에이전트 문서를 main에 먼저 넣는 docs PR (ctx 커밋 충돌 해소. `.claude/CLAUDE.md`는 공동 승인 파일)
  `git switch -c docs/agent-protocol; git add AGENTS.md .claude/CLAUDE.md docs/HANDOFF.md docs/briefs docs/design docs/PROGRESS.md scripts/ai_loop.ps1; git commit; git push -u origin docs/agent-protocol; gh pr create --draft`
- S3 [사용자] S2 병합 후 T1·T3b에서 ctx 커밋을 빼고 main 위로 옮긴 뒤 push + draft PR (아직 push 전이라 force push 불필요)
  `git -C ..\mcqm-wt-T1 rebase --onto origin/main 410d5fb; git -C ..\mcqm-wt-T3b rebase --onto origin/main 04dd093` (git fetch 먼저. `docs/HANDOFF.md` 충돌이 나면 main 쪽을 택함: `git checkout --ours docs/HANDOFF.md; git add docs/HANDOFF.md; git rebase --continue`)
  `git -C ..\mcqm-wt-T1 push -u origin ml/t1-tshark-live; gh pr create --draft --base main --head ml/t1-tshark-live --title "T1: capture/tshark_live.py 분리" --body-file data/ai_runs/pr_T1.md` (T3b도 같게, `pr_T3b.md`. 본문의 "ctx 포함 주의" 줄은 삭제)
- S4 [Codex sol·high] T4. T1·T3b 병합 전이면 둘을 합친 worktree를 직접 만든다 (ai_loop는 main에서 분기하므로):
  `git worktree add ..\mcqm-wt-T4 -b ml/t4-ws ml/t1-tshark-live; git -C ..\mcqm-wt-T4 merge ml/t3b-judge; New-Item -ItemType Directory -Force ..\mcqm-wt-T4\data\models; Copy-Item data\models\* ..\mcqm-wt-T4\data\models\`
  `pwsh scripts/ai_loop.ps1 -Id T4 -Branch ml/t4-ws -Brief docs/briefs/T4.md -ImplEffort high`
- S5 [Claude Opus·high] 리뷰 루프 재시작(`/loop 15m [MCQM 리뷰 루프] …`) + T8 설계(diagnosis v1 `device_cpu`, PROJECT_SPEC §1·§3-4, PROGRESS P2). T4 PASS 후 T4 push만 (PR 없음, 통합 브랜치)
- S6 [사용자] 팀원에게 v1.2 질문 Q1–Q8 전달 / W3 전 사전 점검 S0 (`w3_collection.md` §0, 특히 S0-1)
- judge 임계값 근거: 표준(G.1070) vs 수집 데이터 분위수 (docs/design/judge.md 하단, 권장: [가정]값 시작 → W3 후 보정)
