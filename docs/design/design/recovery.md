# 조치 안내 + 회복 판정 설계 (T10, 2026-10-28, Claude) — 구현은 W4 (Codex)

> 근거: PROJECT_SPEC v8 §5-1·§3-6·절대 규칙 6·7, `docs/design/judge.md`(히스테리시스), `docs/design/diagnosis_v1.md`(원인·투표·dev/test),
> `docs/design/ws_protocol.md`(tick·control·close), `docs/design/w3_collection.md` §2(recovery 300–380초), `docs/SCOPE_CHANGE_v8.md`.
> 확인한 코드 동작(읽기만): `server/judge.py` 회복 2틱(`recovery_ticks`), `server/diagnosis.py` 3창 다수결·기준선 재수집 중 `("none", 0.0)`,
> `server/app.py`는 `type != "control"` 메시지를 무시하고 연결 유지, 진단 입력 `seq_loss=None`(RTP 순번 미결합).
> 여기서 새로 붙는 필드·메시지는 모두 **SCHEMA v1.2 제안**(팀원 미승인)이며 `--schema v1.2`일 때만 낸다.

## 0. 범위 (SPEC 절대 규칙 7)
- 조치는 **안내만** 한다. 앱은 프로세스 종료·네트워크 변경을 하지 않는다.
- 실험에서 "조치" = 주입 해제(`impair_off`). 그래서 평가는 "조치가 효과 있다"가 아니라 **"회복을 얼마나 빨리, 정확히 판정하는가"**(지연·오판정률)다.
  발표·보고서에도 이 문장 그대로 쓴다. 문구가 실제로 효과 있는지는 시험하지 않는다.
- 원인은 추정이다(규칙 6). 모든 문구 끝에 "(추정, 신뢰도 xx%)"를 붙인다. `xx` = `diagnosis.confidence × 100`.

## 1. 원인별 조치 문구
서버는 코드(`recovery.cause`)만 보내고, 문구는 대시보드가 표로 가진다(권장, Q10). 위젯 1줄은 PiP 폭을 생각해 짧게 [가정 40자 내외].

| 원인 | 위젯 1줄 (ko / en) | 카드 단계 (ko) | 카드 단계 (en) | 실험의 "조치" |
|---|---|---|---|---|
| `device_cpu` | 노트북 CPU 포화 — 무거운 앱을 닫아 보세요 / Laptop CPU saturated — close heavy apps | ① 쓰지 않는 앱·브라우저 탭 닫기(작업 관리자에서 CPU 높은 앱 확인) ② 충전기 연결(배터리 모드는 성능이 제한될 수 있음) ③ 그래도 같으면 내 카메라 끄기 | ① Close unused apps and browser tabs (check Task Manager) ② Plug in the charger (battery mode may limit performance) ③ If it persists, turn off your camera | `cpu_load.py` 종료(affinity 복원) |
| `loss` | 네트워크 손실 의심 — 공유기 가까이 또는 유선 연결 / Packet loss suspected — move closer to the router or use wired | ① 공유기에 가까이, 벽·장애물이 적은 곳으로 ② 가능하면 유선(이더넷) 연결 ③ 다른 Wi-Fi·핫스팟으로 바꾸기 | ① Move closer to the router ② Use a wired (Ethernet) connection if possible ③ Switch to another Wi-Fi or hotspot | Clumsy Drop 해제 |
| `bandwidth` | 대역폭 부족 의심 — 다른 다운로드를 멈춰 보세요 / Bandwidth limited — pause other downloads | ① 이 노트북과 같은 네트워크 기기의 다운로드·업데이트·스트리밍 멈추기 ② 통화 앱에서 받는 영상 화질 낮추기 ③ 그래도 같으면 받는 영상 끄기 | ① Pause downloads, updates and streaming on this network ② Lower the received video quality in the call app ③ If it persists, turn off incoming video | clumsy2 해제 |
| `delay_jitter` (평가 대상 아님) | `loss` 문구 재사용 (네트워크 쪽) | 같음 | 같음 | — |
- `bandwidth` ②③의 메뉴 위치(Meet 설정의 수신 해상도, Teams 웹의 받는 영상 끄기)는 **미확인** → 문구에 메뉴 이름을 넣지 않는다.
- `weak_wifi`는 데스크톱에서 나오지 않는다(RSSI 입력 없음). 나오면 `loss` 문구.
- 상태 문구:

| `recovery.state` | ko | en |
|---|---|---|
| `degraded` | 위 1줄 + [조치함] 버튼 | above line + [I did it] button |
| `checking` | 회복 확인 중… ({streak_s}/{need_s}초) | Checking recovery… ({streak_s}/{need_s}s) |
| `recovered` | 회복됨 — 조치 후 {latency_s}초 | Recovered — {latency_s}s after action |
| `not_recovered` | 아직 회복되지 않음 — 다른 조치를 시도해 보세요 | Not recovered yet — try another step |

## 2. 회복 판정 규칙
### 2-1. 한 tick이 "회복 조건을 만족"(ok)하는가
ok ⇔ 아래 셋 모두:
1. `diagnosis.cause == "none"` **이고 `confidence > 0`** — Diagnoser는 warmup·흐름 전환 재수집 중에 `("none", 0.0)`을 내므로 이것은 "판정 못 함"이다.
2. `judgement.overall` ≠ `unknown` 이고 심각도(`good 0 < fair 1 < poor 2`)가 **기준 등급 `ref` 이하**.
3. 직전 tick과 `ts` 간격이 1초 — tick이 빠진 초(패킷 없음 = 영상 멈춤 가능)는 연속을 끊는다 [가정].

`ref` (SPEC "기준선 등급"): 에피소드가 시작되기 직전 `idle` tick 20개 [가정]의 `overall` 최빈값(unknown 제외, 동률이면 더 나쁜 쪽).
비었으면 `fair` [가정]. 정상 통화에서도 모델 오차로 fps가 `fair`일 수 있어(P1 MAE 9.09) 고정 `good` 대신 통화마다 잡는다.

### 2-2. 판정 (조치 시각 `action_ts` 이후, `ts > action_ts`인 tick만 센다)
- `streak` = 연속 ok tick 수. ok가 아니면 즉시 0.
- `streak ≥ N` → **`recovered`**, `latency_s = 그 tick ts − action_ts`.
- `ts − action_ts ≥ T` 이고 아직 아니면 → **`not_recovered`**. 같은 tick에서 둘 다 성립하면 `recovered`가 먼저다.
- **N = 5초, T = 30초 [가정]** (SPEC 예시값). W5 dev 통화에서 N ∈ {3, 5, 8}, T ∈ {30, 60} 중 고른다(§5).
- tick이 아예 안 오면 timeout도 안 난다(다음 tick에서 판정). 그동안 대시보드는 "수신 끊김"(SCHEMA 제안 Q7).

### 2-3. judge 히스테리시스와의 일관성
- judge: **악화 즉시, 회복은 같은 등급 2틱 연속.** 회복 판정도 같은 비대칭이다: **ok가 깨지면 즉시 streak 0, 회복은 N틱 연속.**
- 회복 판정은 judge가 이미 안정화한 등급과 Diagnoser가 투표한 원인 위에서 센다(원시값을 다시 보지 않음). 평활화를 한 번 더 넣지 않는다.
- 그 결과 **구조상 판정 지연 하한 = N + 1초**: 해제 직후 첫 tick부터 추정이 정상이어도 judge 회복 2틱·투표 2/3이 겹쳐 2번째 tick에 처음 ok
  → N=5면 해제 후 6초 [계산, 테스트 표 R3]. 실제 지연에는 Chrome의 적응(비트레이트 재상승)과 모델 오차가 더해진다. §5의 정답 기준 지연으로 이 몫을 분리한다.

### 2-4. 상태 기계 (서버 세션당 1개, `JudgeState`·`Diagnoser`와 같은 수명)
```
idle ──cause≠none──▶ degraded ──[조치함] 또는 cause→none(자동)──▶ checking ──streak≥N──▶ recovered
  ▲                                                                   │ └──elapsed≥T──▶ not_recovered
  └─────────── (recovered/not_recovered에서 cause≠none이면 degraded로) ◀┘
```
- `idle → degraded`: 투표된 `cause ≠ none`이 1틱이라도 (투표가 이미 1초 잡음을 거른다. "악화 즉시"). `ref`를 이때 고정.
- `degraded` 동안 `recovery.cause` = 가장 최근의 none 아닌 원인(문구가 그걸 따라 바뀜). 조치 시각에 고정.
- **자동 조치** (SPEC §5-1, Live 데모용): `degraded`에서 클릭 없이 `cause`가 `none`(confidence > 0)으로 돌아온 tick → 그 tick `ts`가 `action_ts`, `action_source = "auto"`.
- **[조치함]**(§4): `checking`이 아닌 모든 상태에서 받는다. `checking` 중 중복 클릭은 무시(로그). `idle`에서 받으면 그때까지의 `idle` 20틱으로 `ref`.
- `recovered`·`not_recovered`는 다음 에피소드(`cause ≠ none`)까지 유지. 표시를 얼마나 오래 둘지는 UI 몫(Q13).
- 평가(§5)는 이 상태 기계를 쓰지 않고, 같은 2-1·2-2 규칙을 **순수 함수**로 호출한다(`action_ts = impair_off`, `ref`는 `[on−20, on)` tick).
  상태 기계가 impair 중 진단을 놓치면 `ref`가 손상 구간으로 오염되기 때문.

## 3. SCHEMA v1.2 제안 필드 — tick `recovery` (server → client, `--schema v1.2`일 때만, 키 고정)
```json
{"...v1·v1.2 필드...": "...",
 "recovery": {"state": "checking", "cause": "loss", "action_ts": 1791763503.0, "action_source": "click",
              "streak_s": 3, "need_s": 5, "elapsed_s": 7.0, "limit_s": 30, "latency_s": null}}
```
| 필드 | 타입 | 값 | 규칙 |
|---|---|---|---|
| `recovery.state` | string | `idle` \| `degraded` \| `checking` \| `recovered` \| `not_recovered` | 2-4 |
| `recovery.cause` | string \| null | `loss` \| `bandwidth` \| `device_cpu` \| `delay_jitter` | `idle`이면 null. 문구 표의 키 |
| `recovery.action_ts` | number \| null | epoch 초 (**tick `ts`와 같은 시간축**) | `checking` 이후만. Replay에서도 원래 캡처 시각 기준 |
| `recovery.action_source` | string \| null | `click` \| `auto` | |
| `recovery.streak_s` | int | 0… | `checking`에서만 증가, 그 외 0 |
| `recovery.need_s` / `limit_s` | int | N / T | 상수를 같이 보냄 → W5에서 값을 바꿔도 대시보드 수정 불필요 |
| `recovery.elapsed_s` | number \| null | `ts − action_ts` | `checking`·`recovered`·`not_recovered` |
| `recovery.latency_s` | number \| null | | `recovered`일 때만 |
- 고정 키 + null 허용은 `evidence`와 같은 방식(Q5). 승인 후 `sample.jsonl`에 `idle`·`checking`·`recovered`·`not_recovered` 줄을 하나씩 추가(제안 문서 §5 절차에 묶음).
- v1 `advice`는 그대로 null(문구는 대시보드, Q10).

## 4. client → server "조치함" 메시지 제안
```json
{"type": "action", "cause": "loss"}
```
| 필드 | 타입 | 규칙 |
|---|---|---|
| `type` | `"action"` | 고정. **새 type**으로 둔다 — `control`은 설정(threshold 등)이고 매번 전체 필드를 보낼 수 있어 "한 번 일어난 사건"을 섞으면 재전송 때 중복 조치가 된다 |
| `cause` | string, 선택 | 클릭할 때 화면에 보이던 원인. 서버는 기록만 하고 판정에는 안 쓴다(`recovery.cause`와 다르면 로그 1줄) |
- 시각 필드는 없다. 서버가 **받은 순간의 마지막 broadcast tick `ts`**를 `action_ts`로 쓴다(Replay는 tick 시각 ≠ 벽시계이므로 클라이언트 시계를 쓰지 않는다).
- 응답 메시지 없음. 다음 tick의 `recovery.state == "checking"`이 확인이다(server→client는 tick만, ws_protocol §1).
- 연결이 여러 개면 회복 상태는 모두가 공유(threshold와 같음, ws_protocol §6 [가정]). 위젯(PiP)과 대시보드 탭은 같은 WS를 쓴다 [가정, Q11].
- 하위 호환: 현재 서버(`server/app.py:337`)는 `type != "control"`을 무시하고 연결을 유지한다 → 대시보드가 서버보다 먼저 보내도 깨지지 않는다.
- SCHEMA.md의 client→server 절에 추가(승인 후, `control`과 나란히).

## 5. 평가 (W5, SPEC §3-6 — 추가 통화 없음)
- 자료: W3 Meet 30 + W4 Teams 15통화의 `w3_<id>_{pkts,os}.csv`를 Replay(`--speed 0`, `--schema v1.2`)로 서버 파이프라인에 그대로 통과시켜 tick을 얻는다. 시각은 `log.csv`의 `impair_on`·`impair_off`.
- 분리: diagnosis_v1과 **같은 통화 단위 dev/test**(조건마다 1·3번째 dev, 2·4번째 test). N·T는 dev에서만 고르고 test만 보고.
  선택 기준 [가정]: dev 오판정률(아래 2) ≤ 10%를 지키는 조합 중 지연 중앙값이 가장 작은 것.

| # | 지표 | 정의 | 대상 |
|---|---|---|---|
| 1 | **회복 판정 지연** | `action_ts = impair_off`로 2-2 실행 → `recovered` 시각 − `impair_off`. 중앙값·IQR·n, 원인별(L·B·C) | L·B·C 통화 |
| 2 | **오판정률(거짓 회복)** | 손상이 계속되는 중 가상 조치 `action_ts = impair_on + 30` [가정] → `impair_off` 전에 `recovered`가 나온 통화 비율 | L·B·C 통화. "효과 있음" 통화(아래 4의 정답 기준 `overall`이 `ref`보다 나빠진 통화)만으로도 따로 |
| 3 | `not_recovered` 비율 | 1에서 T 안에 `recovered`가 안 된 비율. T=30·60 둘 다 표에 | L·B·C 통화 |
| 4 | 보조: 정답 기준 지연 | 같은 2-2를 `truth`로 만든 judge 등급에 적용(진단 조건 없음, 같은 N) → 추정 기준 − 정답 기준 지연 차이, 둘의 판정 일치율 | 정답 있는 통화(Meet `ok`, Teams는 T9 통과 시) |
- 4는 "판정이 늦은 몫이 우리 추정 때문인지, 통화 품질 자체가 늦게 돌아왔기 때문인지"를 나눈다(2-3 구조 지연은 양쪽에 같이 들어가 상쇄).
- `device_cpu`(C 조건)는 P2에서 수신 fps가 거의 안 떨어졌다 → 수신 기반 judge는 손상을 못 볼 수 있고, 회복 판정은 사실상 진단(`call_core_pct`)의 복귀 시간이다. 결과에 이 한계를 적는다. 보조로 dump의 디코드 시간·송신 fps(diagnosis_v1 "효과 있음" 기준)가 기준선으로 돌아온 시각과 비교 [가정, 여유 시].
- N0 통화의 가짜 에피소드는 diagnosis 평가의 `none` 오탐률로 이미 보고 → 여기서 따로 세지 않는다.
- recovery 구간이 80초라 격자의 가장 긴 T=60도 구간 안에서 끝난다. diagnosis 평가에서 제외한 "recovery 첫 30초"를 여기서 쓴다.

## 6. 구현 범위 (W4, Codex luna·medium — 지금은 만들지 않음)
1. `server/recovery.py`: 2-1·2-2 순수 함수 `check(ticks, action_ts, ref, n, t)` + 2-4 상태 기계 작은 클래스 1개. N·T는 `judge.THRESHOLDS`처럼 모듈 상수.
2. `server/app.py`: `--schema v1.2`일 때 tick에 `recovery`, `receive()`에서 `type == "action"` 처리. 기존 v1 계약 테스트는 수정 없이 통과.
3. `scripts/recovery_eval.py`: §5 표 출력(`--n`·`--t` 격자, dev/test).
4. 의존: 진단 입력이 아직 `seq_loss=None`이라 Live의 `loss` 에피소드는 약한 IP/UDP 규칙뿐이다(재현율 0.03–0.18) → RTP 순번 결합(`RtpSeqLoss`)이 먼저 들어오면 `loss` 회복 평가가 의미를 가진다.

## 7. 테스트 표 (`tests/test_recovery.py`)
| # | 케이스 | 기대 |
|---|---|---|
| R1 | action 후 ok 5틱 (N=5) | `recovered`, `latency_s` = 5번째 tick ts − action_ts |
| R2 | ok 4틱 → 1틱 실패 → ok 5틱 | 실패에서 streak 0, 두 번째 연속 끝에서 `recovered` |
| R3 | 해제 직후부터 추정 정상인 합성 스트림을 실제 `judge` + `Diagnoser`에 통과 | 지연 = N + 1초 (2-3 하한) |
| R4 | T 안에 ok 없음 | `ts − action_ts ≥ 30`인 첫 tick에서 `not_recovered` |
| R5 | N번째 ok가 정확히 `ts − action_ts = T` | `recovered` (우선) |
| R6 | `cause="none", confidence=0.0` | ok 아님 (streak 0) |
| R7 | `overall="unknown"` | ok 아님 |
| R8 | `ref=fair`에서 `overall=fair` / `ref=good`에서 `overall=fair` | ok / ok 아님 |
| R9 | `ref` 계산: idle 20틱 최빈값, 동률이면 나쁜 쪽, 비면 `fair` | 각각 일치 |
| R10 | `ts ≤ action_ts` tick | 세지 않음 |
| R11 | ts 간격 2초(빠진 tick) | streak 0 |
| R12 | 상태 기계: idle → `cause=loss` → degraded → action → checking → recovered → `cause=bandwidth` | 각 전이, 마지막은 degraded·`ref` 새로 고정 |
| R13 | degraded에서 클릭 없이 cause→none(conf>0) | checking, `action_source="auto"`, `action_ts` = 그 tick ts |
| R14 | checking 중 action 다시 | 무시, `action_ts` 그대로 |
| R15 | `{"type":"action"}`(cause 없음)·잘못된 JSON·`cause`가 문자열 아님 | 앞은 받아들임, 뒤 둘은 무시. 연결 유지 |
| R16 | `--schema v1`에서 action 메시지 | tick에 `recovery` 없음, 기존 계약 테스트 통과 |
| R17 | `--schema v1.2` tick의 `recovery` | 키 9개 고정, `state`·`action_source` enum 안, `latency_s`는 `recovered`일 때만 number |
| R18 | Replay `--speed 0`에서 action 수신 | `action_ts` = 마지막 broadcast tick ts (벽시계 아님) |

## 8. 팀원(Web) 확인 질문 (SCHEMA 제안 Q1–Q9에 이어서)
| # | 질문 | 권장안 |
|---|---|---|
| Q10 | 조치 문구(§1 표)를 대시보드 `src/core/`에 표로 둘까, 서버가 `advice` 문자열로 보낼까? | **대시보드 표.** 문구·언어를 바꿔도 서버 배포 불필요, 서버는 코드만 |
| Q11 | 위젯(PiP)에도 [조치함] 버튼을 둘 수 있나? PiP 창의 클릭을 대시보드 탭의 같은 WebSocket으로 보낼 수 있나? (T11 스파이크에서 같이 확인) | 위젯에 버튼 1개. PiP 문서는 opener와 같은 JS 문맥이라 같은 WS 객체를 쓸 수 있다 [가정] |
| Q12 | "조치함"을 새 `{"type":"action"}`로 보내는 데 동의하나? (`control` 안의 필드로 넣는 대안) 지금 대시보드가 `control`을 매번 전체 필드로 보내나? | 새 type (§4 이유) |
| Q13 | `recovered`·`not_recovered` 표시는 서버가 다음 에피소드까지 유지한다. UI에서 얼마나 둘까? | 대시보드는 유지, 위젯은 10초 뒤 1줄로 접기 [가정] |
| Q14 | 데모 화면 언어는 ko·en 중 무엇? | 발표가 영어면 en, 표는 둘 다 유지 |
| Q15 | `checking` 진행 표시로 `streak_s/need_s` 진행 바가 필요한가, "확인 중" 글자만으로 충분한가? | 진행 바 (필드는 어차피 보냄) |

## 미확인 / [가정]
- N=5·T=30·`ref` 20틱·빈 `ref`=`fair`·tick 간격 규칙·가상 조치 `on+30`·오판정률 ≤10% 기준: 모두 [가정], W5 dev에서 조정.
- Chrome이 대역폭 해제 후 비트레이트를 얼마나 빨리 올리는지 미확인 → B300에서 T=30이면 `not_recovered`가 많을 수 있다(그 자체가 결과, 지표 4로 해석).
- 흐름 전환(P2P↔relay)이 recovery 구간에 생기면 Diagnoser 재수집(`confidence 0.0`) 동안 ok가 안 되어 지연이 늘어난다. 평가에서는 `note=path_switch_late` 통화를 따로 표시.
- 메뉴 위치(Meet 수신 해상도, Teams 웹 받는 영상 끄기)·PiP에서 WS 공유: 미확인.
