# HANDOFF — Claude ↔ Codex 작업 인계판
> 두 AI가 세션 시작 때 **이 파일 상단(현재 상태 + 내 몫)만** 읽고, 세션 끝에 갱신한다. 80줄 이하 유지.
> 마일스톤·결과 수치 → PROGRESS.md / 실험·결정 이력 → PROJECT_LOG.md / 여기는 "지금 누가 무엇을" 만.
> 완료 항목은 한 줄로 줄여 PROJECT_LOG에 옮기고 여기서 지운다.

## 현재 상태 (갱신: 2026-10-16 밤, Claude)
- 주차: W2 (10/20–10/26, Midterm 1 10/21). **코드 main 병합 완료**: PR #9(`ml/t8b-diag-v1`, merge commit `9655017`)로 T1·T3b·T4·T8b가 main에 들어왔고 #5 병합, #6~#8 close. main pytest 197 passed. 다음은 **사용자 W3 S0 사전 점검**
- **Codex 샌드박스는 git 쓰기·Python 실행이 막혀 있다** → Codex는 worktree 파일 수정 + `codex_notes.md` 기록까지만, pytest·커밋·push는 Claude 리뷰 루프가 한다
- 테스트 환경: 이벤트 루프 생성 시 `socket.socketpair()`가 WinError 10014로 가끔 실패(앱 없이 `asyncio.run`만 돌려도 300회 중 27회). `3730af1`(test_ws 재시도)에도 main test_ws 반복에서 일부 실패(재시도가 못 막는 경로 남음, `ProactorEventLoop._ssock` AttributeError 포함). 실패가 이 오류뿐이면 환경 문제로 본다. 원인 미확인
- 이번 세션 발견: P2P 흐름 포트가 49152를 넘으면 tshark가 RTP를 해석 못 함 → T1에 수정 커밋 `31243bf`(PR #6). 코어 고정 시 CPU%가 낮게 보임 → `call_core_pct` 설계
- 마지막 작업자: Claude (PR #9 병합 후 검증·문서 갱신)

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
| T1·T3b·T4·T8b | tshark 분리 / judge / FastAPI WS / diagnosis v1 구현 | Codex + Claude 리뷰 | ✅ 병합 (PR #9, `9655017`). 상세 PROJECT_LOG 26–31 | — | 실측은 W3 S0-3·S0-4 |
| T2 | T1 결과 리뷰 (루프가 자동 수행, 최종 사람 확인) | Claude → Opus·high | ✅ (T1·T4 리뷰 PASS) | T1 diff | 발견 목록 |
| T3 | `judge.py` 입출력 설계 → `docs/design/judge.md` | Claude | ✅ | — | 설계 문서 + 테스트 표 |
| T5 | WS 메시지 계약 설계 → `docs/design/ws_protocol.md` | Claude | ✅ 10/16 | — | T4 브리프 |
| T6 | SCHEMA v1.2 제안 → `docs/design/schema_v1.2_proposal.md` | Claude → 팀원(Web) 확인 | ⏳ 팀원 답 대기 (Q1–Q9, Q9 = `call_core_pct` 10/16 추가) | 제안 문서 §4 | 승인 후 §5 반영 PR |
| T7 | W3 수집 절차 → `docs/design/w3_collection.md` | Claude ✅ → 사용자 실측 | ⬜ S0 사전 점검부터 | 절차 문서 | 30통화 `ok` |
| T8 | diagnosis v1 (`device_cpu`) 설계 → `docs/design/diagnosis_v1.md` | Claude | ✅ 10/16 | — | 규칙·입력·평가·테스트 표 |

## 기록 (최신이 위. 항목당 3줄 이내: 한 일 / 다음 담당·모델·effort 추천+이유 / 남은 위험)
- 2026-10-16 밤 Claude: PR #9 merge commit 병합 확인(부모 `dd427bc`·`811c975`), main에서 T1·T3b·T4·T8b 모두 포함. main pytest 197 passed, `T8b_10014.patch`는 `3730af1`로 이미 적용. 다음: 사용자 W3 S0 → diag_eval은 Codex luna·medium. 위험: 10014가 패치 후에도 남음(test_ws 10회 중 1회 실패), tshark/Live 실측 미확인.

## 사용자에게 (걸림돌·제안·모호한 점. 답 받으면 지우고 결정은 PROGRESS "결정 사항"으로)
- Codex sandbox가 `.git/refs` 쓰기·`.venv` Python 실행을 거부한다(Claude가 대신 적용해 해결) → Codex 권한 설정 확인 필요.
**다음 세션 순서 (10/16 작성, 10/16 밤 병합 후 정리. 각 단계 시작 전: 이 HANDOFF "현재 상태" + PROJECT_SPEC 해당 절 확인 → 계획 → 실행)**
- S6 [사용자] 팀원에게 v1.2 질문 Q1–Q9 전달 / W3 전 사전 점검 S0 (`w3_collection.md` §0, 특히 S0-1)
- judge 임계값 근거: 표준(G.1070) vs 수집 데이터 분위수 (docs/design/judge.md 하단, 권장: [가정]값 시작 → W3 후 보정)
