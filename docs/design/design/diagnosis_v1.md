# diagnosis v1 설계 — `device_cpu` 추가 (T8, 2026-10-16, Claude) — 구현은 T8b(Codex)

## 역할
`server/diagnosis.py` v0.1(패킷만)에 **OS 지표**를 더해 원인 `none | loss | bandwidth | device_cpu`를 낸다(SPEC §1, 연구 질문 2).
`delay_jitter`·`weak_wifi`는 코드와 값 목록에 남기되 v6 평가 대상이 아니다. 추정이며 확정 진단이 아니다(SPEC 절대 규칙 6).

## 근거 — P2 원자료 재분석 (이번 세션, `data/pilot/p2_meet{1,2}_*`, 단계별 중앙값)
| 통화·단계 | 전체 CPU % | 통화 프로세스 % (18 논리 코어 대비) | 수신 fps | 디코드 ms | 송신 fps | v0.1 출력 |
|---|---|---|---|---|---|---|
| P2-1 busy loop 0% | 10.4 | 3.6 | 29.8 | 1.4 | 28.4 | none 57/60 |
| P2-1 busy loop 80% | 88.6 | 8.5 | 29.8 | 10.8 | 21.0 | **loss 31**/none 29 |
| P2-1 busy loop 100% | 89.0 | 7.8 | 29.7 | 12.9 | 20.4 | **loss 34**/none 24 |
| P2-2 2코어 고정 + 0% | **22.8** | **5.0** | 30.1 | **21.1** | **6.3** | none 60/60 |
| P2-2 2코어 고정 + 80% | 24.4 | 9.6 | 29.8 | 18.1 | 19.3 | none 58/60 |

발견:
1. **수신 패킷·수신 fps는 모든 단계에서 정상** → 패킷 규칙은 CPU 원인을 볼 수 없다(가설 확인, 2통화). 효과는 디코드 시간·송신 fps·freeze에만 있다.
2. **전체 코어 대비 지표는 코어 고정을 못 잡는다.** P2-2에서 전체 CPU 23%, 통화 프로세스 5–10%인데 디코드 21 ms, 송신 fps 6. 10% × 18코어 / 2코어 ≈ 91% → 허용된 2코어는 포화. **"통화 프로세스가 쓸 수 있는 코어의 사용률"**이 필요하다(아래 `call_core_pct`).
3. **P2-1의 `loss` 오탐은 CPU가 아니라 경로 전환이 주원인으로 보인다.** 통화가 Google relay(`142.250.82.215:3478`)로 시작해 50% 단계 중 같은 LAN의 P2P(`172.30.1.91:53272 → :63929`)로 바뀌었다. 새 흐름은 양쪽 포트가 49152 초과라 tshark `-d udp.port==1024-49152,rtp`가 RTP를 해석하지 않았다(수신 영상 RTP 비율 0.996 → 0.000) → `seq_loss=None` → IP/UDP 손실 규칙(`d_max≥20, r_std≥1.1`)이 relay 기준선과 비교해 발동. CPU의 기여는 이 자료로 분리 불가 [미확인].
   → 조치: T1에 `--enable-heuristic rtp_udp` 추가(`31243bf`, 실통화 검증은 W3 S0-3), v1에 **흐름 전환 시 기준선 재수집** 추가.
4. 노트북 송신 패킷 수는 신호로 못 쓴다: 초당 39–527개로 흔들리고 송신 fps와 같이 움직이지 않는다(P2-1에서는 부하 중 오히려 증가).
5. 효과가 시간에 따라 변한다(P2-2 80% 단계 후반 디코드 6 ms로 회복 후 다시 악화). Chrome의 적응으로 보인다 [추정].

## 입력
```python
Diagnoser.update(f, rssi_dbm=None, seq_loss=None, device=None, flow=None) -> (cause, confidence)
# device: {"cpu_pct": float, "call_core_pct": float, ...} 또는 None (Replay에 OS 기록 없음 / 샘플이 2초보다 오래됨)
# flow:   이 창의 수신 영상 주 흐름 키 (ip.src, udp.srcport) — 바이트가 가장 많은 것. None이면 전환 감지 안 함
```
- **`call_core_pct`** (신규 OS 지표) = 통화 프로세스(chrome.exe·zoom.exe) **affinity 합집합 코어들의 `psutil.cpu_percent(percpu=True)` 평균**.
  affinity가 전체 코어면 `cpu_pct`와 같다(busy loop 경우를 잡음). 코어 고정이면 그 코어만 본다(P2-2 경우를 잡음). 경합(다른 프로세스가 같은 코어 사용)도 포함한다.
  affinity 조회 실패(권한 등) 프로세스는 건너뛰고, 전부 실패면 전체 코어로 본다.
- `device=None`이면 `device_cpu`는 절대 나오지 않는다 → v0.1과 같은 동작(**패킷만 vs 패킷+OS 비교 실험이 이 스위치 하나**).
- P2 원자료에는 `call_core_pct` 열이 없다. 대체 근사(통화 % × 코어 수 / affinity 수)는 경합을 못 보므로 넣지 않는다(YAGNI). 검증은 W3 자료로.

## 규칙 (순서 = 우선순위, v0.1에 두 군데만 끼움)
0. **흐름 전환**: `flow`가 직전 주 흐름과 다른 창이 **2연속**이면 기준선·투표를 비우고 `skip_first`부터 다시 시작(그동안 `none, 0.0`). 1창만 바뀌면 무시.
1. `bandwidth` (v0.1 그대로) → 2. RTP `loss` (`seq_loss ≥ 0.015`) → 3. `delay_jitter` 세 규칙 (그대로)
4. **`device_cpu`**: `device`가 있고 `call_core_pct ≥ 85` [가정] → 강도 `min(1, 0.5 + (u − 85) / 30)`
5. RTP가 보이고 빈칸 없음 → `none` / IP/UDP 손실 규칙 (그대로) / `none`
- 4를 5 앞에 두는 이유: IP/UDP 손실 규칙은 v0.1에서 가장 약하다(Meet 재현율 0.18, Teams 정밀도 0.29). CPU 포화가 확실할 때는 약한 패킷 신호보다 CPU를 택한다. 직접 관측 신호(1–3)는 CPU보다 먼저다(수신 패킷 이상은 CPU가 만들지 않는다 [가정, W3에서 C 조건의 1–3 발동률로 확인]).
- 신뢰도·투표(3창 다수결)는 v0.1과 같다. `device_cpu` 창도 패킷이 정상이면 기준선에 들어간다(`_healthy` 그대로).
- 뜻: `device_cpu` = "패킷은 정상, 노트북 CPU 포화 → 디코드·송신 품질 저하 위험". 수신 패킷으로 저하를 관측한 것이 아니다. UI 문구 제안: "노트북 CPU 포화 — 화질 저하 가능 (추정, 신뢰도 x)".

## 출력 (SCHEMA v1.2 제안 반영)
- `CAUSES`에 `device_cpu` 추가. `last_signals`에 `call_core_pct` 추가 → `evidence.call_core_pct` (제안 문서의 `proc_cpu_pct`를 대체, Q9).
- `device`에 `call_core_pct` 추가(제안 문서 §2 수정). 기존 `proc_cpu_pct`(전체 코어 대비)는 H1 오버헤드 표용으로 유지.

## 평가 (W3, `docs/design/w3_collection.md` 조건표)
- 창 라벨: C2·C2L의 `[on+3, off]` = `device_cpu`, L = `loss`, B = `bandwidth`, 모든 통화의 baseline(150–210)과 N0 전체(150–380) = `none`. on/off 직후 3초와 recovery 첫 30초는 제외.
- 분리: 통화 단위, 조건마다 통화 ID 순서로 번갈아 — 1·3번째 = dev(임계값 조정), 2·4번째 = test(보고만). N0은 3/3, 나머지 조건은 2/2.
- 보고: 클래스별 P/R, confusion matrix, `none` 오탐률, 판정 지연 중앙값. **절제 실험**: 같은 test를 `device=None`으로 → `device_cpu` 재현율 0이 되는지(연구 질문 2의 답).
- 보조 정답(효과 있음): dump에서 디코드 시간 ≥ 기준선 2배 또는 송신 fps ≤ 기준선 0.8배 또는 freeze 증가인 창. `device_cpu` 재현율을 "효과 있음" 창에 대해서도 따로 보고(주입 라벨만으로는 효과 없는 창도 맞혀야 하는 문제 보완).

## 구현 범위 (T8b, Codex → gpt-6-luna · medium)
1. `OsSampler`: `call_core_pct` 열 추가(os.csv 마지막 열). **W3(10/27) 전에 필요** — 없으면 C 조건 통화가 진단 평가에 못 쓰인다.
2. `Diagnoser`: `device`·`flow` 인자, 규칙 0·4, `CAUSES`. 기존 테스트 13개는 수정 없이 통과해야 한다.
3. 파이프라인(T4 tick 루프): 창마다 수신 영상 패킷의 `(ip.src, udp.srcport)` 바이트 합 최대를 `flow`로, 최근 OS 샘플을 `device`로 넘김. Replay는 `--os` CSV.
4. `scripts/diag_eval.py`: W3 `log.csv` + `w3_<id>_{pkts,os}.csv`로 위 평가 표 출력(`--no-device` 절제 옵션).

## 테스트 표 (tests/test_diagnosis.py 추가분)
| 케이스 | 기대 |
|---|---|
| 정상 패킷 + `device=None` | `none` (어떤 입력에도 `device_cpu` 없음) |
| 정상 패킷 + `call_core_pct` 95 × 3틱 | `device_cpu`, 0 < conf ≤ 1 |
| 경계: 84.9 × 3틱 / 85.0 × 3틱 | `none` / `device_cpu` |
| 95 + bandwidth 신호 | `bandwidth` |
| 95 + `seq_loss` 0.05 | `loss` |
| 95 + `seq_loss=None` + IP/UDP 손실 신호(`l_num_pkts` 25/30) | `device_cpu` |
| 95가 1틱만 | `none` (투표) |
| 흐름 A로 기준선 → B(패킷 2.4배, 간격 다름)로 2창 이상 | 재수집 동안 `none`, 이후 B 정상 → `none` (`loss`·`bandwidth` 없음) |
| 흐름이 1창만 B였다가 A로 복귀 | 기준선 유지 |
| `OsSampler` 계산(가짜 psutil): percpu [100,100,10,10], affinity {0,1} / 전체 | 100 / 55 |
| 출력 값이 `CAUSES` 안, conf ∈ [0,1] | 통과 |

## 열린 질문 / [가정]
- 임계값 85%와 우선순위 4번 위치는 [가정] → W3 dev로 조정. P2는 배터리 상태, W3는 충전기 연결이라 포화 양상이 다를 수 있다.
- Teams는 Chrome 웹 클라이언트라 `chrome.exe` 그대로 적용된다 [가정]. W4 Teams 수집은 C 조건 포함(`w3_collection.md` §9, v8에서 Zoom 제외). W3에서 S0-4가 실패하면 Teams도 C 조건 보류. v0.1 합성 실험에서 같은 규칙이 앱마다 다르게 들었으므로(Teams 약 270 pkt/s) 임계값은 앱별로 dev에서 따로 조정한다.
- 메모리(`mem_pct` 85–86%로 상시 높음)는 원인 후보에서 뺐다. 근거 자료 없음.
