# 조치 안내 + 회복 판정 설계 (T10, 2026-10-28, Claude) — 구현은 W4 (Codex)
> r2 (10/28): Codex 교차 리뷰(`data/ai_runs/T10_review.md`, FIX 7건) 반영 — 관측 유효성(2-1 조건 4), 재진입 조건(2-4), `ref` 롤링 버퍼(2-1),
> 구조 지연 정정(2-3), 계약 테스트 수정 필요(§6), Teams 입력 경로(§5), 경계 테스트 R19–R24.
> r3 (10/28): Codex 재리뷰(`data/ai_runs/T10_rereview.md`, P2 3건) 반영 — judge 보류 `poor`를 `ref` 버퍼에서 제외(2-1),
> 실제 창 생성(고정 격자 아님)에 맞춘 간격 검사·정렬·구조 지연(2-1 조건 3, 2-3), 상태도 복귀 화살표(2-4), R11·R21·R24.
> r4 (10/28): Claude 3차 리뷰(`data/ai_runs/T10_rereview3_claude.md`, 같은 계열 리뷰어) 반영 — `ref` 상한 `fair`(2-1), 경량 모드 회복 판정 끔(2-1 조건 3·§3),
> 해제 시각 해상도와 기록 방식 선택지(2-3·§5 "해제 시각"), 평가 스크립트 리팩터·`check()` 인자(§6), R11·R22·R24 갱신, 미해결 목록. 4차 리뷰 없음.

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
ok ⇔ 아래 넷 모두:
1. `diagnosis.cause == "none"` **이고 `confidence > 0`** — Diagnoser는 warmup·흐름 전환 재수집 중에 `("none", 0.0)`을 내므로 이것은 "판정 못 함"이다.
2. `judgement.overall` ≠ `unknown` 이고 심각도(`good 0 < fair 1 < poor 2`)가 **기준 등급 `ref` 이하**.
3. 직전 tick과 `ts` 간격이 **1 또는 2** — 0이거나 3 이상이면 streak 0 [가정]. tick `ts`는 고정 1초 격자가 아니다: 창은 첫 패킷에서 시작해
   1초를 **초과**한 다음 패킷이 닫고, `ts = int(닫은 패킷 epoch)`(`server/features.py:5–9,62–83`, `app.py:71`). 창 길이가 1+δ(δ = 1초 초과분)라
   패킷이 끊김 없이 와도 δ가 쌓이면 정수 `ts`가 2 뛴다 [계산: 30ms 간격이면 창 1.02초(34번째 패킷이 닫음), δ=0.02 → 50창마다 정확히 1회, 위상 무관].
   3 이상 = 영상 패킷 공백 ≈ 1초 이상(멈춤 가능).
   0 = Live idle flush(`app.py:191`, 2초 무패킷)가 닫은 짧은 창이 직전 tick과 같은 정수 `ts`를 낸 경우 → 패킷 공백이므로 끊는다(간격 1인 flush는 못 거름, 미해결).
   **`--every k > 1`(경량 모드)에서는 회복 판정을 하지 않는다** (tick `recovery` = null, `action` 메시지는 로그만). 이유: k창 중 1창만 추론하므로
   (`tshark_live.py:140`) "연속 N초 유지"를 관측할 수 없고(나머지 k−1초는 안 봄), flush 창도 k창 셈에 들어가 ≈k초 무패킷이 간격 검사에 안 걸리며,
   judge 회복 2틱·투표 3틱이 2k·3k초로 늘어 k=5면 첫 ok가 해제 후 ≈10초, `recovered`는 그 뒤 N틱(≈25초) → T=30에서 거의 항상 `not_recovered`.
   streak를 초로 바꿔도 첫째 문제(관측 안 한 초를 유지로 셈)가 남는다. 평가(§5)는 수집 파일을 `--every 1`로 재생하므로 영향 없음 — 잃는 것은 경량 Live 데모의 회복 표시뿐.
   - 그래서 **N·T의 단위**: N = 연속 ok **창(tick) 수**, T = `ts − action_ts` **초**. `--every 1`에서 창 ≈ 1초(1+δ, 가끔 `ts` 2 점프)라 N틱 ≈ N초로 표기한다(`need_s`·`streak_s`).
4. **원인 관측 유효**: 에피소드 원인(`recovery.cause`)이 `device_cpu`이면 그 tick의 `device.call_core_pct`가 number여야 한다.
   OS 샘플이 끊기면(`device=None`: Replay에 OS 기록 없음·샘플이 2초보다 오래됨, diagnosis_v1 "입력") Diagnoser는 `device_cpu`를 아예 못 내고
   패킷이 정상이면 `none, conf>0`이 된다 → "관측 불능"이 "원인 해소"로 보이는 것을 막는다. 끊긴 tick은 3번처럼 streak 0.
   `loss`·`bandwidth`·`delay_jitter`는 패킷 자체가 관측이므로 tick이 있으면 유효(3번이 이미 빈 tick을 막음).

`ref` (SPEC "기준선 등급"): **롤링 버퍼** 최근 20 tick [가정]의 `overall` 최빈값(unknown 제외, 동률이면 더 나쁜 쪽), 비었으면 `fair` [가정].
**상한 `fair`**: 최빈값이 `poor`여도 `ref = fair`. 즉 `overall = poor`인 tick은 어떤 통화에서도 ok가 아니다.
버퍼에 넣는 tick = 상태가 `idle` 또는 `recovered`이고 진단이 `none, conf>0`이고 **judge가 등급을 보류하지 않은** tick(warmup·재수집·손상·보류 tick은 안 들어감).
에피소드가 시작될 때(`→ degraded`) 고정한다.
- **보류** = `overall`이 그 tick의 원시 등급으로 같은 식(`judge.py:98`, unknown 제외 최댓값)을 낸 값보다 나쁨. judge는 악화를 즉시, 회복은 같은 원시 등급
  2틱 연속일 때만 반영한다(`judge.py:54–61`) → 한 번 `poor`가 된 뒤 원시 `good`/`fair`가 교대하면 `overall=poor`가 계속 남는다. 이 `poor`는 측정이 아니라
  히스테리시스 잔상이라, 버퍼에 들어가면 `ref=poor`가 되어 품질이 계속 `poor`여도 회복 조건을 통과한다. 원시 등급은 `JudgeState.recent[m][-1]`
  (`_stabilize`가 이번 tick에 append한 값)이고, tick JSON에는 없다 → 서버(`build_tick`이 `JudgeState`를 가짐)와 평가 스크립트(§5) 모두 `JudgeState`에서 읽는다.
- **상한을 두는 이유 (진단 미검출 경로)**: 버퍼 입장은 "진단 `none, conf>0` + 보류 아님"이라, 진단이 놓친 **실제 저하**도 원시 `poor`로 들어간다.
  Live는 `seq_loss=None`(`app.py:79`)이라 `loss` 재현율이 낮고(diagnosis_v1 0.18), C 조건은 수신 fps가 거의 안 떨어진다. 20틱 중 과반이 이렇게 차면
  `ref=poor` → 조건 2가 항상 참 → 회복이 진단만으로 결정된다. 특히 R22(화질이 나빠 보여 `idle`에서 [조치함])는 바로 이 버퍼로 `ref`를 고정해
  저하가 계속되는데 N틱 뒤 `recovered`가 나온다. 서버는 "진짜 나쁜 기준선"과 "놓친 저하"를 구별할 수 없으므로 `poor` 쪽을 버린다.
  대가: 원시 등급이 계속 `poor`인 통화(모델 오차 등 진짜 나쁜 기준선)는 `recovered`가 안 나오고 `not_recovered`로 간다 — 거짓 회복보다 안전한 쪽(미확인 목록과 같은 원칙).
- **못 막는 것 (한계)**: ① 놓친 저하가 `fair` 수준이면(기준선 `good`인 통화에서 `fair` 저하가 20틱 중 과반) `ref=fair`가 되어 `fair`가 남아도 `recovered`.
  ② 수신 지표가 기준선보다 안 나빠지는 저하(C 조건 다수, §5)는 judge가 처음부터 못 보므로 회복이 진단 복귀만으로 정해진다.
  평가에서는 상한이 작동한 통화(버퍼 최빈값 `poor`)와 `ref=fair`인 통화 수를 따로 보고한다(§5).
`recovered` 뒤 정상 tick도 버퍼에 들어가므로 두 번째 에피소드는 회복 후 상태로 `ref`를 다시 잡는다(이전 에피소드 직전 값을 재사용하지 않음).
정상 통화에서도 모델 오차로 fps가 `fair`일 수 있어(P1 MAE 9.09) 고정 `good` 대신 통화마다 잡는다.

### 2-2. 판정 (조치 시각 `action_ts` 이후, `ts > action_ts`인 tick만 센다)
- `streak` = 연속 ok tick 수. ok가 아니면 즉시 0.
- `streak ≥ N` → **`recovered`**, `latency_s = 그 tick ts − action_ts`.
- `ts − action_ts ≥ T` 이고 아직 아니면 → **`not_recovered`**. 같은 tick에서 둘 다 성립하면 `recovered`가 먼저다.
- **N = 5틱(≈5초), T = 30초 [가정]** (SPEC 예시값, 단위는 2-1 조건 3 아래). W5 dev 통화에서 N ∈ {3, 5, 8}, T ∈ {30, 60} 중 고른다(§5).
- tick이 아예 안 오면 timeout도 안 난다(다음 tick에서 판정). 그동안 대시보드는 "수신 끊김"(SCHEMA 제안 Q7).

### 2-3. judge 히스테리시스와의 일관성
- judge: **악화 즉시, 회복은 같은 등급 2틱 연속.** 회복 판정도 같은 비대칭이다: **ok가 깨지면 즉시 streak 0, 회복은 N틱 연속.**
- 회복 판정은 judge가 이미 안정화한 등급과 Diagnoser가 투표한 원인 위에서 센다(원시값을 다시 보지 않음). 평활화를 한 번 더 넣지 않는다.
- **구조 지연** (클릭·평가처럼 `action_ts`가 해제 시각인 경우). 창은 패킷이 경계를 정하므로(2-1 조건 3) 정수 `ts` 격자로 정렬할 수 없다. 창 수로 센다:
  "해제 후 k번째 창" = 첫 패킷 epoch ≥ `impair_off`인 창 중 k번째(해제를 걸친 창은 0번째, 없으면 해제 직전 창이 0번째).
  - 조건: 해제 후 창은 추정이 정상이고, 0번째 창까지 마지막 3창의 원시 진단이 모두 손상 원인. 이때 투표는 2번째 창(`[손상, 정상, 정상]`)에 처음 `none`이 되고,
    judge 등급이 손상 중 `ref`보다 나빴으면 회복 2틱도 같은 창에 끝나고, 나빠지지 않았으면 투표가 결정한다 → 첫 ok = 2번째 창.
    2번째 창의 `ts` ≥ ⌊`impair_off`⌋+2 > ⌈`impair_off`⌉이므로 항상 집계된다 → **`recovered` = 해제 후 N+1번째 창** [계산, R3·R24].
  - 초로는 고정값이 아니다: `latency_s` = 그 창 `ts` − `action_ts`(=⌈`impair_off`⌉)는 해제 시각과 창 위상에 따라 **N 또는 N+1**, δ 누적으로 `ts`가 2 뛰면 +1.
    하한은 어떤 정렬에서도 **N**이다(집계 tick은 `ts > action_ts`인 서로 다른 정수 → N번째 ≥ `action_ts + N`).
  - 0번째 창의 원시 진단이 none이거나 해제 전이 `[손상, none, 손상]`처럼 3/3이 아니면 투표가 1창 빨라져 N번째 창이 될 수 있다 → 위 값은 조건부이지 하한이 아니다.
  - **자동 모드는 이 하한이 없다**: `action_ts` = 진단이 이미 `none`으로 돌아온 tick이므로 `latency_s` ≥ N이고 해제 시각과 무관하다 → 데모 표시용, 평가 지표에 쓰지 않는다.
  - 실제 지연에는 Chrome의 적응(비트레이트 재상승)과 모델 오차가 더해진다. §5 지표 4로 이 몫을 나누되, 정답 기준과의 구조 차이(0–1초, §5)는 따로 적는다.
  - **해상도 한계**: 위 창 단위 계산은 **실제 해제 시각** 기준이다. 기록된 `impair_off`의 해상도(§5 "해제 시각")가 이보다 거칠면 절대 지연(지표 1)에서
    N과 N+1을 구별하지 않는다. L·B의 현재 기록(`$off` 정수 초, Clumsy Stop 뒤 사람이 입력)은 실제 해제 r에 대해 r ∈ [`off` − 조작 지연, `off` + 1)이라
    지표 1을 **정수 초, 오차 (−1, +조작 지연]**으로만 보고하고 2초 미만 차이는 해석하지 않는다. 지표 4(추정 − 정답 차이)는 두 쪽이 같은 `action_ts`를 쓰므로
    이 오차가 상쇄되어 창 단위(0–1창) 해석을 유지한다. C는 `_load.csv` 종료 행(ms)을 쓰므로 창 단위 해석 가능.

### 2-4. 상태 기계 (서버 세션당 1개, `JudgeState`·`Diagnoser`와 같은 수명)
```
idle / recovered ──cause≠none──▶ degraded ──action·auto──▶ checking ──streak≥N──▶ recovered
                                                            ▲    │
                                                            │    └──elapsed≥T──▶ not_recovered ──┐
                                                            └── action·auto ────────────────────◀┘
```
- `action` = [조치함](§4), `auto` = 자동 조치(`cause→none`, conf>0). `not_recovered`의 유일한 출구는 `checking`(같은 에피소드)이고, `cause≠none`이 계속되면 제자리다(`degraded`로 가지 않음).
- **에피소드** = `idle`/`recovered`에서 `degraded`로 들어간 때부터 다음 `recovered`까지. 새 에피소드는 **`idle` 또는 `recovered`에서만** 시작한다(`ref` 고정은 이때 한 번).
- `idle`/`recovered → degraded`: 투표된 `cause ≠ none`이 1틱이라도 (투표가 이미 1초 잡음을 거른다. "악화 즉시"). `recovered`는 N틱 연속 ok를 거쳤으므로 그 뒤 악화는 새 손상이다.
- `degraded` 동안 `recovery.cause` = 가장 최근의 none 아닌 원인(문구가 그걸 따라 바뀜). 조치 시각에 고정.
- **`not_recovered`는 에피소드를 끝내지 않는다**(재진입 조건): 같은 손상이 계속돼(`cause ≠ none`) 다음 tick이 와도 `degraded`로 돌아가지 않고 `not_recovered`를 유지한다
  (새 에피소드로 세면 `ref`가 손상 구간으로 다시 잡히고 에피소드 수가 부풀려진다). 원인이 다른 none 아닌 값으로 바뀌면 `recovery.cause`만 갱신(`ref` 그대로).
  나가는 길은 `degraded`와 같다: [조치함] → `checking`(새 `action_ts`, "다른 조치를 시도"), 자동(`cause→none`, conf>0) → `checking`(`auto`).
- **자동 조치** (SPEC §5-1, Live 데모용): `degraded`·`not_recovered`에서 클릭 없이 `cause`가 `none`(confidence > 0)으로 돌아온 tick → 그 tick `ts`가 `action_ts`, `action_source = "auto"`.
- **[조치함]**(§4): `checking`이 아닌 모든 상태에서 받는다. `checking` 중 중복 클릭은 무시(로그). `idle`·`recovered`에서 받으면 그때 버퍼로 `ref`를 고정하고 `checking`
  (`recovery.cause = null`, 이미 정상이면 N틱 뒤 `recovered` — 사용자가 "괜찮아졌나" 확인하는 용도. 거부하지 않는 이유: 클릭 시점의 화면과 서버 상태가 1초 어긋날 수 있다).
  이 에피소드에서 이후 none 아닌 원인이 나오면(`checking`·`not_recovered` 어디서든) `recovery.cause`를 그 원인으로 채운다 → 문구가 비지 않는다. `ref`·`action_ts`는 그대로.
- `checking` 중 흐름 전환: Diagnoser 재수집 동안 `none, 0.0` → ok 아님(streak 0). `action_ts`·`ref`·T 타이머는 그대로 → 재수집(≥ `skip_first`+`warmup` = 10틱)이 T 안에 안 끝나면 `not_recovered`.
- `recovered`는 다음 에피소드까지, `not_recovered`는 다음 `checking`까지 유지. 표시를 얼마나 오래 둘지는 UI 몫(Q13).
- 평가(§5)는 이 상태 기계를 쓰지 않고, 같은 2-1·2-2 규칙을 **순수 함수**로 호출한다(`action_ts = ⌈impair_off⌉`, `ref`는 `[on−20, on)` tick 중
  진단 `none, conf>0`이고 보류 아닌 것 — 상태 조건은 평가에 없으므로 뺀다. 상한 `fair`는 같음).
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
| `recovery.cause` | string \| null | `loss` \| `bandwidth` \| `device_cpu` \| `delay_jitter` | `idle`이면 null, 정상 상태에서 [조치함]으로 연 `checking`도 null(R22). 문구 표의 키 |
| `recovery.action_ts` | number \| null | epoch 초 (**tick `ts`와 같은 시간축**) | `checking` 이후만. Replay에서도 원래 캡처 시각 기준 |
| `recovery.action_source` | string \| null | `click` \| `auto` | |
| `recovery.streak_s` | int | 0… | `checking`에서만 증가, 그 외 0 |
| `recovery.need_s` / `limit_s` | int | N / T | 상수를 같이 보냄 → W5에서 값을 바꿔도 대시보드 수정 불필요 |
| `recovery.elapsed_s` | number \| null | `ts − action_ts` | `checking`·`recovered`·`not_recovered` |
| `recovery.latency_s` | number \| null | | `recovered`일 때만 |
- `--every k > 1`이면 `recovery` 키는 있고 값이 **null**(2-1 조건 3, 경량 모드는 회복 판정 안 함). 대시보드는 회복 표시를 숨긴다.
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
- 자료: 앱별 입력이 다르다(w3_collection §3·§9). Replay와 같은 경로(`process_lines` → `build_tick`, `--schema v1.2`)를 `recovery_eval.py` **프로세스 안에서** 돌려 tick을 얻는다
  (WS로 받으면 2-1 버퍼의 "보류" 판단에 필요한 원시 등급이 없음 → tick마다 `JudgeState`에서 보류 여부를 같이 기록). 시각은 각 로그의 `impair_on`·`impair_off`.

| 앱 | 통화 ID | 패킷·OS | dump (지표 4) | 로그 | `--app` |
|---|---|---|---|---|---|
| Meet 30 | `01`–`30` | `data/pilot/w3_<id>_{pkts,os}.csv` | `data/w3/w3_<id>_dump.json` | `data/w3/log.csv` | `meet` |
| Teams 15 | `t01`–`t15` | `data/pilot/w4_<id>_{pkts,os}.csv` | `data/w4/w4_<id>_dump.json` | `data/w4/log.csv` | `teams` |
  `recovery_eval.py`는 로그 경로를 인자로 받아(앱마다 한 번) 같은 표를 앱별로 낸다. Teams는 T9 실패 시 dump가 없거나 무효 → 지표 4만 빠진다.
  `--app teams`는 아직 서버에 없다(`server/app.py:36` 선택지 `meet`·`zoom`) → T9 코드 부분(Codex, w3_collection §8)이 먼저 들어와야 Teams 평가를 돌린다.
- **해제 시각** (`action_ts = ⌈impair_off⌉`의 `impair_off`): C2·C2L은 `data/pilot/w3_<id>_load.csv`의 **마지막 행**(level 0, ms, `cpu_load.py:91`이
  affinity 복원 뒤 `finally`에서 기록)을 쓴다 — 이미 기록되므로 수집 변경 없음, `$off`보다 정확. L·B는 수집 전에 아래 중 하나로 정한다(**사용자 결정**, 2-3 해상도 한계):

  | 안 | L·B 기록 방식 | 지표 1 해상도 | 수집 부담 |
  |---|---|---|---|
  | A (권장) | `$off`를 `[DateTimeOffset]::Now.ToUnixTimeMilliseconds()/1000`으로, 명령을 미리 입력해 두고 Clumsy Stop 직후 Enter | 조작 지연(≈0.5–2초 [가정])만 남음, 소수 초 | 명령 1줄 변경 |
  | B | 지금 그대로(정수 초) | 정수 초, 오차 (−1, +조작 지연] | 없음 |
  | C | Clumsy를 스크립트로 시작·90초 뒤 종료·ms 기록(cpu_load처럼) | 창 단위 | Clumsy·clumsy2 CLI 지원 미확인, 스크립트 작성 필요 → S0에서 확인 |

  어느 안이든 지표 4(추정 − 정답)는 영향 없음(2-3). A·B면 지표 1 표에 "L·B는 조작 지연 포함" 주석을 단다.
- `ref` 보고: 통화별 `ref`와 상한 작동 여부(버퍼 최빈값 `poor`)를 표에 적는다. `ref=fair` 통화에서는 `fair` 수준 저하를 회복으로 볼 수 있다(2-1 한계 ①).
- 분리: diagnosis_v1과 **같은 통화 단위 dev/test**(조건마다 1·3번째 dev, 2·4번째 test). N·T는 dev에서만 고르고 test만 보고.
  선택 기준 [가정]: dev 오판정률(아래 2) ≤ 10%를 지키는 조합 중 지연 중앙값이 가장 작은 것.

| # | 지표 | 정의 | 대상 |
|---|---|---|---|
| 1 | **회복 판정 지연** | `action_ts = ⌈impair_off⌉`로 2-2 실행 → `recovered` 시각 − `impair_off`. 중앙값·IQR·n, 원인별(L·B·C) | L·B·C 통화 |
| 2 | **오판정률(거짓 회복)** | 손상이 계속되는 중 가상 조치 `action_ts = impair_on + 30` [가정] → `impair_off` 전에 `recovered`가 나온 통화 비율 | L·B·C 통화. "효과 있음" 통화(아래 4의 정답 기준 `overall`이 `ref`보다 나빠진 통화)만으로도 따로 |
| 3 | `not_recovered` 비율 | 1에서 T 안에 `recovered`가 안 된 비율. T=30·60 둘 다 표에 | L·B·C 통화 |
| 4 | 보조: 정답 기준 지연 | 같은 2-2를 `truth`로 만든 judge 등급에 적용(진단 조건 없음, 같은 N). 정답 쪽 `ref`는 truth 전용 `JudgeState`로 같은 `[on−20, on)`·보류 제외·상한 `fair` 규칙(진단 조건만 뺌) → 추정 기준 − 정답 기준 지연 차이, 둘의 판정 일치율 | 정답 있는 통화(Meet `ok`, Teams는 T9 통과 시) |
- 4는 "판정이 늦은 몫이 우리 추정 때문인지, 통화 품질 자체가 늦게 돌아왔기 때문인지"를 나눈다. **구조 지연은 상쇄되지 않는다**: 정답 기준은 judge 회복 2틱만,
  추정 기준은 judge 2틱과 투표 중 늦은 쪽이다. judge 등급이 손상 중 `ref`보다 나빴으면 둘 다 N+1번째 창, 나빠지지 않았으면(C 조건에서 흔함) 정답 N·추정 N+1번째 창
  → 같은 tick 열 위의 차이이므로 **0–1창(`ts`로 1초, 2 점프가 끼면 2초)은 구조 몫**으로 표에 따로 적고, 그 이상만 추정 오차·적응 차이로 해석한다.
- `device_cpu`(C 조건)는 P2에서 수신 fps가 거의 안 떨어졌다 → 수신 기반 judge는 손상을 못 볼 수 있고, 회복 판정은 사실상 진단(`call_core_pct`)의 복귀 시간이다. 결과에 이 한계를 적는다. 보조로 dump의 디코드 시간·송신 fps(diagnosis_v1 "효과 있음" 기준)가 기준선으로 돌아온 시각과 비교 [가정, 여유 시].
- N0 통화의 가짜 에피소드는 diagnosis 평가의 `none` 오탐률로 이미 보고 → 여기서 따로 세지 않는다.
- recovery 구간이 80초라 격자의 가장 긴 T=60도 구간 안에서 끝난다. diagnosis 평가에서 제외한 "recovery 첫 30초"를 여기서 쓴다.

## 6. 구현 범위 (W4, Codex luna·medium — 지금은 만들지 않음)
1. `server/recovery.py`: 2-1·2-2 순수 함수 + 2-4 상태 기계 작은 클래스 1개. N·T는 `judge.THRESHOLDS`처럼 모듈 상수.
   - **보류 여부는 tick JSON에 없으므로 인자로 받는다**: `held(grades, judge_state) -> bool`(`judge()` 직후 `recent[m][-1]`로 원시 overall 계산, 2-1),
     `ref_of(ticks, held_flags) -> "good"|"fair"`(버퍼 조건·최빈값·상한), `check(ticks, held_flags, action_ts, ref, n, t)`. `held_flags`는 ticks와 같은 길이.
     서버는 `build_tick` 직후 `held()`를 불러 상태 기계에 넘긴다.
2. **리팩터 (`server/app.py`, 동작 불변)**: 평가가 "Replay와 같은 경로"를 쓰려면 지금 `create_app().pipeline()` 클로저 안에 있는 부분을
   모듈 함수로 뺀다 — OS CSV 읽기(`app.py:217–233`), tick 시각의 `device` 고르기(2초 만료, `:257–267`), truth 행 만들기(`:208–216`).
   `recovery_eval.py`는 이 함수들 + `process_lines` + `build_tick`을 `--every 1`로 직접 부른다(서버·WS 없이). 기존 test_ws·계약 테스트가 그대로 통과해야 한다.
   안 빼고 복사하면 서버와 평가가 어긋날 수 있다(2초 만료·truth 선택 규칙).
3. `server/app.py`: `--schema v1.2`일 때 tick에 `recovery`(`--every > 1`이면 null), `receive()`에서 `type == "action"` 처리.
   - `--schema v1` 계약 테스트는 수정 없이 통과(`recovery`를 안 냄). 새 `action` 메시지도 기존 테스트를 깨지 않는다(`control`만 처리, 나머지 무시).
   - **수정 필요한 기존 테스트 1곳**: `tests/test_ws.py:274`(제외 집합)는 v1.2 tick에서 `{"judgement","device","diagnosis"}`만 빼고 `check()`하므로
     `recovery`가 남아 `tests/test_schema_contract.py:47`(최상위 키 일치)에서 실패한다 → 제외 집합에 `"recovery"` 추가(같은 PR).
4. `scripts/recovery_eval.py`: §5 표 출력(`--n`·`--t` 격자, dev/test, `--log`·`--app`으로 Meet·Teams 각각). C는 `_load.csv` 종료 행을 해제 시각으로(§5).
5. 의존: 진단 입력이 아직 `seq_loss=None`이라 Live의 `loss` 에피소드는 약한 IP/UDP 규칙뿐이다(재현율 0.03–0.18) → RTP 순번 결합(`RtpSeqLoss`)이 먼저 들어오면 `loss` 회복 평가가 의미를 가진다.

## 7. 테스트 표 (`tests/test_recovery.py`)
| # | 케이스 | 기대 |
|---|---|---|
| R1 | action 후 ok 5틱 (N=5) | `recovered`, `latency_s` = 5번째 tick ts − action_ts |
| R2 | ok 4틱 → 1틱 실패 → ok 5틱 | 실패에서 streak 0, 두 번째 연속 끝에서 `recovered` |
| R3 | 합성 tick 열(`ts` 연속 정수, 창 경계 = 해제 시각인 이상 정렬)을 실제 `judge` + `Diagnoser`에 통과. 초기 상태: 기준선 완성 후 손상 ≥ 3틱(원시 진단 3/3 손상, judge `poor`, `ref=good`), `action_ts` = 정수 ts, `action_ts+1`부터 정상 | (a) `recovered` = 해제 후 N+1번째 tick(이 열에서 `ts = action_ts + N + 1`) (b) 같은 조건에서 judge가 손상 중 `ref` 이하(device_cpu형)여도 N+1번째(투표) (c) 같은 스트림 자동 모드 → `latency_s = N`. 실제 창 위상은 R24 |
| R4 | T 안에 ok 없음 | `ts − action_ts ≥ 30`인 첫 tick에서 `not_recovered` |
| R5 | N번째 ok가 정확히 `ts − action_ts = T` | `recovered` (우선) |
| R6 | `cause="none", confidence=0.0` | ok 아님 (streak 0) |
| R7 | `overall="unknown"` | ok 아님 |
| R8 | `ref=fair`에서 `overall=fair` / `ref=good`에서 `overall=fair` | ok / ok 아님 |
| R9 | `ref` 계산: 버퍼 20틱 최빈값, 동률이면 나쁜 쪽, 비면 `fair`, `conf=0.0`·손상·judge 보류 tick은 버퍼에 안 들어감, 최빈값 `poor`(보류 아닌 원시 `poor` 20틱) | 각각 일치, 마지막은 `fair`(상한) |
| R10 | `ts ≤ action_ts` tick | 세지 않음 |
| R11 | ts 간격 0 / 2 / 3 (`--every 1`) · `--every 2`로 서버 실행 | streak 0 / 유지 / 0 · 모든 tick `recovery` = null, action 메시지 무시(연결 유지) |
| R12 | 상태 기계: idle → `cause=loss` → degraded → action → checking → recovered → `cause=bandwidth` | 각 전이, 마지막은 degraded·`ref` 새로 고정 |
| R13 | degraded에서 클릭 없이 cause→none(conf>0) | checking, `action_source="auto"`, `action_ts` = 그 tick ts |
| R14 | checking 중 action 다시 | 무시, `action_ts` 그대로 |
| R15 | `{"type":"action"}`(cause 없음)·잘못된 JSON·`cause`가 문자열 아님 | 앞은 받아들임, 뒤 둘은 무시. 연결 유지 |
| R16 | `--schema v1`에서 action 메시지 | tick에 `recovery` 없음, 기존 계약 테스트 통과 |
| R17 | `--schema v1.2` tick의 `recovery` | `--every 1`: 키 9개 고정, `state`·`action_source` enum 안, `latency_s`는 `recovered`일 때만 number / `--every > 1`: null |
| R18 | Replay `--speed 0`에서 action 수신 | `action_ts` = 마지막 broadcast tick ts (벽시계 아님) |
| R19 | CPU 샘플 소실: `device_cpu` 에피소드 `checking` 중 `device=None` tick(패킷 정상, `none, conf>0`) | ok 아님(streak 0), `recovered` 안 나옴. 같은 상황의 `loss` 에피소드는 영향 없음 |
| R20 | 재진입: `not_recovered` 뒤 같은 `cause` 지속 10틱 / 원인이 `bandwidth`로 바뀜 / action 수신 | `not_recovered` 유지·`ref` 그대로 / `recovery.cause`만 갱신 / `checking`, 새 `action_ts` |
| R21 | 두 번째 에피소드 `ref`: (a) 1차 `ref=fair` → `recovered` 뒤 `good` 20틱 → 새 손상 (b) 경계, 실제 `judge` 사용: 버퍼 `good` 20틱 → 원시 `poor` 1틱 → 원시 `good`/`fair` 교대 20틱(`overall=poor` 유지, 진단 `none, conf>0`, 상태 `idle`) → 새 손상 | (a) 2차 `ref=good`(회복 후 버퍼) (b) 교대 20틱은 보류라 버퍼에 안 들어감 → `ref=good`(≠`poor`). 이어서 `checking`에서 `overall=poor`가 계속되면 `recovered` 안 나옴 |
| R22 | (a) 이미 정상인 `idle`에서 action (b) 진단이 놓친 저하: 버퍼가 원시 `poor` 20틱(진단 `none, conf>0`, 상태 `idle`) → action → `overall=poor` 계속 (c) (a)의 `checking` 중 진단 `loss` | (a) `checking`, `recovery.cause=null`, `ref` = 버퍼 값, N틱 뒤 `recovered`(`latency_s = N`) (b) `ref=fair`(상한), `recovered` 안 나옴 → T에서 `not_recovered` (c) `recovery.cause="loss"`, `ref`·`action_ts` 그대로 |
| R23 | `checking` 중 실제 흐름 전환(`flow` 2연속 변경) → Diagnoser 재수집 | 재수집 동안 streak 0, `action_ts`·`ref`·elapsed 유지 / 재수집이 T 안에 끝나고 N틱 ok면 `recovered`, 아니면 elapsed ≥ T에서 `not_recovered` |
| R24 | 실제 창 생성 경로: 영상 크기 UDP 합성 패킷을 `WindowFeatures.push`(또는 `stream_csv`)에 넣어 tick `ts` 열을 만든다. ① 30ms 간격 연속 **60초**(≥ 51창), 시작 epoch 소수부 0.0·0.5 두 가지 ② 중간 3초 공백 ③ `impair_off = 100.4`(C 조건처럼 ms 해제 시각) ④ Live idle flush(`process_lines`에 `None`) | ① 두 위상 모두 `ts` 간격이 1 또는 2뿐이고 2가 1회 이상(50창 주기 [계산]), 조건 3이 streak를 끊지 않음 ② 공백 뒤 간격 ≥ 3 → streak 0 ③ `action_ts = 101`, 첫 집계 tick = `ts > 101`인 첫 창(102 또는 103), 그 창 첫 패킷 epoch ≥ 100.4 ④ 직전과 같은 `ts`면 streak 0 |

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
- N=5·T=30·`ref` 버퍼 20틱·빈 `ref`=`fair`·tick 간격 규칙·가상 조치 `on+30`·오판정률 ≤10% 기준: 모두 [가정], W5 dev에서 조정.
- OS 샘플이 자주 끊기면(2초 만료) `device_cpu` 회복이 `not_recovered`로 기운다 — 거짓 회복보다 안전한 쪽으로 둔 선택. W3 `_os.csv`의 샘플 간격으로 빈도 확인.
- Chrome이 대역폭 해제 후 비트레이트를 얼마나 빨리 올리는지 미확인 → B300에서 T=30이면 `not_recovered`가 많을 수 있다(그 자체가 결과, 지표 4로 해석).
- 흐름 전환(P2P↔relay)이 recovery 구간에 생기면 Diagnoser 재수집(`confidence 0.0`) 동안 ok가 안 되어 지연이 늘어난다. 평가에서는 `note=path_switch_late` 통화를 따로 표시.
- 메뉴 위치(Meet 수신 해상도, Teams 웹 받는 영상 끄기)·PiP에서 WS 공유: 미확인.
- 조작 지연 ≈0.5–2초(§5 해제 시각 A안): [가정], 리허설 S0-3에서 Clumsy Stop → Enter 간격을 몇 번 재 보면 확인 가능.

## 미해결 (r4, 4차 리뷰 없이 남김)
- ~~L·B 해제 시각 기록 방식~~ → **A안 확정(10/28)**: `$on`·`$off` ms 기록, `w3_collection.md` 반영 완료. 조작 지연 약 0.5–2초 [가정]은 S0-3에서 실측.
- 간격 1인 idle flush tick은 ok로 셀 수 있음(2초 전면 무패킷 직전에 `recovered` 가능). tick이 flush에서 왔는지 표시하려면 `process_lines`에 플래그가 필요해 W4 구현 때 판단. 영향 작음(인터페이스 전체 2초 무패킷일 때만).
- `ref` 상한 `fair`의 한계 ①②(2-1): `fair` 수준 미검출 저하, 수신 지표가 안 나빠지는 C 조건. 평가에서 통화 수로 보고만 한다.
- 경량 모드(`--every > 1`) 회복 표시 없음: 오버헤드 실험 E5 결과로 경량 모드가 데모 기본이 되면 다시 설계(그때 관측 안 한 초를 어떻게 셀지부터). **E5 결과 후 재검토 필요**(경량 모드 끄기는 10/28 사용자 동의). `ref` 상한 `fair`도 수용(10/28).
