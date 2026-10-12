# SCHEMA — 서버 ↔ 대시보드 WebSocket 계약

- 버전:
  - **v1 초안** (2026-10-12): `sample.jsonl`, 더미 서버, 계약 테스트가 구현하고 있는 버전이다.
  - **v1.1 초안** (맨 아래 절): **팀원 확인 대기**. 양쪽(ML·Web) 승인 시 "확정"으로 바꾼다.
- 기준: `docs/PROJECT_SPEC.md` §1 메시지를 그대로 쓰고, client→server `control` 메시지만 추가했다.
- 구독자: React 대시보드(노트북)와 Flutter 오버레이 앱(S20). 둘 다 같은 메시지를 받는다.
- 실행 가능한 계약: [`docs/schema/sample.jsonl`](schema/sample.jsonl) — 이 문서와 다르면 **sample.jsonl이 우선**.

## 연결
| 항목 | 값 |
|---|---|
| URL | `ws://localhost:8000/ws` ([가정] 실제 서버도 같은 주소) |
| server → client | `tick` 메시지, 1초(`window_s`)마다 1개, JSON 텍스트 프레임 |
| client → server | `control` 메시지 (초안, 서버 구현은 W5) |
| 개발용 더미 | `uv run server/dummy_stream.py` (uv만 있으면 됨, 옵션은 `--help`) |

## tick (server → client)
```json
{"ts": 1791763203.0, "mode": "live", "app": "kakao_video", "window_s": 1.0,
 "est": {"fps": 24.1, "bitrate_kbps": 850, "frame_jitter_ms": 12.3, "height": 360},
 "truth": null,
 "impair": {"loss_pct": 0, "delay_ms": 0, "jitter_ms": 0, "bw_kbps": null},
 "qoe": 71.5, "verdict": "passed", "advice": null, "validated": false}
```

| 필드 | 타입 | 단위·값 | 설명 |
|---|---|---|---|
| `ts` | number | epoch 초 (노트북 시계) | 윈도우 끝 시각 |
| `mode` | string | `live` \| `replay` \| `whatif` | 입력 모드 |
| `app` | string | `meet` \| `kakao_video` \| `kakao_voice` \| `zoom` [가정] | 통화 앱 |
| `window_s` | number | 초 | 추정 윈도우 길이 (기본 1.0) |
| `est.fps` | number \| null | frames/s | 추정 프레임률. 영상 없음(음성통화)이면 null |
| `est.bitrate_kbps` | number \| null | kbps | 추정 수신 비트레이트 (vcaml은 bps → 서버가 /1000) |
| `est.frame_jitter_ms` | number \| null | ms | 추정 프레임 간격 표준편차 |
| `est.height` | number \| null | px | 추정 해상도 높이 |
| `truth` | object \| null | `est`와 같은 구조 | 정답(getStats). **Meet 실측에만** 존재, 그 외 null |
| `impair.loss_pct` | number | % (0–20) | What-if 손실률. `whatif`가 아니면 0 |
| `impair.delay_ms` | number | ms (0–300) | What-if 지연. `whatif`가 아니면 0 |
| `impair.jitter_ms` | number | ms (0–100) | What-if 지터. `whatif`가 아니면 0 |
| `impair.bw_kbps` | number \| null | kbps (100–5000) | What-if 대역폭 제한. null = 제한 없음 |
| `qoe` | number | 0–100 | QoE 점수 (G.1070 참고 모델, 서버 계산) |
| `verdict` | string | `passed` \| `failed` | `qoe` ≥ 임계값이면 passed |
| `advice` | string \| null | 자유 문구 | 규칙 기반 권고. 없으면 null. 문구 언어는 미정 (sample은 영어) |
| `validated` | bool | | `truth`가 있을 때만 true. Kakao·Zoom은 항상 false → UI에 "모델 추정값" 표시 |

UI 표시 규칙 (명세 절대 규칙):
- `validated: false`이면 "추정값" 배지를 표시한다.
- `mode: "whatif"`이면 "에뮬레이션: 송신 측 혼잡 제어 반응은 반영하지 않음"을 표시한다.

## control (client → server, 초안)
```json
{"type": "control", "mode": "whatif", "app": "meet",
 "impair": {"loss_pct": 5, "delay_ms": 100, "jitter_ms": 20, "bw_kbps": null},
 "threshold": 70, "live_noise": false, "reset": false}
```
| 필드 | 타입 | 설명 |
|---|---|---|
| `type` | `"control"` | 고정 |
| `mode`, `app` | string | tick과 같은 값. 바꾸면 서버 입력 전환 |
| `impair` | object | tick의 `impair`와 같은 구조 (슬라이더 값) |
| `threshold` | number | 판정 임계값 50–90 ([가정] 기본 70) |
| `live_noise` | bool | Live Noise 토글 (의미는 W5에 확정) |
| `reset` | bool | true면 서버가 impair·threshold를 기본값으로 되돌림 |

## 변경 규칙
1. **optional 필드 추가**: PR 설명에 적기만 하면 된다. 소비자는 모르는 필드를 무시한다.
2. **이름·타입·단위 변경 또는 삭제**: 같은 PR에서 이 문서, `sample.jsonl`, 양쪽 테스트를 함께 고치고 **둘 다 승인**해야 merge한다.

## 계약 테스트
| 쪽 | 테스트 | 실행 |
|---|---|---|
| Python | `tests/test_schema_contract.py`: 서버 메시지의 키·타입이 sample과 같은지 | `uv run pytest` |
| Web | (팀원 작성) `dashboard/src/core`의 `parseMessage`가 sample.jsonl 모든 줄을 받아들이는지 | `npm --prefix dashboard test` |
| Flutter | (Sungmin 작성, 11/8 더미 연동 때) 오버레이 파서가 sample.jsonl 모든 줄을 받아들이는지 | `flutter test` (`overlay/`) |

---

## v1.1 초안 — 팀원 확인 대기
v1에 **optional 필드만 추가**한다. 그래서 v1 소비자는 수정 없이 계속 동작한다(변경 규칙 1).

확정되면 같은 PR에서 다음을 함께 바꾼다:
- `sample.jsonl`에 아래 두 필드를 추가하고 `device` 예시를 넣는다.
- 더미 서버와 계약 테스트에 반영한다.
- 이 절을 위로 합친다.

### tick 추가 필드 (server → client)
```json
{"...v1 필드...": "...",
 "diagnosis": {"cause": "loss", "confidence": 0.72},
 "action": {"code": "open_wifi_panel", "text": "Move closer to the Wi-Fi router or turn off video."}}
```
| 필드 | 타입 | 값 | 설명 |
|---|---|---|---|
| `diagnosis.cause` | string | `bandwidth` \| `delay_jitter` \| `loss` \| `weak_wifi` \| `none` | 품질 저하의 주원인 추정. 저하가 없으면 `none` |
| `diagnosis.confidence` | number | 0–1 | 규칙 기반 신뢰도. UI는 값을 함께 보여 주고 "확정"처럼 쓰지 않는다 |
| `action` | object \| null | | 사용자 조치 1개. `cause: none`이면 null |
| `action.code` | string | 아래 표 | 오버레이 [조치] 버튼이 할 동작 |
| `action.text` | string | 1줄 | 버블과 대시보드에 표시할 문구 (최종 문구는 11/20 확정, 언어 미정) |

`action.code` → Android 동작 (초안). 패널 API가 Android 13에서 동작하는지는 M0(a)에서 확인한다(미확인).

| code | cause | Android 동작 |
|---|---|---|
| `open_wifi_panel` | `weak_wifi`, `loss` | Wi-Fi 설정 패널 |
| `open_internet_panel` | `bandwidth`, `delay_jitter` | 인터넷 연결 설정 패널 |

### device (client → server, 오버레이 앱만)
```json
{"type": "device", "ts": 1791763203.0, "rssi_dbm": -67, "wifi": true}
```
| 필드 | 타입 | 설명 |
|---|---|---|
| `type` | `"device"` | 고정 |
| `ts` | number | epoch 초 (폰 시계) |
| `rssi_dbm` | number \| null | 연결된 Wi-Fi의 RSSI. 읽을 수 없으면 null (권한은 M0에서 확인, 미확인) |
| `wifi` | bool | Wi-Fi 연결 여부 (false = 모바일 데이터) |

- 1초마다 보낸다. 서버는 최근 값으로 `weak_wifi`를 판정한다. 임계값은 [가정] RSSI ≤ −75 dBm이고, M2에서 근거와 함께 정한다.
- `rssi_dbm`이 null이거나 대시보드만 연결된 경우 서버는 `weak_wifi`를 판정하지 않는다.

### 팀원 확인 요청 사항
1. 대시보드도 `diagnosis`와 `action.text`를 표시할지(권고 영역을 대체할지), 아니면 `advice`를 계속 쓸지.
2. v1의 `advice`를 v1.1에서 유지할지. 초안은 하위 호환을 위해 유지한다. 대신 `action.text`와 내용이 같을 수 있다.
