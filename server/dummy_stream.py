# /// script
# requires-python = ">=3.11"
# dependencies = ["websockets>=14"]
# ///
"""docs/SCHEMA.md v1 형식의 더미 tick을 1초마다 보내는 WebSocket 서버.

vcaml·ML 의존성이 없다. inline 의존성이라 `uv run`이 프로젝트와 격리된 환경에서 실행한다
(Mac에서도 uv만 있으면 동작, submodule 불필요).

실행: uv run server/dummy_stream.py [--app meet|kakao_video|kakao_voice|zoom] [--mode replay|live|whatif] [--port 8000] [--host localhost]
폰 오버레이에서 접속: adb reverse tcp:8000 tcp:8000 후 ws://127.0.0.1:8000/ws (방화벽 변경 불필요)
접속: ws://localhost:8000/ws  (경로는 보지 않으므로 /ws 외 경로도 동작)
값은 60초 주기로 정상(0–14s) → 손상(15–44s, 30s에 최악) → 회복을 반복한다. QoE는 가짜 값이다.
client→server control 메시지는 무시한다 (What-if 연결은 W5).
"""
import argparse
import asyncio
import json
import math
import time

THRESHOLD = 70  # [가정] 기본 판정 임계값 (대시보드 슬라이더 50–90)


def tick(i: int, app: str = "meet", mode: str = "replay", now: float | None = None) -> dict:
    """i번째(초) tick 메시지."""
    phase = i % 60
    s = math.sin(math.pi * (phase - 15) / 30) if 15 <= phase < 45 else 0.0  # 손상 강도 0..1

    if app == "kakao_voice":
        est = {"fps": None, "bitrate_kbps": round(40 - 20 * s, 1), "frame_jitter_ms": None, "height": None}
    else:
        est = {
            "fps": round(30 - 20 * s, 1),
            "bitrate_kbps": round(1500 - 1100 * s, 1),
            "frame_jitter_ms": round(8 + 50 * s, 1),
            "height": 720 if s < 0.3 else 360 if s < 0.7 else 180,
        }

    truth = None
    if app == "meet" and mode != "whatif":  # 정답(getStats)은 Meet 실측에만 있다
        truth = {
            "fps": est["fps"] + 1,
            "bitrate_kbps": round(est["bitrate_kbps"] * 1.04, 1),
            "frame_jitter_ms": round(est["frame_jitter_ms"] - 1.5, 1),
            "height": est["height"],
        }

    if mode == "whatif":
        impair = {"loss_pct": round(10 * s, 1), "delay_ms": round(200 * s), "jitter_ms": round(50 * s), "bw_kbps": None}
    else:
        impair = {"loss_pct": 0, "delay_ms": 0, "jitter_ms": 0, "bw_kbps": None}

    qoe = round(90 - 60 * s, 1)
    passed = qoe >= THRESHOLD
    return {
        "ts": time.time() if now is None else now,
        "mode": mode,
        "app": app,
        "window_s": 1.0,
        "est": est,
        "truth": truth,
        "impair": impair,
        "qoe": qoe,
        "verdict": "passed" if passed else "failed",
        "advice": None if passed else "Quality degraded: check Wi-Fi signal or turn off video.",
        "validated": truth is not None,
    }


async def run(app: str, mode: str, port: int, host: str = "localhost") -> None:
    from websockets.asyncio.server import serve
    from websockets.exceptions import ConnectionClosed

    async def handler(ws):
        i = 0
        try:
            while True:
                await ws.send(json.dumps(tick(i, app, mode)))
                i += 1
                await asyncio.sleep(1)
        except ConnectionClosed:
            pass

    async with serve(handler, host, port) as server:
        print(f"dummy stream: ws://{host}:{port}/ws  app={app} mode={mode}  (Ctrl+C로 종료)", flush=True)
        await server.serve_forever()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--app", default="meet", choices=["meet", "kakao_video", "kakao_voice", "zoom"])
    p.add_argument("--mode", default="replay", choices=["replay", "live", "whatif"])
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="localhost", help="0.0.0.0 = 핫스팟 LAN에서도 접속 (방화벽 허용 필요)")
    a = p.parse_args()
    try:
        asyncio.run(run(a.app, a.mode, a.port, a.host))
    except KeyboardInterrupt:
        pass
