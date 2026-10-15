# PROGRESS — MCQM
> 마일스톤마다 완료/미완료/검증 결과를 갱신한다. 상태: ⬜ 예정 · 🟡 진행 · ✅ 완료 · ⏸ 보류 · ❌ 실패
> ☎ = 팀원 iPhone 통화 세션 필요. 원자료는 `data/m0/` 등 `data/` 아래 (git 제외)

## 결정 사항 / 대기
| # | 질문 | 답 (10/12) | 상태 |
|---|---|---|---|
| Q1 | Midterm 1(10/21)·2(11/25)의 성격 | 시험. 프로젝트 산출물과 무관 → 시험 주간은 작업량만 줄임 | ✅ |
| Q2 | vcaml public fork | 승인. `sungmin-c/vcaml` 생성, `mcqm` 브랜치 push, submodule URL 교체 완료 | ✅ |
| Q3 | 팀원 GitHub 계정명, `main` 보호 | 계정명은 추후 전달. 그때까지 collaborator·브랜치 보호 보류 | ⏳ |
| Q4 | ☎ 세션 | 다음 주 중 (날짜 미정). M0 #3–9는 그때 실행. Kakao·Zoom 계정 준비 여부는 미확인 | ⏳ |
| Q5 | Flutter 앱(APK) | **P0 확정, 담당 Sungmin.** 통화 앱 위 오버레이 버블. 추론은 노트북. 상세는 PROJECT_SPEC §1.4 | ✅ |
| Q6 | `weak_wifi` 판정 근거 | 오버레이 앱이 RSSI를 `device` 메시지로 송신(SCHEMA v1.1 초안). **v5: `weak_wifi`는 정량 평가에서 제외, 정성 확인만** | ✅ |
| Q7 | 일정 | 발표 12/2, 동결 11/24. M2 11/6, M3 11/13, M4 11/20. M0은 10/19(폰 불필요)·10/23(통화) 분할 | ✅ |
| Q8 | SCHEMA v1.1 | 초안 작성 완료. **팀원 확인 대기** → M1(10/26)까지 확정 | ⏳ |
| Q9 | 진단 실험의 `delay_jitter` 라벨 | **결정(10/13, v5)**: 고정 지연은 진단 대상이 아님. 진단 정량 평가는 `loss`·`bandwidth`·`none`만. 지터는 합성 결과 보조 보고 | ✅ |
| Q10 | 라이브 손상 주입 방법 | **결정(10/13, v5): Plan E** — 노트북 브라우저가 Meet 통화 상대, 노트북 송신에 Clumsy(손실·대역폭). 핫스팟 경유 폰 트래픽엔 Clumsy/WinDivert 불가(실측). 핫스팟은 캡처 기준선용. 미검증: 가상 카메라 구성, Clumsy의 Meet 송신 효과 | ✅(검증 대기) |
| Q10-B | gnirehtet 시험 (10/13) | **폐기(v5)**. USB 연결이 수 초마다 끊겼고 PCAPdroid와 VPN 슬롯 충돌 가능성. 폰의 앱은 설치된 채이며 필요 없으면 `adb uninstall com.genymobile.gnirehtet` | ❌ 폐기 |
| Q11 | 방향 재설정 (10/13) | 비판적 분석 후 승인: **방향 1(모바일 측정 타당성 검증) + 방향 3 축소(손실·대역폭 원인)**. 방향 2(화면 기반 정답)는 **하루 파일럿**. 0–100 QoE 점수는 **지표별 판정**으로 대체(SCHEMA v1.2 초안). 라이브 데모는 Meet·Kakao 둘 다. 대시보드=팀원(주 3시간, 최소 범위), 버블 UI=Sungmin. Zoom 제외. 루팅 기기 없음 | ✅ |
| Q12 | SCHEMA v1.2 (지표별 판정) | 초안 작성. **팀원 확인 대기** (v1.1과 함께 M1 10/26까지 확정) | ⏳ |
| Q13 | 방향 재설정 v6 (10/14) | 교수님 면담: **데스크톱(Windows) 우선**, 12/2 = 데스크톱 MVP 구현·검증, Android는 설계·실현 가능성 분석까지(구현 없음), 대상 Meet·Zoom. v5 모바일 작업은 설계 근거로 보관. 계획 승인됨 | ✅ |
| Q14 | 통화 상대 기기 | **S20 단독**(Meet·Zoom 앱, 거치대 고정 [가정]). 안 되면 팀원 노트북과 서로 측정(나중) | ✅ |
| Q15 | Zoom 정답 | 학생 계정(요금제 미확인, QoS API는 Business 이상 필요). **화면 기반 fps**로 간다. 파일럿 P4에서 가능 여부 확인 | ✅(검증 대기) |
| Q16 | 대역폭 제한 도구 | **clumsy2 설치 승인**. 설치는 W3 직전, 되돌리는 방법 함께 기록. 동작 미확인 | ✅(설치 대기) |
| Q17 | 브랜치 정리 | `ml/m2-core`(PR #1) merge, `ml/overlay-spike`는 브랜치만 보존(PR 없음). 실행 직전 PR 상태 확인 | ⏳ 실행 대기 |
| Q18 | H4 / 팀원 범위 / 웹 중심 | H4 = 노트북 상주 서비스 + 입력 모듈로 확정. 대시보드 필수 = 원인·근거·CPU 카드(What-if 슬라이더는 선택), 팀원 동의함. **최종 화면은 웹 대시보드, 네이티브 앱 없음** | ✅ |

## 방향 재설정 v6 (10/14)
- 근거: 교수님 면담 결과 + 4개 조사(R1 vcaml 논문, R2 데스크톱 정답·손상 도구, R3 Android 접근성, R4 선행 연구). 요지는 `docs/PROJECT_SPEC.md` v6.
- 핵심 변화: 모바일 정확도 → **데스크톱에서 네트워크 vs 기기(CPU) 원인 진단 + 실시간 추정 + 모니터 오버헤드**.
- 보관(개발 중단): `capture/pcapdroid_rx.py`, `overlay/`(브랜치 `ml/overlay-spike`), `data/m0/udp_run*`. 폐기: 핫스팟·Plan E·gnirehtet·scrcpy·Kakao 데모.
- 알려진 위험: vcaml 모델이 Linux·에뮬레이션 학습이라 Windows 실환경 이전 오차가 클 수 있다(논문 Meet MAE 12.41, Table 5) → W1 P1에서 측정, 크면 재학습.

## 일정 (발표 12/2, 동결 11/24) — v6
| 주 | 기간 | 외부 일정 | 마감 | 나 — Python·실험 | 팀원 — Web | 상태 |
|---|---|---|---|---|---|---|
| **W1 파일럿** | 10/14–10/19 | | | 문서 v6. **P1** Meet 1통화 tshark 실시간 → 기존 모델 → 정답(webrtc dump) MAE. **P2** CPU 부하 3단계: "패킷 정상, fps 하락" 확인. **P3** H1 모니터 on/off. **P4** Zoom 정답(화면 녹화 fps, Statistics 창 내보내기 여부) | SCHEMA v1.2 + device 리뷰, `dashboard/` scaffold | 🟡 P1·P2·P3 완료(아래 "W1 파일럿 결과"), P4 대기 |
| W2 | 10/20–10/26 | **Midterm 1 (10/21)** | | `capture/tshark_live.py`, `judge.py`, FastAPI WS(Live·Replay), psutil 수집기 | WS 클라이언트, `parseMessage`+Vitest, 판정 배지, 차트 | ⬜ |
| W3 | 10/27–11/2 | | | Meet ≈30통화 수집(조건표), clumsy2 설치·확정 | 추정·정답 겹침 차트 | ⬜ |
| W4 | 11/3–11/9 | | | Zoom ≈15통화, `diagnosis.py` v1(`device_cpu`) | 원인·근거 카드, CPU 게이지 | ⬜ |
| W5 | 11/10–11/16 | | | 평가: MAE, confusion matrix, H1 표 | 결과 화면 | ⬜ |
| W6 | 11/17–11/23 | | **Freeze 11/24** | Android 4계층 설계 문서, README, 정적 데모·녹화본 | 다듬기, 접근성 | ⬜ |
| W7 | 11/24–12/1 | **Midterm 2 (11/25)** | **Final Demo 12/2** | 리허설 2회(Replay 전환 점검), 발표 | 리허설, 발표 | ⬜ |
| W8 | 12/3–12/12 | 종료 12/12 | | 최종 보고서 초안(한국어, [가정] 12/12까지) | | ⬜ |

일정 리스크: 통화 30–45건은 S20 단독이라 시간이 직접 든다(약 2.5–4시간 + 설정). W3–W4에 몰리므로 W2에서 자동화 스크립트를 먼저 만든다. 동결 다음 날이 Midterm 2이므로 M5 작업은 W6 안에 끝낸다.

v5 모바일 일정(E1 충실도, E2 정확도, E3 진단, Flutter 오버레이 마일스톤)은 git 이력(커밋 4bfda7b)에 있다.

## W1 파일럿 결과 (10/15) — P1·P2·P3 완료, P4 대기
도구: `scripts/pilot_live.py`(tshark 실시간 → 모델 → CSV, psutil 1 Hz, 정답 비교), `scripts/cpu_load.py`(busy loop + `--pin N` Chrome 코어 제한). 데이터는 `data/pilot/`(git 제외). 환경: Windows 노트북 Wi-Fi 수신, 상대 S20 Meet 앱(P2P 직접 연결), 노트북 Chrome.

**P1 — Meet 실시간 추정 vs webrtc-internals 정답 (196초)**
| 지표 | 정답 | 추정 | 오차 |
|---|---|---|---|
| fps | 29.4 | 20.4 | **MAE 9.09** (vcaml 재현 1.33) |
| bitrate | 1932 kbps | 331 kbps | 약 6배 과소 |
| frameHeight | 1280 | 270 | 정확도 0% |
- 시간 정렬 문제 아님(±3초 이동해도 MAE 불변). 패킷에서 직접 계산한 수신 bitrate는 2111 kbps로 정답과 비슷 → **캡처는 정상, 모델이 학습 범위를 벗어남**. in-lab Meet 40통화 표본: bitrate 중앙값 125·최대 566 kbps, 높이 180/270/360뿐, 우리 통화는 1.9 Mbps·1280·30 fps.
- 결론: 논문의 in-lab → real-world 이전 실패(MAE 12.41)와 같은 양상. **W3 수집 데이터로 재학습이 필요하다** (통화 단위 분리). 이 결과 자체를 발표 소재로 쓴다.
- 정답 파서 주의: Meet는 통화 중 PeerConnection을 갈아탄다(예: 540p 800 kbps → 720p/1280 2 Mbps). vcaml `WebRTCReader`는 첫 PC만 읽어 fps 0이 나온다 → `pilot_live.py compare`가 캡처 구간에 fps>0이 가장 많은 PC를 고른다. **수집 단계에서도 같은 처리 필요.**
- 모니터 오버헤드(P3 예비): tshark+python CPU 평균 1.4%, 최대 2.5%. tick 추론 약 110 ms(전체 CPU 부하 상태에서 측정, 벤치 36 ms와 다름 [미확인 원인]).

**P2 — CPU 부하에서 "패킷 정상, 품질 하락"이 보이는가**
- P2-1 (busy loop 18프로세스, 배터리 → 충전기 연결): 총 CPU 89%까지 올라도 수신 fps 28.6–29.9 유지, 드롭·freeze 0. **디코드 시간 1.5 → 12.5 ms(약 8배)**로 신호는 있었다(소프트웨어 디코더, `powerEfficientDecoder=false`).
- P2-2 (Chrome을 2코어로 제한, **배터리 상태**): 제한 직후 45초간 디코드 시간 6.6 → 최대 57 ms, **freeze 36회**, 송신 fps 16.5 → 3.5, 패킷 수·bitrate는 정상. 이후 Chrome이 적응해 안정. 수신 fps(`framesReceived/s`)는 끝까지 27.7–29.7.
- 결론: (1) vcaml 라벨인 수신 fps는 기기 병목을 못 본다 → **device_cpu 정답은 freeze·디코드 시간·송신 fps로 정의**한다. (2) 부하는 busy loop보다 **코어 제한이 효과적** → W3 조건표에 사용. (3) `qualityLimitationReason`은 송신 fps가 3.5로 떨어져도 끝까지 `none` → **기기 원인의 정답으로 쓸 수 없다.**
- 한계: 각 조건 1회, 단계 안에서 시간에 따라 변함(적응). P2-2의 "부하 0%" 단계도 이미 2코어 제한 상태. 통계적 주장은 W3 반복 수집 뒤에 한다.
- 사고 기록: `cpu_load.py --pin` 첫 버전이 종료 시 Chrome affinity를 복원하지 못했다(묶인 뒤 뜬 자식 프로세스가 2코어를 물려받음). 수동으로 전체 코어 복원 후 확인, 스크립트는 항상 전체 코어로 복원하도록 수정. 되돌리기: Chrome 완전 종료 후 재실행.

**P3 — 모니터 on/off 오버헤드 (H1), Meet 1통화, 배터리 상태**
- 방법: `scripts/overhead_ab.py`가 한 통화에서 모니터(tshark + 모델 + psutil)를 끔/켬 50초씩 3번 번갈아 실행(앞 150초는 연결 전환 대기, 제외). 통화 쪽은 webrtc-internals dump로 단계별 비교.
| 지표 (단계 평균, 각 3회) | 끔 | 켬 |
|---|---|---|
| 모니터 CPU(tshark+python) | — | **1.27%** (±0.31) |
| Chrome CPU / 전체 CPU | 9.2% / 22.7% | 8.9% / 23.7% |
| 수신 fps / 디코드 fps | 28.16 / 29.78 | 28.20 / 29.79 |
| 디코드 시간 | 5.78 ms | 5.70 ms |
| freeze / 드롭 | 0.05 / 0 | 0 / 0 |
| 송신 fps | 29.16 | 28.76 |
- 결론: **H1은 데스크톱에서 기각** — 모니터 CPU 약 1.3%, 통화 지표 차이는 단계 간 변동 안. 기준(fps 차이 < 1, CPU < 10%) 통과. 모델 1회 추론 p50 81 ms·p95 126 ms(배터리 상태, 벤치 36 ms보다 느림 [추정: CPU 속도 제한]).
- 한계: 통화 1건, 각 3회, 배터리 상태. W5에서 반복해 발표용 표로 만든다.

## Bootstrap (10/12)
| 항목 | 결과 | 상태 |
|---|---|---|
| vcaml submodule | `vcaml/` = upstream `8466954`, 로컬 브랜치 `mcqm`에 2줄 변경(미커밋). fork 생성 후 URL 교체 (Q2) | 🟡 |
| 데이터 junction | `data/in_lab_data`(900 폴더), `data/real_world_data`(15) → 솔로 자료. 복사 0 | ✅ |
| Python 환경 | `uv sync` 성공. numpy 2.4.6 / pandas 2.3.3 / scikit-learn 1.8.0 / mlflow 3.13.0 (솔로와 동일) | ✅ |
| `data_root` 해석 | `…\cse310_MCQM\data`, MLflow `sqlite:///data\mlruns.db` (팀 전용) | ✅ |
| SCHEMA v1 초안 + 계약 테스트 | `docs/SCHEMA.md`, `docs/schema/sample.jsonl`, `uv run pytest` → 3 passed | ✅ |
| 더미 스트림 | `uv run server/dummy_stream.py` → 1.01초 간격 수신 확인 (프로젝트와 격리 실행) | ✅ |
| 솔로 자료 무변경 | `mlruns.db` SHA256 `4a8ae33d…dfd` 전후 동일, `git status` 동일 | ✅ |

## M0 — 검증 스파이크 (마감: 폰 불필요 항목 10/19, ☎ 항목 10/23, 오버레이 권한 10/18)
| # | 항목 | 성공 기준 | 결과 | 상태 |
|---|---|---|---|---|
| a | Android 13 Flutter 오버레이 (10/18) | debug APK로 S20에서 Kakao·Meet 통화 화면 위에 버블이 10분 동안 유지된다. **오버레이 패키지명·버전을 pub.dev와 `pubspec.lock`으로 실제 확인해 기록**한다. `SYSTEM_ALERT_WINDOW` 권한 요청 흐름을 확인한다. Wi-Fi RSSI를 읽을 수 있고 필요한 권한을 기록한다. Wi-Fi 패널·인터넷 연결 패널이 열린다. 노트북 WS 연결 경로(LAN 또는 `adb reverse`)를 정한다 | **10/13 스파이크 (`overlay/`, 브랜치 `ml/overlay-spike`)**: Flutter 3.41.4, 패키지 **`flutter_overlay_window` 1.0.0**(pub.dev, iheb.tech, MIT). 다른 앱 위 버블 ✅, 권한 요청 흐름 ✅(`SYSTEM_ALERT_WINDOW`, 알림 권한), 더미 스트림 WS 수신 ✅(경로: **무선 adb + `adb reverse tcp:8000`** → 방화벽 변경 불필요), Wi-Fi·인터넷 설정 패널 ✅(`Settings.Panel`), [조치] 버튼 → 패널 ✅, 크기 작게/크게·닫기 버튼 ✅, **RSSI ✅**: `NetworkCapabilities.getSignalStrength()` + `ACCESS_NETWORK_STATE`(위치 권한 불필요. `WifiManager.connectionInfo`는 Android 13에서 위치 권한 없이 가려져 null). 발견한 플러그인 버그: ① 시작 위치를 안 주면 화면 위로 사라짐 ② 이미 떠 있을 때 다시 show하면 서비스가 멈춤 ③ 드래그 경계 계산 오류 → `overlay/third_party/flutter_overlay_window`(MIT 수정본, `MCQM_PATCH.md`)에서 ③ 수정, ①② 앱 쪽 우회. 남은 것: **Kakao·Meet 통화 위 10분 유지(☎)**, 버블 UI/UX 다듬기(→ 팀원 인계, 아래) | 🟡 |
| b | `app_filter`로 오버레이 트래픽 제외 ☎ | Kakao 통화 중 `app_filter`=Kakao 패키지, 오버레이 WS 연결 상태로 2분 캡처한다. pcap에서 노트북 WS 포트(8000) 패킷 = **0개**이고, Kakao 패킷 수는 필터가 없을 때와 비슷하다 | | ⬜ |
| 0 | 도구 설치 (Wireshark+Npcap, scrcpy, PCAPdroid, Clumsy) | 버전 출력, `adb devices`에 S20 | 10/13 winget 설치: tshark 4.6.9 ✅, Npcap 1.89 실행 중 ✅ (`tshark -D`에 Wi-Fi 등 인터페이스 표시), scrcpy 4.1 ✅, Clumsy 0.3 ✅. 남은 것: PCAPdroid(폰), `adb devices`에 S20 (폰 연결 필요). 경로·되돌리기는 `CLAUDE.local.md` | 🟡 |
| 1 | vcaml 팀 repo 재현 | `pytest vcaml/tests` 50 passed + FPS×ip-udp-ml MAE 솔로(Meet 1.33/Teams 1.81/Webex 1.33) ±0.05 | 50 passed ✅. 10/13 학습 재현 (약 13분, 팀 repo `data/mlruns.db`): **Meet 1.334 / Teams 1.812 / Webex 1.328** (솔로와 차이 +0.004 / +0.002 / −0.002, 3개 평균 1.491, 논문 1.50). 학습 중 절전을 임시로 껐다가 복원. 솔로 DB 해시 불변 | ✅ |
| 2 | 1 tick 추론 예산 | p95 < 200 ms, 모델 메모리 < 500 MB, 버전 경고 없음 | 솔로 `model_meet.pkl`(FPS cv_1): 로드 5.5s, +112MB, 경고 없음, 45 윈도우 p50 24.6 / **p95 74.7** / max 113.7 ms. 단일 지표 기준 — 4지표 동시는 미측정 | ✅ |
| 3 | PCAPdroid pcap 파싱 ☎ | linktype RAW(101), CSV `ip.*/udp.*` 채워짐, `readIpUdpFile` ≠ None | linktype **101 확인** ✅ (UDP exporter 헤더, extensions 끔). 폰 주소는 Wi-Fi IP(192.168.137.60)가 아니라 **PCAPdroid VPN 주소 `10.215.173.1`**로 기록됨 → 수신 dst 선택·캡처 충실도 비교(노트북 쪽은 192.168.137.60) 때 주소 대응 필요. VPN MTU 10000이라 TCP는 최대 7,151 B로 기록(UDP는 최대 1,278 B로 정상). tshark CSV 변환·`readIpUdpFile`은 통화 pcap으로 남음 | 🟡 |
| 4 | Kakao 트래픽 분석 ☎ (Zoom은 여유 시) | UDP/TCP 비율, 상위 flow, 크기 분포(>306B), RTP 여부, ip-udp-ml 입력 조건 예/아니오 | | ⬜ |
| 5 | PCAPdroid → 노트북 스트리밍 ☎ | 10분 무단절, 수신 ≥ 99%, 지연 p95 < 500 ms | 10/13 UDP exporter(PCAPdroid v2.0.2 → 노트북 핫스팟 `192.168.137.1:1234`, `capture/pcapdroid_rx.py`). **수신률 ≥ 99.6%(실제로는 100%)**: YouTube 3.7분, 30,462개·35.1 MB. 앱 Connections #8(QUIC)과 패킷 수(27,148/2,452)·바이트(33.0 MiB/232.7 KiB)·first/last seen이 ms까지 일치. 형식 오류 0, 순서 뒤바뀜 ≤ 3. 10분 연속 연결 유지(1차, 저부하) ✅. **지연: p50 96 ms, p95 1.1 s → 기준 미달이지만 원인은 PCAPdroid의 1초 묶음 전송**(`pcap_dump.c` `MAX_PCAP_DUMP_DELAY_MS 1000`, 묶음 내 최신 패킷은 약 47 ms). 기준을 'p95 < 2.5 s'(대시보드 약 2초 지연)로 바꾸는 안 제안. TCP exporter 비교는 미실시 | 🟡 |
| 6 | 핫스팟 baseline (igc_user + 집) | A 직결 / B 핫스팟 / C 노트북에서 speedtest·ping을 측정한다(W1, 통화 불필요). 기준[가정]: B 다운·업 ≥ 5 Mbps, RTT 증가 ≤ 20 ms, 손실 ≤ 1%. B 경로로 2분 Meet 무끊김은 ☎ 세션 때 확인한다 | **집(TP-Link 5 GHz) 10/13 ✅**: 노트북 Wi-Fi 하나로 받으면서 핫스팟 공유 동작. A 폰 직결 fast.com 4회 평균 다운 91.5 / 업 78.5 Mbps, ping 8.8.8.8 평균 35.6 ms·손실 0%. B 핫스팟 경유 다운 75 / 업 81 Mbps(1회), ping 평균 38.7 ms(**A 대비 +3.2 ms**, 최소값 기준 +1.5 ms)·손실 0%. C 노트북 다운 110 / 업 59 Mbps(1회), ping 평균 32 ms. → 다운로드 약 18% 감소, 기준 모두 충족. 폰→노트북(192.168.137.1) ping은 100% 손실(방화벽이 ICMP 차단 추정, 인터넷 경로엔 영향 없음). **남은 것: 학교 igc_user에서 같은 측정**(대역·인증 방식이 달라 결과가 다를 수 있음), B 경로 2분 Meet 통화(☎). 원자료 `data/m0/hotspot_home_summary.json`, `ping_*.txt` | 🟡 |
| 7 | Clumsy 중계 트래픽 적용 | Drop 10% → ping 손실 10±3%. Lag 100 → RTT +100±15 ms. Bandwidth 500 kbps → speedtest ≤ 550 kbps. 통화 중 화면 저하는 ☎ 세션 때 육안으로 확인한다. 세 모듈은 진단 정확도 실험의 라벨 소스다 | **❌ 중계 트래픽에는 적용 안 됨 (10/13, 집, 핫스팟 5 GHz)**. 필터 `ip.SrcAddr == 192.168.137.60 or ip.DstAddr == 192.168.137.60`. Drop 10% → 폰→8.8.8.8 손실 **0%**. Lag 300 ms → 폰→8.8.8.8 평균 39.4 ms(기준 38.7, **변화 없음**), 반면 노트북↔폰 ping은 684 ms(**적용됨**). 원인: Clumsy 0.3 `divert.c`가 `WinDivertOpen(..., WINDIVERT_LAYER_NETWORK, ...)`만 사용 → 노트북 자신의 패킷만 보고, 핫스팟 NAT 중계 패킷(`NETWORK_FORWARD` 계층)은 못 봄. → Plan A(핫스팟+Clumsy) 그대로는 불가. 추가 시험: NAT 이후 주소 필터(`ip.DstAddr == 8.8.8.8 or ip.SrcAddr == 8.8.8.8`) + Lag 300 → 폰 ping **응답 중복(+29 duplicates)**, 최소 34.8 ms(원본)·최대 400 ms(지연된 복사본). 즉 WinDivert는 NAT된 패킷의 복사본만 보고 원본은 Windows NAT 경로로 그대로 통과 → Drop·Lag 모두 실효 없음. WinDivert 2.2 문서 경고('forward layer does not interact well with the Windows NAT', 'not possible to block packets pre-NAT')와 일치 → A′(forward 계층)도 같은 문제 예상. 대안 결정 필요(Q10) | ❌ |
| 8 | scrcpy ☎ | ≥ 30 fps, PCAPdroid와 동시 동작, 통화 화면 검지 않음(FLAG_SECURE) | **보류**. 증상=기본 코덱에서 연결 끊김("Device disconnected"), 원인 미확정. 케이블 도착 후 재시도. (10/13 관찰: adb 상태가 `offline`↔`device`로 한 번 흔들림 → 케이블·포트 문제 가능성, 미확인) | ⏸ |
| 9 | 폰 Chrome getStats ☎ | 가능 여부 먼저 보고. 2분간 inbound video 지표 ≥ 95% 초 존재 | | ⬜ |
| 10 | 노트북 측 캡처 | `tshark -D`에 핫스팟 인터페이스, 폰 IP 필터로 캡처 | | ⬜ |

M0 설계 메모 (M2 `features.py`에 반영):
- 스트리밍 윈도우의 첫 IAT는 **직전 윈도우 마지막 패킷 기준**으로 계산해야 배치(vcaml)와 같다. 슬라이스를 그대로 넣으면 첫 IAT가 통화 시작 기준이 되어 커진다.
- vcaml 배치 윈도우는 "첫 패킷 + 1초 초과 시 새 윈도우"(가변 경계), 스트리밍은 고정 1초 격자 → 작은 차이 가능, M2에서 수치 비교.

## M1 — 더미 스트림 + 대시보드 뼈대 / vcaml 재현 수치 / SCHEMA v1.1 확정 (마감 10/26)
## M2 — Replay 실시간 추론 + 지표별 판정 + 진단 v0 / Meet 정답 수집 / 충실도 스크립트 (마감 11/6)

### 선행 작업 (10/12 밤, 브랜치 `ml/m2-core`, Opus 5.5 xhigh)
| # | 항목 | 결과 | 상태 |
|---|---|---|---|
| 1 | 실시간 feature 추출 `server/features.py` | vcaml 배치(ip-udp-ml)와 **완전히 같은 값**. in-lab 15통화(Meet·Teams·Webex 각 5), rtol 1e-9. vcaml `FeatureExtractor`를 그대로 호출하고 윈도우 경계·첫 IAT만 배치 규칙에 맞춤 | ✅ |
| 2 | What-if 손상 `server/impair.py` | Bernoulli·Gilbert 손실, 토큰 버킷 대역폭(대기 200ms 초과 시 버림), 지연+지터(FIFO, 재정렬 없음). 1초 단위로 나눠 적용해도 한 번에 적용한 것과 같음. 테스트 10개 | ✅ |
| 3 | 원인 진단 v0.1 `server/diagnosis.py` + 합성 실험 `scripts/diag_synth.py` | 아래 결과표. 테스트 13개 | ✅ |
| 4 | 1 tick 처리 시간 `scripts/bench_tick.py` | **p95 36 ms** (목표 200 ms) — 아래 | ✅ |

전체 테스트: `uv run pytest` → 43 passed (10/13).

#### 1 tick 처리 시간 (지표 4개 모델 + 진단, in-lab Meet test 10통화, 438 tick)
| 경로 | p50 | p95 | 최대 |
|---|---|---|---|
| Replay/Live (패킷 push + feature + RF 4개 predict + 진단) | 26.5 ms | **36.2 ms** | 103 ms |
| What-if (위 + 손상 5%/버스트2, 100±30 ms, 120 kbps) | 25.3 ms | **35.1 ms** | 113 ms |

- 모델 4개(fps, bitrate, frame_jitter, frameHeight; 솔로 Meet fold-1)를 읽는 데 2.0초가 걸리고, 메모리는 252 MB 늘어 프로세스 전체가 341 MB다. scikit-learn 버전 경고는 없다.
- 첫 측정에서 최대값이 4.8시간으로 나왔다. 측정 중 노트북이 **절전(Modern Standby)** 에 들어간 탓이다. 그래서 60초가 넘는 tick은 별도로 세어 제외하도록 고쳤고, 재측정에서 제외된 tick은 0개였다. **데모·리허설 중에는 절전을 꺼야 한다.**
- 1초 예산 대비 여유는 충분하다(p95가 4%). 단 이는 in-lab의 약 30 pkt/s 기준이다. Teams처럼 약 270 pkt/s인 통화와 실제 폰 통화에서는 M2 Replay 때 다시 잰다.

#### 원인 진단 합성 실험 결과 (test 세트 = 규칙 조정에 쓰지 않은 통화)
방법: 손상이 거의 없는 in-lab 통화(처리량 ≥ 3000 kbps, 지연 ≤ 60 ms, 손실 0)를 골랐다. 각 통화는 **영상 시작 12초 뒤부터** 한 가지 손상을 받는다. 손상 종류는 손실 2/5/10%와 5% 버스트, 지터 20/40/80 ms, 대역폭 기준의 60/40/25%다. 윈도우별로 정답 라벨과 비교했다. 통화를 짝/홀로 나눠 dev(규칙 조정용)와 test(보고용)로 썼다.

**v0** — 규칙을 Meet dev로만 정함. Teams·Webex는 규칙을 그대로 적용(전이 확인).

| VCA | 모드 | 통화 | 정확도 | bandwidth P / R | delay_jitter P / R | loss P / R | none R |
|---|---|---|---|---|---|---|---|
| Meet | IP/UDP만 | 26 | 0.695 | 0.88 / 0.94 | 0.98 / 0.91 | 0.90 / 0.19 | 0.97 |
| Meet | + RTP 순번 | 26 | 0.823 | 0.87 / 0.94 | 1.00 / 0.91 | 0.93 / 0.58 | 0.98 |
| Teams | IP/UDP만 | 25 | 0.399 | 1.00 / 0.96 | — / 0.00 | 0.01 / 0.00 | 1.00 |
| Teams | + RTP 순번 | 25 | 0.719 | 1.00 / 0.96 | 1.00 / 0.00 | 0.96 / 0.95 | 1.00 |
| Webex | IP/UDP만 | 26 | 0.482 | 0.99 / 1.00 | 1.00 / 0.18 | 0.20 / 0.10 | 0.99 |
| Webex | + RTP 순번 | 26 | 0.720 | 0.99 / 1.00 | 1.00 / 0.18 | 0.99 / 0.80 | 0.99 |

v0의 Teams 실패 원인을 **Teams dev**에서 분석했다.
- Teams는 영상 시작 후 비트레이트가 약 4배까지 오른다. 그런데 기준선이 "±15% 이내 윈도우만" 받아서 초반 값에 고정됐다.
- Teams는 원래 짧은 간격(q1)이 약 1 ms라서, 지터가 와도 "q1 −3 ms 이상 감소" 조건을 만족할 수 없다.

**v0.1** — 수정 내용:
- 기준선은 비트레이트 상승을 허용한다(하한만 둠).
- 지터 규칙을 하나 추가했다: q1 비율이 0.3 이하이고 최대 간격이 40 ms 넘게 증가하면 지터로 본다.
- 조정에는 Meet dev와 Teams dev만 썼고, **Webex는 어느 쪽도 쓰지 않았다**(가장 깨끗한 전이 검증).
- 다만 Teams·Webex test v0 결과를 본 뒤에 고쳤으므로, 그 점을 감안해서 읽어야 한다.

| VCA | 모드 | 정확도 | bandwidth P / R | delay_jitter P / R | loss P / R | none R |
|---|---|---|---|---|---|---|
| Meet | IP/UDP만 | 0.693 | 0.86 / 0.95 | 0.97 / 0.91 | 0.89 / 0.18 | 0.96 |
| Meet | + RTP 순번 | **0.819** | 0.86 / 0.95 | 0.99 / 0.91 | 0.94 / 0.56 | 0.97 |
| Teams | IP/UDP만 | 0.493 | 1.00 / 1.00 | 1.00 / 0.30 | 0.29 / 0.03 | 0.98 |
| Teams | + RTP 순번 | **0.807** | 1.00 / 1.00 | 1.00 / 0.31 | 1.00 / 0.94 | 1.00 |
| Webex | IP/UDP만 | 0.589 | 0.99 / 1.00 | 0.99 / 0.63 | 0.57 / 0.08 | 0.99 |
| Webex | + RTP 순번 | **0.826** | 0.99 / 1.00 | 0.99 / 0.63 | 1.00 / 0.77 | 0.99 |

요약 (v0.1, RTP 사용):
- **대역폭 부족**: 세 VCA 모두 잡는다(재현율 0.95–1.00, 판정 약 1.6초). 병목 대기열이 패킷 간격을 전송 속도대로 벌리는 흔적은 앱과 상관없이 뚜렷하다.
- **손실**: RTP 순번으로 0.56–0.94를 잡는다. IP/UDP만으로는 0.03–0.18이라 사실상 불가능하다.
- **지터**: 앱마다 크게 다르다. Meet은 20 ms 0.73, 40 ms 이상 0.99다. Webex는 40 ms 이상 0.88–0.99이고 20 ms 0.03이다. Teams는 80 ms에서만 0.84이고 40 ms 이하는 0.10 이하다.
- **정상 통화 오탐**: 1–4%.
- 판정 지연(중앙값): 대역폭·지터 약 1.5초. 손실은 RTP를 쓰면 1–5초, IP/UDP만 쓰면 4–19초.
- **발견 1 — 고정 지연은 보이지 않는다.** 지터 없이 200 ms 지연만 넣은 경우 97%를 "none"으로 판정했다. 수신 측 trace의 간격은 지연이 고정이면 변하지 않기 때문이다. **Clumsy lag는 고정 지연이라, 실험 ③에서 `delay_jitter` 라벨로 쓰면 원리적으로 맞힐 수 없다.** → lag 대신 지터를 만드는 모듈(throttle 등)을 쓰거나 라벨을 재정의해야 한다. M4 전에 결정이 필요하다.
- **발견 2 — 손실은 IP/UDP만으로는 거의 못 잡는다.** in-lab Meet 영상은 초당 약 30패킷이라, 5% 손실은 초당 1.5패킷에 불과해 자연 변동에 묻힌다. RTP 순번(SRTP에서도 평문 헤더)을 쓰면 재현율이 0.19에서 0.58로 오른다. Kakao가 RTP를 쓰는지는 M0-4에서 확인한다.
- **발견 3 — in-lab 데이터의 한계.** 영상이 녹화 시작 약 24초 뒤부터 흐르고, 초당 약 150 kbps(프레임당 패킷 약 1개)로 실제 폰 통화보다 훨씬 낮다. 임계값은 실제 폰 통화(Clumsy 실험)에서 재조정해야 한다.
- **발견 4 — 같은 규칙이 앱마다 다르게 듣는다.** 송신 패턴이 다르기 때문이다(Meet 약 30 pkt/s, Teams 약 270 pkt/s에 비트레이트 증가). 실제 Meet·Kakao 폰 통화에서도 앱별 임계값이 필요할 것으로 보인다 [가정]. 그래서 M4 Clumsy 실험을 dev와 test로 나눠 수집하는 것을 권장한다.
- 원자료: v0 `data/diag/test/`, v0.1 `data/diag/v01_test/` (`summary_*.json`, `windows_*.csv`, git 제외).
- 재현: `uv run python scripts/diag_synth.py --vca <vca> --split test --rtp`. 규칙만 바꿨다면 `--rescore data/diag/test/windows_<vca>_test_rtp.csv [--rtp] --out <폴더>`로 몇 초 만에 재채점할 수 있다.
## M3 — (v6) 평가: 정답 대비 정확도 + 원인 진단 + 오버헤드 (마감 11/16, W5)
## M4 — (v6) Meet·Zoom 수집(손실·대역폭·CPU 조건표) + device_cpu 진단 (마감 11/9, W3–W4)
## M5 = Freeze — 테스트, README, 정적 데모, 녹화본, 데모 스크립트 (마감 11/24)

## Flutter 오버레이 (v6: 보관 — 개발 중단, Android 설계의 실측 근거)
> v6(10/14)부터 오버레이는 더 개발하지 않는다. 아래 표의 11/8·11/15·11/20 항목은 취소. 브랜치 `ml/overlay-spike`만 보존.
| 기한 | 내용 | 결과 | 상태 |
|---|---|---|---|
| 10/18 | Android 13 오버레이 권한·표시 확인 (= M0 a) | 10/13 기능 확인 완료(위 M0-a). 통화 위 10분 유지만 ☎ 세션에서 | 🟡 |
| 11/8 | 더미 스트림 연동 | | ⬜ |
| 11/15 | Live 연동 | | ⬜ |
| 11/20 | 표시 문구 확정 | | ⬜ |

**버블 UI/UX 담당 (10/13 재결정): Sungmin이 직접 한다.** 어제(10/13 오전) 적은 "팀원 인계"는 취소한다.
- 이유: 팀원은 주 3시간 정도이고 React 대시보드(최소 범위)에 집중한다. 오버레이는 Android 전용이라 팀원(Mac·iPhone)이 기기 시험을 할 수 없다.
- 알려진 UX 과제(Sungmin): ① 크게 모드의 문구 밀도 ② 좌우 벽 없음(플러그인 `minVisibleWidth`, 한 줄) ③ 드래그 감각 ④ 색 외 글자로도 상태 구분(접근성) ⑤ 11/20 문구 확정
