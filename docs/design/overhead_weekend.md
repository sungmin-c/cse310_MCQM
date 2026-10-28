# 모니터·위젯 오버헤드 실험 P5 (2026-10-28 계획, Claude) — 준비: Claude Code, 실측: Sungmin

> 질문: 모니터(tshark + 모델 + WS 서버)와 위젯(Chrome PiP)이 CPU·RAM을 나눠 쓰면서 **통화 QoE를 떨어뜨리는가**, 특히 **기기가 이미 포화됐을 때**.
> 배경: P3(PROGRESS W1)는 모니터 CPU 1.27%, 통화 지표 차이 없음. 그러나 ① 전체 CPU 23%(여유)에서만 측정 ② 위젯 미포함 ③ P2 코어 고정은 모니터를 빈 코어에서 돌게 해 경쟁을 숨김 ④ 배터리 상태 ⑤ 통화 1건. 이 실험은 ①–④를 메운다(⑤는 한계로 남김).
> 네트워크: 모니터는 수동 캡처라 패킷을 보내지 않는다. 단 CPU가 모자라면 Chrome이 **송신 fps·bitrate를 낮추므로 상대 화질이 떨어질 수 있다** → 송신 지표를 반드시 본다.
> 일정: 준비 10/29–10/30, 실측 10/31–11/1(주말, 약 4.5시간), 분석 직후. 명령은 모두 **repo 루트, PowerShell**.

## 0. 사전 준비 (실측 전 코드, 실측 45분 안에는 점검만)
| # | 만들 것 | 완료 기준 |
|---|---|---|
| R1 | `capture/tshark_live.py`(또는 실제 tshark 명령을 만드는 곳)에 `--snaplen N`(tshark `-s`, 기본 0 = 지금과 같음) | 기본값에서 기존 pytest 그대로 통과. `-s 96`에서도 RTP 필드(seq, ssrc)가 나옴 |
| R2 | 추론 간격 `--every N`(N초마다 추론, 캡처는 계속, 기본 1) | 기본값 동작 불변. N=5에서 tick이 5초마다 |
| R3 | `scripts/overhead_ab.py`에 단계 종류 `--modes`(예: `off,capture,server,widget`)와 `--pin-monitor N`(모니터와 자식 tshark를 코어 0..N-1에 묶음). 각 단계는 순서를 돌려가며 `--pairs`회. `widget` 단계 시작·끝에 콘솔 안내 + 비프 | 단계 시각이 `<name>_phase.csv`에 기록, 종료 시 affinity 복원(P2 사고 재발 방지) |
| R4 | `scripts/mem_hog.py --avail-mb 500`: 가용 RAM이 목표에 닿을 때까지 메모리를 잡고 유지, Ctrl+C로 해제 | 가용 MB가 목표 ±100 MB에서 유지 |
| R5 | `scripts/widget_proxy.html`: WS 서버에 붙어 1초마다 숫자 4개 + canvas 차트(최근 60초) 갱신, 버튼으로 Document PiP 열기. 실제 위젯 대신 **최악 조건 대역**(T11 PiP 스파이크와 겹치면 팀원에게 공유) | Chrome에서 PiP 창이 뜨고 tick마다 갱신 |
| R6 | `scripts/overhead_report.py --name <n>`: `*_os.csv`·`*_mem.csv`·`*_phase.csv`·webrtc dump·typeperf csv → 단계별 평균(앞 15초 제외)과 끔 대비 차이표(markdown) | 합성 csv로 만든 자체 검사 1개 통과 |

실측 당일 점검(P0, 45분): 충전기 연결, 다른 앱 종료, 전원 모드 고정, 가용 RAM 기록, S20 거치·충전, 시험 통화 1분으로 dump 저장 확인, R1–R5 각각 10초 실행.

## 1. 공통 규칙
- Meet 1:1, 노트북 Chrome 수신 ↔ S20. 각 단계 60초(`--step 60`), 앞 15초 버림, 단계 순서를 돌려가며 3회. 처음 `--warm 150`.
- webrtc-internals 탭은 모든 단계에서 같은 상태로 열어 둔다. 블록마다 dump 저장.
- 시스템 카운터(블록마다 따로 실행, 끝나면 Ctrl+C):
  ```powershell
  typeperf "\Processor(_Total)\% Processor Time" "\Memory\Available MBytes" "\Memory\Pages/sec" "\GPU Engine(*engtype_3D)\Utilization Percentage" -si 1 -o data\pilot\<name>_perf.csv
  ```
- 통화 지표(dump): 수신 fps, 디코드 시간(`totalDecodeTime/framesDecoded`), freeze 수, **송신 fps·송신 bitrate**. 시스템: 총 CPU, Chrome CPU, 모니터 CPU, 가용 RAM, 모니터 RSS, Pages/sec, GPU.

## 2. 블록
| 블록 | 질문 | 조건 | 시간 |
|---|---|---|---|
| E1 구성요소 분해 | 무엇이 얼마나 먹는가 | `--modes off,capture,server,widget` (capture = tshark만, server = tshark+모델+WS, widget = server + R5 PiP를 통화 창 위에) | 35분 |
| E2 전체 코어 포화 | 꽉 찬 CPU에서 악화시키나 | 다른 창에서 `cpu_load.py --levels 90 --step 1200` 유지 × `--modes off,widget` | 25분 |
| E3 같은 코어 경쟁 | 최악의 경쟁 | `cpu_load.py --pin 2`로 Chrome을 2코어에. ① 모니터 자유 ② `--pin-monitor 2`(같은 코어). 각각 `--modes off,widget` | 30분 |
| E4 메모리 압박 | 페이징이 생기나 | `mem_hog.py --avail-mb 500` 유지 × `--modes off,widget` | 25분 |
| E5 경량 모드 | 가볍게 하면 해결되나 | E2–E4 중 차이가 가장 컸던 조건에서 `full`(기본) / `--snaplen 96 --every 5` / OS 지표만(tshark 끔) | 30분 |
| E6 장시간 | 메모리가 새나 | 부하 없이 widget 단계 20분 연속. 모니터 RSS 기울기(MB/분) | 25분 |
| E7 (선택) 기기 밖 | 망 쪽에서도 같은 추정인가 | 팀원 Mac 핫스팟 + Wireshark로 같은 통화 동시 캡처, 특징·추정 비교. 팀원이 있을 때만 | +30분 |
| 분석 | | `overhead_report.py` → PROGRESS "P5" | 45분 |

이름 규칙: `p5_e1`, `p5_e2`, `p5_e3a`, `p5_e3b`, `p5_e4`, `p5_e5_full`, `p5_e5_lite`, `p5_e5_os`, `p5_e6`. 원자료는 `data/pilot/`(git 제외).

## 3. 통과 기준 (실측 전에 고정, 바꾸지 않는다)
| 항목 | 기준 |
|---|---|
| 모니터+위젯 CPU 평균 | < 5% |
| 끔 대비 차이: 수신·송신 fps | < 1 |
| 끔 대비 차이: 디코드 시간 | < 10% |
| freeze | 증가 없음 |
| Pages/sec (E4) | 끔 대비 증가 없음 |
| 모니터 RSS 기울기 (E6) | < 1 MB/분 |

## 4. 해석
| 결과 | 주장 |
|---|---|
| E1–E4 통과 | "포화 상태를 포함해도 측정 가능한 QoE 영향이 없다" (통화 1건 기준) |
| E2·E3 실패, E5 통과 | "포화 시 영향이 있으나 경량 모드로 기준 안" → 포화 감지 시 감속(`call_core_pct` > 85%이면 추론 중단, OS 지표만으로 진단)을 기본으로 |
| E5까지 실패 | "포화된 기기에서는 기기 안 측정에 한계" → 망 쪽 배치(E7) 권장, 그때는 기기 원인 진단을 잃음 |
| E1에서 widget 증가분이 가장 큼 | 위젯 갱신 주기·차트를 팀원과 조정 |

## 5. 한계·되돌리기
- 한계: 통화 1건·기기 1대·대체 위젯. 실제 위젯이 나오면 E1만 재측정.
- 되돌리기: `cpu_load.py`는 종료 시 전체 코어 복원. 의심되면 Chrome 완전 종료 후 재실행. `mem_hog.py`는 Ctrl+C로 해제. typeperf는 Ctrl+C.
