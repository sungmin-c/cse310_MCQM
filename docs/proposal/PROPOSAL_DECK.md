# Final Project Proposal 발표 자료 — 팀원용 안내 + 발표 스크립트 (v2, 2026-10-25)

> 발표 시간: **약 8분 30초** (허용 5–10분), 슬라이드 11장, 언어: **영어 슬라이드 + 영어 스크립트**. 한국어 메모는 팀원 이해용
> 흐름: ① vcaml이 뭔가 → ② 기존 산업 제품과 한계 → ③ vcaml로 가능한 것 → ④ 그래서 우리가 하는 것 → ⑤ 계획 + 파일럿 → ⑥ 최종 데모에서 보일 것
> 전체 배경은 `PROJECT_OVERVIEW_KO.md` / `PROJECT_OVERVIEW_EN.md`

---
## Part 1 — vcaml, 1분 요약 (0:00–1:30)

### Slide 1 — Title + hook (0:00–0:20)
**On slide:** MCQM: Is It the Network or My Laptop? / Real-time video call quality monitoring from packet headers / CSE310 Final Project Proposal / Sungmin Choo · [Teammate]
**Script:**
> Hi, we are Sungmin and [Teammate]. When a video call starts to stutter, is it the network, or is it your own laptop? Our project, MCQM, tries to answer that in real time — without opening the app.

**한국어 메모:** 제목 질문이 프로젝트 전체의 질문이다.

### Slide 2 — vcaml in one minute (0:20–1:30)
**On slide:**
- vcaml (IMC 2023, my solo project base): estimate video quality **without decrypting** anything
- Input: only **packet size + arrival time** (IP/UDP headers), 1-second windows
- Model: **Random Forest** → frame rate · bitrate · frame jitter · resolution
- Result: ~**1.5 fps** average error (Meet, Teams, Webex) — we reproduced **1.49**
- Limits: offline · Linux lab data · estimates quality only (no cause)

**Script:**
> First, one minute on vcaml, the research system my earlier solo project was about. Video calls are encrypted, so you can't read the video. But you can still see the envelope: how big each packet is and when it arrives. vcaml takes those two things, in one-second windows, and a Random Forest estimates the frame rate, bitrate, frame jitter and resolution. The paper reports about 1.5 frames per second of error on Meet, Teams and Webex, and we reproduced 1.49. The ground truth in the paper comes from Chrome's own WebRTC statistics. But vcaml has limits: it runs offline after the call, it was trained on Linux lab data, and it only says how good the call is, never why.

**한국어 메모:**
- "솔로 프로젝트" = vcaml 논문 재현·학습(솔로 repo는 읽기 전용 보관). 정답 = Chrome webrtc-internals.
- 1.5 fps 오차 = 30 fps 영상을 28.5–31.5로 맞힘. 재현값 3개 앱 평균 1.491 (Meet 1.334 / Teams 1.812 / Webex 1.328).
- RTP 헤더까지 쓰는 옵션(rtp-ml, 오차 1.33)도 있지만 핵심은 IP/UDP 방식.

---
## Part 2 — 기존 산업의 솔루션과 한계 (1:30–3:00)

### Slide 3 — What the industry already has (1:30–2:10)
**On slide:** (table)
| | In-call, for users | For IT admins |
|---|---|---|
| Google Meet | "Troubleshooting & help": CPU load, network stability, suggested actions | Meet Quality Tool |
| Microsoft Teams | Call health panel (refresh every 15 s) | Call Quality Dashboard, Real-Time Analytics |
| Zoom | Statistics window (we used it in a pilot) | Zoom Dashboard (MOS 1–5) |
| Webex | — (not reviewed) | Control Hub + ThousandEyes (network path) |

**Script:** `SCRIPT_ChatGPT.md` Slide 3 (발표용 최종 스크립트는 그 파일)

**한국어 메모:** 근거 출처는 문서 맨 아래 "출처". 우리 조사는 **공식 문서 검색만**이다(제품을 직접 써 보지 않음). Meet은 사용자에게 CPU 부하와 조치 제안까지 보여 준다 → "업계에 없다"고 말하지 않는다.

### Slide 4 — Why that is not enough (2:10–3:00)
**On slide:**
1. **Inside one app only** — each uses the vendor's internal data; no common monitor across Meet, Teams, Zoom
2. **Different in every app** — raw numbers vs. hints; deeper views need admin rights, sometimes extra licenses
3. **Accuracy can't be checked from outside** — no published hit rate for cause hints; no independent check that the call recovered
→ **Our question:** can it be done from outside the app, for any app — and how accurately?

**Script:** `SCRIPT_ChatGPT.md` Slide 4

**한국어 메모:** 한계는 "기능이 없다"가 아니라 **앱마다 따로 + 벤더 내부 데이터 + 외부에서 정확도 검증 불가**다.

---
## Part 3 — vcaml로 가능해지는 것 (3:00–3:50)

### Slide 5 — What vcaml makes possible (3:00–3:50)
**On slide:**
- **No app cooperation:** works from outside, on the user's own machine, for any app that sends UDP video
- **No decryption:** headers only → privacy-friendly, own-laptop traffic only
- **Per-second numbers:** fps · bitrate · jitter · resolution
- **Cheap:** one inference ≈ 36 ms (p95) — fits a 1-second budget (we measured)
- → the missing piece for an **app-independent monitor** that doesn't rely on vendor data

**Script:**
> This is what vcaml makes possible. A monitor that runs on the user's own laptop, outside the app, with no help from the vendor and no decryption. It gives numbers every second, and one inference takes about 36 milliseconds in our measurement, so it fits in real time. That is exactly the piece the vendor tools are missing.

**한국어 메모:** 36 ms = 4개 모델 + 진단, in-lab Meet 10통화 438 tick의 p95 (10/13). 실통화 배터리 상태에서는 p95 126 ms (그래도 1초 이내).

---
## Part 4 — 업계가 하지 않은 것을 우리가 한다 (3:50–4:30)

### Slide 6 — What we add (3:50–4:30)
**On slide:** vcaml gives *how good*. MCQM adds *why* and *did it get better*:
1. **Real time** — every second during the call
2. **Real-world accuracy** — measure on real Windows calls, **retrain**
3. **Cause diagnosis** — network (loss, bandwidth) vs. device (CPU), using packets **+ OS metrics**
4. **Action → recovery check** — suggest a fix, verify quality came back
5. **Dashboard + mini widget** — always-on-top window next to the call

**Script:**
> So here is the gap. The platforms help users, but each only inside its own app, with its own data. vcaml works from outside, but offline and without causes. MCQM does it from outside, live, for any app — and measures how accurate it is. We add five things: real time; real-world accuracy with retraining; cause diagnosis that combines packets with operating-system metrics; an action suggestion with a recovery check; and a dashboard plus a small always-on-top widget.

**한국어 메모:** 5개 순서를 외운다. 위젯 = 대시보드를 Chrome Document Picture-in-Picture로 띄운 작은 창(새 앱 아님). 조치는 **안내만**, 실행은 사용자.

---
## Part 5 — 현재 계획과 파일럿 결과 (4:30–7:10)

### Slide 7 — System + plan (4:30–5:20)
**On slide:** Meet/Teams/Zoom on Windows → **tshark** (headers only) → 1-s features → **Random Forest** → **judge** (good/fair/poor) → **diagnosis** (packets + CPU) → **action + recovery** → WebSocket → **dashboard + widget**
Timeline: Oct pilots ✅ · Oct 27 Meet ~30 calls · Nov 3 Teams ~15 · Nov 10 Zoom ~15 + evaluation · **Nov 24 freeze** · **Dec 2 demo**
Roles: Sungmin — capture, ML, experiments · [Teammate] — dashboard, widget

**Script:**
> Here is the plan. The call runs on our Windows laptop. tshark captures only the headers. Every second we compute features and the Random Forest estimates quality, a judge rates each metric, and the diagnosis uses packet signals plus CPU metrics. Then we suggest an action and track recovery, and stream everything to the dashboard and widget. Everything runs locally on our own traffic. We collect Meet first, about 30 calls, then Teams, then Zoom, freeze features on November 24th, and demo on December 2nd. Sungmin does capture, machine learning and experiments; [Teammate] builds the dashboard and widget.

**한국어 메모:** 코드(실시간 파이프라인·judge·WS·진단 v1)는 main 병합 완료, pytest 197 통과. 측정 순서 이유: Meet은 정답 확보, Teams는 vcaml이 다룬 앱, Zoom은 정답이 근사값이라 가장 위험 → 마지막.

### Slide 8 — Pilot results (5:20–6:30)
**On slide:** (one pilot call each — direction check, not final results)
| Pilot | Finding | So what |
|---|---|---|
| Original model, real Windows Meet call | fps error **9.09** (lab: 1.33); bitrate ~6× too low | **Retrain** on our data |
| Chrome limited to 2 CPU cores | Packets normal, but **36 freezes**, decode time **~9×** | Packets alone **can't see** device problems → add OS metrics |
| Monitor on vs. off | **~1.3%** CPU, no change in call quality | Light enough to run during calls |

**Script:**
> We already ran pilots, one call each, so these are direction checks. First, the original model on a real Windows Meet call had 9.09 frames per second of error, against 1.33 in the lab. The capture was fine — bitrate computed straight from packets matched the truth. The model had simply never seen calls like ours: ours ran at 1.9 megabits and 1280 pixels, its training data had a median of 125 kilobits. The vcaml paper saw the same drop in real-world data. So retraining is needed. Second, when we limited Chrome to two cores, packets looked completely normal, but the video froze 36 times and decoding took nine times longer. So packets alone can't see device problems; we need OS metrics. Third, our monitor uses about 1.3 percent CPU and didn't change call quality.

**한국어 메모:** "One pilot call each"를 반드시 말한다. 9.09의 이유(학습 범위 밖)와 논문 Table 5(Meet 12.41)와 같은 양상이라는 점이 핵심. 원인 진단 합성 실험(in-lab trace에 손상 삽입)에서는 대역폭 재현율 0.95–1.00, 손실은 RTP 순번이 있을 때 0.56–0.94, IP/UDP만이면 0.03–0.18 — 질문 나오면 답용.

### Slide 9 — Evaluation plan + risks (6:30–7:10)
**On slide:**
Ground truth: Chrome WebRTC stats (Meet, Teams) · Zoom stats window (approximate). Injected problems: loss · bandwidth · CPU.
| Question | Metric |
|---|---|
| Accurate? | fps/bitrate error, before vs. after retraining |
| Cause? | precision/recall, with vs. without OS metrics |
| Recovery? | seconds to detect, false "recovered" rate |
| Light? | CPU, call quality monitor on vs. off |
Risks → backup: retrain fails → report the gap · Teams truth missing → "estimate only" · live demo fails → replay

**Script:**
> To evaluate, we inject controlled problems — loss, a bandwidth limit, a CPU limit — and measure four things: estimation error before and after retraining, diagnosis precision and recall with and without OS metrics, how fast we detect recovery, and the monitor's own overhead. Risks: if retraining doesn't close the gap, we report the gap; if Teams ground truth isn't available, we label it estimate-only; if the live demo fails, we replay recorded calls. Honest limits: small sample with one phone as the call partner, artificial problems, and in experiments the "fix" is removing the injected problem — so we measure how well we detect recovery, not whether the advice works in the wild.

**한국어 메모:** 마지막 문장이 "순환 실험 아니냐" 질문의 답이다.

---
## Part 6 — 최종 데모의 내용과 지향점 (7:10–8:30)

### Slide 10 — Final demo: what you will see (7:10–8:00)
**On slide:**
**Live demo (≈5 min of the 12-min final):** normal call → inject loss or CPU limit → widget names the **cause + confidence** and suggests an **action** → problem removed → widget shows **"Recovered"**
**Deliverables:** working monitor (Meet · Teams · Zoom) · dashboard + widget · results table: accuracy before/after retraining · diagnosis confusion matrix · recovery delay · overhead · Android 4-layer design note (design only) · replay + recording as backup
**Success looks like:** retraining shrinks the Windows gap (or we explain why not) · OS metrics clearly improve CPU diagnosis · recovery detected within seconds with few false "recovered"

**Script:**
> In the final demo you'll see a live call degrade. The widget names the cause with a confidence, suggests an action, and when the problem is removed, shows "Recovered". Behind it, we'll show the numbers: accuracy before and after retraining, a diagnosis confusion matrix with and without OS metrics, recovery delay and overhead. Android is a design note only. If the live demo fails we switch to a replay.

**한국어 메모:** 성공 기준의 구체 수치(예: 회복 연속 N초)는 아직 [가정] — 설계 T10에서 확정. 진단은 "추정"이며 UI에 confidence 표시.

### Slide 11 — Summary (8:00–8:30)
**On slide:**
- vcaml: call quality from **encrypted packets**
- Platforms: help users, but each inside its own app, with its own data
- MCQM: **outside the app · any app · real-time · cause · action · recovery · measured accuracy**
- Demo: **Dec 2**

**Script:** `SCRIPT_ChatGPT.md` Slide 11

---
## 예상 질문 (영어 답, 짧게)
| Q | A |
|---|---|
| How is this different from vcaml? | vcaml is offline and estimates quality only. We add real-time, real-world accuracy + retraining, cause diagnosis with OS metrics, and recovery checking. |
| Don't Teams/Zoom/Meet already show this? | Partly, yes — Meet even shows CPU load and suggests actions. But each works only inside its own app with the vendor's internal data, and their accuracy can't be checked from outside. We work from outside, for any app, and measure accuracy against ground truth. (Doc review only — we did not test them.) |
| Isn't the recovery test circular? | We don't claim the advice works in the field. We measure detection delay and false "recovered" rate; Chrome adapts on its own, so recovery is not trivial to detect. |
| Why Teams before Zoom? | vcaml already covers Teams, so there's a baseline model; Zoom has none and only approximate ground truth, so it's riskiest. |
| Is capturing packets a privacy problem? | Only our own laptop's traffic, only headers — content is encrypted and never used. |
| What if retraining fails? | We report the accuracy gap as a result, as the vcaml paper did for real-world data. |
| Why a widget instead of an app? | It's the same React dashboard opened in Chrome's Picture-in-Picture window. |
| 9.09 fps error — isn't that a failure? | For the unmodified model, yes — same pattern as the paper's real-world result. The capture was fine; the model was out of its training range. Retraining is the plan. |

## 아직 확인 안 된 것 (발표에서 "확정"처럼 말하지 않기)
- Teams 브라우저 정답(webrtc-internals) 가능 여부 — Teams 파일럿(T9) 전
- PiP 위젯이 전체 화면 통화 위에 계속 뜨는지 — 팀원 스파이크(T11)
- Clumsy 손실이 캡처에 보이는지(S0-1), clumsy2 대역폭 제한 동작(S0-2)
- 재학습 후 정확도 — 아직 데이터 없음
- 조치·회복 판정 규칙의 N초/T초 — [가정], T10에서 확정
- 업계 제품 비교는 문서 조사만(직접 테스트 안 함). "none of them"으로 단정 금지
- Proposal 발표 정확한 시간 제한

## 출처 (Part 2)
`SCRIPT_ChatGPT.md` 하단 "출처"로 통합(2026-10-25 재확인: 사용자용 통화 중 패널 추가, CQD "30분 지연"은 벤더 2차 출처라 삭제).
