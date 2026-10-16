# WebSocket Live/Replay 메시지 계약 (설계 초안, 2026-10-16, Claude) — 구현은 T4(Codex)

> 근거: `docs/SCHEMA.md`(v1·v1.1 초안), `docs/schema/sample.jsonl`, `docs/design/judge.md`, `server/diagnosis.py`,
> T1 `capture/tshark_live.py`(`process_lines`, `OsSampler`). **계약의 원본은 여전히 SCHEMA.md + sample.jsonl**이다.
> 이 문서는 T4가 그 계약을 FastAPI로 어떻게 채우는지 정한다. 여기서 새로 붙는 필드는 모두 **SCHEMA v1.2 제안**
> (팀원 미승인, `docs/design/schema_v1.2_proposal.md`)이며 기본 출력에는 넣지 않는다.

## 1. 결정 요약
| 항목 | 결정 | 이유 |
|---|---|---|
| 엔드포인트 | `ws://localhost:8000/ws` (FastAPI `@app.websocket("/ws")`) | SCHEMA v1 그대로. 대시보드가 더미 서버에서 실서버로 주소만 바꾸지 않고 넘어옴 |
| 메시지 종류 | server→client는 **tick만**. client→server는 `control`만 | 계약 테스트가 tick 키를 정확히 비교한다(`check()`의 `keys() ==`). status·error 같은 새 메시지 종류를 만들면 v1 `parseMessage`가 깨질 수 있다 |
| 입력 원본 | 서버 프로세스 1개 = 입력 1개. 시작 인자로 고른다 (`--live` 또는 `--replay`) | 런타임 전환은 W5(What-if)와 함께. 지금 필요 없음 |
| 오류·종료 | 메시지 대신 **WebSocket close code + reason** | 새 메시지 종류 없이 전달 가능 |
| 출력 스키마 | 기본 `--schema v1` (sample.jsonl과 키 동일). `--schema v1.2`일 때만 제안 필드 추가 | v1 소비자·계약 테스트를 깨지 않으면서 대시보드가 제안 필드로 미리 개발 가능 |
| 여러 클라이언트 | 같은 tick을 모든 연결에 broadcast. 파이프라인은 연결 수와 무관하게 1개 | 대시보드 탭 2개를 열어도 tshark·모델이 두 번 돌지 않게 |

## 2. 실행 (T4가 만들 명령, [가정] 모듈명 `server/app.py`)
```powershell
# Live: tshark 실시간 (T1 capture/tshark_live.py 경로 재사용)
uv run python -m server.app --live --iface Wi-Fi [--dst <내 노트북 IP>] [--app meet|zoom]
# Replay: 저장된 패킷 CSV(T1 *_pkts.csv, vcaml pcap2csv와 같은 14필드) 재생
uv run python -m server.app --replay data/pilot/<name>_pkts.csv [--truth <webrtc dump.json>] [--os data/pilot/<name>_os.csv] [--speed 1.0] [--loop]
```
- 모두 repo 루트에서 실행. 기본 포트 8000, `--port`로 변경. COMMANDS.md에 추가는 T4 담당.
- `--speed 0` = 기다리지 않고 최대 속도 (테스트용). `--loop` = 끝나면 처음부터 (데모 fallback).

## 3. 서버 내부 흐름 (1초 창마다)
```
패킷 줄 (Live: tshark stdout / Replay: *_pkts.csv 행)
 → capture.tshark_live.parse → server.features.WindowFeatures.push  (창 닫히면 feature 1행 w)
 → RF 4개 predict  {fps, bitrate(bps), frameHeight, frame_jitter(ms)}   ← process_lines의 row와 같은 키
 → server.judge.judge(row, vca, JudgeState)                             ← 키가 그대로 맞음 (judge.md)
 → server.diagnosis.Diagnoser.update(w, seq_loss=...)                   ← v1.2 출력일 때만
 → OS 샘플 결합 (Live: psutil 1 Hz / Replay: --os CSV)                   ← v1.2 출력일 때만
 → tick 조립 → broadcast
```
- **T1 의존**: 현재 `process_lines`의 `emit(row)`은 예측값만 넘기고 feature 행 `w`를 넘기지 않는다. 진단에는 `w`의
  `l_num_bytes, l_num_pkts, t_q1, t_q2, t_std, t_max`가 필요하다. T4는 `emit`이 `w`도 받도록 **T1 위에서** 최소 변경한다
  (예: `emit(row, w)` 또는 row에 필요한 6개 열 추가). 동작 불변이어야 한다(overhead_ab·cpu_load 회귀 확인).
- 세션 상태(`JudgeState`, `Diagnoser`)는 **입력 1회 재생(통화 1개)당 1개**. `--loop`로 처음으로 돌아가면 새로 만든다.
- 파이프라인은 블로킹 루프(tshark 읽기·predict)이므로 별도 thread에서 돌리고, tick은
  `asyncio.run_coroutine_threadsafe`(또는 `loop.call_soon_threadsafe` + `asyncio.Queue`)로 이벤트 루프에 넘긴다. [가정]
  predict p95 126 ms(P3) → 1초 예산 안. 느린 클라이언트가 있어도 파이프라인을 막지 않도록 연결별 큐는 maxlen 10, 넘치면 오래된 tick 버림.

## 4. tick 필드 채우는 규칙 (v1, sample.jsonl과 키 동일)
| 필드 | 값 | 비고 |
|---|---|---|
| `ts` | `row["et"]` (float) | `WindowFeatures._emit(et=…)`: 창을 닫은 패킷의 epoch를 `int`로 자른 값 = 창 끝 시각. Replay도 **원래 캡처 시각**(재생 시각 아님) |
| `mode` | `"live"` \| `"replay"` | 시작 인자. `whatif`는 W5 |
| `app` | `--app` (기본 `meet`) | 모델은 meet용뿐 → zoom이면 추정이 부정확(P4). `validated`로 표시 |
| `window_s` | `1.0` | `config["prediction_window"]` |
| `est.fps` | `row["fps"]` 반올림 1자리 | |
| `est.bitrate_kbps` | `row["bitrate"] / 1000` | **bps → kbps 변환은 서버가** (SCHEMA) |
| `est.frame_jitter_ms` | `row["frame_jitter"]` | 이미 ms |
| `est.height` | `row["frameHeight"]` 정수 | |
| `truth` | Replay + `--truth` + 해당 초 정답 있음 → `{fps, bitrate_kbps, frame_jitter_ms, height}`, 그 외 `null` | 아래 5절. **Live는 항상 null** (dump는 통화 후 수동 저장) |
| `impair` | `{"loss_pct": 0, "delay_ms": 0, "jitter_ms": 0, "bw_kbps": null}` 고정 | What-if 아님 |
| `qoe` | [가정] `max(0, 100 − 25·n_fair − 60·n_poor)` (judge 지표 등급 수, unknown 제외) | v6에서 QoE 점수는 제외됐지만 v1 키는 필수 → **호환용 파생값**. poor가 하나라도 있으면 ≤ 40 → threshold 50–90 어디서든 failed (= PROJECT_SPEC §5 "하나라도 나쁨이면 failed") |
| `verdict` | `qoe >= threshold` ? `passed` : `failed` | threshold 기본 70, control로 변경 |
| `advice` | `null` | v1.1 `action.text`가 확정되면 그쪽으로. 지금 문구 생성 안 함 |
| `validated` | `truth is not None` | SCHEMA 규칙. **`judge()`가 돌려주는 `validated`는 쓰지 않는다** (T3b 리뷰 1번: 의미가 다름) |

빈 창: 패킷이 없는 초에는 `WindowFeatures`가 창을 만들지 않으므로 tick도 없다. 클라이언트는 tick이 3초 이상 없으면
"수신 끊김"으로 표시한다(대시보드 쪽 규칙, 팀원 확인 필요). Live에서 마지막 창이 열린 채 남지 않도록 서버는 패킷이 2초
없으면 `flush()`한다 [가정]. 이때 `est` 값이 null이 될 수는 없다(v1 sample에서 `bitrate_kbps`는 number만 허용).

## 5. Replay 정답(`truth`) 결합
- `--truth`의 webrtc-internals dump는 `scripts/pilot_live.py compare`와 **같은 PC 선택 규칙**을 쓴다: PeerConnection마다
  따로 읽어 재생 구간에서 `framesReceivedPerSecond > 0`인 초가 가장 많은 PC (Meet는 통화 중 PC를 갈아탐, 첫 PC만 보면 fps 0).
  → T4는 이 부분을 함수로 뽑아 `compare`와 공유한다 (복붙 금지).
- 정렬: `truth.ts == tick.ts` (epoch 초, 같은 노트북 시계). **lag 0만 사용**. `compare`의 ±3초 lag 탐색은 정답으로 오차를
  줄이는 것이라 재생 표시에는 쓰지 않는다.
- 단위: `framesReceivedPerSecond → fps`, `bitrate`(bps) → `/1000` → `bitrate_kbps`, `frame_jitter → frame_jitter_ms`, `frameHeight → height`.
- 그 초에 정답이 없거나 하나라도 NaN이면 `truth: null` (부분 truth 금지 — v1 계약은 `truth` 안 4키가 모두 number).

## 6. control (client → server) — v1 초안 그대로, T4에서 처리 범위
| 필드 | T4 처리 |
|---|---|
| `threshold` | 반영 (50–90 밖이면 무시). 이후 tick의 `verdict`에 바로 적용. 모든 연결이 공유 [가정] |
| `reset` | true면 threshold=70 |
| `mode`, `app` | 현재 입력과 다르면 **무시** (서버 1개 = 입력 1개). 로그 한 줄 |
| `impair`, `live_noise` | 무시 (W5) |
- 파싱 실패·`type != "control"`: 무시하고 연결 유지 (로그). 알 수 없는 필드도 무시.

## 7. 종료·오류 (close code)
| 상황 | 동작 |
|---|---|
| Replay 끝 (`--loop` 없음) | 모든 연결 `close(1000, "replay finished")` |
| tshark 실행 실패·조기 종료 | `close(1011, "capture failed: <요지>")`, 서버 프로세스는 종료 코드 ≠ 0 |
| 모델 파일 없음 | 서버 시작 단계에서 실패 (연결 받기 전) |
| 서버 Ctrl+C | `close(1001, "server shutdown")` |

## 8. SCHEMA v1.2 제안 필드 (`--schema v1.2`일 때만, 팀원 미승인)
> **SCHEMA v1.2 제안** — 상세·질문은 `docs/design/schema_v1.2_proposal.md`. 승인 전에는 sample.jsonl·계약 테스트에 넣지 않는다.
```json
{"...v1 필드...": "...",
 "judgement": {"fps": "good", "bitrate": "fair", "frameHeight": "unknown", "frame_jitter": "good", "overall": "fair"},
 "device": {"cpu_pct": 23.7, "proc_cpu_pct": 8.9, "mem_pct": 71.0},
 "diagnosis": {"cause": "none", "confidence": 0.67}}
```
| 필드 (v1.2 제안) | 출처 | 규칙 |
|---|---|---|
| `judgement.<지표>`·`overall` | `judge()` 반환값에서 `validated`만 뺀 것 | 값 `good\|fair\|poor\|unknown`. 키 이름은 judge.py 그대로(vcaml 이름) |
| `device` | Live: T1 `OsSampler`와 같은 psutil 계산 / Replay: `--os` CSV, 없으면 `null` | `cpu_pct`=전체 CPU, `proc_cpu_pct`=통화 프로세스(chrome.exe·zoom.exe 합, 전체 코어 대비), `mem_pct`. **tick.ts 이하 중 가장 최근 샘플**, 2초보다 오래됐으면 `null`. (T8b 이후) `call_core_pct` 열이 없는 옛 os.csv(P2 등)를 Replay하면 `device` 전체가 `null`이라 CPU도 안 보인다. 의도된 동작(10/16 리뷰 낮음, 미수정) |
| `diagnosis` | `Diagnoser.update(w, rssi_dbm=None, seq_loss=…)` | v1.1 초안 구조. `cause`에 `device_cpu` 추가 제안(diagnosis v1, W4). 데스크톱에는 RSSI 입력이 없어 `weak_wifi`는 나오지 않음. `evidence`(6키 고정, `last_signals` 이름 변환)는 제안 문서 §2 — T4는 넣어도 되고 생략해도 됨 [가정] |
| `seq_loss` 입력 | T1 `process_lines`는 rtp 필드를 파싱하지 않음 | T4 v0은 `seq_loss=None`(IP/UDP 규칙). RTP 순번 결합(`server.features.RtpSeqLoss`)은 후속 |
- v1.1 초안의 `action`은 v6에서 Android 패널 동작이 없어졌으므로 넣지 않는다(제안 문서에서 폐기 제안).
- v1.1 초안의 client→server `device` 메시지(폰 RSSI)와 **이름이 겹친다**. v6에서는 오버레이가 없으므로 그 메시지는 폐기하고
  `device`를 tick의 서버 측 OS 지표로 쓰자는 것이 제안이다.

## 9. T4 완료 기준 (HANDOFF와 같게)
1. `--replay docs/…` 또는 테스트용 작은 `*_pkts.csv` → WS로 받은 모든 tick이 `tests/test_schema_contract.py`의 `check()` 통과 (`--schema v1`).
2. `--truth` 결합 시 `validated == (truth is not None)` 이고 truth가 있는 초가 1개 이상.
3. control `threshold` 변경 후 다음 tick의 `verdict`가 바뀐 기준으로 계산됨.
4. 클라이언트 2개 동시 연결 시 같은 `ts` 순서열을 받음. 한쪽이 끊겨도 다른 쪽 계속.
5. Replay 끝 → close 1000. `--speed 0`으로 테스트가 수 초 안에 끝남.
6. 의존성 (10/16 `.venv` 확인): `fastapi 0.143.0`·`uvicorn 0.54.0`·`starlette 1.7.0`은 mlflow가 이미 끌어와 설치돼 있다.
   `httpx`·`websockets`·`psutil`은 **미설치**. Codex 루프는 네트워크·새 의존성이 금지이므로 T4는 **pyproject·uv.lock을 건드리지 않는다**:
   - WS 테스트는 `TestClient`(httpx 필요) 대신 ASGI 앱을 직접 호출한다 (`await app(scope, receive, send)`, `scope["type"]="websocket"`).
   - psutil은 Live 경로에서 지연 import (지금처럼 `uv run --with psutil ...`). Replay·테스트는 psutil 없이 동작.
   - fastapi·uvicorn·psutil을 직접 의존성으로 명시하는 것은 병합 전 Sungmin 후속 작업 (`uv add` 필요, 네트워크).
7. `uv run --no-sync pytest tests/ -q` 전체 통과. dashboard/·vcaml/·SCHEMA.md 변경 없음.

## 미확인 / [가정]
- tick 큐 크기 10, flush 2초, `qoe` 공식, threshold를 연결 간 공유: 모두 [가정]. 대시보드 팀원 의견에 따라 바꿀 수 있음.
- Zoom 수신 프로세스 이름이 `zoom.exe` 하나인지 미확인 (T1 `CALL_PROCS` 그대로).
- Live tshark 실캡처 경로는 T1에서도 미검증 (사용자 실측 대기).
