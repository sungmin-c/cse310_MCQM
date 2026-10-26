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

## 예상 질문과 답변 (Q&A, 2026-10-25 기록)
근거는 `docs/PROGRESS.md`, `docs/PROJECT_SPEC.md`, `scripts/cpu_load.py`, vcaml 코드. 모르는 것은 "모른다"고 적었다.

**Q0. vcaml은 정확히 어떤 모델이고, 어떻게 payload 없이 품질을 아는가?**
- 클래스는 `vcaml.models.ip_udp_ml.IP_UDP_ML`이고 안에 sklearn Random Forest가 하나 들어 있다. 해상도(`frameHeight`)는 `RandomForestClassifier`, fps·bitrate·frame jitter는 `RandomForestRegressor`이며 하이퍼파라미터는 sklearn 기본값이다.
- 앱(Meet/Teams/Webex) × 지표(4개)마다 모델이 따로 있다(12개). 우리가 쓰는 파일은 `data/models/meet_*_cv1.pkl`(교차검증 fold 1).
- 입력은 패킷 **크기와 도착 시각**뿐이다(`ip_udp_ml.py`: `length`, `time`, `time_normed`). 1초 창마다 크기 통계(LSTATS)와 도착 간격 통계(TSTATS)를 만들어 모델에 넣는다. 정답은 Chrome `webrtc-internals` 값으로 학습했다.
- 이유: 프레임이 하나 만들어지면 비슷한 크기의 패킷 묶음이 연달아 나간다. 통계적 상관을 배운 것이라 학습하지 않은 환경에서는 틀린다(우리 파일럿 9.09, 논문 Table 5 12.41).

**Q1. (Slide 6) 36 ms와 95 percentile은 무슨 의미인가? 빠르다는 기준은 1초인가?**
- 36 ms = 1 tick의 처리 시간(패킷 push + feature + RF 4개 predict + 진단). p95 = 438 tick 중 95%가 36.2 ms 안에 끝남(최대 103 ms). in-lab Meet test 10통화 기준.
- 물리적 기준은 1초다. tick이 1초보다 오래 걸리면 지연이 쌓여 실시간이 깨진다. 목표 200 ms는 **우리가 정한 내부 예산**이다(tshark·WebSocket·UI 여유). 외부 표준이 아니다.
- 의미는 "1초 추정을 그 1초 안에 계산할 수 있다"까지다. 품질과는 무관하고, "문제를 실시간으로 탐지한다"는 뜻도 아니다(판정 지연 중앙값: 대역폭·지터 약 1.5초, 손실 1–19초).
- 한계: in-lab 약 30 pkt/s 기준(Teams 약 270 pkt/s는 미측정). 실통화 배터리 상태에서는 p95 126 ms였고 36 ms와 다른 **원인은 미확인**(CPU 속도 제한 추정). 라이브 파이프라인 전체를 실통화에서 검증한 적은 없다.

**Q2. (Slide 7) accuracy를 어떻게 재는가? 기준은?**
- QoE는 4개 지표(fps, bitrate, frame jitter, 해상도)로 정의하고, **정확도는 그 추정값이 정답(Chrome `webrtc-internals`)과 얼마나 다른지(오차)**로 말한다.
- 지표: fps·bitrate·frame jitter MAE, ±2 fps 이내 비율, 해상도 분류 정확도. 재학습 전후를 같은 test 통화로 비교하고 train/test는 **통화 단위**로 나눈다.
- 원인 진단은 별개다. 정답 = 주입한 조건(손실·대역폭·CPU), 지표 = Precision·Recall·F1·confusion matrix.
- frame jitter는 SPEC 평가 지표 줄에 빠져 있었으므로 추가한다(정답 필드 정의는 vcaml과 맞춰야 함).

**Q3. (Slide 8) 30·15·15통화의 이유와 기준은? 최소치인가?**
- **통계적 근거 없음.** 일정 안에서 가능한 계획이다(W3 Meet 30 → W4 Teams 15, 부족하면 Teams부터 축소).
- Meet이 가장 많은 이유: 정답이 가장 확실하고 재학습·진단 평가의 중심. Teams는 정답 확보가 아직 미확인이라 적음.
- 조건(정상·손실·대역폭·CPU)별로 나누면 조건당 몇 통화 안 된다. 충분하다고 주장하지 않고 "파일럿 규모의 탐색적 결과"로 한계 절에 적는다.

**Q4. (Slide 9) Chrome을 2코어로 제한할 때 무슨 툴을 썼나?**
- 별도 도구 없이 직접 만든 `scripts/cpu_load.py`. Python `psutil`의 `cpu_affinity()`로 모든 `chrome.exe`를 코어 0·1에만 묶는다(예: `--pin 2 --workers 4`).
- "CPU를 못 쓰게" 한 것이 아니라 **쓸 수 있는 코어 수를 줄여** 저사양 노트북을 흉내 낸 것이다. 그래서 전체 CPU는 23%로 낮게 보이고, affinity 코어 기준 `call_core_pct` 지표가 필요해졌다.
- 첫 버전은 종료 때 affinity를 복원하지 못했고 지금은 항상 전체 코어로 복원하도록 고쳤다. 조건당 1회뿐인 파일럿이다.

**Q5. 왜 다른 회사들은 이런 시도를 안 했나? 실시간 피드백은 왜 안 했나?**
- 모른다. 문헌·업계를 따로 조사하지 않았고 제품 문서와 웹 검색 결과만 봤다.
- **전제가 일부 틀렸다.** 벤더는 앱 안에서 실시간 안내를 이미 한다(Meet: CPU·네트워크 + 조치 제안, Teams Call health 15초 갱신, Zoom 통계 창).
- vcaml 논문은 IP/UDP 방식이 **네트워크 운영자**가 대규모로 쓰기 쉽다는 점을 근거로 든다. 평가는 오프라인(in-lab 54,696초 + 실제 15개 네트워크), 한계로 다른 기기·OS·네이티브 클라이언트·다자 통화를 향후 과제로 적었다. 실시간 배포 비용은 찾지 못했다.
- 기술적으로는 가능해 보인다(tick p95 36 ms, 모델 +252 MB, 모니터 CPU 약 1.3%). 단 이 노트북에서만 재었고 진짜 저사양 기기는 미측정.
- 벤더가 패킷 추정을 안 쓰는 이유는 **추론**이다: 앱 안에서 진짜 값을 얻으므로 추정이 오히려 부정확하다. "리스크 때문에 안 한다"는 **근거 없음**.
- 답변 틀: "누구도 안 했다고 주장하지 않는다. 우리가 찾은 가까운 연구는 오프라인 평가다. 벤더는 내부 데이터가 있다. 우리는 앱 밖에서, 실시간으로, 정확도를 측정한다."

**Q6. 벤더가 이미 하는데 이 프로젝트의 의의는?**
- 새 제품이 아니라 **측정과 검증 연구**다. 질문은 "앱 밖에서 패킷만으로 품질과 원인을 얼마나 정확히 알 수 있는가"이고, 결과가 나쁘면 그것이 결과다(SPEC §7).
- 의의 4가지: (1) 앱 밖에서 앱 상관없이 같은 방법으로 실시간 추정 — 사실이지만 "있으면 좋은" 수준. (2) 정답 대비 오차를 수치로 측정(벤더의 정확도 공개 수치는 문서 범위에서 못 찾음) — 가장 단단한 의의. (3) 네트워크/기기 원인 구분과 정확도 측정 — Meet도 CPU·네트워크를 보여 주므로 기능이 아니라 **평가**가 차이. (4) 회복 확인 — 단 우리 실험에서 조치는 "주입 해제"라 실제 조언 효과는 검증하지 못한다.
- "업계에 없는 기능"이라고 말하지 않는다.

**Q7. 다른 암호화 서비스에도 적용되는가?**
- 영상통화 외에는 시험하지 않았다. 옮겨 갈 수 있는 것은 대시보드가 아니라 **방법**(헤더의 크기·타이밍 → 특징 → 모델 → 정답과 비교해 오차 측정)이다.
- 다른 서비스는 정답 데이터를 따로 구해 재학습해야 하고 vcaml 특징은 영상 프레임 패턴에 맞춰져 있다. "방향이지 결과가 아니다"라고 답한다.

**Q8. 모니터가 CPU를 더 잡아먹는 것 아닌가?**
- 패킷을 읽기만 하고 아무것도 보내지 않으므로 네트워크에는 영향을 줄 수 없다. 하지만 CPU 자원은 쓴다.
- CPU는 약 1.3%였고, 통화 1건에서 통화 품질 변화는 보이지 않았다.
- 더 큰 비용은 메모리다. 모델이 약 250 MB를 쓰고, 시스템 메모리는 약 400 MB(0.4 GB) 늘었다.
- 요즘 16 GB 노트북에서는 감당할 만하다고 본다. 단 대시보드를 켠 상태와 저사양 기기에서는 아직 재지 않았고, 이는 계획에 들어 있다.

**Q9. 앱마다 지표 값이 다른데 판정 기준은 어떻게 하나? 왜 통화 초반 기준선 대비 비율인가?**
- 지표 4개의 **정의**는 논문에서 Meet·Teams·Webex 모두 같고 정답도 모두 Chrome `webrtc-internals`다. 다른 것은 **값의 분포**다: 같은 네트워크 조건에서 bitrate 중앙값이 Teams 1700 kbps, Webex 500 kbps이고, 해상도 값은 Meet 3종(180/270/360), Teams 11종(90–720), Webex 2종(180/360)이다(논문 §4.2, §5.1.5).
- 우리 judge가 bitrate·frameHeight를 통화 초반 정상 구간(`base_len`초) 대비 비율(≥0.8 good, 0.5–0.8 fair, <0.5 poor)로 판정하는 **기록된 이유**는, 첫 파일럿에서 모델이 학습 범위 밖이라 bitrate를 약 6배 과소 추정하고 해상도 정확도가 0%였기 때문이다(`docs/design/judge.md`). 앱별 분포 차이는 논문이 뒷받침하는 추가 근거다.
- "기기마다 다르다"는 일반 이유로 말하지 않는다. 논문이 기기 영향을 직접 언급하는 것은 frame jitter 하나다(정답이 디코딩 지연을 포함, §5.1.4).
- 한계: 기준선은 정답이 아니라 **모델 추정값**의 초반 중앙값이라 모델의 일정 비율 편향만 상쇄한다. 통화가 나쁜 상태로 시작하면 기준선이 틀린다. fps와 frame jitter는 아직 절대 임계값이고 임계값은 임시값이다(표준 사용 vs 수집 데이터 분위수 미정). 논문에는 좋음/나쁨 임계값이 없다.

---

## Expected Questions and Answers (English translation of the Korean Q&A above, 2026-10-25)
Sources: `docs/PROGRESS.md`, `docs/PROJECT_SPEC.md`, `scripts/cpu_load.py`, the vcaml code. Where we do not know, we say "we don't know."

**Q0. Exactly what model is vcaml, and how does it know quality without the payload?**
- The class is `vcaml.models.ip_udp_ml.IP_UDP_ML`, and it wraps a scikit-learn Random Forest. Resolution (`frameHeight`) uses a `RandomForestClassifier`; fps, bitrate, and frame jitter use a `RandomForestRegressor`. Hyperparameters are the sklearn defaults.
- There is a separate model for each app (Meet/Teams/Webex) × metric (4), so 12 in total. We use `data/models/meet_*_cv1.pkl` (cross-validation fold 1).
- The only inputs are packet **size and arrival time** (`ip_udp_ml.py`: `length`, `time`, `time_normed`). For each one-second window it builds size statistics (LSTATS) and inter-arrival statistics (TSTATS) and feeds them to the model. It was trained with Chrome `webrtc-internals` values as ground truth.
- Why it works: when one video frame is produced, a burst of similarly sized packets follows. The model learns that statistical correlation, so it is wrong in environments it was not trained on (our pilot: 9.09; paper Table 5: 12.41).

**Q1. (Slide 6) What do 36 ms and the 95th percentile mean? Is the standard for "fast" one second?**
- 36 ms is the processing time of one tick (packet push + features + 4 RF predictions + diagnosis). p95 means 95% of 438 ticks finished within 36.2 ms (maximum 103 ms). This is from 10 in-lab Meet test calls.
- The physical limit is one second: if a tick takes longer, delay accumulates and real time breaks. The 200 ms target is **our own internal budget** (headroom for tshark, WebSocket, and UI), not an external standard.
- It only means "we can compute a one-second estimate within that second." It says nothing about quality, and it does not mean problems are detected in real time (median decision delay: about 1.5 s for bandwidth and jitter, 1–19 s for loss).
- Limits: in-lab traffic was about 30 packets/s (Teams, about 270 packets/s, is not measured). On a real call on battery, p95 was 126 ms, and the **cause of the difference from 36 ms is unconfirmed** (we suspect CPU throttling). We have never verified the full live pipeline on a real call.

**Q2. (Slide 7) How do you measure accuracy? What is the criterion?**
- We define QoE with four metrics (fps, bitrate, frame jitter, resolution), and we define **accuracy as how far the estimate is from the ground truth (Chrome `webrtc-internals`), that is, the error**.
- Metrics: MAE for fps, bitrate, and frame jitter; the share within ±2 fps; and classification accuracy for resolution. We compare before and after retraining on the same test calls, and we split train/test **by call**.
- Cause diagnosis is separate. Ground truth is the injected condition (loss, bandwidth, CPU); metrics are precision, recall, F1, and a confusion matrix.
- Frame jitter was missing from the SPEC evaluation line, so we add it (its ground-truth field must be defined the same way as in vcaml).

**Q3. (Slide 8) Why 30, 15, and 15 calls? What is the basis? Is it a minimum?**
- **There is no statistical basis.** It is simply the plan that fits our schedule (W3 Meet 30 → W4 Teams 15; if time is short, we cut Teams first).
- Meet gets the most because its ground truth is the most reliable and it is the center of the retraining and diagnosis evaluation. Teams gets fewer because we have not yet confirmed we can get its ground truth.
- Split by condition (normal, loss, bandwidth, CPU), that is only a few calls per condition. We do not claim it is enough; we state the results as "exploratory, pilot-scale" in the limitations.

**Q4. (Slide 9) What tool did you use to limit Chrome to two cores?**
- No outside tool. We wrote `scripts/cpu_load.py`, which uses Python `psutil`'s `cpu_affinity()` to pin all `chrome.exe` processes to cores 0 and 1 (for example `--pin 2 --workers 4`).
- We did not stop Chrome from using the CPU; we **reduced the number of usable cores** to imitate a low-end laptop. That is why total CPU looks low (23%), and why we needed a per-core metric, `call_core_pct`, over the pinned cores.
- The first version did not restore affinity on exit; it now always restores all cores. This is a single-run pilot per condition.

**Q5. Why haven't other companies tried this? Why no real-time feedback?**
- We don't know. We did not survey the literature or industry separately; we only looked at product documentation and web search results.
- **Part of the premise is wrong.** Vendors already give real-time guidance inside the app (Meet: CPU and network plus suggested actions; Teams Call health refreshing every 15 seconds; Zoom statistics window).
- The vcaml paper argues that the IP/UDP approach is easy for **network operators** to use at scale. Its evaluation is offline (54,696 seconds in the lab plus 15 real-world networks), and it lists other devices, operating systems, native clients, and multi-party calls as future work. We did not find the cost of real-time deployment.
- Technically it looks feasible (tick p95 36 ms, model +252 MB, monitor CPU about 1.3%), but we measured only on this laptop and not on a truly low-end device.
- Why vendors do not use packet-based estimation is our **inference**: inside the app they get the true values, so an estimate would only be less accurate. "They don't do it because of risk" has **no evidence**.
- Answer frame: "We don't claim nobody has tried it. The closest work we found evaluates offline. Vendors have internal data. We measure accuracy from outside the app, in real time."

**Q6. Vendors already do this. What is the significance of this project?**
- It is not a new product; it is a **measurement and verification study**. The question is "how accurately can quality and cause be known from outside the app, using packets only," and if the result is poor, that is the result (SPEC §7).
- Four contributions: (1) a real-time estimate from outside the app, the same method for any app — true, but only "nice to have." (2) Error against ground truth, measured in numbers (we found no published vendor accuracy numbers in the documentation) — the strongest contribution. (3) Separating network from device causes and measuring its accuracy — Meet also shows CPU and network, so the difference is not the feature but the **evaluation**. (4) Recovery checking — but in our experiments the action is "remove the injected problem," so we cannot verify the real effect of advice.
- We do not say "industry has no such feature."

**Q7. Does it apply to other encrypted services?**
- We have tested only video calls. What can carry over is not the dashboard but the **method** (size and timing from headers → features → model → compare with ground truth to measure error).
- Another service needs its own ground-truth data and retraining, and vcaml's features are tuned to video-frame patterns. Our answer is: "It is a direction, not a result."

**Q8. Doesn't the monitor eat more CPU?**
- It only reads packets and sends nothing, so it cannot affect the network. In terms of CPU, yes, it does use resources.
- CPU use was about 1.3%, and we saw no change in call quality in one pilot call.
- Memory is the larger cost: the model adds about 250 MB, and system memory rose by about 400 MB (0.4 GB).
- On a modern 16 GB laptop, we think that is acceptable for users. But we have not measured it with the dashboard open or on a low-end device, and that is part of our plan.

**Q9. Metric values differ by app. How do you judge quality, and why a ratio to an early-call baseline?**
- The **definitions** of the four metrics are the same for Meet, Teams, and Webex in the paper, and the ground truth is always Chrome `webrtc-internals`. What differs is the **distribution of values**: under the same network conditions, median bitrate is 1700 kbps for Teams and 500 kbps for Webex, and resolution takes 3 values for Meet (180/270/360), 11 for Teams (90–720), and 2 for Webex (180/360) (paper §4.2, §5.1.5).
- The **documented reason** our judge scores bitrate and frameHeight as a ratio to the early, healthy part of the call (`base_len` seconds; ≥0.8 good, 0.5–0.8 fair, <0.5 poor) is that in the first pilot the model was outside its training range: bitrate was underestimated about 6×, and resolution accuracy was 0% (`docs/design/judge.md`). The per-app distribution differences in the paper are supporting evidence.
- We do not say "it differs by device" as a general reason. The paper mentions device effects directly only for frame jitter (the ground truth includes decoding delay, §5.1.4).
- Limits: the baseline is the early median of the **model's estimate**, not ground truth, so it only cancels a constant-ratio bias. If a call starts in a bad state, the baseline is wrong. fps and frame jitter still use absolute thresholds, and those are provisional (standard vs. quantiles of our data is undecided). The paper has no good/bad thresholds.
