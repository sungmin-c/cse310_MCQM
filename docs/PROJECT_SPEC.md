# Task: MCQM — Multi-layer Call Quality Monitor: 실시간 추정 + 네트워크 vs 기기 원인 진단 + 조치 후 회복 검증 (CSE310 Final, vcaml 기반)

> **v8 (2026-10-28)**: **Zoom 제외, 측정 앱 = Meet + Teams.** 측정·캡처·주입은 전부 **Windows 노트북 + Chrome 웹 클라이언트**에서 한다. 통화 수 Meet≈30 / Teams≈15, 부족하면 Teams부터 줄인다. 근거는 `docs/PROGRESS.md` Q25.
> v7 (10/22): 측정 순서 Meet → Teams → Zoom, **조치 안내 + 조치 후 회복 검증**과 **미니 위젯**(대시보드를 Chrome Document Picture-in-Picture로 띄운 항상-위 창) 추가. 조치는 안내형이고 실행은 사용자가 한다(자동 복구 없음). Q22·Q23.
> v6 (10/14, 교수님 면담: 데스크톱 우선, Android는 설계만), v5·v4 이력은 git log와 `docs/PROGRESS.md`. 메시지 계약은 `docs/SCHEMA.md`.

## 팀과 제약
- 2인 팀, 마감은 **2026-12-02 Final Demo**(기능 동결 **11/24**), 발표는 **약 12분**이다.
  - **Sungmin** (Windows): Python·ML 백엔드, 캡처, 진단·회복 판정, 실험, Android 설계 문서.
  - **팀원** (Mac): React 대시보드 + 미니 위젯(PiP). **Python·ML 코드는 거의 다루지 못한다.**
  - 모든 단계에 "실행 방법과 확인 방법"을 한국어로 짧게 붙이고, 명령은 OS 중립(`uv run`, `npm --prefix`)으로 쓴다.
  - 설명은 한국어로 쓰고, 코드·명령어·기술 용어는 영어 그대로 둔다.
- 노트북: Windows 11, Core Ultra 5 125H, RAM 16GB (여유 메모리 적음), GPU 미사용.
- 측정 기기는 **이 노트북**(통화 수신 측). 통화 상대는 **Sungmin의 Galaxy S20**(Meet·Teams 앱). 안 되면 팀원 노트북과 서로 측정(나중). 상대 기기에서는 캡처하지 않는다.
- **netem(Linux)과 Odroid는 사용하지 않는다.**

## 핵심 메시지 (모든 설계 판단의 기준)
> "Windows 데스크톱에서, 앱 내부 정보 없이 **패킷 헤더와 OS 지표만으로** 영상통화 품질을 **얼마나 정확히** 실시간 추정하고, 저하의 원인이 **네트워크인지 기기(CPU)인지** 구분하며, **안내한 조치 뒤 품질이 회복됐는지** 확인할 수 있는가."

**연구 질문 (v8)**
1. Meet·Teams(Chrome 웹) 수신 영상의 초당 품질(fps·bitrate·해상도)을 IP/UDP 헤더만으로 얼마나 정확히 추정하는가? vcaml 모델은 Linux·에뮬레이션 데이터로 학습했는데, Windows 실환경에서도 통하는가? 재학습하면 얼마나 회복되는가?
2. 품질 저하의 원인을 **네트워크(손실·대역폭)와 기기(CPU)**로 얼마나 정확히 구분하는가? 패킷만 보면 CPU 병목은 보이지 않고(패킷은 정상, 품질만 하락) OS 지표를 더하면 구분되는가? **[W1 P2 파일럿에서 신호 확인, W3에서 검증]**
3. 조치(원인 해소) 뒤 **회복을 얼마나 빨리, 정확히 판정**하는가? (회복 판정 지연, 오판정률)
4. 모니터(tshark + 추론) 자신이 통화에 주는 부하는 얼마인가? **[W1 P3에서 약 1.3% CPU, 반복 측정 예정]**

**측정 정확도와 검증**이 중심이다. 대시보드와 위젯은 이 결과를 보여 주는 도구다.

## 기반과 추가 범위
기반은 `github.com/noise-lab/vcaml`(IMC'23)이다(fork `sungmin-c/vcaml` 브랜치 `mcqm`, `vcaml/` submodule, 원본에 LICENSE 없음 → 코드 복사 금지). vcaml은 pcap → LSTATS/TSTATS feature → Random Forest로 fps·bitrate·frame jitter·해상도를 추정하며, 데스크톱 오프라인 배치다. 입력 방식은 `ip-udp-ml`(IP/UDP 헤더만, 핵심)과 `rtp-ml`(RTP 헤더 포함) 두 가지이고, 측정 앱은 Meet·Teams·Webex(정답 = Chrome webrtc-internals)다. 학습 데이터는 Linux Chrome + 에뮬레이션 조건이고, 논문도 in-lab → real-world 이전에서 Meet FPS MAE 12.41로 실패했다(Table 5). 그래서 **Windows 실환경 정확도는 직접 재야 한다.**

**측정 대상·순서 (v8)**: Meet(파일럿·정답 확보) → Teams(vcaml 선행·모델 있음). 둘 다 **Windows 노트북 + Chrome 웹 클라이언트**로 측정한다(Clumsy·WinDivert·코어 고정이 Windows 전용이고, OS와 앱이 같이 바뀌면 원인을 분리할 수 없다). 팀원의 Mac은 대시보드 개발용이라 측정과 무관하다. 통화 수 Meet≈30 / Teams≈15, 시간이 부족하면 Teams부터 줄인다. Zoom은 v8에서 제외(정답이 근사값·RTP 접근 미확인, 2인 팀·남은 5주).

**우리가 추가하는 것 (우선순위 순):**
- **P0** 실시간 파이프라인(tshark → 1초 창 → RF) + 정답 대비 정확도 + 재학습 (Meet)
- **P0** 원인 진단: `none | loss | bandwidth | device_cpu` + 근거 피처 + 신뢰도 (OS 지표 결합)
- **P1** 조치 안내 + 회복 검증 (아래 §5-1)
- **P1** React 대시보드 + 미니 위젯(Document PiP) (지표별 판정, 원인·근거·조치 카드, 회복 상태, CPU 게이지, 추정·정답 겹침 차트)
- **P1** Teams 확장 (정답 webrtc-internals, **Chrome 웹 클라이언트에서 가능한지 미확인 → T9 파일럿**)
- **P2** 모니터 오버헤드 반복 측정 (W1 P3 반복)
- **P2** Android 4계층 설계 문서 (구현 없음, 10/14 합의)
- **P3** What-if 슬라이더 UI (여유 시)

**범위에서 제외**: 모바일 정확도 주장, Kakao, Flutter 오버레이 개발, 핫스팟 캡처, MOS/0–100 QoE 점수, **자동 복구(앱이 직접 조치 실행)**, 고정 지연 진단, **Zoom(v8)**, Webex, Teams 데스크톱 앱, macOS 측정.

## 절대 규칙
1. **확인하지 않은 것을 사실처럼 쓰지 않는다.** 확인하지 못했으면 "미확인", 가정은 `[가정]`.
2. 정답이 없는 결과에는 항상 `validated: false`와 "모델 추정값" 표시를 붙인다. Teams는 정답 경로가 확인되기 전까지 `validated:false`.
3. What-if는 **trace 기반 에뮬레이션**이므로 송신 측 혼잡 제어 반응을 반영하지 않는다. UI와 README에 명시한다. (실측 손상이 주력이다.)
4. **내 노트북 자신의 트래픽만** 캡처한다. 다른 사람의 트래픽 캡처나 Wi-Fi 스니핑 코드는 만들지 않는다.
5. 마일스톤마다 테스트와 빌드를 실행하고 결과를 요약한 뒤 승인을 받고 넘어간다. 파일 삭제·덮어쓰기 전에는 알린다. 의존성·드라이버 설치는 이유와 되돌리는 방법을 함께 기록한다.
6. 원인 진단은 **추정**이다. UI에 `confidence`를 함께 표시하고 "확정 진단"처럼 쓰지 않는다. CPU 원인은 주입한 조건이 라벨이며, 실제 현장의 CPU 병목 일반화는 주장하지 않는다.
7. **조치는 안내만 한다.** 앱이 프로세스 종료·네트워크 변경을 직접 하지 않는다. 실험에서 "조치"는 주입 조건 해제이므로, 회복 검증은 "조치가 현장에서 효과 있다"가 아니라 **"회복을 얼마나 빨리, 정확히 판정하는가"**를 잰다. 발표·보고서에 이렇게 쓴다.

## 1. 아키텍처
```
[Chrome(Meet·Teams 웹)]   ← 상대: S20 (영상 송신)
        │ UDP (노트북 수신)
        ▼
tshark -i <Wi-Fi> -f udp -T fields (epoch, ip.dst, proto, udp.length[, rtp.ssrc, rtp.seq])
  → server/features.py   (vcaml FeatureExtractor, 1초 창)
  → estimator (vcaml RF → W3 이후 재학습 모델) → judge.py (지표별 판정)
  + sample_os (psutil 1 Hz: 전체 CPU%, 통화 프로세스 CPU%, call_core_pct, 메모리%)
  → diagnosis.py v1: {none, loss, bandwidth, device_cpu} → 조치 문구 + 회복 판정
  → FastAPI WebSocket ─→ React 대시보드 + 미니 위젯(Document PiP, 같은 노트북 Chrome)
```
- 백엔드는 `server/`에 두고 uv로 관리한다. 모든 추론은 노트북에서 한다. 대시보드·위젯은 SCHEMA를 구독하는 표시 전용 클라이언트다 (H4: 노트북 상주 서비스 + 입력 모듈 구조).
- 프론트엔드는 React + TypeScript(Vite), Tailwind, Chart.js. 로직은 `src/core/` 순수 함수. **미니 위젯은 별도 앱이 아니라** 대시보드가 `documentPictureInPicture.requestWindow()`로 연 작은 창이다(Chrome 116+, 사용자 클릭 필요). 통화 창(특히 전체 화면) 위에 계속 보이는지는 **미확인 → W2 스파이크**. 안 되면 대시보드 창을 작게 띄우는 것으로 대체한다.
- **정적 데모 빌드**: 대표 시나리오 결과를 JSON으로 미리 계산해 백엔드 없이 재생한다.
- **입력 모드**: `Live`(tshark 실시간), `Replay`(저장 pcap/CSV 재생, 데모 fallback), `What-if`(P3).
- 정식 계약은 `docs/SCHEMA.md`와 `docs/schema/sample.jsonl`. v1.2(지표별 `judgement`, `device`, cause `device_cpu`)는 팀원 확인 대기. **조치·회복 필드와 client→server "조치함" 메시지는 설계 전(T10)**.
- 서버 `--app`은 현재 `meet|zoom`만 받는다 → `teams` 추가 필요(T9, 작은 변경). `zoom` 선택지는 코드에 남아 있으나 v8 범위 밖.

## 2. 손상·부하 주입 (Windows, 자기 기기)
| 조건 | 도구 | 비고 |
|---|---|---|
| 손실 | Clumsy `drop`, 필터 `udp and inbound` | 노트북 자신의 트래픽에는 동작함(10/13 실측). 캡처에 손실이 보이는지는 W3 S0-1에서 확인 |
| 지연·지터 | Clumsy `lag` | 고정 지연은 수신 trace에 보이지 않아 진단 대상 제외 |
| **대역폭** | **clumsy2** (오픈소스 fork, 승인됨) | Clumsy `throttle`은 몰아 보내기일 뿐 속도 제한이 아님. 설치·동작 **미확인**, W3 S0-2 |
| CPU 부하 | `scripts/cpu_load.py` Chrome **코어 고정**(+ busy loop) | 설치 없음. P2에서 코어 고정이 busy loop보다 효과적 |
- 주입한 조건이 곧 라벨이다. 주입 **해제**가 실험상의 "조치"다(§5-1). 시스템 변경(드라이버)은 되돌리는 방법을 함께 기록한다.
- Clumsy/clumsy2는 관리자 권한과 WinDivert 드라이버가 필요하다.

## 3. 정답과 검증
1. **Meet 정답**: webrtc-internals dump(vcaml `WebRTCReader` 재사용). PeerConnection 교체 때문에 캡처 구간 fps>0이 가장 많은 PC를 고른다(`pilot_live.py compare`).
2. **Teams 정답**: Chrome 웹 클라이언트 + webrtc-internals [가정]. **미확인 → Teams 파일럿 1건(T9, 절차 `docs/design/w3_collection.md` §8)**에서 패킷 경로(P2P/서버), dump에 inbound video 통계가 있는지, S20 Teams 앱과 통화되는지 확인. 안 되면 Teams는 추정만(`validated:false`) 보고하고 재학습·MAE에서 뺀다.
3. (v8 제외) Zoom 정답 — W1 P4 결과는 PROGRESS "W1 파일럿 결과"에 보관.
4. **지표**: QoE는 4개 지표(fps·bitrate·frame jitter·frameHeight)로 정의하고, "정확도"는 그 추정값이 정답(webrtc-internals)과 얼마나 다른지(오차)로 말한다. fps·bitrate·frame jitter MAE, fps ±2 이내 비율, 해상도 분류 정확도. 판정·진단은 Precision·Recall·F1·Confusion Matrix. frame jitter 정답 필드는 vcaml 정의와 맞춘다.
5. **원인 진단 평가**: 라벨 = 주입 조건. `none/loss/bandwidth/device_cpu`. 통화 단위로 dev/test 분리. 손실은 RTP 순번이 보여야 구분된다(IP/UDP만 재현율 0.03–0.18). **Teams의 RTP 헤더 해석은 미확인(T9).** 절제 실험: 같은 test를 OS 지표 없이(`device=None`).
6. **회복 검증 평가** (§5-1): 같은 W3 통화의 recovery 구간(해제 후 80초)을 쓴다. 추가 통화 없음.
7. **도메인 차이**: Meet MAE가 크면(P1 9.09) W3 수집분으로 통화 단위 분리 재학습하고, "Linux 에뮬레이션 → Windows 실환경 이전" 결과로 보고한다. 재학습해도 개선이 작으면 그 자체를 결과로 보고한다.
8. **오버헤드**: 모니터 끔/켬 교대(`scripts/overhead_ab.py`). 기준 [가정]: fps 차이 < 1, CPU < 10%, **메모리**: 켬 단계에서 시스템 가용 메모리 감소(MB)와 모니터 RSS(tshark + Python)를 보고하고, freeze·드롭·디코드 시간 변화가 없는지 함께 본다(메모리 자체의 합격선은 두지 않는다 [가정]). 메모리에는 대시보드·PiP 위젯이 든 Chrome RSS를 포함해 재측정한다(`<name>_mem.csv`). P3 1통화: CPU·fps 통과. 메모리는 P3에서 시스템 `mem_pct` 83.2–83.6% → 85.9–86.1%(켬, 약 +2.5%p ≈ 0.4GB), 모델 로딩 +252MB·프로세스 341MB(`bench_tick`)로만 확인됐고 tshark·대시보드·WS 서버 실행 시 값은 미측정. W5에 반복.
9. 한계: 앱 2개(Meet·Teams)·둘 다 Chrome 웹 클라이언트만 측정, 표본 수(Meet≈30·Teams≈15통화는 일정에서 정한 계획이며 통계적으로 산정한 값이 아님, 조건별로 나누면 조건당 소수), 상대 기기 영상 변동, Linux→Windows 이전, 라벨이 인위적 손상·부하라는 점, 조치=주입 해제라는 점, 영상통화 외 암호화 서비스로의 일반화는 시험하지 않음.
10. **프로젝트 성격 (10/25)**: 새 제품이 아니라 **측정과 검증 연구**다. 벤더(Meet·Teams·Zoom)도 앱 안에서 실시간 안내를 이미 하므로 "업계에 없는 기능"이라고 주장하지 않는다. 의의: (1) 앱 밖에서 같은 방법으로 실시간 추정, (2) 정답 대비 오차 측정(가장 단단한 의의), (3) 네트워크/기기 원인 구분의 정확도 평가, (4) 회복 판정. 다른 암호화 서비스로의 확장은 "방법이 옮겨 갈 가능성(방향)"일 뿐 결과가 아니다.

## 4. What-if 손상 함수 (`impair.py`, P3 보조)
Bernoulli/Gilbert 손실, 토큰 버킷 대역폭(200 ms 초과 시 버림), 지연+지터(FIFO). seed 고정, 청크 적용이 전체 적용과 같음(테스트 있음).

## 5. 지표별 판정 (0–100 QoE 점수 대체)
- fps, bitrate, frame jitter, 해상도마다 **정상 / 주의 / 나쁨**. 전체 `verdict`는 하나라도 나쁨이면 failed. 상세는 `docs/design/judge.md`.
- 기준값은 공개 자료에서 가져와 **출처를 코드 주석과 문서에 단다**. 기준이 정해지기 전까지는 [가정]값, W3 후 보정.
- 테스트: 단조성, 경계값, 전체 판정 일관성.

### 5-1. 조치 안내 + 회복 검증 (v7, 설계 T10)
| 원인 | 조치 안내 (예시, 문구는 T10에서 확정) | 실험에서의 "조치" |
|---|---|---|
| `device_cpu` | 무거운 앱 종료, 충전기 연결, 카메라 화질 낮추기 | `cpu_load.py` 종료(affinity 복원) |
| `loss` | 공유기 가까이, 유선 연결, 다른 네트워크 | Clumsy Drop 해제 |
| `bandwidth` | 다른 기기의 다운로드 중지, 영상 끄기 | clumsy2 해제 |
- 흐름: 진단이 `none`이 아니면 위젯에 원인·조치 1줄 → 사용자가 실행 후 **[조치함]** 클릭(선택) → 서버가 회복 판정 시작.
- 회복 판정 [가정, T10에서 확정]: 조치 시각 이후 judge `overall`이 기준선 등급으로 돌아오고 진단이 `none`인 상태가 **연속 N초(예: 5)** 유지되면 `recovered`, **T초(예: 30)** 안에 안 되면 `not_recovered`. 지표: 회복 판정 지연(해제 → `recovered`) 중앙값, 해제 없이 `recovered`가 나오는 오판정률, `not_recovered` 비율.
- [조치함] 클릭이 없으면 진단이 `none`으로 돌아온 시각을 조치 시각으로 본다(Live 데모용). 평가에서는 log의 `impair_off` 시각을 쓴다.

## 6. 마일스톤
| 주 | 기간 | 내용 |
|---|---|---|
| W1 파일럿 | 10/14–10/19 | ✅ P1 Meet 정확도, P2 CPU 부하, P3 오버헤드, P4 Zoom 정답 경로 |
| **W2** | 10/20–10/26 | ✅ 실시간 파이프라인·judge·WS·진단 v1 코드 병합(PR #9). **남은 것**: W3 S0 사전 점검·Teams 파일럿(→ W3 이월), 위젯 PiP 스파이크(팀원), 조치·회복 설계(T10), Proposal 발표 (Midterm 1 10/21) |
| W3 | 10/27–11/2 | S0 사전 점검, Meet ≈30통화 수집(조건표, recovery 구간 포함), clumsy2 확정, **Teams 파일럿 T9**(W2에서 이월, W4 전 필수) |
| W4 | 11/3–11/9 | Teams ≈15통화(`w3_collection.md` §9), 회복 판정 구현, 위젯에 조치·회복 표시 |
| W5 | 11/10–11/16 | 재학습(Meet·Teams, 통화 단위 분리) + 평가(MAE 재학습 전후, 진단 confusion matrix, 회복 지연, 오버헤드 표) |
| W6 | 11/17–11/23 | Android 4계층 설계 문서, README, 정적 데모·녹화본, **11/24 동결** (Midterm 2 11/25) |
| W7 | 11/24–12/1 | 리허설 2회, Replay 대체 시연 점검. **12/2 Demo** |

대체안: 실시간 tshark 불안정 → Replay. CPU 부하에도 품질 불변 → 부하 강화 후 "기기 원인 관측 안 됨"으로 보고. Teams 정답 실패 → 추정만 `validated:false`(진단 평가에는 사용). 시간 부족 → Teams부터 축소(15 → 조건당 1통화 7 → 0이면 파일럿 결과만 보고). clumsy2 불가 → 손실·CPU만. PiP가 통화 창 위에 안 뜸 → 작은 대시보드 창.

## 7. Android 4계층 설계 (구현 없음, P2)
계층 L1 앱/QoE, L2 전송, L3 무선(Wi-Fi·셀룰러), L4 기기. 분류 N(일반) / S(특수 접근) / P(특권) / X(불가). 상세는 향후 `docs/ANDROID_DESIGN.md`. 요지:
- L1은 다른 앱 통계를 읽을 수 없다(X) → L2 추정이 대신한다.
- L4의 다른 앱 CPU는 읽을 수 없다 → `device_cpu`는 Android에서 발열 상태 등으로 대체해야 한다(한계).
- 조치는 안내형(Settings.Panel)만 가능. 자동 Wi-Fi↔셀룰러 전환은 일반 앱 불가. → 데스크톱의 "안내형 조치"와 같은 원칙.
- **팀 실측 근거(10/13, S20 Android 13)**: PCAPdroid VpnService 캡처·UDP 스트리밍, RSSI(`NetworkCapabilities` + `ACCESS_NETWORK_STATE`), `Settings.Panel`, `SYSTEM_ALERT_WINDOW` 오버레이(브랜치 `ml/overlay-spike`). 공식 문서 원문을 확인하지 못한 항목은 `[미확인-원문]`으로 표기한다.

## 8. 발표 구성 (최종 12분)
| 시간 | 내용 |
|---|---|
| 0–2분 | 문제: 암호화된 통화에서 품질 저하의 원인이 네트워크인지 기기인지 어떻게 아는가 |
| 2–4분 | 방법: vcaml 원리 + 우리가 추가한 것(실시간, 재학습, OS 지표 결합, 조치·회복) |
| 4–9분 | **라이브 데모**: 정상 통화 → 손실/CPU 부하 주입 → 위젯에 원인·조치 → 해제 → "회복됨" |
| 9–11분 | 결과: 정답 대비 정확도(재학습 전후), 원인 진단 정확도, 회복 판정 지연, 오버헤드, Android 설계 요약 |
| 11–12분 | 한계와 향후 과제 |

라이브 데모가 실패하면 즉시 Replay와 녹화본으로 전환한다. Proposal 발표(5–10분) 자료는 `docs/proposal/`.

## 9. 테스트
- pytest: impair, features, judge(단조성·경계), diagnosis(조건별 규칙), 회복 판정(T10), SCHEMA 계약. Vitest: 프론트엔드 `core/`.

## 10. 산출물
`README.md`(한국어 + 영어 요약, 맨 위 "vcaml 대비 추가한 것" 3줄), `capture/ server/ dashboard/ scripts/ docs/ tests/ vcaml/`, `overlay/`는 보관(Android 설계 근거), 데모 스크립트, Android 설계 문서, 최종 보고서 초안(한국어).
