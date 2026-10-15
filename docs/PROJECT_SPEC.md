# Task: MCQM — Multi-layer Call Quality Monitor: 네트워크 vs 기기 원인 진단 + 실시간 추정 (CSE310 Final, vcaml 기반)

> **v6 (2026-10-14)**: 교수님 면담 결과 반영 — **데스크톱(Windows) 우선**, 12/2까지 데스크톱 MVP 구현·검증, **Android는 설계와 실현 가능성 분석까지만**(구현 없음), 측정 대상은 Windows의 **Google Meet·Zoom**, 최종 화면은 **웹 대시보드**(네이티브 앱 없음). v5(모바일 측정 타당성)는 폐기하지 않고 Android 설계의 실측 근거로 보관한다. 계획 근거는 `docs/PROGRESS.md`의 "방향 재설정 v6".
> v5 (10/13), v4 (10/12) 이력은 git log와 `docs/PROGRESS.md`에 있다. 메시지 계약은 `docs/SCHEMA.md`.

## 팀과 제약
- 2인 팀, 마감은 **2026-12-02 Final Demo**(기능 동결 **11/24**), 발표는 **약 12분**이다.
  - **Sungmin** (Windows): Python·ML 백엔드, 캡처, 실험, Android 설계 문서.
  - **팀원** (Mac): React 대시보드. **Python·ML 코드는 거의 다루지 못한다.**
  - 모든 단계에 "실행 방법과 확인 방법"을 한국어로 짧게 붙이고, 명령은 OS 중립(`uv run`, `npm --prefix`)으로 쓴다.
  - 설명은 한국어로 쓰고, 코드·명령어·기술 용어는 영어 그대로 둔다.
- 노트북: Windows 11, Core Ultra 5 125H, RAM 16GB (여유 메모리 적음), GPU 미사용.
- 측정 기기는 **이 노트북**(통화 수신 측). 통화 상대는 **Sungmin의 Galaxy S20**(Meet·Zoom 앱, 혼자 실험 가능한 구성). 안 되면 팀원 노트북과 서로 측정(나중). 상대 기기에서는 캡처하지 않는다.
- **netem(Linux)과 Odroid는 사용하지 않는다.**

## 핵심 메시지 (모든 설계 판단의 기준)
> "Windows 데스크톱에서, 앱 내부 정보 없이 **패킷 헤더와 OS 지표만으로** 영상통화 품질을 **얼마나 정확히** 실시간 추정하고, 저하의 원인이 **네트워크인지 기기(CPU)인지** 구분할 수 있는가."

**연구 질문 (v6)**
1. Meet·Zoom 수신 영상의 초당 품질(fps·bitrate·해상도)을 IP/UDP 헤더만으로 얼마나 정확히 추정하는가? (vcaml 모델이 Linux·에뮬레이션 학습인데 Windows 실환경에서도 통하는가)
2. 품질 저하의 원인을 **네트워크(손실·대역폭)와 기기(CPU)**로 얼마나 정확히 구분하는가? 패킷만 보면 CPU 병목은 보이지 않고(패킷은 정상, fps만 하락), OS 지표를 더하면 구분되는가? **[가설, W1 파일럿으로 확인]**
3. 모니터(tshark + 추론) 자신이 통화에 주는 부하는 얼마인가?

**측정 정확도와 검증**이 중심이다. 화면은 이 결과를 보여 주는 도구다.

## 기반과 추가 범위
기반은 `github.com/noise-lab/vcaml`(IMC'23)이다(fork `sungmin-c/vcaml` 브랜치 `mcqm`, `vcaml/` submodule, 원본에 LICENSE 없음 → 코드 복사 금지). vcaml은 pcap → LSTATS/TSTATS feature → Random Forest로 fps·bitrate·frame jitter·해상도를 추정하며 데스크톱 오프라인 배치다. 학습 데이터는 Linux Chrome + 에뮬레이션 조건이고, 논문도 in-lab → real-world 이전에서 Meet FPS MAE 12.41로 실패했다(Table 5). 그래서 **Windows 실환경 정확도는 직접 재야 한다.**

**우리가 추가하는 것 (우선순위 순):**
- **P0** 실시간 파이프라인(tshark → 1초 창 → RF) + 정답 대비 정확도 평가 (Meet)
- **P0** 원인 진단: `none | loss | bandwidth | device_cpu` + 근거 피처 + 신뢰도 (OS 지표 결합)
- **P1** 모니터 오버헤드 측정 (H1)
- **P1** Zoom 확장 (정답은 화면 기반 fps, 결과는 `validated:false` 기본)
- **P1** React 대시보드 (지표별 판정, 원인·근거 카드, CPU 게이지, 추정·정답 겹침 차트)
- **P2** Android 4계층 설계 문서 (구현 없음)
- **P3** What-if 슬라이더 UI (여유 시)

**범위에서 제외 (v6)**: 모바일 정확도 주장, Kakao, Flutter 오버레이 개발, 핫스팟 캡처, MOS/QoE 점수, 자동 복구, 고정 지연 진단.

## 절대 규칙
1. **확인하지 않은 것을 사실처럼 쓰지 않는다.** 확인하지 못했으면 "미확인", 가정은 `[가정]`.
2. 정답이 없는 결과에는 항상 `validated: false`와 "모델 추정값" 표시를 붙인다. Zoom은 정답 경로(화면 기반 fps)가 검증되기 전까지 `validated:false`.
3. What-if는 **trace 기반 에뮬레이션**이므로 송신 측 혼잡 제어 반응을 반영하지 않는다. UI와 README에 명시한다. (실측 손상이 주력이다.)
4. **내 노트북 자신의 트래픽만** 캡처한다. 다른 사람의 트래픽 캡처나 Wi-Fi 스니핑 코드는 만들지 않는다.
5. 마일스톤마다 테스트와 빌드를 실행하고 결과를 요약한 뒤 승인을 받고 넘어간다. 파일 삭제·덮어쓰기 전에는 알린다. 의존성·드라이버 설치는 이유와 되돌리는 방법을 함께 기록한다.
6. 원인 진단은 **추정**이다. UI에 `confidence`를 함께 표시하고 "확정 진단"처럼 쓰지 않는다. CPU 원인은 주입한 조건이 라벨이며, 실제 현장의 CPU 병목 일반화는 주장하지 않는다.

## 1. 아키텍처
```
[Chrome(Meet) / Zoom 데스크톱 클라이언트]   ← 상대: S20 (영상 송신)
        │ UDP (노트북 수신)
        ▼
tshark -i <Wi-Fi> -f udp -T fields (epoch, ip.dst, proto, udp.length[, rtp.ssrc, rtp.seq])
  → server/features.py   (vcaml FeatureExtractor, 1초 창)
  → estimator (vcaml RF: data/models/meet_*_cv1.pkl) → judge.py (지표별 판정)
  + sample_os (psutil 1 Hz: 전체 CPU%, 통화 프로세스 CPU%, 메모리%)
  → diagnosis.py v1: {none, loss, bandwidth, device_cpu}
  → FastAPI WebSocket ─→ React 대시보드 (같은 노트북 브라우저, 웹 중심)
```
- 백엔드는 `server/`에 두고 uv로 관리한다. 모든 추론은 노트북에서 한다. 대시보드는 SCHEMA를 구독하는 표시 전용 클라이언트다 (H4: 노트북 상주 서비스 + 입력 모듈 구조).
- 프론트엔드는 React + TypeScript(Vite), Tailwind, Chart.js. 로직은 `src/core/` 순수 함수.
- **정적 데모 빌드**: 대표 시나리오 결과를 JSON으로 미리 계산해 백엔드 없이 재생한다.
- **입력 모드**: `Live`(tshark 실시간), `Replay`(저장 pcap/CSV 재생, 데모 fallback), `What-if`(P3).
- 정식 계약은 `docs/SCHEMA.md`와 `docs/schema/sample.jsonl`. v1.2(지표별 `judgement`)와 device 필드 추가(`device{cpu_pct, proc_cpu_pct, mem_pct}`, cause `device_cpu`)는 팀원 확인 대기.

## 2. 손상·부하 주입 (Windows, 자기 기기)
| 조건 | 도구 | 비고 |
|---|---|---|
| 손실 | Clumsy `drop`, 필터 `udp and inbound` | 노트북 자신의 트래픽에는 동작함(10/13 실측) |
| 지연·지터 | Clumsy `lag` | 고정 지연은 수신 trace에 보이지 않아 진단 대상 제외 |
| **대역폭** | **clumsy2** (오픈소스 fork, 승인됨) | Clumsy `throttle`은 몰아 보내기일 뿐 속도 제한이 아님. 설치·동작 **미확인**, W3 직전 확인 |
| CPU 부하 | Python `multiprocessing` busy loop (50/80/100%) | 설치 없음 |
- 주입한 조건이 곧 라벨이다. 시스템 변경(드라이버)은 되돌리는 방법을 함께 기록한다.
- Clumsy/clumsy2는 관리자 권한과 WinDivert 드라이버가 필요하다.

## 3. 정답과 검증
1. **Meet 정답**: webrtc-internals dump(vcaml `WebRTCReader` 재사용) 또는 `getStats()` 1초 폴링. 자동 dump 기능은 없다(수동 다운로드, vcaml은 pyautogui로 버튼 클릭). 방식은 W1에서 정한다.
2. **Zoom 정답**: 데스크톱 Statistics 창은 내보내기 **미확인**. REST QoS API는 Business 이상 + Dashboard 권한이 필요하고 1분 단위인데 **학생 계정은 해당 안 될 가능성이 높다**(미확인). Zoom 웹 클라이언트는 WebRTC 미디어 경로를 거의 쓰지 않는다(2019–2020 자료, 현재 미확인). → **화면 기반 fps**: 프레임 번호가 찍힌 영상을 보내고, 수신 화면을 60 fps로 녹화해 번호 변화를 센다(W1 파일럿 P4).
3. **지표**: fps·bitrate MAE, ±2 fps 정확도, 해상도 정확도, 판정 Precision·Recall·F1·Confusion Matrix.
4. **원인 진단 평가**: 라벨 = 주입 조건. `none/loss/bandwidth/device_cpu`. 통화 단위로 dev/test 분리. 손실은 RTP 순번이 보여야 구분된다(IP/UDP만 재현율 0.03–0.18). **Zoom은 RTP 헤더 접근 미확인.**
5. **도메인 차이**: W1 MAE가 크면 W3–W4 수집분(Windows Meet)으로 재학습·보정하고, 이를 "Linux 에뮬레이션 → Windows 실환경 이전" 결과로 보고한다.
6. **H1 오버헤드**: Meet 3분 × {모니터 끔, 켬} × 3회. 모니터 프로세스 CPU%와 정답 fps·framesDropped 비교. 기준 [가정]: fps 차이 < 1, CPU < 10%.
7. 한계: 표본 수, 상대 기기 영상 변동, Linux→Windows 이전, 라벨이 인위적 부하라는 점.

## 4. What-if 손상 함수 (`impair.py`, P3 보조)
Bernoulli/Gilbert 손실, 토큰 버킷 대역폭(200 ms 초과 시 버림), 지연+지터(FIFO). seed 고정, 청크 적용이 전체 적용과 같음(테스트 있음).

## 5. 지표별 판정 (0–100 QoE 점수 대체)
- fps, bitrate, frame jitter, 해상도마다 **정상 / 주의 / 나쁨**. 전체 `verdict`는 하나라도 나쁨이면 failed.
- 기준값은 공개 자료에서 가져와 **출처를 코드 주석과 문서에 단다**. 후보: OpenTok network test의 해상도별 bitrate·손실 표, vcaml freeze 정의(`config.yaml`), Meet/Zoom 권장치. 네트워크 jitter 권장치를 frame jitter에 그대로 쓰지 않는다. 기준이 정해지기 전까지는 "미정".
- 테스트: 단조성, 경계값, 전체 판정 일관성.

## 6. 마일스톤
| 주 | 기간 | 내용 |
|---|---|---|
| **W1 파일럿** | 10/14–10/19 | 문서 v6. P1 Meet 1통화 실시간→정답 MAE. P2 CPU 부하 3단계에서 "패킷 정상, fps 하락" 확인. P3 H1 on/off. P4 Zoom 정답 경로 |
| W2 | 10/20–10/26 | `capture/tshark_live.py`, `judge.py`, FastAPI WS(Live·Replay), psutil 수집기 / 팀원: WS 클라이언트·배지·차트. (Midterm 1 10/21) |
| W3 | 10/27–11/2 | Meet ≈30통화 수집(조건표), clumsy2 확정 |
| W4 | 11/3–11/9 | Zoom ≈15통화, `diagnosis.py` v1(device_cpu) |
| W5 | 11/10–11/16 | 평가(MAE, confusion matrix, H1 표) |
| W6 | 11/17–11/23 | Android 4계층 설계 문서, README, **11/24 동결** (Midterm 2 11/25) |
| W7 | 11/24–12/1 | 리허설 2회, 녹화본, Replay 대체 시연 점검. **12/2 Demo** |

대체안: 실시간 tshark 불안정 → Replay. CPU 부하에도 fps 불변 → 부하 강화 후 "기기 원인 관측 안 됨"으로 보고. Zoom 정답 실패 → 추정값만 `validated:false`. clumsy2 불가 → 손실·CPU만.

## 7. Android 4계층 설계 (구현 없음, P2)
계층 L1 앱/QoE, L2 전송, L3 무선(Wi-Fi·셀룰러), L4 기기. 분류 N(일반) / S(특수 접근) / P(특권) / X(불가). 상세 표는 계획 문서 3-3절과 향후 `docs/ANDROID_DESIGN.md`. 요지:
- L1은 다른 앱 통계를 읽을 수 없다(X) → L2 추정이 대신한다.
- L4의 다른 앱 CPU는 읽을 수 없다 → `device_cpu`는 Android에서 발열 상태 등으로 대체해야 한다(한계).
- 조치는 안내형(Settings.Panel)만 가능. 자동 Wi-Fi↔셀룰러 전환은 일반 앱 불가.
- **팀 실측 근거(10/13, S20 Android 13)**: PCAPdroid VpnService 캡처·UDP 스트리밍, RSSI(`NetworkCapabilities` + `ACCESS_NETWORK_STATE`), `Settings.Panel`, `SYSTEM_ALERT_WINDOW` 오버레이. 공식 문서 원문을 확인하지 못한 항목은 `[미확인-원문]`으로 표기한다.

## 8. 발표 구성 (12분)
| 시간 | 내용 |
|---|---|
| 0–2분 | 문제: 암호화된 통화에서 품질 저하의 원인이 네트워크인지 기기인지 어떻게 아는가 |
| 2–4분 | 방법: vcaml 원리 + 우리가 추가한 것(실시간, OS 지표 결합, 원인 진단) |
| 4–9분 | **라이브 데모**: 정상 통화 → 손실/대역폭/CPU 부하 주입 → 대시보드에서 판정·원인·근거 변화 |
| 9–11분 | 결과: 정답 대비 정확도, 원인 진단 정확도, 오버헤드, Android 설계 요약 |
| 11–12분 | 한계와 향후 과제 |

라이브 데모가 실패하면 즉시 Replay와 녹화본으로 전환한다.

## 9. 테스트
- pytest: impair, features, judge(단조성·경계), diagnosis(조건별 규칙), SCHEMA 계약. Vitest: 프론트엔드 `core/`.

## 10. 산출물
`README.md`(한국어 + 영어 요약, 맨 위 "vcaml 대비 추가한 것" 3줄), `capture/ server/ dashboard/ scripts/ docs/ tests/ vcaml/`, `overlay/`는 보관(설계 근거), 데모 스크립트, Android 설계 문서, 최종 보고서 초안(한국어).
