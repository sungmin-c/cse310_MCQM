# PROGRESS — MCQM
> 마일스톤마다 완료/미완료/검증 결과를 갱신한다. 상태: ⬜ 예정 · 🟡 진행 · ✅ 완료 · ❌ 실패/보류
> ☎ = 팀원 iPhone 통화 세션 필요. 원자료는 `data/m0/` 등 `data/` 아래 (git 제외)

## 결정 사항 / 대기
| # | 질문 | 답 (10/12) | 상태 |
|---|---|---|---|
| Q1 | Midterm 1(10/21)·2(11/25)의 성격 | 시험. 프로젝트 산출물과 무관 → 시험 주간은 작업량만 줄임 | ✅ |
| Q2 | vcaml public fork | 승인. `sungmin-c/vcaml` 생성, `mcqm` 브랜치 push, submodule URL 교체 완료 | ✅ |
| Q3 | 팀원 GitHub 계정명, `main` 보호 | 계정명은 추후 전달. 그때까지 collaborator·브랜치 보호 보류 | ⏳ |
| Q4 | ☎ 세션 | 다음 주 중 (날짜 미정). M0 #3–9는 그때 실행. Kakao·Zoom 계정 준비 여부는 미확인 | ⏳ |
| Q5 | Flutter 앱(APK) | **P0 확정, 담당 Sungmin.** 통화 앱 위 오버레이 버블. 추론은 노트북. 상세는 PROJECT_SPEC §1.4 | ✅ |
| Q6 | `weak_wifi` 판정 근거 | 오버레이 앱이 RSSI를 `device` 메시지로 송신(SCHEMA v1.1 초안). 진단 정확도 실험은 Clumsy 4종(`bandwidth`/`delay_jitter`/`loss`/`none`), `weak_wifi`는 정성 확인 | ✅ |
| Q7 | 일정 | 발표 12/2, 동결 11/24. M2 11/6, M3 11/13, M4 11/20. M0은 10/19(폰 불필요)·10/23(통화) 분할 | ✅ |
| Q8 | SCHEMA v1.1 | 초안 작성 완료. **팀원 확인 대기** → M1(10/26)까지 확정 | ⏳ |

## 일정 (발표 12/2, 동결 11/24)
| 주 | 기간 | 외부 일정 | 마감 | 나 — ML·Python | 나 — Flutter 오버레이 | 팀원 — Web | ☎ 세션 | 상태 |
|---|---|---|---|---|---|---|---|---|
| W1 | 10/12–10/18 | | 오버레이 권한 10/18 | bootstrap ✅, M0 폰 불필요 항목(0, 1, 2, 6, 7, 10) | M0 (a): Android 13 오버레이·RSSI·설정 패널 확인 | uv·node 설치, `dashboard/` scaffold(Vite+TS+Tailwind+Chart.js+Vitest), SCHEMA v1·v1.1 리뷰, 더미 스트림 연결 | — | 🟡 |
| W2 | 10/19–10/25 | **Midterm 1 (10/21)** | M0 10/19 · 10/23 | M0 통화 항목(3, 4, 5, 8, 9, b), M0 보고·범위 재조정, vcaml 재현 수치 | — | WS client(`core/stream.ts`), `parseMessage`+Vitest(sample.jsonl), 배지·게이지·고정 레이아웃 | M0 세션 (학교 1 + 집 1) | ⬜ |
| W3 | 10/26–11/1 | | M1 10/26 | SCHEMA v1.1 확정·반영, Replay: pcap→윈도우→features→RF→`qoe.py`(+pytest)→FastAPI WS | 버블 UI (sample.jsonl 고정 데이터) | 시계열 차트(30 tick, 임계선), 모드·앱 선택, 경고 배지, 반응형 | — | ⬜ |
| W4 | 11/2–11/8 | | M2 11/6 · 오버레이 더미 11/8 | 진단 v0 `diagnosis.py`(+pytest), Meet 정답 수집 파이프라인, `impair.py`+pytest | 더미 스트림 연동, [조치] 버튼, RSSI 송신 | 정답 겹침 차트, 진단·조치 표시, fixture 재생 모드 | Meet 정답 수집 | ⬜ |
| W5 | 11/9–11/15 | | M3 11/13 · 오버레이 Live 11/15 | Live 모드(TCP exporter), 캡처 충실도, 정답 대비 정확도(MAE, ±2fps, P/R/F1, CM) | Live 연동 | What-if 슬라이더 → control 메시지, 접근성 | 충실도 실험 | ⬜ |
| W6 | 11/16–11/22 | Midterm 2 준비 | M4 11/20 · 문구 11/20 | What-if 연결, Meet·Kakao 교차 실험, **원인 진단 정확도 실험**, 일반화, 결과표, README 초안 | 표시 문구 확정, debug APK | 결과 화면, 정적 데모 빌드 | 교차·진단 실험 (11/16–11/18 집중) | ⬜ |
| W7 | 11/23–11/29 | **Midterm 2 (11/25)** | **Freeze 11/24** | M5: pytest 정리, 녹화본, 데모 스크립트 → 동결. 리허설 1 (igc_user, [가정] 11/27) | APK 최종 | 동결, 리허설 | 리허설 1 | ⬜ |
| W8 | 11/30–12/6 | | **Final Demo 12/2** | 리허설 2 ([가정] 12/1), 발표 | | 발표 | 리허설 2 | ⬜ |
| W9 | 12/7–12/12 | 종료 12/12 | | 최종 보고서 초안(한국어, [가정] 12/12까지) | | | — | ⬜ |

일정 리스크:
- **W6은 Sungmin의 부하가 가장 크다.** M4, Flutter 문구 확정, README가 겹친다. Zoom은 W6이 끝난 시점에 시간이 남을 때만 한다.
- 동결 다음 날이 Midterm 2이므로, M5 작업은 W6 안에 대부분 끝내야 한다.

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
| a | Android 13 Flutter 오버레이 (10/18) | debug APK로 S20에서 Kakao·Meet 통화 화면 위에 버블이 10분 동안 유지된다. **오버레이 패키지명·버전을 pub.dev와 `pubspec.lock`으로 실제 확인해 기록**한다. `SYSTEM_ALERT_WINDOW` 권한 요청 흐름을 확인한다. Wi-Fi RSSI를 읽을 수 있고 필요한 권한을 기록한다. Wi-Fi 패널·인터넷 연결 패널이 열린다. 노트북 WS 연결 경로(LAN 또는 `adb reverse`)를 정한다 | Flutter 3.41.4 stable 설치 확인 (10/12). 나머지 미확인 | ⬜ |
| b | `app_filter`로 오버레이 트래픽 제외 ☎ | Kakao 통화 중 `app_filter`=Kakao 패키지, 오버레이 WS 연결 상태로 2분 캡처한다. pcap에서 노트북 WS 포트(8000) 패킷 = **0개**이고, Kakao 패킷 수는 필터가 없을 때와 비슷하다 | | ⬜ |
| 0 | 도구 설치 (Wireshark+Npcap, scrcpy, PCAPdroid, Clumsy) | 버전 출력, `adb devices`에 S20 | 노트북에 tshark·scrcpy 없음 (10/12 확인) | ⬜ |
| 1 | vcaml 팀 repo 재현 | `pytest vcaml/tests` 50 passed + FPS×ip-udp-ml MAE 솔로(Meet 1.33/Teams 1.81/Webex 1.33) ±0.05 | 50 passed ✅. 학습(약 16분)은 여유 RAM 1.9GB라 보류 — Chrome 종료 후 실행 | 🟡 |
| 2 | 1 tick 추론 예산 | p95 < 200 ms, 모델 메모리 < 500 MB, 버전 경고 없음 | 솔로 `model_meet.pkl`(FPS cv_1): 로드 5.5s, +112MB, 경고 없음, 45 윈도우 p50 24.6 / **p95 74.7** / max 113.7 ms. 단일 지표 기준 — 4지표 동시는 미측정 | ✅ |
| 3 | PCAPdroid pcap 파싱 ☎ | linktype RAW(101), CSV `ip.*/udp.*` 채워짐, `readIpUdpFile` ≠ None | | ⬜ |
| 4 | Kakao 트래픽 분석 ☎ (Zoom은 여유 시) | UDP/TCP 비율, 상위 flow, 크기 분포(>306B), RTP 여부, ip-udp-ml 입력 조건 예/아니오 | | ⬜ |
| 5 | PCAPdroid → 노트북 스트리밍 ☎ | 10분 무단절, 수신 ≥ 99%, 지연 p95 < 500 ms | | ⬜ |
| 6 | 핫스팟 baseline (igc_user + 집) | A 직결 / B 핫스팟 / C 노트북에서 speedtest·ping을 측정한다(W1, 통화 불필요). 기준[가정]: B 다운·업 ≥ 5 Mbps, RTT 증가 ≤ 20 ms, 손실 ≤ 1%. B 경로로 2분 Meet 무끊김은 ☎ 세션 때 확인한다 | | ⬜ |
| 7 | Clumsy 중계 트래픽 적용 | Drop 10% → ping 손실 10±3%. Lag 100 → RTT +100±15 ms. **Bandwidth 500 kbps → speedtest ≤ 550 kbps**. 통화 중 화면 저하는 ☎ 세션 때 육안으로 확인한다. 세 모듈은 진단 정확도 실험의 라벨 소스다 | | ⬜ |
| 8 | scrcpy ☎ | ≥ 30 fps, PCAPdroid와 동시 동작, 통화 화면 검지 않음(FLAG_SECURE) | | ⬜ |
| 9 | 폰 Chrome getStats ☎ | 가능 여부 먼저 보고. 2분간 inbound video 지표 ≥ 95% 초 존재 | | ⬜ |
| 10 | 노트북 측 캡처 | `tshark -D`에 핫스팟 인터페이스, 폰 IP 필터로 캡처 | | ⬜ |

M0 설계 메모 (M2 `features.py`에 반영):
- 스트리밍 윈도우의 첫 IAT는 **직전 윈도우 마지막 패킷 기준**으로 계산해야 배치(vcaml)와 같다. 슬라이스를 그대로 넣으면 첫 IAT가 통화 시작 기준이 되어 커진다.
- vcaml 배치 윈도우는 "첫 패킷 + 1초 초과 시 새 윈도우"(가변 경계), 스트리밍은 고정 1초 격자 → 작은 차이 가능, M2에서 수치 비교.

## M1 — 더미 스트림 + 대시보드 뼈대 / vcaml 재현 수치 / SCHEMA v1.1 확정 (마감 10/26)
## M2 — Replay 실시간 추론 + QoE + 판정 + 진단 v0 / Meet 정답 수집 (마감 11/6)
## M3 — Live + 캡처 충실도 + 정답 대비 정확도 (마감 11/13)
## M4 — What-if + Meet·Kakao 교차 실험 + 원인 진단 정확도 + 결과표 (마감 11/20)
## M5 = Freeze — 테스트, README, 정적 데모, 녹화본, 데모 스크립트 (마감 11/24)

## Flutter 오버레이 (담당 Sungmin)
| 기한 | 내용 | 결과 | 상태 |
|---|---|---|---|
| 10/18 | Android 13 오버레이 권한·표시 확인 (= M0 a) | | ⬜ |
| 11/8 | 더미 스트림 연동 | | ⬜ |
| 11/15 | Live 연동 | | ⬜ |
| 11/20 | 표시 문구 확정 | | ⬜ |
