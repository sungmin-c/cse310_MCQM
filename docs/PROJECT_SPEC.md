# Task: Mobile Call Quality Monitor — 폰 실측 기반 실시간 QoE 추정 + What-if Lab (CSE310 Final, vcaml 기반)

Claude Code의 첫 메시지로 이 문서 전체를 붙여넣는다.

> **v4 (2026-10-12)**: Flutter 오버레이 앱 P0 확정, 원인 진단(diagnosis·action) 추가, 앱 비교를 Meet·Kakao로 축소, 일정 변경(동결 11/24, 발표 12/2). 진행 기록은 `docs/PROGRESS.md`, 메시지 계약은 `docs/SCHEMA.md`.

## MODE
**Plan mode로 시작한다.** 계획을 승인받기 전에는 애플리케이션 코드를 작성하지 않는다.
1. 아래 참고 자료와 repo를 직접 읽는다.
2. 진행을 막는 질문을 최대 5개까지 한 번에 묻는다.
3. 계획을 제시한다: 파일 트리, 데이터 흐름, 공식, 리스크, 마일스톤. 모든 가정에는 `[가정]` 표시를 붙인다.

## 팀과 제약
- 2인 팀, 마감은 **2026-12-02 Final Demo**(기능 동결 **11/24**), 발표는 **약 12분**이다.
  - **Sungmin** (Windows, Galaxy S20): Python·ML 백엔드, Flutter 오버레이 앱.
  - **팀원** (Mac, iPhone): React 대시보드. **Python·ML 코드는 거의 다루지 못한다.**
  - 그래서 모든 단계에 "실행 방법과 확인 방법"을 한국어로 짧게 붙이고, 명령은 OS 중립(`uv run`, `npm --prefix`)으로 쓴다.
  - 설명은 한국어로 쓰고, 코드·명령어·기술 용어는 영어 그대로 둔다.
- 노트북: Windows 11, Core Ultra 5 125H, RAM 16GB (여유 메모리 적음), GPU 미사용.
- 측정 기기: Galaxy S20 (Android 13) + PCAPdroid. 통화 상대는 팀원의 iPhone이며, iPhone에서는 캡처하지 않는다.
- **netem(Linux)과 Odroid는 사용하지 않는다.** Wi-Fi 환경은 학교 igc_user 또는 집이다.

## 핵심 메시지 (모든 설계 판단의 기준)
> "모바일 기기에서, 앱 내부 정보 없이 네트워크 트래픽만으로 통화 품질을 **얼마나 정확하게** 실시간 추정할 수 있는가."

**측정 정확도와 검증**이 이 프로젝트의 중심이다. 시각적인 연출은 이 메시지를 보여주는 도구로만 쓴다.

## 기반과 추가 범위
기반은 `github.com/noise-lab/vcaml`(IMC'23)이다. fork해서 직접 실행하고 수정하는 방식으로 진행한다. vcaml은 이미 pcap → LSTATS/TSTATS feature → Random Forest 순서로 fps, bitrate, frame jitter, resolution을 추정하며, 데스크톱 환경에서 오프라인 배치로 동작한다.

**우리가 추가하는 것 (우선순위 순):**
1. **모바일 실시간 파이프라인**: PCAPdroid 스트림 → 슬라이딩 윈도우 추론 → WebSocket → 대시보드·오버레이 앱.
2. **모바일 측정 정확도 검증**: (a) 캡처 충실도 검증, (b) getStats 정답과 추정값 비교, (c) 원인 진단 정확도. 아래 3절 참고.
3. **QoE 점수, 판정, 원인 진단, 조치**: 0–100 점수, PASSED/FAILED, 원인(`bandwidth | delay_jitter | loss | weak_wifi | none`)과 신뢰도, 규칙 기반 조치 1줄.
4. **Flutter 오버레이 앱 (P0)**: S20에서 통화 앱 위에 뜨는 버블(`SYSTEM_ALERT_WINDOW`). 1.4절 참고.
5. **세 가지 입력 모드**: `Live`(폰 실시간), `Replay`(저장된 pcap 재생, 데모 fallback), `What-if`(녹화된 실제 pcap에 슬라이더로 손상 적용).
6. **앱 간 교차 테스트**: Meet, Kakao(음성/영상). Zoom은 시간이 남을 때만 한다.

## 절대 규칙
1. **확인하지 않은 것을 사실처럼 쓰지 않는다.** repo 구조, 명령어, API, 도구 동작, 라이선스는 실제로 열어 보거나 실행해서 확인한다. 확인하지 못했으면 "미확인"이라고 쓰고 나에게 묻는다.
2. Kakao와 Zoom에는 정답 지표가 없다. 결과에 항상 `validated: false`와 "모델 추정값" 표시를 붙인다. "QoE를 측정했다"고 쓰지 않는다.
3. What-if는 **trace 기반 에뮬레이션**이므로 송신 측 혼잡 제어 반응을 반영하지 않는다. 이 점을 UI와 README에 명시한다.
4. **내 폰과 내 노트북 자신의 트래픽만** 캡처한다. 다른 사람의 트래픽을 캡처하거나 Wi-Fi를 스니핑하는 코드는 만들지 않는다.
   - 오버레이 앱 자신의 트래픽은 PCAPdroid `app_filter`로 측정 대상에서 뺀다.
5. 마일스톤마다 테스트와 빌드를 실행하고 결과를 요약한 뒤, 승인을 받고 다음 단계로 넘어간다. 파일을 삭제하거나 덮어쓰기 전에는 먼저 알린다. 의존성을 추가할 때는 이유를 한 줄로 적는다.
6. 원인 진단은 **트래픽 기반 추정**이다. UI에 `confidence`를 함께 표시하고, "확정 진단"처럼 쓰지 않는다. (`weak_wifi`만 폰 RSSI를 근거로 쓴다.)

## 1. 아키텍처 (계획 단계에서 검증한 뒤 확정)
```
[Galaxy S20: Kakao/Zoom/Meet 통화] ─ PCAPdroid ─(USB/adb 또는 LAN)→ 노트북
   pcap 스트림 | 저장 파일
   → impair.py (What-if 모드일 때만; 순수 함수, seed 고정)
   → features.py (vcaml LSTATS/TSTATS 재사용, 슬라이딩 윈도우)
   → estimator.py (vcaml RF) → qoe.py → verdict / diagnosis / action
   → FastAPI WebSocket ─┬→ React 대시보드 (노트북, 분석·발표 화면)
                        └→ Flutter 오버레이 버블 (S20, 통화 중 표시)
```
- 백엔드는 `server/`에 두고 uv로 관리한다. vcaml 코드는 가능한 한 import해서 재사용한다.
  - vcaml은 fork `sungmin-c/vcaml`(브랜치 `mcqm`)을 `vcaml/` submodule로 둔다.
  - 원본에 LICENSE 파일이 없으므로 코드를 복사하지 않고 submodule로만 참조한다.
- **모든 추론은 노트북에서 한다.** 대시보드와 오버레이 앱은 같은 SCHEMA를 구독하는 표시 전용 클라이언트다.
- 프론트엔드는 React + TypeScript(Vite), Tailwind, Chart.js를 쓴다. 로직은 `src/core/`에 순수 함수로 두고, 컴포넌트는 렌더링만 담당한다.
- **정적 데모 빌드**: 대표 시나리오의 결과를 JSON으로 미리 계산해 두어 백엔드 없이도 재생할 수 있게 한다.

WebSocket 메시지 스키마:
```json
{"ts": 1730000000.0, "mode": "live", "app": "kakao_video", "window_s": 1.0,
 "est": {"fps": 24.1, "bitrate_kbps": 850, "frame_jitter_ms": 12.3, "height": 360},
 "truth": null,
 "impair": {"loss_pct": 0, "delay_ms": 0, "jitter_ms": 0, "bw_kbps": null},
 "qoe": 71.5, "verdict": "passed", "advice": null, "validated": false}
```
`truth`에는 정답(getStats)이 있을 때만 같은 필드 구조로 값을 채운다. **M1에서 이 스키마로 더미 스트림 서버를 먼저 만든다.** 웹 담당 팀원이 백엔드 완성을 기다리지 않고 바로 작업을 시작할 수 있게 하기 위해서다.
- 정식 계약은 `docs/SCHEMA.md`와 `docs/schema/sample.jsonl`이다.
- v1.1 초안(팀원 확인 대기)은 tick에 `diagnosis {cause, confidence}`와 `action {code, text}`를 추가한다. 또 오버레이 앱이 Wi-Fi RSSI를 보내는 client→server `device` 메시지를 추가한다.

### 1.4 Flutter 오버레이 앱 (P0, 담당 Sungmin)
- **형태**: S20에서 통화 앱(Kakao·Meet) 위에 뜨는 버블이다(`SYSTEM_ALERT_WINDOW`).
- **표시**: 상태 색(passed/failed), QoE 점수, 원인 1줄(`diagnosis`), 조치 1줄(`action.text`).
- **[조치] 버튼**: `action.code`에 맞는 Android 설정 패널을 연다(Wi-Fi 패널 또는 인터넷 연결 패널).
- **입력**: SCHEMA WebSocket을 구독한다. 노트북 연결 경로는 LAN 또는 USB `adb reverse` 중 M0에서 정한다.
- **송신**: 1초마다 Wi-Fi RSSI를 `device` 메시지로 보낸다. 이 값은 `weak_wifi` 판정 근거가 된다.
- **패키지**: 오버레이 패키지명·버전과 RSSI 권한은 **M0에서 실제로 확인해 기록**한다. 지금은 미확인이다.
- **트래픽 분리**: 앱 트래픽은 PCAPdroid `app_filter`로 측정에서 제외한다. 제외되는지는 M0에서 확인한다.
- **디렉토리**: `overlay/`(Flutter 프로젝트). 테스트는 `flutter test`로 메시지 파싱과 상태 색·문구 매핑을 검사한다.

## 2. 데모 구성 (발표 임팩트와 측정 정확도를 동시에 보여주기)
- 화면 배치: 왼쪽에는 **scrcpy로 미러링한 폰 화면**(실제 Kakao 통화와 그 위의 오버레이 버블), 오른쪽에는 대시보드를 둔다. 둘을 나란히 놓아 "폰에서 체감하는 품질 저하", "버블의 원인·조치", "대시보드 추정값 변화"가 동시에 보이게 한다.
- **실시간 손상 주입 (M0에서 검증 필요)**: 노트북은 igc_user Wi-Fi에 연결하고, 같은 Wi-Fi 어댑터로 Windows 모바일 핫스팟을 켠다(설정에 토글이 있는 것은 확인했다). 폰을 이 핫스팟에 연결한 뒤, 노트북에서 WinDivert 기반 도구(예: Clumsy)로 중계되는 트래픽에 손실과 지연을 건다. 아래 항목은 **아직 검증하지 않았다**.
  - Wi-Fi→Wi-Fi 공유가 실제로 동작하는지, 그리고 그때의 처리량과 지연. 어댑터 하나로 수신과 송신을 동시에 하므로 성능이 떨어질 수 있다. **손상을 걸지 않은 baseline부터 반드시 측정한다.**
  - Clumsy가 중계(forward) 트래픽에도 적용되는지. 문서에는 언급이 없어 미확인이다.
    - Clumsy 0.3에는 lag, drop, throttle, duplicate, out-of-order, tamper, **bandwidth** 모듈이 있다. bandwidth는 0.3 릴리스 노트와 소스 `bandwidth.c`로 확인했다.
  - **Plan B**: gnirehtet(USB 역테더링). 폰 트래픽이 노트북 프로세스를 거치므로 손상 도구가 적용될 가능성이 높다. 단점은 두 가지다. 첫째, gnirehtet도 Android VPN 슬롯을 쓰기 때문에 **PCAPdroid와 동시에 쓸 수 없다**. 따라서 캡처는 노트북에서만 할 수 있다. 둘째, 중계 과정에서 패킷 타이밍이 왜곡된다.
  - **Plan C**: What-if 모드로 대체한다.
- 대시보드 기능: PASSED/FAILED 배지, QoE 및 추정 지표 게이지, 임계선이 있는 시계열 차트(약 30 tick), 모드 선택, 앱 선택, `truth`가 있을 때 추정값과 정답을 겹쳐 그린 차트, 경고 배지("추정값", "에뮬레이션"), 권고 영역, What-if 슬라이더 패널(Loss 0–20 %, Delay 0–300 ms, Jitter 0–100 ms, Bandwidth 제한 없음 또는 100–5000 kbps, 임계값 50–90, Live Noise, Reset). 반응형으로 만들고, 레이아웃이 움직이지 않게 하며, 접근성을 고려한다.

## 3. 측정 정확도 검증 (이번 버전의 핵심 추가 사항)
1. **캡처 충실도**: PCAPdroid는 VPN(tun) 방식으로 캡처하므로 타임스탬프와 패킷 크기가 실제 유선 구간과 다를 수 있다. 동일한 통화를 (a) 폰의 PCAPdroid와 (b) 노트북 핫스팟 인터페이스의 Wireshark/tshark로 동시에 캡처하고, 패킷 수·크기 분포·IAT 분포·추정 결과를 비교한다. 차이가 있으면 그 크기를 수치로 보고한다.
2. **정답 대비 정확도**: 폰 Chrome에서 Meet 통화를 하는 동안, USB 디버깅으로 노트북 DevTools(chrome://inspect)에 연결해 getStats를 1초 간격으로 수집하는 방법을 조사하고 구현한다. 가능하다면 스니펫을 주입하거나 webrtc-internals를 덤프하는 방식으로 한다. **먼저 가능 여부를 보고한다.** 정답을 얻으면 fps·bitrate의 MAE, ±2 fps 정확도, Normal/Degraded 판정의 Precision·Recall·F1·Confusion Matrix를 계산한다.
3. **일반화**: vcaml 데스크톱 데이터로 학습한 모델과, 폰에서 수집한 Meet 데이터로 재학습(또는 보정)한 모델의 성능을 비교한다.
4. **원인 진단 정확도**: Clumsy로 주입한 손상 종류를 정답 라벨로 쓴다.
   - 라벨 매핑: drop → `loss`, lag(+jitter) → `delay_jitter`, bandwidth → `bandwidth`, 손상 없음 → `none`.
   - 지표: 클래스별 Precision·Recall, Confusion Matrix, 판정 지연(손상 시작부터 첫 정답 판정까지 걸린 초).
   - `weak_wifi`는 Clumsy로 주입할 수 없다. 폰을 AP에서 멀리 옮기면서 RSSI와 함께 기록하는 정성 확인으로만 다룬다.
5. 앱 간 비교: 같은 손상 조건에서 Meet와 Kakao의 추정·진단 결과를 비교한다. 정답이 없으므로 "정성 비교"로 표기한다. Zoom은 시간이 남을 때만 한다.
6. 한계: 정답 부재, 표본 수, 에뮬레이션과 캡처 방식의 한계, 진단 라벨이 인위적 손상이라는 점을 그대로 적는다.

## 4. What-if 손상 함수 (`impair.py`)
- 손실: Bernoulli 또는 Gilbert-Elliott(버스트) 모델로 패킷을 제거한다.
- 지연·jitter: 타임스탬프를 이동시킨다. 순서 뒤바뀜을 어떻게 처리할지 계획 단계에서 제안한다.
- 대역폭: 토큰 버킷으로 초과 패킷을 지연시키거나 제거한다.
- seed를 고정해 재현 가능하게 한다. 1 tick 안에 손상 적용 → feature 추출 → RF 추론이 끝나는지 성능을 확인한다.

## 5. QoE 점수
- **ITU-T G.1070 계열을 참고한** 파라메트릭 모델로 만든다. 입력은 추정 fps, bitrate, frame jitter, resolution이고, 손실·지연은 페널티로 반영한다. 모든 계수에 근거를 주석으로 단다. 표준을 준수한다고 주장하지 않고 "참고했다"고만 쓴다.
- 테스트: 손실·지연이 늘면 점수가 올라가지 않는지(단조성), 경계값, 0–100 범위를 확인한다.

## 6. 마일스톤
| # | 기한 | 내용 |
|---|---|---|
| M0 | 10/19 (폰 불필요 항목), 10/23 (통화 필요 항목) | 검증 스파이크: vcaml 학습 재현(`uv run python vcaml/train.py`), Kakao pcap 분석(UDP/TCP, 패킷 크기), PCAPdroid pcap 파싱(linktype), PCAPdroid → 노트북 스트리밍, 핫스팟 + 손상 도구, scrcpy, 폰 Chrome getStats 수집 가능 여부, **Android 13 Flutter 오버레이 동작(10/18)**, **PCAPdroid `app_filter`로 오버레이 트래픽 제외**. **결과를 보고한 뒤 범위를 재조정한다** |
| M1 | 10/26 | 더미 스트림 + 대시보드 뼈대(웹 담당) / vcaml 재현 수치 / SCHEMA v1.1 확정 |
| M2 | 11/6 | Replay 실시간 추론 + QoE + 판정 + 진단 v0 / Meet 정답 수집 파이프라인 |
| M3 | 11/13 | Live 모드 + 캡처 충실도 실험 + 정답 대비 정확도 |
| M4 | 11/20 | What-if 모드 + Meet·Kakao 교차 실험 + 원인 진단 정확도 + 결과표 |
| M5 = Freeze | 11/24 | 테스트, README, 정적 데모 빌드, 녹화본, 데모 스크립트, **기능 동결** |
| 리허설 | 11/26–12/1 | 리허설 2회 (**발표장과 같은 igc_user 환경에서**: 핫스팟, 통화, 손상 주입, scrcpy, 오버레이를 모두 점검. 실패 시 전환할 Replay와 녹화본도 점검) |
| Demo | 12/2 | Final Demo |

**Flutter 오버레이 마일스톤**
| 기한 | 내용 |
|---|---|
| 10/18 | Android 13 오버레이 권한·표시 확인 (M0) |
| 11/8 | 더미 스트림 연동 |
| 11/15 | Live 연동 |
| 11/20 | 표시 문구 확정 |

외부 일정: Midterm 1(10/21)과 Midterm 2(11/25)는 프로젝트와 무관한 시험이다. 해당 주간은 작업량만 줄인다.

## 7. 발표 구성 (12분)
| 시간 | 내용 |
|---|---|
| 0–2분 | 문제 제기: 앱 내부 정보 없이 모바일 통화 품질을 알 수 있는가 |
| 2–4분 | 방법: vcaml 원리 + 우리가 추가한 것 3가지 |
| 4–9분 | **라이브 데모**: 정상 통화 → 손상 주입 → 폰 화면, 오버레이 버블(원인·조치), 대시보드가 함께 변화 → [조치] 버튼 → What-if 슬라이더 |
| 9–11분 | 결과: 캡처 충실도, 정답 대비 정확도(MAE, F1), 원인 진단 정확도, Meet·Kakao 비교 |
| 11–12분 | 한계와 향후 과제 |

라이브 데모가 실패하면 즉시 Replay와 녹화본으로 전환한다.

## 8. 테스트
- pytest: impair(손실률 통계, seed 재현성), features(알려진 입력에 대한 기대값), qoe(단조성, 경계값), diagnosis(손상 종류별 규칙 판정), SCHEMA 계약(`tests/test_schema_contract.py`).
- Vitest: 프론트엔드 `core/`.
- `flutter test`: 오버레이 앱의 메시지 파싱, 상태 색·문구 매핑.

## 9. 산출물
- `README.md` (한국어 + 영어 요약): 맨 위에 **"vcaml 대비 바꾼 것/추가한 것" 3줄**을 두고, 이어서 아키텍처 다이어그램, 공식, 재현 방법, 정확도 결과표, 한계를 적는다.
- 디렉토리: `capture/`, `server/`, `dashboard/`, `overlay/`(Flutter), `scripts/`, `docs/`, `tests/`, `vcaml/`(submodule).
- 오버레이 앱 APK(debug 빌드 가능).
- 데모 스크립트와 발표 구성안, 최종 보고서 초안(한국어).

## 부록: 초파리 connectome 패널 (기본 범위에서 제외)
M4가 예정보다 일찍 끝나고 나 또는 팀원이 명시적으로 요청한 경우에만, 동결(11/24) 전까지의 범위에서 착수한다. 착수하면 QoE를 보상 신호로 삼아 DAN→KC→MBON 회로가 반응하는 2D 패널을 만들고, **"예시적 은유이며 생물물리 모델이 아님"**을 명시한다. 데이터는 오프라인 스크립트로 추출한 정적 JSON(노드 수백 개 이하)만 쓰고, 추출에 실패하면 "schematic"으로 표기한다. 출처와 라이선스를 표기한다.

## 시작
위 내용을 3줄로 요약하고, Plan mode에서 질문(최대 5개)과 계획을 제시한다.