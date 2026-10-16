# HANDOFF — Claude ↔ Codex 작업 인계판
> 두 AI가 세션 시작 때 **이 파일 상단(현재 상태 + 내 몫)만** 읽고, 세션 끝에 갱신한다. 80줄 이하 유지.
> 마일스톤·결과 수치 → PROGRESS.md / 실험·결정 이력 → PROJECT_LOG.md / 여기는 "지금 누가 무엇을" 만.
> 완료 항목은 한 줄로 줄여 PROJECT_LOG에 옮기고 여기서 지운다.

## 현재 상태 (갱신: 2026-10-16 밤, Claude)
- 주차: W2 (10/20–10/26, Midterm 1 10/21). draft PR #5(문서)·#6(T1)·#7(T3b) 병합 대기. **T4 ✅ 리뷰 PASS·push (`ml/t4-ws` `431faef`, T1 `31243bf` 포함)**. **T8b ✅ ①②③ 리뷰 PASS·push (`ml/t8b-diag-v1` `6cfaf2c`, = T8b + T4, 176 passed+1 skipped)** → W3 전 코드 준비 끝, 다음은 사용자 W3 S0 사전 점검
- **Codex 샌드박스는 git 쓰기·Python 실행이 막혀 있다** → Codex는 worktree 파일 수정 + `codex_notes.md` 기록까지만, pytest·커밋·push는 Claude 리뷰 루프가 한다
- 테스트 환경: 이벤트 루프 생성 시 `socket.socketpair()`가 WinError 10014로 가끔 실패(앱 없이 `asyncio.run`만 돌려도 300회 중 27회). test_ws 실패가 이 오류뿐이면 환경 문제로 본다
- 이번 세션 발견: P2P 흐름 포트가 49152를 넘으면 tshark가 RTP를 해석 못 함 → T1에 수정 커밋 `31243bf`(PR #6). 코어 고정 시 CPU%가 낮게 보임 → `call_core_pct` 설계
- 마지막 작업자: Claude (T4 리뷰·수정 2건·push, T8b ③ 리뷰·커밋·push)

## 역할과 모델/effort 추천표 (시작값. 결과가 나쁘면 한 단계 올리고 이유를 아래 기록에 남긴다)
| 작업 유형 | 담당 | 모델 · effort | 이유 |
|---|---|---|---|
| 설계, 스키마·계약, 원인진단 로직 설계, 실험 해석, 문서 | Claude | Opus 5.5 · high (가벼운 문서는 Sonnet 5.5 · medium) | 문맥·판단 비중이 큼 |
| 구현, 리팩터링, 테스트 작성 (Codex **기본값**) | Codex | **gpt-6-luna · medium · Fast** | 속도·토큰 효율. 이 repo에서 luna 성능은 미확인 → 결과를 기록에 남긴다 |
| 같은 작업이 2회 실패 (리뷰 FIX 2회 또는 테스트 2회 실패), 동시성·실시간 파이프라인 | Codex | gpt-6.1-sol · high | 추론 필요. 해결되면 기본값으로 복귀 |
| 단순 수정, 이름 변경, 명령 문서화 | 둘 중 지금 열린 쪽 | Sonnet 5.5 · low 또는 luna · low | 비용 최소 |
| 코드 리뷰 | **작성자와 반대편** | Codex: `codex review --uncommitted` / Claude: `/code-review` | 다른 모델이 보면 놓침이 줄어듦 |
| 실측(tshark 캡처, 통화, CPU 부하) | **사용자** | — | 장비 필요. AI는 절차·스크립트만 준비 |

## 큐 (T번호 = 작업 ID. 한 항목은 한 번에 한 작업자만 수정)
| ID | 작업 | 담당 → 모델·effort | 상태 | 읽을 것 | 완료 기준 |
|---|---|---|---|---|---|
| T1 | `scripts/pilot_live.py` capture 로직을 `capture/tshark_live.py`로 분리 (브랜치 `ml/t1-tshark-live`) | Codex sol·high + Claude 리뷰 | ✅ 리뷰 PASS 2회(2차는 미커밋 수정 기준), **커밋·push 완료·draft PR #6 (base: docs/agent-protocol)** | PROGRESS W1 결과 절, pilot_live.py, overhead_ab.py | overhead_ab·cpu_load 안 깨짐, 동작 불변, COMMANDS.md 반영, pytest 통과 |
| T2 | T1 결과 리뷰 (루프가 자동 수행, 최종 사람 확인) | Claude → Opus·high | 🟡 | T1 diff | 발견 목록 |
| T3 | `judge.py` 입출력 설계 → `docs/design/judge.md` | Claude | ✅ | — | 설계 문서 + 테스트 표 |
| T3b | `server/judge.py` 구현 (브랜치 `ml/t3b-judge`) | Codex → gpt-6.1-sol·xhigh + Claude 리뷰 루프 | ✅ 리뷰 PASS 2회(2차 미커밋 기준, 중간 지적 처리됨), **커밋·push 완료·draft PR #7 (base: docs/agent-protocol)** | docs/design/judge.md | 테스트 표 전부 통과 |
| T4 | FastAPI WS (Live·Replay) 구현 (브랜치 `ml/t4-ws` = T1+T3b 위) | Codex → sol·high + Claude 리뷰 | ✅ 10/16 리뷰 PASS(Claude 수정 2건: `WebSocketDisconnected` 처리, Live tshark `rtp_udp`), 커밋 `0e6b96d`·T1 merge `431faef`·push(PR 없음, 통합 브랜치). 125 passed+1 skipped (환경 오류 제외) | docs/design/ws_protocol.md, docs/briefs/T4.md | ws_protocol §9 |
| T5 | WS 메시지 계약 설계 → `docs/design/ws_protocol.md` | Claude | ✅ 10/16 | — | T4 브리프 |
| T6 | SCHEMA v1.2 제안 → `docs/design/schema_v1.2_proposal.md` | Claude → 팀원(Web) 확인 | ⏳ 팀원 답 대기 (Q1–Q9, Q9 = `call_core_pct` 10/16 추가) | 제안 문서 §4 | 승인 후 §5 반영 PR |
| T7 | W3 수집 절차 → `docs/design/w3_collection.md` | Claude ✅ → 사용자 실측 | ⬜ S0 사전 점검부터 | 절차 문서 | 30통화 `ok` |
| T8 | diagnosis v1 (`device_cpu`) 설계 → `docs/design/diagnosis_v1.md` | Claude | ✅ 10/16 | — | 규칙·입력·평가·테스트 표 |
| T8b | diagnosis v1 구현: ① `OsSampler.call_core_pct` ② `Diagnoser(device, flow)` ③ T4 tick 연결 ④ `scripts/diag_eval.py` (브랜치 `ml/t8b-diag-v1`, ③은 T4 위) | Codex → luna·medium (기본값) + Claude 리뷰 | 🟡 ①② ✅ Claude 리뷰 PASS·push (`f044681`·`1d16ced`, 87 passed+1 skipped). ✅ ③ Codex 패치 → Claude 리뷰 PASS·커밋 `6cfaf2c`·push (낮음 2건, `codex_notes.md` "Claude 리뷰 T8b ③"). 실측 미확인(W3 S0-3·S0-4) | docs/briefs/T8b.md 3단계, docs/design/t8b_implementation.md "3단계 후속 지점" | ③ 테스트 통과 및 Claude 리뷰 |

## 기록 (최신이 위. 항목당 3줄 이내: 한 일 / 다음 담당·모델·effort 추천+이유 / 남은 위험)
- 2026-10-16 밤 Claude 루프: Codex T8b ③ 패치(창별 주 흐름 집계 + device·flow를 Diagnoser로) 적용 → 176 passed+1 skipped, 리뷰 PASS(낮음 2), 커밋·push `6cfaf2c`, 루프 종료. 다음: 사용자 W3 S0(특히 S0-3 RTP 비율, S0-4 `call_core_pct` 2코어 고정 ≥85) → 이후 diag_eval은 Codex luna·medium. 위험: WinError 10014 환경 문제 지속, 브랜치 PR·병합 순서(#5→#6·#7→t4→t8b) 사람 결정.
- 2026-10-16 밤 Claude: T4 미커밋 변경 리뷰 → 높음(종료 시 `WebSocketDisconnected` 미처리, 결정적 테스트 실패)·중간(Live tshark `rtp_udp` 누락) 직접 수정, 커밋·T1 merge·push(`431faef`). T8b에 T4 merge·push(`2dd55ea`, 172 passed+1 skipped, 환경 오류 1). 다음: T8b ③ Codex sol·high(실시간 연결, 표의 "동시성" 행). 위험: WinError 10014 환경 문제 원인 미확인(보안 프로그램 `KOSinj` 등 Winsock 후킹 의심), tshark 인자 두 곳 중복(낮음).
- 2026-10-16 밤 Claude 루프: Codex 패치 T8b_01·02를 새 worktree `mcqm-wt-T8b`(브랜치 `ml/t8b-diag-v1`, T1 `31243bf` 위)에 적용 → pytest 47+1s / 87+1s, 리뷰 PASS(낮음 3건, `codex_notes.md` "Claude 리뷰 T8b"), 커밋·push(PR 없음). T1 worktree는 그대로. 다음: T4 커밋·PASS 뒤 ③ Codex sol·high(실시간 연결). 위험: 실측 affinity·≥85 미확인(W3 S0-4), diag_eval 실 dump 미검증.
- 2026-10-16 사용자 지시: T1·T4 완료까지 대기. 둘 다 완료되면 Codex가 T8b ③ 연결을 시작한다. 선행 조건과 T4 변경사항을 그때 재확인한다.
- 2026-10-16 Codex: T4 미커밋·PASS 없음 확인. T8b ①②를 `data/ai_runs/T8b-work`에 구현, 단계 패치 2개가 T1 `31243bf`에 `git apply --check` 통과. 기존 diagnosis 13개 테스트 유지. 다음: 사용자 권한 세션에서 `ml/t8b-diag-v1` 생성·pytest → Claude 리뷰(반대편 AI), ③은 T4 PASS 뒤 Codex sol·high(실시간 연결). 위험: Python 실행·Git 쓰기 차단, 실행 테스트·실측 미확인. 상세 `docs/design/t8b_implementation.md`.
- 2026-10-16 저녁 Claude: T8 설계(`diagnosis_v1.md`) — P2 원자료 재분석으로 근거 확보(수신 패킷 정상, 코어 고정 시 CPU%가 낮게 보임, v0.1 `loss` 오탐은 relay→P2P 전환+RTP 미해석). T1에 `--enable-heuristic rtp_udp` 커밋·push(`31243bf`, 39 passed+1 skipped). v1.2 제안 Q9·W3 S0-3/S0-4 추가. 다음: T8b → Codex luna·medium(설계가 테스트 표까지 정해져 범위 명확). 위험: RTP 휴리스틱은 실통화 pcap이 없어 미검증(W3 S0-3), T4와 tshark_live.py 충돌 가능, 리뷰 루프는 T4 커밋 뒤 대상 생김.
- 2026-10-16 Codex: 사용자 요청으로 게시 재개. 공유 .venv에서 T1 39 passed+1 skipped, T3b 104 passed+1 skipped 재확인 후 후속 수정 커밋. 문서 #5·T1 #6·T3b #7 draft PR 게시 완료(중복 ctx 제거). 다음: 문서 PR 병합 후 T1·T3b base main 전환. 이후 T4 Codex sol·high(동시성). 위험: data 없는 테스트 skip, tshark 실측 미확인.
- 2026-10-16 15:20 Claude 루프: T1·T3b 미커밋 후속 수정 리뷰 PASS (`data/ai_runs/review_T1_2.md` 39 passed+1 skipped, `review_T3b_2.md` 104 passed+1 skipped). 대신 커밋하려 했으나 권한 분류기가 worktree 커밋·이후 git 조회를 막아 push·PR 못 함. 다음: 사용자가 커밋·push·PR(아래 "사용자에게" 1번) → T4 Codex sol·high. 위험: codex_notes에 Codex 답 기록 없음(Codex 실행 여부 미확인).
- 2026-10-16 Claude: T5 ws_protocol·T4 브리프, T6 v1.2 제안, T7 W3 절차 작성. 리뷰 지적은 `data/ai_runs/codex_notes.md` "Claude 리뷰"로 이관, 15분 리뷰 루프 시작. 다음: T4 → Codex sol·high (스레드↔asyncio 연결이 실시간 파이프라인이라 표의 "동시성" 행). 위험: T4는 pyproject 변경 금지라 WS 테스트를 ASGI 직접 호출로 함(httpx 미설치); W3 S0-1(캡처에 손실이 보이는지) 미확인.
- 2026-10-16 루프(T1): Codex 구현 → Claude PASS, pytest 39 passed+1 skipped(data 없음; 기존 43+신규 11이면 54 예상, 미확인). 다음: 사용자가 `ml/t1-tshark-live` diff 확인·병합, tshark 실측. 위험: 문서 2곳("pytest 차단" 문구)과 테스트의 전역 `time.perf_counter` 패치(tests/test_tshark_live.py:153)는 luna·low 후속 수정 필요.
- 2026-10-16 Claude: 자동 루프 도입(Codex 구현→Claude 리뷰→수정, 최대 3라운드, worktree 격리·push 없음). T3 설계 완료, T1·T3b 루프 시작. 다음: 결과는 사용자가 브랜치 diff 확인 후 병합. 위험: SCHEMA judgement 필드는 팀원 승인 전 미반영.
- 2026-10-16 Claude: 프로토콜 도입, T1–T4 시드. 다음: T1 → Codex luna·medium (범위가 명확한 리팩터링). 위험: 실제 tshark 캡처는 사용자 실측 전까지 미검증.

## 사용자에게 (걸림돌·제안·모호한 점. 답 받으면 지우고 결정은 PROGRESS "결정 사항"으로)
- T8b: Codex sandbox가 `.git/refs` 쓰기·`.venv` Python 실행을 거부한다(①②는 Claude가 대신 적용해 해결). T4도 같은 이유로 막혔을 수 있다 → Codex 권한 설정 확인 필요. ③은 T4 커밋·PASS 뒤.
**다음 세션 순서 (10/16 작성. 각 단계 시작 전: 이 HANDOFF "현재 상태" + PROJECT_SPEC 해당 절 확인 → 계획 → 실행)**
- S1–S3 완료: 문서 draft PR [#5](https://github.com/sungmin-c/cse310_MCQM/pull/5), T1 [#6](https://github.com/sungmin-c/cse310_MCQM/pull/6), T3b [#7](https://github.com/sungmin-c/cse310_MCQM/pull/7). T1·T3b는 중복 ctx 제거 후 docs/agent-protocol 위로 rebase·push했다. #5 먼저 병합 → #6·#7 base를 main으로 전환. 이번 범위는 draft PR까지이며 병합·T4는 미실행.
- S4 [Codex sol·high] T4. T1·T3b 병합 전이면 둘을 합친 worktree를 직접 만든다 (ai_loop는 main에서 분기하므로):
  `git worktree add ..\mcqm-wt-T4 -b ml/t4-ws ml/t1-tshark-live; git -C ..\mcqm-wt-T4 merge ml/t3b-judge; New-Item -ItemType Directory -Force ..\mcqm-wt-T4\data\models; Copy-Item data\models\* ..\mcqm-wt-T4\data\models\`
  `pwsh scripts/ai_loop.ps1 -Id T4 -Branch ml/t4-ws -Brief docs/briefs/T4.md -ImplEffort high`
- S5 [Claude] ✅ T8 설계 + T1 RTP 수정(`31243bf`). **결정(10/16): 리뷰 루프는 T4 커밋 확인 후 새 Claude 세션에서** `/loop 15m [MCQM 리뷰 루프] …`(대상 `mcqm-wt-T4`, 상태 `data/ai_runs/claude_review_state.txt`). T4 PASS 후 T4 push만 (PR 없음, 통합 브랜치)
- S5b [Codex luna·medium] T8b — 브리프 `docs/briefs/T8b.md`. 1단계(`call_core_pct`, `ml/t1-tshark-live`에서 분기)부터. 2단계(Diagnoser·diag_eval)는 T4와 무관해 이어서, 3단계만 T4 뒤
- S6 [사용자] 팀원에게 v1.2 질문 Q1–Q9 전달 / W3 전 사전 점검 S0 (`w3_collection.md` §0, 특히 S0-1)
- judge 임계값 근거: 표준(G.1070) vs 수집 데이터 분위수 (docs/design/judge.md 하단, 권장: [가정]값 시작 → W3 후 보정)
- AGENTS.md·.claude/CLAUDE.md 외부 수정(규칙 통합, Codex 기본값 luna·Fast)과 `docs/design/agent_permissions.md`를 10/16 저녁 문서 PR #5에 반영(공동 승인 필요). `.codex/`는 개인 설정이라 .gitignore에 추가
- PR 본문 편집(`gh pr edit`)·댓글이 권한에서 거부됨. 사람이 PR #5 본문 끝 "공동 승인 필요"에 `.gitignore`(`.codex/` 추가, `37cd545`)를 덧붙이고, PR #6에 `31243bf`(RTP 휴리스틱) 리뷰를 Codex에 요청
