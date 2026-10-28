# W3 Meet 30통화 + Teams 파일럿·15통화 수집 절차 (2026-10-16, v8 보강 10/28, Claude) — 실측: Sungmin

> 목적: (1) 모델 재학습용 추정·정답 쌍(P1: 기존 모델 fps MAE 9.09 → 재학습 필요), (2) 원인 진단 평가용 라벨 구간
> `none | loss | bandwidth | device_cpu`. 근거: PROGRESS W1 P1–P3, PROJECT_SPEC §2–3. 명령은 모두 **repo 루트, PowerShell**.
> 세 번에 나눠 한 번에 10통화씩 한다(아래 "세션 배정"). 각 통화는 위에서 아래로 체크하며 따라 한다.
> **v8 (10/28)**: 측정 앱은 Meet(W3, 0–7절) → Teams(파일럿 T9 = 8절, W4 15통화 = 9절) 두 개뿐이다(Zoom 제외, SPEC v8). 둘 다 이 Windows 노트북의 Chrome 웹 클라이언트로 받는다. recovery 구간(300–380초)은 **회복 판정 평가**(SPEC §5-1)에도 쓰므로 해제 시각 `$off`를 정확히 기록한다.

## 0. 처음 한 번만: 사전 점검 (S0, 약 40분) — 통과 전에는 본 수집 금지
| # | 확인 | 방법 | 통과 기준 | 실패하면 |
|---|---|---|---|---|
| S0-1 | **Clumsy가 버린 수신 패킷이 tshark에 보이는가** | 시험 통화 중 Clumsy `udp and inbound` Drop 10%를 60초. 그동안 캡처 + webrtc dump. `compare` 후 tshark 패킷 수 감소와 dump `packetsLost` 증가를 비교 | tshark 패킷 수가 dump 수신 패킷 수와 같이 줄어든다 | **[추정] Npcap은 WinDivert보다 아래(NDIS)에서 잡으므로 버리기 전 패킷이 보일 수 있다.** 그러면 캡처에는 손실 흔적이 없다 → loss·bandwidth 조건 수집 중단, HANDOFF "사용자에게"에 기록 후 대안 결정 (CPU·none 조건은 계속 가능) |
| S0-2 | clumsy2 대역폭 제한 동작 | clumsy2 설치(Q16 승인됨, 되돌리기 아래) → 1000 kbps inbound에서 speedtest 다운로드 | ≤ 1100 kbps | 대역폭 조건 8통화를 표 아래 "대체 배정"으로 |
| S0-3 | 리허설 1통화 | 아래 1–6절을 그대로 한 번 | `compare`의 `n_seconds` ≥ 300, lag scan 최소가 0초, **수신 영상 패킷의 `rtp.seq` 비율 ≥ 0.99**(P2P 전환 후 구간 포함) | 원인 기록 후 재시도. RTP 비율이 낮으면 `31243bf`(`--enable-heuristic rtp_udp`)가 안 듣는 것 → HANDOFF |
| S0-4 | `os.csv`에 `call_core_pct` 열 | T8b 1번 구현 후 S0-3 결과 확인 | 열이 있고 C2 조건에서 ≥ 85 근처 | C 조건 수집 보류(진단 평가 불가), N0·L·B만 |

clumsy2 되돌리기: 프로그램 종료 → 남으면 관리자 PowerShell `sc stop WinDivert` → 설치 폴더 삭제. 설치 경로·버전은 `docs/SETUP.local.md`에 기록.

## 1. 조건표 (30통화, 통화 1개 = 조건 1개)
| 코드 | 라벨 | 주입 (손상 구간 90초) | 통화 수 |
|---|---|---|---|
| N0 | none | 없음 (끝까지 정상) | 6 |
| L3 | loss | Clumsy Drop **3%**, 필터 `udp and inbound` | 4 |
| L10 | loss | Clumsy Drop **10%**, 같은 필터 | 4 |
| B1000 | bandwidth | clumsy2 대역폭 **1000 kbps** inbound | 4 |
| B300 | bandwidth | clumsy2 대역폭 **300 kbps** inbound | 4 |
| C2 | device_cpu | Chrome **2코어 고정** (`cpu_load.py --pin 2 --levels 0`) | 4 |
| C2L | device_cpu | 2코어 고정 + 부하 80% (`--pin 2 --levels 80`) | 4 |
- 대체 배정: S0-2 실패 → B1000·B300 8통화를 L5(Drop 5%) 4 + C2L 4로. S0-1 실패 → L·B 16통화를 보류하고 N0·C만 먼저.
- 고정 조건 (모든 통화 같게, 바뀌면 log `note`에): **충전기 연결**(P2·P3는 배터리 상태라 결과가 달랐다), 절전 끔, Chrome에는 Meet 탭 + webrtc-internals 탭만, 다른 앱 종료(여유 RAM 적음), S20 거치대 고정·같은 장면, 노트북 위치 고정, 같은 Wi-Fi.
- 왜 코어 제한인가: P2에서 busy loop(CPU 89%)는 수신 품질을 거의 못 떨어뜨렸고, 2코어 제한이 freeze 36회·송신 fps 3.5를 만들었다.

### 세션 배정 (조건이 한 세션에 몰리지 않게 섞음. 시간대 효과 분리)
| 세션 | 통화 ID → 조건 |
|---|---|
| A | 01 N0, 02 L3, 03 C2, 04 B1000, 05 L10, 06 C2L, 07 B300, 08 N0, 09 L3, 10 C2 |
| B | 11 B1000, 12 N0, 13 L10, 14 C2L, 15 B300, 16 L3, 17 C2, 18 N0, 19 B1000, 20 L10 |
| C | 21 C2L, 22 B300, 23 N0, 24 L3, 25 C2, 26 B1000, 27 L10, 28 C2L, 29 B300, 30 N0 |

## 2. 한 통화 시간표 (캡처 시작 = t0, 총 380초)
| t (초) | 구간 | 하는 일 |
|---|---|---|
| 0–150 | warm | 손대지 않음. Meet가 PeerConnection을 갈아타는 구간(P3에서 150초 대기 사용) |
| 150–210 | baseline | 정상. judge·diagnosis 기준선이 여기서 만들어짐 |
| **210–300** | **impair** | 조건 주입 (N0은 아무것도 안 함) |
| 300–380 | recovery | 주입 해제 후 회복 (= 실험상의 "조치". 회복 판정 지연을 여기서 잰다) |
- 한 통화 소요: 준비 2분 + 캡처 6분 20초 + dump·비교·기록 2분 ≈ **10–11분**. 10통화 세션 ≈ **1시간 50분** (쉬는 시간 별도). 30통화 ≈ 5.5시간.

## 3. 세션 시작 때 한 번
```powershell
New-Item -ItemType Directory -Force data\w3 | Out-Null
$ip = (Get-NetIPAddress -InterfaceAlias Wi-Fi -AddressFamily IPv4).IPAddress; $ip   # 노트북 IP (--dst)
uv run python scripts/pilot_live.py ifaces    # Wi-Fi 인터페이스 이름 확인 (기본 --iface Wi-Fi)
if (-not (Test-Path data\w3\log.csv)) { "call_id,date,cond,t0,impair_on,impair_off,pc_id,charger,n_seconds,fps_mae,status,note" | Set-Content data\w3\log.csv }
```

## 4. 통화 1개 체크리스트 (`$id`만 바꿔 반복)
```powershell
$id = "01"; $cond = "N0"     # 세션 배정표에서
```
- [ ] Chrome 새 탭에서 `chrome://webrtc-internals`를 **통화 참가 전에** 연다 (열려 있을 때만 통계가 쌓인다)
- [ ] 노트북 Chrome으로 Meet 참가 → S20 Meet 앱 참가 → 양쪽 카메라 켬, S20 영상이 노트북에 보이는지 확인
- [ ] 캡처 시작 (380초 후 자동 종료). 새 PowerShell 창에서:
  ```powershell
  $t0 = [DateTimeOffset]::Now.ToUnixTimeSeconds(); $t0
  uv run --with psutil python scripts/pilot_live.py capture --name w3_$id --dst $ip --duration 380
  ```
  터미널에 1초마다 `fps … kbps …` 줄이 나와야 한다. 10초 안에 안 나오면 → 7절 F1.
- [ ] t=150 무렵 webrtc-internals에서 **영상 통계가 갱신되는 PC**(inbound-rtp video 그래프가 움직이는 쪽)의 ID를 적어 둔다 → log `pc_id`
- [ ] **t=210 손상 시작** (`$t0 + 210`이 되면). 시작 직후 시각 기록:
  ```powershell
  $on = [DateTimeOffset]::Now.ToUnixTimeSeconds()
  ```
  - L3/L10/B1000/B300: Clumsy(관리자)에서 필터 `udp and inbound`, 해당 모듈·값 → Start
  - C2: `uv run --with psutil python scripts/cpu_load.py --name w3_$id --pin 2 --levels 0 --step 90` (90초 뒤 스스로 끝나고 affinity 복원. 시작 시각은 `data/pilot/w3_${id}_load.csv`에도 남음)
  - C2L: `uv run --with psutil python scripts/cpu_load.py --name w3_$id --pin 2 --levels 80 --step 90`
  - N0: 아무것도 안 함 (그래도 `$on`은 기록)
- [ ] **t=300 손상 해제**: Clumsy Stop (cpu_load는 자동 종료). `$off = [DateTimeOffset]::Now.ToUnixTimeSeconds()`
- [ ] 캡처가 끝나면(380초) webrtc-internals → "Create a WebRTC-Internals dump" → **Download** → `data\w3\w3_${id}_dump.json`으로 저장. **dump를 받기 전에 탭을 닫거나 새로고침하지 않는다**
- [ ] 통화 종료 (양쪽)
- [ ] 바로 비교 (정답 PC 자동 선택 = 캡처 구간 fps>0인 초가 가장 많은 PC):
  ```powershell
  uv run python scripts/pilot_live.py compare --name w3_$id --dump data\w3\w3_${id}_dump.json
  ```
  출력의 `PC <id>: … 초` 줄들과 `n_seconds`, `fps_mae`, `lag_scan_fps_mae`를 본다.
- [ ] 기록 한 줄 (status: `ok` | `redo` | `no_truth` | `drop`):
  ```powershell
  "$id,$(Get-Date -Format yyyy-MM-dd),$cond,$t0,$on,$off,<pc_id>,yes,<n_seconds>,<fps_mae>,ok," | Add-Content data\w3\log.csv
  ```
- [ ] Clumsy 창 닫힘·Chrome affinity 정상(작업 관리자 → 세부 정보 → chrome.exe → 선호도 = 전체 코어) 확인 후 다음 통화

결과 파일 (통화마다): `data/pilot/w3_<id>_{pkts,est,os,cmp}.csv`, `w3_<id>_summary.json`, C 조건이면 `_load.csv`, `data/w3/w3_<id>_dump.json`, `data/w3/log.csv` 한 줄. 모두 git 제외.

## 5. PeerConnection 갈아타기 처리
- Meet는 통화 중 PC를 바꾼다(P1: 540p 800 kbps → 720p 2 Mbps). `compare`는 PC마다 따로 읽어 캡처 구간 fps>0이 가장 많은 PC를 고른다.
- 그래서 **warm 150초**를 둔다: 전환이 손상 전에 끝나게. `compare` 출력에서 두 PC가 모두 수십 초 이상이면 전환이 캡처 중에 있었다는 뜻.
- 판정:
  - 전환이 t < 210 (손상 전): 정상. `ok`
  - 전환이 손상·회복 구간(t ≥ 210) 안: 선택된 PC가 손상 구간을 덮으면 `ok` + `note=pc_switch_late`. 손상 구간이 다른 PC에 있으면 `redo`
  - 확인 방법: `w3_<id>_cmp.csv`의 `et`가 `$on`–`$off` 구간을 덮는지 (`n_seconds`만으로는 모름)
- dump는 PC 전체를 담으므로 나중에 초 단위로 PC를 합치는 파서를 만들 수 있다 → 원본 dump는 지우지 않는다.

## 6. 되돌리기 (세션 끝)
- Clumsy·clumsy2 종료 → 남으면 관리자 `sc stop WinDivert`
- Chrome 완전 종료 후 재실행 (affinity가 남았을 때의 확실한 복원, P2 사고 기록)
- 절전 설정 원래대로

## 7. 실패 시 기록 (log `status`·`note`)
| # | 증상 | 조치 | status |
|---|---|---|---|
| F1 | 캡처 줄이 안 나옴 | `ifaces`로 인터페이스 확인, `$ip` 재확인(Wi-Fi 재연결 시 바뀜), Meet가 영상 중인지 | 고치고 처음부터 → `redo` |
| F2 | dump를 못 받음(탭 닫음 등) | 추정만 있음. 진단 평가(라벨=조건)에는 쓸 수 있고 재학습에는 못 씀 | `no_truth` |
| F3 | 손상 구간이 다른 PC (5절) | 같은 조건으로 다시 | `redo` |
| F4 | S20 화면 꺼짐·영상 멈춤·통화 끊김 | 다시 | `drop` + 이유 |
| F5 | Clumsy 시작 실패·관리자 권한 없음 | 관리자 실행 후 다시 | `redo` |
| F6 | cpu_load 후 Chrome 선호도가 2코어로 남음 | Chrome 완전 재시작 | 그 통화는 `ok`, `note=affinity_restore_manual` |
| F7 | `compare` lag scan 최소가 0이 아님 | 시계 어긋남 의심. 그대로 기록 | `ok` + `note=lag<값>` |
| F8 | Meet 경로가 P2P가 아님(서버 경유 의심: dst 포트 3478/19305 등). P2-1 원자료는 Google relay(`142.250.82.215:3478`)로 시작해 통화 중 P2P(같은 LAN)로 바뀌었다 | 기록만. 전환 시각이 210초 뒤면 `note=path_switch_late` | `ok` + `note=relay?` |
- `redo`·`drop`은 같은 조건으로 추가 통화. 조건별 `ok` 수가 표의 수에 도달할 때까지.
- 세션이 끝나면 `log.csv` 요약(조건별 ok 수, 실패 종류)을 HANDOFF 기록에 한 줄로.

## 8. Teams 파일럿 T9 (1통화, 약 40분) — 통과 전에는 9절 수집 금지
노트북 Chrome **Teams 웹**(학교 계정 `teams.microsoft.com` 또는 개인 `teams.live.com`, 어느 쪽이 되는지 미확인) ↔ S20 **Teams 앱**. 통화 1건을 2·4절 시간표 그대로(N0, 380초) 진행하되 이름은 `t9_pilot`, 저장은 `data\w4\`. 3절(`$ip`)을 먼저 한다.
```powershell
New-Item -ItemType Directory -Force data\w4 | Out-Null
uv run --with psutil python scripts/pilot_live.py capture --name t9_pilot --dst $ip --duration 380
uv run python scripts/pilot_live.py compare --name t9_pilot --dump data\w4\t9_pilot_dump.json
```
| # | 확인 | 방법 | 통과 기준 | 실패하면 |
|---|---|---|---|---|
| T9-1 | 웹 ↔ S20 앱 통화가 되고 S20 영상이 노트북에 보이는가 | 같은 계정 종류로 회의 링크 참가 | 380초 동안 영상 유지 | 계정 종류 바꿔 재시도 → 그래도 안 되면 Teams 제외, PROGRESS·HANDOFF 기록 |
| T9-2 | **dump에 inbound-rtp video 통계**가 있는가 | 통화 참가 **전** `chrome://webrtc-internals` 열기 → 끝나고 dump 저장 | `framesPerSecond`·`frameHeight`·`bytesReceived`가 초 단위로 있음 | 정답 없음 → Teams는 추정만 `validated:false`, 9절은 진단 평가용으로만(재학습·MAE 제외) |
| T9-3 | 패킷 경로 | `t9_pilot_pkts.csv` 상위 flow의 상대 IP·포트 기록 | 기록만 (P2P / relay) | — (참고 [가정]: Teams relay는 UDP 3478–3481) |
| T9-4 | RTP 해석 | S0-3과 같은 `rtp.seq` 비율 | ≥ 0.99 | 낮으면 loss 진단이 IP/UDP 규칙뿐(재현율 낮음) → 결과에 한계로 적고 수집은 진행 |
| T9-5 | `compare` 동작 | 출력 `PC …: … 초`, `n_seconds`, `lag_scan_fps_mae` | `n_seconds` ≥ 300, lag 최소 0초 | PC 갈아타기 시각 기록(5절). 150초 안에 안 끝나면 9절 warm 구간을 늘린다 |
- 결과는 PROGRESS Q25 아래와 HANDOFF T9에 "정답 가능 / 불가 + 경로 + RTP 비율" 한 줄. `fps_mae`는 Meet 모델 기준이라 참고값.
- 서버 `--app teams`(T9 코드 부분, Codex)는 파일럿 결과와 무관하게 추가한다.

## 9. Teams 15통화 수집 (W4, T9 통과 후)
2–7절을 그대로 따른다. 다른 점만:
- 통화 ID `t01`–`t15`(Meet `01`–`30`과 겹치지 않게), 캡처 이름 `w4_$id`, dump `data\w4\w4_${id}_dump.json`, 로그 `data\w4\log.csv`(3절 헤더와 같은 형식).
- 4절 체크리스트의 "Meet 참가"는 "Teams 웹 참가 ↔ S20 Teams 앱"으로. Chrome에는 Teams 탭 + webrtc-internals 탭만.
- S0(0절)는 Meet에서 통과했으면 다시 하지 않는다. Clumsy·clumsy2·cpu_load 명령은 같다.

| 코드 | 라벨 | 주입 (1절과 같음) | 통화 수 |
|---|---|---|---|
| N0 | none | 없음 | 3 |
| L3 | loss | Drop 3% | 2 |
| L10 | loss | Drop 10% | 2 |
| B1000 | bandwidth | clumsy2 1000 kbps | 2 |
| B300 | bandwidth | clumsy2 300 kbps | 2 |
| C2 | device_cpu | 2코어 고정 | 2 |
| C2L | device_cpu | 2코어 고정 + 80% | 2 |
- 대체 배정은 1절과 같다(S0-1·S0-2 결과를 따른다).

| 세션 | 통화 ID → 조건 |
|---|---|
| D | t01 N0, t02 L3, t03 C2, t04 B1000, t05 L10, t06 C2L, t07 B300, t08 N0 |
| E | t09 L3, t10 C2, t11 B1000, t12 L10, t13 C2L, t14 B300, t15 N0 |
- 시간: 8통화 ≈ 1.5시간, 7통화 ≈ 1.3시간.
- **줄이는 순서** (시간 부족 시 Teams부터, SPEC v8): 15 → 세션 D만(조건당 1통화 + N0 2) → 0(T9 파일럿 결과만 보고).
- 추가 실패 코드: **F9** Teams 웹이 영상을 받지 못함·회의 참가 실패 → 계정·브라우저 재시작 후 다시, 같은 증상 3회면 세션 중단 후 HANDOFF 기록. status `drop`.

## 미확인 / [가정]
- S0-1(캡처에 손실이 보이는지)이 가장 큰 위험. 실패하면 loss·bandwidth 진단 평가 설계를 다시 정해야 한다.
- clumsy2 UI의 대역폭 모듈 이름·단위 미확인. Drop 3%/10%, 1000/300 kbps, 90초 구간 길이는 [가정] — S0-3 리허설 후 조정 가능.
- `--duration 380`은 tshark `-a duration`이라 모델 로드 시간만큼 실제 캡처가 조금 짧을 수 있다(미확인).
