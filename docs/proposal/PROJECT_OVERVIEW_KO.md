# MCQM — 프로젝트 개요 (다른 AI 전달용), 2026-10-25 기준

> 목적: 지금까지의 과정을 Proposal 발표 순서대로 한 파일에 정리한다.
> 근거: `docs/PROJECT_SPEC.md`(v7), `docs/PROGRESS.md`, `docs/PROJECT_LOG.md`, `docs/HANDOFF.md`, `docs/MEETING_1022.md`, `docs/design/*`, `docs/SCHEMA.md`.
> 표기: **[확인됨]** 실측·실행으로 확인 · **[가정]** 아직 확인 안 함 · **[계획]**. [가정]을 사실처럼 쓰지 않는다.

## 0. 기본 정보
- **MCQM = Multi-layer Call Quality Monitor.** CSE310 Final Project(SUNY Korea), 2인 팀.
- 핵심 질문: *"Windows 데스크톱에서 앱 내부 정보 없이 패킷 헤더와 OS 지표만으로 영상통화 품질을 얼마나 정확히 실시간 추정하고, 저하 원인이 네트워크인지 기기(CPU)인지 구분하며, 안내한 조치 뒤 품질이 회복됐는지 확인할 수 있는가?"*
- 팀: **Sungmin**(Windows) — Python·ML 백엔드, 캡처, 진단, 실험. **팀원**(Mac) — React 대시보드 + 미니 위젯. Python·ML은 다루지 않는다.
- 일정: Proposal 발표 2026-10-26(5–10분) · 기능 동결 **11/24** · **Final Demo 12/2**(약 12분) · 보고서 12/12 무렵 [가정].
- 장비: Windows 11 노트북(Core Ultra 5 125H, RAM 16GB, 여유 메모리 적음)이 수신 측이다. 통화 상대는 Sungmin의 Galaxy S20.

## 1. 솔로 프로젝트: vcaml 1분 요약
- **vcaml**(noise-lab, IMC 2023)은 WebRTC 영상 품질을 **복호화 없이** 추정한다. 1초 창마다 IP/UDP 헤더 정보(패킷 크기, 도착 간격)로 피처(LSTATS/TSTATS)를 만들고, **Random Forest**가 fps·bitrate·frame jitter·해상도(frameHeight)를 낸다.
- 입력 방식은 둘이다. `ip-udp-ml`(헤더만, 우리 주력)과 `rtp-ml`(RTP 헤더 추가). 대상 앱은 Meet·Teams·Webex, 정답은 Chrome `webrtc-internals`.
- 논문 fps MAE는 약 1.50이다. **우리 재현 [확인됨]:** Meet 1.334 / Teams 1.812 / Webex 1.328(평균 1.491), vcaml 테스트 50개 통과.
- 한계: 오프라인 배치(통화 후 처리), Linux Chrome + 에뮬레이션 조건으로 학습, 품질만 내고 원인은 없음, 사용자 화면 없음. 논문도 in-lab → real-world 이전에서 실패했다(Meet FPS MAE 12.41, Table 5).
- 솔로 repo는 읽기 전용이다. 팀 repo는 fork `sungmin-c/vcaml`(브랜치 `mcqm`)을 submodule로 쓴다. 원본에 LICENSE가 없어 코드를 복사하지 않는다.

## 2. 기존 산업의 솔루션과 한계 (2026-10-25 문서 조사만)
| | 통화 중, 사용자용 | IT 관리자용 |
|---|---|---|
| Google Meet | "Troubleshooting & help" 패널: CPU 부하, 네트워크 안정성, 조치 제안과 그 효과 피드백 | Meet Quality Tool(지터·손실·RTT·CPU, 30일 보관) |
| Microsoft Teams | Call health 패널(RTT·손실·bitrate 등, 15초마다 갱신) | Call Quality Dashboard(Good/Poor 분류), 진행 중 회의 Real-Time Analytics(Teams Premium이면 자동 수집) |
| Zoom | 통계 창(P4 파일럿에서 직접 사용: fps·해상도·지연·지터·손실, 내보내기 없음) | Zoom Dashboard(MOS 1–5, CPU 포함 경고) |
| Webex | 조사 안 함 | Control Hub + ThousandEyes(네트워크 경로, Webex 데스크톱 앱만) |

한계(우리 정리. "아무도 안 한다"가 **아니다**):
1. **앱 안에서만**: 각자 벤더 내부 데이터를 쓴다. 여러 앱에 공통으로 쓰는 모니터가 없다.
2. **앱마다 다르다**: 원시 수치를 주는 곳도, 힌트를 주는 곳도 있다. 깊은 화면은 관리자 권한이 필요하고 라이선스가 필요할 때도 있다.
3. **외부에서 정확도를 검증할 수 없다**: 조사한 문서에서는 원인 힌트가 얼마나 맞는지 공개된 수치를 찾지 못했다. 사용자가 조치한 뒤 회복됐는지 독립적으로 확인하지 않는다.
- → 연구 질문: 이것을 **앱 밖에서, 어느 앱에나** 할 수 있는가, **얼마나 정확히** 할 수 있는가?
- 정직하게 말할 것: Meet은 이미 사용자에게 CPU 부하와 조치 제안을 보여 준다. 제품을 직접 시험하지 않았다(문서 조사만). 출처는 `SCRIPT_ChatGPT.md`의 "출처" 절.

## 3. vcaml로 가능해지는 것
- 사용자 노트북에서, **앱 밖에서**, **벤더 협조 없이**, **복호화 없이**(자기 트래픽의 헤더만) 동작하는 모니터를 만들 수 있다.
- UDP 영상을 보내는 앱이면 초당 수치를 얻는다.
- 가볍다: 모델 4개 + 진단 1 tick p95는 in-lab에서 **36 ms** [확인됨], 실통화(배터리 상태)에서 126 ms [확인됨]. 둘 다 1초 예산 안이다.
- → 벤더 데이터에 기대지 않는 **앱 무관, 실시간** 모니터에 빠져 있던 조각이 이것이다.
- 대시보드·위젯 상태: repo에는 아직 없다(10/25 기준 `dashboard/` 폴더 없음). 팀원 진행 상황은 미확인 → "만드는 중, 파이프라인과 연결 전"이라고 말한다.

## 4. 우리 프로젝트: 앱 밖에서, 어느 앱에나, 정확도를 측정하며
vcaml은 *얼마나 좋은지*를 말한다. MCQM은 *왜*와 *회복됐는지*를 더한다. 우선순위:
- **P0** 실시간 파이프라인(tshark → 1초 창 → RF) + 정답 대비 정확도 + **재학습**(Meet)
- **P0** 원인 진단 `none | loss | bandwidth | device_cpu` + 근거 + 신뢰도. 패킷과 **OS 지표**를 결합한다.
- **P1** **조치 안내 + 회복 검증**. 안내만 하고 실행은 사용자가 한다. 자동 복구는 없다.
- **P1** React 대시보드 + **미니 위젯**(같은 대시보드를 Chrome Document Picture-in-Picture로 띄운 항상-위 창)
- **P1** Teams(Chrome 웹) · **P2** Zoom, 오버헤드 반복 측정, Android 4계층 설계 문서(구현 없음) · **P3** What-if 슬라이더
- 범위 밖: 모바일 정확도 주장, Kakao, Flutter 오버레이 개발, 핫스팟 캡처, 0–100 MOS 점수, 자동 복구, 고정 지연 진단, Teams·Zoom 데스크톱 앱 정답.

### 방향이 바뀐 과정
- **v5(10/13) 모바일 우선**: PCAPdroid 스트리밍(전달률 약 100%)과 S20 Flutter 오버레이는 동작했다. 그러나 **핫스팟을 거친 폰 트래픽에는 Clumsy가 적용되지 않았다**(WinDivert NETWORK 계층은 노트북 자신의 패킷만 본다). 폰 트래픽에 통제된 손상을 걸 수 없었다.
- **v6(10/14, 교수님 면담)**: 데스크톱(Windows) 우선. 12/2 = 데스크톱 MVP, Android는 설계만, 웹 대시보드로 가고 네이티브 앱은 없다. 모바일 작업은 보관했다(`overlay/`, 브랜치 `ml/overlay-spike`).
- **v7(10/22)**: 측정 순서 **Meet → Teams(웹) → Zoom**, 통화 30/15/15. 조치 + 회복 검증과 PiP 미니 위젯을 추가했다.

## 5. 현재 계획과 파일럿 결과
### 시스템
```
Meet/Teams(Chrome) 또는 Zoom 데스크톱  ← 상대: S20
 → tshark(헤더만, 내 노트북) → server/features.py(vcaml FeatureExtractor, 1초 창. 배치와 동일, rtol 1e-9)
 → RF 추정(W3 뒤 재학습 모델) → judge.py(지표별 good/fair/poor)
 + psutil 1 Hz(CPU%, 통화 프로세스 CPU, call_core_pct, 메모리%)
 → diagnosis.py v1 → 조치 문구 + 회복 판정
 → FastAPI WebSocket(ws://localhost:8000/ws, 초당 tick 1개) → React 대시보드 + PiP 위젯
```
- 모드: Live, Replay(데모 대체), What-if(P3). 계약은 `docs/SCHEMA.md` + `docs/schema/sample.jsonl`. v1.2(judgement, device, `device_cpu`)는 팀원 승인 대기.
- judge 기준 [가정]: fps ≥24 good / 15–24 fair / <15 poor. jitter <30 / 30–60 / ≥60 ms. bitrate·해상도는 통화 초반 기준선 대비 비율(≥0.8 / 0.5–0.8 / <0.5). 히스테리시스: 악화는 즉시, 회복은 2틱 뒤.
- 진단 v1 규칙 순서: 흐름 전환 시 기준선 재수집 → bandwidth → RTP 손실(seq_loss ≥ 1.5%) → 지터 → **call_core_pct ≥ 85%이면 device_cpu [가정]** → IP/UDP 손실 규칙 → none. `device=None`이면 device_cpu가 꺼지므로 "패킷만 vs 패킷+OS" 비교 실험은 스위치 하나다.
- `call_core_pct` = 통화 프로세스가 쓸 수 있는 코어(affinity)의 평균 사용률. Chrome을 2코어에 묶었을 때 전체 CPU는 23%로만 보였기 때문에 필요하다.
- 코드 상태 [확인됨]: tshark 캡처, judge, WS 서버, 진단 v1이 main에 병합됐다(PR #9). pytest 197 통과. 실통화 Live 경로는 아직 검증 전이다.

### 파일럿 (W1, 10/15, **각 통화 1건**, 방향 확인용)
| 파일럿 | 결과 | 의미 |
|---|---|---|
| P1 정확도(Meet, 196초) | fps MAE **9.09**(lab 1.33), bitrate 331 vs 1932 kbps(약 6배 과소), 해상도 정확도 0% | 캡처는 정상(패킷에서 직접 계산한 bitrate 2111 kbps ≈ 정답)이다. 모델이 학습 범위 밖이다(학습 중앙값 125 kbps, 높이 180–360 vs 우리 1.9 Mbps, 1280). 논문 12.41과 같은 양상 → **재학습** |
| P2 CPU(Chrome 2코어 고정) | 패킷·수신 fps 정상(27.7–29.7). 그러나 **freeze 36회**, 디코드 6.6 → 57 ms(약 9배), 송신 fps 16.5 → 3.5. `qualityLimitationReason`은 끝까지 `none` | **패킷만으로는 기기 문제가 안 보인다** → OS 지표 필요. 기기 정답은 freeze·디코드 시간·송신 fps로 정의. busy loop보다 코어 고정이 효과적 |
| P3 오버헤드(끔/켬 3회씩) | 모니터 **CPU 약 1.3%**, 통화 지표 차이 없음 | 모니터는 가볍다 |
| P4 Zoom | 서버 경유 UDP(약 1.9 Mbps). 통계 창에 fps는 있지만 내보내기 없음 | Zoom 정답은 근사값. Meet 모델은 Zoom에도 안 맞음 |
- 진단 합성 실험(in-lab trace에 손상을 소프트웨어로 삽입, v0.1): 대역폭 재현율 0.95–1.00. 손실은 RTP 순번이 있으면 0.56–0.94, IP/UDP만이면 0.03–0.18. 정상 오탐 1–4%. 고정 지연은 수신 측에서 보이지 않는다(97% "none").
- 찾은 문제: P2P 포트가 49152를 넘으면 tshark가 RTP를 해석하지 못했다 → `--enable-heuristic rtp_udp` 추가(검증은 S0-3).

### 일정
| 주 | 계획 |
|---|---|
| W2 10/20–26 | ✅ 코드 병합. 남은 것: W3 사전 점검 S0, Teams 파일럿(T9), 위젯 PiP 스파이크(T11, 팀원), 조치·회복 설계(T10), Proposal 발표 |
| W3 10/27–11/2 | Meet 약 30통화(N0 정상, L3/L10 손실, B1000/B300 대역폭, C2/C2L CPU), 재학습 시작 |
| W4 11/3–9 | Teams 약 15통화, 회복 판정 구현, 위젯에 조치·회복 표시 |
| W5 11/10–16 | Zoom 약 15통화, 평가 표 |
| W6 11/17–23 | Android 설계 문서, README, 정적 데모·녹화본. **11/24 동결** |
| W7 11/24–12/1 | 리허설 2회(Replay 전환 점검). **12/2 데모** |
- 통화 1건 = 380초: warm 0–150, baseline 150–210, **손상 210–300**, recovery 300–380. 주입한 조건이 라벨이고, 해제가 실험상의 "조치"다.
- 도구: Clumsy(손실), clumsy2(대역폭, 동작 미확인), `scripts/cpu_load.py --pin 2`(CPU).

## 6. 최종 데모: 내용과 지향점
- **라이브 데모**: 정상 통화 → 손실 또는 CPU 제한 주입 → 위젯에 **원인 + 신뢰도 + 조치** → 문제 해제 → **"Recovered"**. 실패하면 Replay + 녹화본.
- **보여 줄 결과**: 재학습 전후 fps·bitrate 오차, OS 지표 유무별 진단 정밀도·재현율과 confusion matrix, 회복 판정 지연과 "회복" 오판정률, 모니터 오버헤드, Android 4계층 설계 요약.
- **성공 기준**: 재학습이 Windows 격차를 줄인다(못 줄이면 이유를 음성 결과로 설명한다). OS 지표가 패킷만일 때보다 `device_cpu` 재현율을 분명히 올린다. 회복을 몇 초 안에, 오판정 적게 판정한다.
- 최종 발표(약 12분): 문제 2분 → 방법 2분 → **라이브 데모 5분** → 결과 2분 → 한계 1분.

## 규칙과 미확인 항목
- 규칙: 확인 안 된 것을 사실처럼 쓰지 않는다. 정답이 없으면 `validated: false`("모델 추정값"). 진단은 신뢰도가 붙은 추정이다. 내 노트북 트래픽만 캡처한다. 조치는 안내만 한다. 회복 평가는 현장 효과가 아니라 *판정의 속도·정확도*를 잰다.
- 미확인: Teams 웹 정답, PiP가 전체 화면 통화 위에 뜨는지, Clumsy가 버린 패킷이 tshark에 보이는지(S0-1, 가장 큰 위험), clumsy2, 재학습 정확도, 회복 N/T초(T10), SCHEMA v1.2 팀원 승인.
- 한계: 표본 수, 통화 상대 폰 1대, 인위적 손상, Linux → Windows 이전, 조치 = 주입 해제.

## 주요 파일
`docs/PROJECT_SPEC.md`(명세 v7) · `docs/PROGRESS.md`(결과, 결정 Q1–Q23) · `docs/PROJECT_LOG.md`(이력) · `docs/HANDOFF.md`(누가 무엇을) · `docs/design/{judge,diagnosis_v1,ws_protocol,w3_collection,schema_v1.2_proposal}.md` · `docs/SCHEMA.md` · `docs/COMMANDS.md` · `docs/proposal/PROPOSAL_DECK.md`
