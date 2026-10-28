# SCHEMA v1.2 제안 — `judgement` · `device` · `diagnosis`(+`device_cpu`) (2026-10-16, Claude)

> **상태: 제안. 팀원(Web) 확인 대기.** `docs/SCHEMA.md`는 수정하지 않았다. 승인되면 아래 "반영 절차"대로 한 PR에서 바꾼다.
> 근거: PROJECT_SPEC v6 §1·§5(지표별 판정, 원인 `none|loss|bandwidth|device_cpu` + 근거 + 신뢰도, CPU 카드),
> `docs/design/judge.md`, `server/diagnosis.py`, T1 `OsSampler`, PROGRESS W1 P2(CPU 부하) 결과. 서버 쪽 채우는 규칙은 `docs/design/ws_protocol.md` §8.

## 1. 왜 바꾸나
- v6에서 0–100 QoE 점수가 **지표별 판정**으로 바뀌었다(SPEC §5). v1 tick에는 판정을 담을 곳이 `qoe`·`verdict`뿐이다.
- 대시보드 필수 화면이 "원인·근거·CPU 카드"다(PROGRESS Q18). 원인(v1.1 `diagnosis`)은 있지만 **근거 값과 CPU 지표**를 담을 곳이 없다.
- v1.1 초안은 Android 오버레이 전제(폰 RSSI `device` 메시지, `action.code` 패널 동작)인데, v6에서 오버레이 개발이 중단됐다.

## 2. tick 추가 필드 (server → client, 모두 optional — v1 소비자는 무시하면 됨)
```json
{"...v1 필드...": "...",
 "judgement": {"fps": "good", "bitrate": "fair", "frameHeight": "unknown", "frame_jitter": "good", "overall": "fair"},
 "device": {"cpu_pct": 23.7, "proc_cpu_pct": 8.9, "call_core_pct": 24.1, "mem_pct": 71.0},
 "diagnosis": {"cause": "none", "confidence": 0.67,
               "evidence": {"bytes_ratio": 0.98, "pkts_ratio": 1.01, "iat_q1_delta_ms": 0.4,
                            "iat_std_ratio": 1.05, "seq_loss": null, "call_core_pct": 24.1}}}
```

### judgement (신규)
| 필드 | 타입 | 값 | 설명 |
|---|---|---|---|
| `judgement.fps` | string | `good` \| `fair` \| `poor` \| `unknown` | 절대 기준 [가정] ≥24 / 15–24 / <15 (judge.md) |
| `judgement.frame_jitter` | string | 같음 | 절대 기준 [가정] <30 / 30–60 / ≥60 ms |
| `judgement.bitrate` | string | 같음 | **통화 초반 기준선 대비 비율**(≥0.8 / 0.5–0.8 / <0.5). 기준선 전(약 20초)은 `unknown` |
| `judgement.frameHeight` | string | 같음 | bitrate와 같은 상대 기준 |
| `judgement.overall` | string | 같음 | 지표 중 최악. unknown 제외, 전부 unknown이면 unknown |
- 키 이름은 서버 코드(vcaml)와 같게 `bitrate`, `frameHeight`, `frame_jitter`이다. `est`의 키(`bitrate_kbps`, `height`, `frame_jitter_ms`)와 다르다 — **질문 Q2**.
- 히스테리시스: 악화는 즉시, 회복은 같은 등급 2틱 연속일 때. UI가 따로 평활화할 필요 없음.
- judgement에는 `validated`를 넣지 않는다. 검증 여부는 tick의 `validated` 하나만 쓴다(judge.py 반환값의 `validated`는 앱 기준이라 의미가 달라 버림).

### device (의미 변경: v1.1 client→server 메시지 → v1.2 tick 안의 서버 측 OS 지표)
| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `device` | object \| null | | 노트북 OS 지표. Replay에 OS 기록이 없거나 샘플이 2초보다 오래되면 null |
| `device.cpu_pct` | number | % (0–100) | 전체 CPU (psutil `cpu_percent`) |
| `device.proc_cpu_pct` | number | % (0–100, **전체 코어 대비**) | 통화 프로세스 합(chrome.exe·zoom.exe). 작업 관리자의 "프로세스 %"와 같은 기준 |
| `device.call_core_pct` | number | % (0–100) | **통화 프로세스가 쓸 수 있는 코어(affinity)의 사용률 평균**. `device_cpu` 판정 입력 (`docs/design/diagnosis_v1.md`). P2에서 코어 고정 시 `proc_cpu_pct`는 5–10%로 낮게 보였다 |
| `device.mem_pct` | number | % | 메모리 사용률 |
- 모니터 자신의 CPU(`monitor_cpu_pct`)는 T1 CSV에는 있지만 tick에는 넣지 않는다(H1 평가용, 화면 불필요). 필요하면 optional 추가.

### diagnosis (v1.1 구조 + 값 1개 추가 + `evidence`)
| 필드 | 타입 | 값 | 설명 |
|---|---|---|---|
| `diagnosis.cause` | string | `none` \| `loss` \| `bandwidth` \| `device_cpu` \| `delay_jitter` \| `weak_wifi` | **`device_cpu` 추가.** v6 평가 대상은 앞 4개. `delay_jitter`는 diagnosis.py v0.1이 내므로 유지, `weak_wifi`는 데스크톱에서 나오지 않음(RSSI 입력 없음)이지만 값 목록에는 남김 |
| `diagnosis.confidence` | number | 0–1 | 규칙 기반 신뢰도. UI는 값을 같이 보여 주고 "확정"처럼 쓰지 않는다(SPEC 절대 규칙 6) |
| `diagnosis.evidence` | object | 아래 6키 고정, 각 number \| null | "근거 카드"용. 기준선 전이면 6키 모두 null |

`evidence` 키 (diagnosis.py `last_signals`를 이름만 풀어 씀):
| 키 | 원래 신호 | 뜻 |
|---|---|---|
| `bytes_ratio` | `r_bytes` | 수신 바이트 / 기준선 |
| `pkts_ratio` | `r_pkts` | 영상 패킷 수 / 기준선 |
| `iat_q1_delta_ms` | `d_q1` | 패킷 간격 하위 25% 값의 증가량 (대역폭 병목 신호) |
| `iat_std_ratio` | `r_std` | 패킷 간격 표준편차 / 기준선 (지터 신호) |
| `seq_loss` | `seq_loss` | RTP 순번 기반 손실률. RTP가 안 보이면 null |
| `call_core_pct` | `device.call_core_pct` | `device_cpu` 근거 (device가 null이면 null). 10/16 `proc_cpu_pct`에서 변경 — Q9 |

`device_cpu` 의미 (판정 규칙은 diagnosis v1, W4에서 확정): **패킷 신호는 정상인데 노트북 CPU가 높은** 상태. W1 P2에서 CPU 89%에서도 수신 fps는 유지되고 디코드 시간만 8배 늘었고, 코어 제한 시 송신 fps가 3.5까지 떨어졌다 → 패킷만으로는 안 보이므로 `device`를 결합한다. 정답 라벨은 주입한 부하 조건(SPEC 절대 규칙 6).

### 바꾸지 않는 것
- v1 필드 전부 그대로. `qoe`·`verdict`는 **호환용으로 유지**(서버가 judgement에서 파생, ws_protocol §4). 제거는 v1.3 이후 별도 합의.
- `advice` 유지(null 가능).

## 3. v1.1 초안에서 폐기 제안
| 항목 | 이유 |
|---|---|
| tick `action` (`code`, `text`) | `code`는 Android `Settings.Panel` 동작이라 데스크톱에 해당 없음. 문구가 필요하면 `advice`로 충분 |
| client→server `device` 메시지 (`rssi_dbm`, `wifi`) | 오버레이 앱 개발 중단(v6). 이름이 v1.2 `device`와 겹쳐 혼동 |
| `diagnosis`는 v1.1 → v1.2로 그대로 승계 | (폐기 아님) |

## 4. 팀원(Web) 확인 질문 (권장안 포함)
| # | 질문 | 권장안 |
|---|---|---|
| Q1 | `judgement` 4지표 배지 + `overall`을 메인으로 쓰고 `qoe` 숫자는 화면에서 숨겨도 되나? | 숨김. 필드는 서버가 계속 보냄 |
| Q2 | `judgement` 키를 `est`와 맞춰 `bitrate_kbps`/`height`/`frame_jitter_ms`로 바꿀까, 서버 이름(`bitrate`/`frameHeight`/`frame_jitter`) 그대로 둘까? | **`est` 키에 맞춘다** (TS에서 `est[k]`와 `judgement[k]`를 같은 키로 순회 가능). 서버가 변환. 동의하면 judge.md·ws_protocol §8 수정 |
| Q3 | `unknown`을 어떻게 보일까? (통화 시작 약 20초는 bitrate·해상도가 unknown) | 회색 배지 + "기준선 수집 중" |
| Q4 | `device`가 null이면 CPU 카드는? | 카드 유지, "OS 지표 없음" 표시 |
| Q5 | `evidence` 6키 고정 + null 허용 형식이 TS 타입으로 쓰기 편한가? (가변 키 dict는 계약 테스트·타입 모두 불편해서 고정함) | 이대로 |
| Q6 | v1.1의 `action`, client `device` 메시지 폐기에 동의하나? | 동의 |
| Q7 | tick이 3초 이상 안 오면 "수신 끊김" 표시는 대시보드가 맡나? (서버는 패킷 없는 초에 tick을 보내지 않음) | 대시보드가 맡음 |
| Q9 | `device.call_core_pct` 추가, `evidence.proc_cpu_pct` → `call_core_pct` (코어 고정 시 전체 코어 대비 %는 포화를 못 보여 줌, diagnosis_v1 근거 2). CPU 카드 게이지는 어느 값? | 게이지 = `call_core_pct`, 보조 숫자 = `cpu_pct` |
| Q8 | 서버→클라이언트 메시지는 tick 한 종류뿐이라 `type` 필드가 없다. 앞으로 다른 종류가 생기면 그때 `type`을 추가해도 되나? | 그때 추가 (지금은 YAGNI) |

## 5. 반영 절차 (승인 후, 한 PR)
1. `docs/SCHEMA.md`: v1.1 절을 v1.2로 대체(이 문서 2·3절), 버전 표기 "v1.2 확정".
2. `docs/schema/sample.jsonl`: v1 줄은 그대로 두고 v1.2 필드가 있는 줄 추가(Meet replay 정상·저하 / `device: null` / `cause: device_cpu` 각 1줄 이상).
3. `tests/test_schema_contract.py`: 지금은 `msg.keys() == ref.keys()`로 **optional 필드도 막는다** → "v1 필수 키 ⊆ msg 키, 나머지는 v1.2 optional 키 목록 안" 으로 완화. enum 값 검사 추가.
4. `server/dummy_stream.py`에 v1.2 필드 생성, 대시보드 Vitest(`parseMessage`)가 새 sample 전 줄을 받는지.
5. 양쪽 승인 후 squash merge (변경 규칙 1: optional 추가지만 계약 테스트 변경을 포함하므로 둘 다 승인).
