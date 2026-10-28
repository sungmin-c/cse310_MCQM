# HANDOFF — Claude ↔ Codex 작업 인계판
> 두 AI가 세션 시작 때 **이 파일 상단(현재 상태 + 내 몫)만** 읽고, 세션 끝에 갱신한다. 80줄 이하 유지.
> 마일스톤·결과 수치 → PROGRESS.md / 실험·결정 이력 → PROJECT_LOG.md / 여기는 "지금 누가 무엇을" 만.
> 완료 항목은 한 줄로 줄여 PROJECT_LOG에 옮기고 여기서 지운다.

## 현재 상태 (갱신: 2026-10-28, Claude)
- **v8 (10/28)**: **Zoom 제외, 측정 앱 = Meet ≈30 + Teams ≈15**, 측정은 Windows 노트북 + Chrome 웹만. 부족하면 Teams부터 축소. SPEC v8·PROGRESS Q25·`w3_collection.md` §8–9. v7의 조치 안내 + 회복 검증·미니 위젯은 그대로. 문서만 바뀌었고 코드는 그대로(`--app`에 teams 없음, zoom 선택지 남음)
- 주차: W3 (10/27–11/2). 코드 main 병합 완료(PR #9, `9655017`), main pytest 197 passed. 다음은 **사용자 W3 S0 사전 점검 → Meet 30통화, 같은 주에 Teams 파일럿(T9)**, Claude는 T10 설계. 교수님께 `docs/SCOPE_CHANGE_v8.md` 전달(사용자)
- Codex는 프로젝트 파일 편집과 번들 Python 실행 가능(10/26 PPT 생성 확인). `.venv`·pytest·Git 상태 확인은 submodule 접근 오류가 있어 이번 세션 미확인
- 테스트 환경: 이벤트 루프 생성 시 `socket.socketpair()`가 WinError 10014로 가끔 실패(앱 없이 `asyncio.run`만 돌려도 300회 중 27회). `3730af1`(test_ws 재시도)에도 main test_ws 반복에서 일부 실패(재시도가 못 막는 경로 남음, `ProactorEventLoop._ssock` AttributeError 포함). 실패가 이 오류뿐이면 환경 문제로 본다. 원인 미확인
- 이번 세션 발견: P2P 흐름 포트가 49152를 넘으면 tshark가 RTP를 해석 못 함 → T1에 수정 커밋 `31243bf`(PR #6). 코어 고정 시 CPU%가 낮게 보임 → `call_core_pct` 설계
- 마지막 작업자: Claude (v8 범위 문서 반영; 코드 변경 없음)

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
| T7 | W3–W4 수집 절차 → `docs/design/w3_collection.md` (v8: §9 Teams 추가) | Claude ✅ → 사용자 실측 | ⬜ S0 사전 점검부터 | 절차 문서 | Meet 30 + Teams 15통화 `ok` (Teams는 축소 가능) |
| T8 | diagnosis v1 (`device_cpu`) 설계 → `docs/design/diagnosis_v1.md` | Claude | ✅ 10/16 | — | 규칙·입력·평가·테스트 표 |
| T9 | Teams 파일럿 1건 (Chrome 웹 ↔ S20 Teams): T9-1–5(통화, dump inbound video, 경로, RTP 비율, `compare`) + 서버 `--app teams` 추가 | 사용자 실측 → `--app`은 Codex luna·low | ⬜ **W3 (W4 Teams 수집 전 필수)** | `w3_collection.md` §8, SPEC v8 §3-2 | 정답 가능/불가 결론, PROGRESS Q25 아래에 결과 |
| T10 | 조치·회복 설계 → `docs/design/recovery.md`: 조치 문구, 회복 판정 규칙(N초 유지·T초 제한), SCHEMA 필드·"조치함" client→server 메시지 제안, 테스트 표 | Claude → Opus·high / 구현 W4 Codex luna·medium | ✅ 설계 10/28 → ⏳ 팀원 Q10–Q15 대기 | `docs/design/recovery.md` §6–8 | 설계 문서 + 팀원 확인 질문 |
| T11 | 위젯 PiP 스파이크: `documentPictureInPicture.requestWindow()`로 더미 스트림 표시, Meet 전체 화면 위에 뜨는지 | 팀원(Web) | ⬜ W2 | SPEC v8 §1 | 가능/불가 + 스크린샷 |
| T12 | 오버헤드 실험 P5: 준비 R1–R6 구현 → 사용자 실측 E1–E7 → 해석 | 구현 Claude Sonnet·medium (또는 Codex luna·medium) → 사용자 → 해석 Claude Opus·high | 🟡 준비 R1–R6 구현 완료(10/28, 미커밋, pytest 201 통과, dry-run 확인). 실측 10/31–11/1 | `docs/design/overhead_weekend.md`, PROGRESS Q27·P3 | R1–R6 + pytest 통과 / 실측 csv·dump / PROGRESS "P5" |
| T9a | `--app teams` 추가 (server·dummy_stream·문서) — `docs/briefs/T9a.md` | Codex sol·high → Claude Opus·high 리뷰 (`run_queue.ps1`) | ⬜ 10/28 야간 큐 | brief | pytest 통과, zoom은 유지 |
| T13 | P5 도구 보강 (build_phases·입력 검증·report 견고성·테스트) — `docs/briefs/T13.md` | Codex sol·high → Claude Opus·high 리뷰 (`run_queue.ps1`) | ⬜ 10/28 야간 큐 | brief, overhead_weekend.md | pytest 통과, 실측 전 병합 |

## 기록 (최신이 위. 항목당 3줄 이내: 한 일 / 다음 담당·모델·effort 추천+이유 / 남은 위험)
- 2026-10-28 Claude: T10 설계 `docs/design/recovery.md` — 조치 문구(ko/en), 회복 판정(ok 3조건, N=5·T=30 [가정], 하한 N+1초), tick `recovery` 필드·`{"type":"action"}` 제안, 평가 4지표, 테스트 R1–R18, 팀원 Q10–Q15. 코드 변경 없음. 다음: 팀원 답 → W4 구현 Codex luna·medium(범위 명확). 위험: Live 진단 `seq_loss=None`이라 `loss` 회복 평가는 RTP 결합 후, 대역폭 해제 후 Chrome 재상승 속도 미확인.
- 2026-10-28 Claude: 범위 v8(Zoom 제외, Meet 30 + Teams 15) 반영 — SPEC v8, w3_collection §8 T9·§9 Teams, diagnosis_v1 L78, PROGRESS Q22·Q25·일정·M3·M4, LOG #37, README·AGENTS, 교수님 메모 `SCOPE_CHANGE_v8.md`. 코드 변경 없음(pytest 미실행). 다음: 사용자 S0·Meet 수집·T9, T10은 Claude Opus·high. 위험: Teams 웹 정답 미확인, 코드·SCHEMA·ws_protocol·COMMANDS에 `zoom` 선택지·문구 남음(코드 정리 때 함께).
- 2026-10-26 Codex: `SCRIPT_ChatGPT.md` 기준 목차 포함 12장 Google Meet/Google 색 테마 덱과 재생성 스크립트 작성. 구조·발표자 노트·슬라이드 경계 확인, PowerPoint COM 접근 거부로 PNG 렌더링은 미확인. 다음: 사용자 자료 확인 후 화면 캡처가 있으면 슬라이드 4 갱신; 추가 편집 Codex gpt-6-luna·medium(Fast). 위험: 시각적 최종 확인 미완료.
- 2026-10-25 Codex: `SCRIPT_ChatGPT.md` Slide 1–11 본문과 기존 미니멀 PPT를 대조하고 `MCQM_Proposal_Minimal_2026-10-25_updated.pptx` 생성. 슬라이드 2–11 화면 문구·전 슬라이드 노트 갱신, 이전 수치·일정 제거, PowerPoint 11장 렌더링·구조 검사 완료. 다음: 사용자 리허설, 추가 표현 수정은 Codex gpt-6-luna·medium(Fast; 범위 명확). 위험: Teams 정답·라이브 정확도는 여전히 미확인.
- 2026-10-25 Codex: 스크립트 v3에 맞춘 미니멀 PPT 사본 생성, 4곳 표현 정합(해상도, 원인 힌트 검증, 속도 표현, 파일럿 freeze 수치). 기존 PPT가 잠겨 있어 별도 `_script-aligned` 파일로 저장. 다음: 사용자 리허설, 추가 조정은 Codex gpt-6-luna·medium(Fast). 위험: 렌더링은 미확인.
- 2026-10-25 Codex: proposal PPT를 미니멀 11장으로 재배치(`docs/proposal/MCQM_Proposal_Minimal_2026-10-25.pptx`), 공식 플랫폼 로고·관련 그림·수치 비교·발표자 노트 포함. PowerPoint PNG 11장 렌더링, PPTX 구조·노트·도형 경계 확인. 다음: 사용자 리허설/표현 확인, 추가 시각 수정은 Codex gpt-6.1-sol·high(수치 해석과 레이아웃 병행). 위험: vcaml 원 논문의 직접 비교 가능한 라이브 실행시간 미보고; 슬라이드 5는 측정 범위가 다른 두 값과 1초 갱신 간격만 비교. 메모리 답변은 PPT·원고에 미반영.
- 2026-10-25 Codex: `SCRIPT_ChatGPT.md` 기반 영어 학술 발표 PPT 11장 제작(`docs/proposal/MCQM_Proposal_2026-10-25.pptx`), 표지·결론 삽화·발표자 노트·2번 슬라이드 암호화 전후 예시 포함. PowerPoint PNG 렌더링으로 확인. 다음: 사용자 발표 리허설·내용 확인, 경미한 슬라이드 수정은 Codex luna·low(범위 명확). 위험: Teams 정답 확보·재학습 결과·라이브 데모는 아직 미확인; PPT는 계획으로 표기.
- 2026-10-22 Claude: v7 문서 정리(SPEC·PROGRESS·LOG·design·README·AGENTS), OVERVIEW·briefs 삭제, 면담 문서 `MEETING_1022.md`, Proposal 자료 `docs/proposal/`. 다음: T10 설계 Claude Opus·high(판단 비중 큼), T9 사용자. 위험: Teams 웹 정답·PiP 미확인, 통화 60건 일정.
- 2026-10-16 밤 Claude: PR #9 merge commit 병합 확인(부모 `dd427bc`·`811c975`), main에서 T1·T3b·T4·T8b 모두 포함. main pytest 197 passed, `T8b_10014.patch`는 `3730af1`로 이미 적용. 다음: 사용자 W3 S0 → diag_eval은 Codex luna·medium. 위험: 10014가 패치 후에도 남음(test_ws 10회 중 1회 실패), tshark/Live 실측 미확인.

## 사용자에게 (걸림돌·제안·모호한 점. 답 받으면 지우고 결정은 PROGRESS "결정 사항"으로)
- Codex sandbox가 `.git/refs` 쓰기·`.venv` Python 실행을 거부한다(Claude가 대신 적용해 해결) → Codex 권한 설정 확인 필요.
**다음 세션 순서 (10/16 작성, 10/16 밤 병합 후 정리. 각 단계 시작 전: 이 HANDOFF "현재 상태" + PROJECT_SPEC 해당 절 확인 → 계획 → 실행)**
- S6 [사용자] 팀원에게 v1.2 질문 Q1–Q9 전달 / W3 전 사전 점검 S0 (`w3_collection.md` §0, 특히 S0-1)
- judge 임계값 근거: 표준(G.1070) vs 수집 데이터 분위수 (docs/design/judge.md 하단, 권장: [가정]값 시작 → W3 후 보정)
