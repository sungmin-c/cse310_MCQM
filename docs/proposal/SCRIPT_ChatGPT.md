# MCQM — English Presentation Script
**Project:** MCQM — Multi-layer Call Quality Monitor
**Presenters:** Sungmin Choo and Yerim Cho

## Slide 1 — Title and Motivation
Hi, we are Sungmin and Yerim Cho.

Our Teamname is MCQM(Multiple-layer Call Quality Monitor).

Imagine you are having a video call and it begins to stutter. Is the problem the network, or your own laptop?

That is the question MCQM tries to answer, from outside the call app: what the cause is, what action to take, and whether the network has recovered, in the same way for every app.

## Slide 2 — Agenda
Here is our plan for today.

We start with the motivation, the problem we want to solve. Then, as background, we briefly introduce the vcaml paper on which my solo project was built.

Next, we look at existing industry solutions and their limitations, and at what vcaml makes possible.

Then we present our contribution, the system architecture and plan, and our pilot results.

Finally, we cover the evaluation plan and risks, the final demo, and our conclusion.

## Slide 3 — vcaml: Our Starting Point
What is vcaml? Vcaml is a public github project based an IMC 2023 paper. It claims that Estimating WebRTC Video QoE Metrics Without Using Application Headers is possible.

Here is the breakdown: during a video call, the app keeps sending packets. The payload of each packet is encrypted, so we cannot see the video itself. But the packet headers are visible, and from them we can read two things: the packet size and the arrival time.

vcaml extracts features from these sizes and arrival times and trains a Random Forest on them. The model estimates four quality metrics: frame rate, bitrate, frame jitter, and resolution. The paper defines these 4 features as QoE. Its accuracy is measured by comparing these estimates with the ground truth, the values Chrome itself reports for the call.

The paper reports about 1.5 frames per second of frame-rate error; we reproduced it and got 1.49.

But vcaml has three gaps: it was evaluated offline on recorded calls, it was trained on Linux lab data, and it says how good a call is, not why.

## Slide 4 — Existing Industry Solutions
Before building anything, we checked what typical WebRTC platforms already offer. Inside the call, Google Meet has a "Troubleshooting and help" panel, Teams has Call health, and Zoom has a statistics window.

For administrators, there are deeper tools, such as Microsoft's Call Quality Dashboard and Webex Control Hub.

So the platforms agree that users need this kind of help.

## Slide 5 — Limitations of Existing Solutions
However, each tool works only inside its own app, using the vendor's internal data, and what it shows differs from app to app, meaning there is no common monitor across apps.

Also, as outsiders, we found no published numbers on how often their cause hints are right.

So our question: can this be done from outside the app, and can we measure how accurate it is?

## Slide 6 — What vcaml Makes Possible
This is where vcaml helps, because it needs only packet headers: no decryption, no vendor help, only our own laptop's traffic, meaning it can work from outside the app.

Its method also already works one second at a time. For each one-second window, it computes statistics of the packet sizes, called LSTATS, and statistics of the gaps between packet arrivals, called TSTATS. The Random Forest predicts from that one window alone; it does not need the rest of the call. So the paper evaluated offline, but nothing in the method stops us from running it every second on a live call.

The remaining question is speed. We call one second of processing one tick. (within one tick, there are feature extraction, prediction for the four metrics, and diagnosis). At the 95th percentile, a full tick takes about 36 milliseconds in our lab benchmark, and on a real call on battery, the model prediction alone took about 126 milliseconds. So, both are within the one-second limit.

Therefore, speed is not the problem. Accuracy on real calls is the hard part.

## Slide 7 — Our Contribution: MCQM
Building on that, vcaml estimates how good the call is, but MCQM is a measurement and verification study built on top of it: how well can this be done from outside the app, and how do we know?

We contribute four things.

First, real time measurement. One method from outside the app: the same pipeline for Meet and Teams, updated every second.

Second, Real-world accuracy, meaning measured error: we compare estimates with Chrome's own statistics on real Windows calls, and retrain with our own data.

Third, cause diagnosis with measured accuracy: packet signals plus CPU metrics separate network problems from device problems, and we report precision and recall against the conditions we inject.

Fourth, action and recovery: we suggest an action, then check whether quality recovers, or at least whether our monitor detects the recovery. The action is guidance only; the user decides.

A dashboard and a small widget show your real time network quality next to the call. They are being built and not yet connected to the pipeline.

## Slide 8 — System Architecture and Plan
Here is how it fits together. The call runs on our Windows laptop, and tshark captures only packet headers.

Every second, we extract features, estimate quality, judge each metric, diagnose the likely cause, suggest an action, track recovery, and send it all over a WebSocket to the dashboard and widget.

The core modules are merged, and all 197 automated tests pass. These are pytest tests that run on recorded or synthetic data, without a live call. They check 1. our streaming features match vcaml's original code, 2. the diagnosis and judging rules behave correctly at their thresholds, 3. our loss injection is reproducible, and 4. the WebSocket messages have the format the dashboard expects.

But the full live pipeline is not yet verified on real calls, meaning we cannot claim live accuracy yet. Next we collect Meet calls, then Teams calls, and we will demo in the final presentation.

(I handle capture, machine learning, diagnosis, and experiments. [Teammate] builds the dashboard and the widget.)

## Slide 9 — Pilot Results
To test these ideas early, we ran three pilots. Each is a single call, meaning these are direction checks, not results.

First, the original vcaml model on a real Meet call had a frame-rate error of 9.09, against 1.33 on lab data. The capture was fine, but the model had never seen calls like our testing environment. Therefore, we must retrain.

Second, with Chrome limited to two CPU cores, packets looked normal but the video froze repeatedly. Packets alone cannot see a device bottleneck; therefore, we add operating-system metrics.

Third, our monitor used about 1.3 percent CPU and did not change the call quality.

## Slide 10 — Evaluation Plan and Risks
For the full evaluation, in each test call we inject one problem: packet loss, a bandwidth limit, or a CPU limit. That condition is our label, and Chrome's statistics are the ground truth for quality.

We measure estimation error before and after retraining, diagnosis precision and recall, recovery-detection delay, and overhead.

If retraining doesn't close the gap, we report the gap. One honest limit: our "fix" is removing the injected problem, meaning we measure recovery detection, not whether advice works in the wild.

## Slide 11 — Final Demo and Expected Outcome
Finally, in the demo you'll see a normal call, then an injected problem. The widget shows the estimated cause, its confidence, and a suggested action, then shows recovery when we remove the problem.

Alongside it we present accuracy before and after retraining, a diagnosis confusion matrix, and monitoring overhead.

These are goals, not results yet.

## Slide 12 — Conclusion
To sum up, vcaml showed that call quality can be read from encrypted packets. Platforms help users, but each only inside its own app.

Building on both, MCQM is a measurement and verification study. From outside the app, in real time, it estimates quality, finds the likely cause, checks recovery, and reports how accurate each step is, including where it fails.

Beyond video calls, the same idea may carry over to other encrypted services. We have only tested video calls, so this is a direction, not a result.

Thank you. We're happy to take questions.

---

## 수정 내역 (원본 ChatGPT 스크립트 대비)
| 위치 | 원본 | 수정 | 이유 |
|---|---|---|---|
| 전체 | "VCAML" | "vcaml" | 논문·repo 표기가 소문자 |
| Slide 3 | "Linux laboratory data" | "Linux lab data with emulated network conditions", 정답 = Chrome WebRTC 통계 추가 | SPEC: 학습 데이터는 Linux Chrome + 에뮬레이션 조건 |
| Slide 4·5 | 업계 도구 = 관리자용, 조치·회복 확인 없음 | 통화 중 **사용자용 패널**(Meet Troubleshooting & help: CPU·네트워크·조치 제안 / Teams Call health 15초 / Zoom 통계 창)을 먼저 소개. 한계는 "앱마다 따로, 벤더 내부 데이터, 정확도를 외부에서 검증할 수 없음"으로 재구성 | 웹 확인 결과 Meet은 사용자에게 CPU 부하와 조치 제안까지 보여 준다. "관리자만 본다"·"조치 제안 없음"은 사실이 아니다. Teams도 관리자 Real-Time Analytics로 진행 중 회의를 볼 수 있다 |
| Slide 6 | "126 ms … four models" 맥락 모호 | 36 ms = in-lab, 모델 4개 + 진단 / 126 ms = 실통화 배터리 상태, 추론 단계 | PROGRESS M2·P3 원문 |
| Slide 7 | "not implemented yet" | "being built now, not yet connected to the pipeline". 조치는 안내만 한다는 점 추가 | repo에 `dashboard/` 폴더는 아직 없다. 팀원 쪽 진행 상황은 미확인이라 연결 전이라고만 말한다 |
| Slide 8 | 테스트 수 없음, Teams 방식 없음 | "197 tests pass", "Teams through the Chrome web client" | PR #9 병합 후 main pytest 197 |
| Slide 9 | "Each pilot was small" | "Each one is a single call" | 모든 파일럿이 통화 1건 |
| Slide 9 | "decoding increased ~9×" | "in the first 45 seconds … up to about nine times", 수신 fps 정상 유지 추가 | 디코드 6.6 → 최대 57 ms(약 8.6배)는 제한 직후 45초 동안의 값 |
| Slide 10 | 주입 조건·정답 출처 없음, 순환 실험 언급 없음 | 손실·대역폭·CPU 주입 = 라벨, Meet/Teams 정답 = Chrome 통계, "조치 = 주입 해제" 한계 추가 | SPEC §3·규칙 7, 가장 많이 받을 질문 |
| Slide 1 | "answer in real time, from outside the call app…" | "cause, action, recovered network … for every app we test" | 사용자 요청. "for any app" 금지 규칙에 맞춰 "we test"를 붙임 |
| Slide 2 | 없음 | 목차 슬라이드 추가 (10개 항목) | 사용자 요청. 이후 슬라이드 번호와 Q&A 참조를 1씩 밀었다 (기존 Slide 2~11 → 3~12) |
| Slide 3 | "Calls are encrypted" | payload는 암호화, 헤더에서 크기·도착 시각 → 특징 → RF → 4개 지표, 정답과 비교. "runs offline" → "evaluated offline on recorded calls" | 청자 이해. 방법 자체는 실시간 가능하다는 Slide 6와 모순 제거 |
| Slide 6 | "36 ms per second of call" | 1초 창 LSTATS·TSTATS로 창 하나만 보고 예측 → 실시간 가능 설명 추가. 36 ms = 1 tick(특징 + 예측 + 진단) 처리 시간 | "vcaml이 실시간 되나?" 질문 선제 차단 |
| Slide 7 | "check whether quality recovers" | "or at least whether our monitor detects the recovery" | Slide 10 한계(회복 탐지만 측정)와 일관 |
| Slide 8 | "197 automated tests pass" | pytest, 녹화·합성 데이터, 실통화 없음 + 검사 내용 예시 | `pytest --collect-only` 197개 확인 (10/26) |
| Q&A | 없음 | Q8 CPU·메모리 비용 추가 | 사용자 요청 |
| Slide 12 | "identified an opportunity for a user-side monitor" | "platforms help users, but only inside their own app" → 앱 밖, 어느 앱이든, 정확도 측정 | Slide 4·5 수정과 일관 |

## 발표 때 말하지 말 것
- "업계에 이런 기능이 없다" — Meet은 사용자에게 CPU·네트워크 정보와 조치 제안을 보여 준다
- "대시보드가 동작한다" — 아직 파이프라인과 연결 전
- 파일럿 수치를 "결과"로 말하기 — 항상 "one pilot call"을 붙인다
- Teams 정답 확보, 재학습 효과, Clumsy 손실이 캡처에 보이는지 — 모두 미확인
- "다른 암호화 서비스에도 적용된다" — 영상통화 외에는 시험하지 않았다. "방향"이라고만 말한다
- "벤더는 리스크 때문에 안 한다" — 근거 없음 (벤더도 앱 안에서는 실시간 안내를 한다)
- "for any app" — Meet·Teams만 시험한다 (Zoom은 계획에서 제외)

## 출처 (2026-10-25 웹 확인. 제품을 직접 시험하지 않았다)
- Google Meet Troubleshooting & help 패널: https://workspaceupdates.googleblog.com/2021/01/network-performance-troubleshoot-issues-google-meet.html (2021년 발표 자료. 현재 UI는 바뀌었을 수 있음)
- Teams Call health(15초 갱신): https://support.microsoft.com/office/7bb1747c-d91a-4fbb-84f6-ad3f48e73511
- Teams Real-Time Analytics(관리자, 진행 중 회의, Premium이면 자동 수집): https://learn.microsoft.com/el-GR/microsoftteams/use-real-time-telemetry-to-troubleshoot-poor-meeting-quality
- Teams CQD 분류(임계값 초과 ≠ 사용자 체감): https://learn.microsoft.com/en-in/MicrosoftTeams/stream-classification-in-call-quality-dashboard
- Zoom Dashboard MOS·관리자 경고: https://library.zoom.com/admin-corner/network-management/quality-of-service-and-network-best-practices-explainer/using-zoom-dashboard-to-troubleshoot-network-issues
- Zoom 통계 창: 우리 P4 파일럿에서 직접 확인(내보내기 없음, 정수 fps)
- Meet Quality Tool(관리자): https://support.google.com/a/answer/9204857
- Webex Control Hub + ThousandEyes: https://help.webex.com/en-us/article/nymfj2d/Integrate-ThousandEyes-with-Troubleshooting-in-Control-Hub

---

## Expected Q&A

**Q0. What is vcaml, and how does it know quality without the payload?**
- Per app x metric, one scikit-learn Random Forest (12 models; default hyperparameters)
- Input = packet size + arrival time only -> per 1 s window: size stats (LSTATS) + inter-arrival stats (TSTATS) -> RF -> metric
- Why it works: one video frame -> a burst of similar-size packets -> the model learns that correlation
- Ground truth for training = Chrome `webrtc-internals`
- Limit: statistical, so wrong outside its training data (our pilot MAE 9.09; paper Table 5: 12.41)

**Q1. (Slide 6) What do 36 ms and p95 mean? Is "fast" measured against one second?**
- 36 ms = processing time of one tick (packet push + features + 4 RF predictions + diagnosis)
- p95 = 95% of 438 ticks finished within 36.2 ms (max 103 ms), 10 in-lab Meet calls
- Real limit = 1 s (a slower tick -> delay builds up -> not real time); 200 ms is our own internal budget
- Means only "a 1 s estimate is computed within that second" -> not "problems are detected in real time" (decision delay: ~1.5 s bandwidth/jitter, 1-19 s loss)
- Limits: lab traffic ~30 pkt/s (Teams ~270 pkt/s not measured); real call on battery: model prediction alone p95 126 ms, cause of gap unconfirmed (CPU throttling suspected)

**Q2. (Slide 7) How do you measure accuracy?**
- QoE = 4 metrics (fps, bitrate, frame jitter, resolution) -> accuracy = error vs. Chrome `webrtc-internals`
- fps / bitrate / frame jitter: MAE (+ share within 2 fps); resolution: classification accuracy
- Same test calls before vs. after retraining; train/test split by call
- Diagnosis is separate: label = injected condition (loss / bandwidth / CPU) -> precision, recall, F1, confusion matrix

**Q3. (Slide 8) Why 30 and 15 calls? Is it a minimum?**
- No statistical basis -> what fits our schedule (Meet 30 -> Teams 15; cut Teams first if short)
- Meet most: most reliable ground truth, center of retraining and diagnosis evaluation; Teams fewer: ground-truth path not yet confirmed
- Split by condition -> only a few calls each -> we report results as exploratory, pilot-scale

**Q4. (Slide 9) How did you limit Chrome to two cores?**
- Our own script `scripts/cpu_load.py`: psutil `cpu_affinity()` pins all `chrome.exe` to cores 0-1
- Fewer usable cores -> imitates a low-end laptop (total CPU looks low, 23% -> we also track per-core `call_core_pct`)
- Affinity is always restored on exit; one pilot run per condition

**Q5. Why hasn't anyone tried this? Why no real-time feedback?**
- We don't know; we only read product docs and web results, no literature survey
- Premise is partly wrong: vendors already give in-app real-time hints (Meet: CPU/network + actions; Teams: Call health, 15 s; Zoom: statistics window)
- vcaml paper: IP/UDP approach suits network operators at scale; evaluated offline; other devices, OSes, native clients, multi-party calls = future work
- Looks feasible (tick p95 36 ms, +252 MB, CPU ~1.3%), but measured on one laptop only
- Why vendors skip packet estimation = our inference (they have true values in-app); "they avoid the risk" = no evidence
- Frame: "We don't claim nobody tried. Closest work is offline. Vendors have internal data. We measure accuracy from outside, in real time."

**Q6. Vendors already do this. What is the significance?**
- Not a product -> a measurement and verification study: how accurately can quality and cause be known from outside, packets only? Bad result = still a result
- Strongest: error vs. ground truth in numbers (we found no published vendor accuracy)
- Network vs. device cause: Meet also shows CPU/network -> the difference is the evaluation, not the feature
- Recovery check: our "action" = removing the injected problem -> advice effect not verified
- Never say "no such feature in industry"

**Q7. Does it apply to other encrypted services?**
- Only video calls tested -> what may carry over is the method: header size/timing -> features -> model -> error vs. ground truth
- Other services need their own ground truth + retraining; vcaml features are tuned to video-frame patterns -> "a direction, not a result"

**Q8. Doesn't the monitor use more CPU?**
- Only reads packets, sends nothing -> cannot affect the network; but it does use CPU
- CPU ~1.3%; no change in call quality in one pilot call
- Memory is larger: model ~+250 MB, system memory ~+400 MB (0.4 GB)
- Acceptable on a modern 16 GB laptop; not yet measured with the dashboard open or on a low-end device (in our plan)

**Q9. Metric values differ by app. How do you judge quality? Why a ratio to an early-call baseline?**
- Paper: metric definitions are the same for all apps, ground truth always `webrtc-internals` -> but value distributions differ (median bitrate: Teams 1700 vs. Webex 500 kbps; resolution values: Meet 3, Teams 11, Webex 2)
- Our reason (docs/design/judge.md): first pilot model out of training range -> bitrate ~6x low, resolution accuracy 0% -> absolute thresholds misjudge -> bitrate / frameHeight = ratio to early healthy median (>=0.8 good, 0.5-0.8 fair, <0.5 poor)
- Don't claim "differs by device": the paper mentions device effects only for frame jitter (decoding delay in ground truth)
- Limits: baseline = model estimate, not ground truth -> cancels only a constant-ratio bias; bad start -> wrong baseline; fps / frame jitter still absolute and provisional; paper has no good/bad thresholds
