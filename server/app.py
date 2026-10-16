"""단일 Live/Replay 입력을 모든 WebSocket 연결에 방송한다."""
import argparse
import asyncio
import csv
import json
import logging
import math
import queue
import subprocess
import threading
import time
from bisect import bisect_right
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketDisconnected

from capture.tshark_live import FIELDS, OsSampler, load_models, parse, process_lines, tshark_path
from scripts.pilot_live import select_truth
from server.diagnosis import Diagnoser
from server.features import stream_csv
from server.judge import METRICS, JudgeState, judge
from vcaml.config import project_config

log = logging.getLogger(__name__)


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--live", action="store_true")
    source.add_argument("--replay")
    ap.add_argument("--iface", default="Wi-Fi")
    ap.add_argument("--dst")
    ap.add_argument("--app", choices=("meet", "zoom"), default="meet")
    ap.add_argument("--truth")
    ap.add_argument("--os")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--schema", choices=("v1", "v1.2"), default="v1")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args(argv)
    if not math.isfinite(a.speed) or a.speed < 0:
        ap.error("--speed must be finite and nonnegative")
    if not 1 <= a.port <= 65535:
        ap.error("--port must be between 1 and 65535")
    if a.live and (a.truth or a.os or a.loop):
        ap.error("--truth, --os and --loop require --replay")
    return a


def _metrics(row):
    return {"fps": float(row["fps"]),
            "bitrate_kbps": float(row["bitrate"]) / 1000,
            "frame_jitter_ms": float(row["frame_jitter"]),
            "height": int(row["frameHeight"])}


def build_tick(row, w, options, judge_state, diagnoser, threshold, truth=None, device=None):
    if not all(math.isfinite(float(row[metric])) for metric in METRICS):
        raise ValueError("model returned nonfinite prediction")
    grades = judge(row, options.app, judge_state)
    judgement = {k: v for k, v in grades.items() if k != "validated"}
    levels = [grades[k] for k in METRICS]
    qoe = max(0, 100 - 25 * levels.count("fair") - 60 * levels.count("poor"))
    tick = {"ts": float(row["et"]), "mode": "live" if options.live else "replay",
            "app": options.app, "window_s": float(project_config["prediction_window"]),
            "est": _metrics(row), "truth": None if options.live else truth,
            "impair": {"loss_pct": 0, "delay_ms": 0, "jitter_ms": 0, "bw_kbps": None},
            "qoe": qoe, "verdict": "passed" if qoe >= threshold else "failed",
            "advice": None, "validated": not options.live and truth is not None}
    tick["est"]["fps"] = round(tick["est"]["fps"], 1)
    if options.schema == "v1.2":
        cause, confidence = diagnoser.update(w, seq_loss=None)
        tick.update(judgement=judgement, device=device,
                    diagnosis={"cause": cause, "confidence": confidence})
    return tick


def create_app(options, models=None):
    stop = threading.Event()
    process = None
    ready_models = models
    finished = None

    @asynccontextmanager
    async def lifespan(app):
        nonlocal ready_models
        if ready_models is None:
            ready_models = load_models()
        try:
            yield
        finally:
            await shutdown()
            if app.state.worker is not None:
                await app.state.worker

    app = FastAPI(lifespan=lifespan)
    app.state.threshold = 70
    app.state.failure = None
    app.state.worker = None
    app.state.clients = {}
    app.state.handlers = set()
    app.state.on_fatal = None

    def publish(tick):
        if finished is not None:
            return
        for pending, _ in list(app.state.clients.values()):
            if pending.full():
                pending.get_nowait()
            pending.put_nowait(tick)

    def finish(code, reason):
        nonlocal finished
        if finished is None:
            finished = (code, reason)
            for _, closed in list(app.state.clients.values()):
                closed.set()

    async def shutdown():
        stop.set()
        for pending, _ in list(app.state.clients.values()):
            while not pending.empty():
                pending.get_nowait()
        finish(1001, "server shutdown")
        if process is not None and process.poll() is None:
            process.terminate()
        if app.state.handlers:
            # 느린 전송은 Uvicorn의 후속 종료에 맡기되 정상 연결에는 close를 먼저 보낸다.
            await asyncio.wait(list(app.state.handlers), timeout=2)

    app.state.shutdown = shutdown

    def replay_lines():
        with open(options.replay, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or not set(FIELDS).issubset(reader.fieldnames):
                raise ValueError("packet CSV must contain the 14 tshark fields")
            previous = None
            for row in reader:
                if stop.is_set():
                    break
                fields = [row[field] or "" for field in FIELDS]
                packet = parse(fields)
                if packet is not None:
                    epoch = packet[0]
                    if previous is not None and options.speed:
                        if stop.wait(max(0, epoch - previous) / options.speed):
                            break
                    previous = epoch
                yield "\t".join(fields)

    def live_lines():
        nonlocal process
        command = [tshark_path(), "-i", options.iface, "-p", "-f", "udp", "-l", "-n",
                   "-d", "udp.port==1024-49152,rtp", "--enable-heuristic", "rtp_udp",
                   "-T", "fields", "-E", "separator=/t"]  # capture/tshark_live.py capture()와 같은 인자
        for field in FIELDS:
            command += ["-e", field]
        # stderr는 파이프로 쌓아 두면 캡처가 멈출 수 있으므로 소비하지 않는 파이프를 만들지 않는다.
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   text=True, encoding="utf-8", errors="replace")
        lines = queue.Queue(maxsize=1024)

        def read():
            try:
                for line in process.stdout:
                    while not stop.is_set():
                        try:
                            lines.put(line, timeout=0.2)
                            break
                        except queue.Full:
                            pass
            finally:
                while not stop.is_set():
                    try:
                        lines.put(None, timeout=0.2)
                        break
                    except queue.Full:
                        pass

        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        try:
            while not stop.is_set():
                try:
                    line = lines.get(timeout=2.0)
                except queue.Empty:
                    yield None  # process_lines가 열린 마지막 창을 flush한다.
                    continue
                if line is None:
                    if not stop.is_set():
                        raise RuntimeError(f"tshark exited ({process.wait()})")
                    break
                yield line
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait()
            reader.join(2)
            process.stdout.close()

    def pipeline(loop):
        sample_thread = None
        try:
            truth_rows = {}
            if options.truth:
                features = stream_csv(options.replay, dst_ip=options.dst)
                epochs = features["et"] if not features.empty else []
                for item in select_truth(options.truth, epochs).to_dict("records"):
                    values = {"fps": item["framesReceivedPerSecond"], "bitrate": item["bitrate"],
                              "frame_jitter": item["frame_jitter"], "frameHeight": item["frameHeight"]}
                    if all(v is not None and math.isfinite(float(v)) for v in values.values()):
                        truth_rows[float(item["ts"])] = _metrics(values)
            os_rows, os_times = [], []
            if options.schema == "v1.2" and options.os:
                with open(options.os, newline="", encoding="utf-8-sig") as f:
                    samples = sorted(csv.DictReader(f), key=lambda r: float(r["ts"]))
                for sample in samples:
                    values = {"cpu_pct": float(sample["cpu_pct"]),
                              "proc_cpu_pct": float(sample["call_proc_cpu_pct"]),
                              "mem_pct": float(sample["mem_pct"])}
                    if all(math.isfinite(v) for v in values.values()):
                        os_times.append(float(sample["ts"]))
                        os_rows.append(values)
            live_samples = deque(maxlen=10)
            if options.live and options.schema == "v1.2":
                # OsSampler의 CPU priming·코어 정규화 로직을 파일 없이 재사용한다.
                sampler = OsSampler(None, [])

                def sample_os():
                    sampler.ps.cpu_percent(None)
                    sampler._group_cpu()
                    while not stop.wait(1.0):
                        call, _ = sampler._group_cpu()
                        device = {"cpu_pct": sampler.ps.cpu_percent(None),
                                  "proc_cpu_pct": round(call, 1),
                                  "mem_pct": sampler.ps.virtual_memory().percent}
                        live_samples.append((time.time(), device))

                sample_thread = threading.Thread(target=sample_os, daemon=True)
                sample_thread.start()
            while not stop.is_set():
                state, diagnoser = JudgeState(), Diagnoser()

                def emit(row, features):
                    device = None
                    if options.live:
                        for timestamp, sample in reversed(list(live_samples)):
                            if timestamp <= row["et"]:
                                if row["et"] - timestamp <= 2:
                                    device = sample
                                break
                    elif os_times:
                        index = bisect_right(os_times, row["et"]) - 1
                        if index >= 0 and row["et"] - os_times[index] <= 2:
                            device = os_rows[index]
                    tick = build_tick(row, features.iloc[0], options, state, diagnoser,
                                      app.state.threshold, truth_rows.get(row["et"]), device)
                    loop.call_soon_threadsafe(publish, tick)

                source = live_lines() if options.live else replay_lines()
                process_lines(source, ready_models, lambda row: None, dst_ip=options.dst,
                              feature_emit=emit)
                if options.live or not options.loop:
                    break
                if stop.wait(0.01):
                    break
            loop.call_soon_threadsafe(finish, 1000, "replay finished")
        except Exception as exc:
            app.state.failure = exc
            log.exception("input pipeline failed")
            reason = "capture failed" if options.live else "replay failed"
            # WebSocket reason은 UTF-8 123바이트 제한. 원래 예외는 서버 로그에 남긴다.
            detail = str(exc).encode("utf-8")[:90].decode("utf-8", errors="ignore")
            loop.call_soon_threadsafe(finish, 1011, f"{reason}: {detail}")
            if options.live and app.state.on_fatal is not None:
                loop.call_soon_threadsafe(app.state.on_fatal)
        finally:
            if sample_thread is not None:
                stop.set()
                sample_thread.join(2)

    @app.websocket("/ws")
    async def websocket(ws: WebSocket):
        await ws.accept()
        if finished is not None:
            await ws.close(code=finished[0], reason=finished[1])
            return
        pending, closed = asyncio.Queue(maxsize=10), asyncio.Event()
        app.state.clients[ws] = (pending, closed)
        app.state.handlers.add(asyncio.current_task())
        if app.state.worker is None:
            app.state.worker = asyncio.create_task(asyncio.to_thread(pipeline, asyncio.get_running_loop()))

        async def send():
            while True:
                if not pending.empty():
                    tick = dict(pending.get_nowait())
                    tick["verdict"] = "passed" if tick["qoe"] >= app.state.threshold else "failed"
                    await ws.send_json(tick)
                    continue
                if closed.is_set():
                    await ws.close(code=finished[0], reason=finished[1])
                    return
                next_tick = asyncio.create_task(pending.get())
                end = asyncio.create_task(closed.wait())
                try:
                    done, _ = await asyncio.wait((next_tick, end), return_when=asyncio.FIRST_COMPLETED)
                    if next_tick in done:
                        tick = dict(next_tick.result())
                        tick["verdict"] = "passed" if tick["qoe"] >= app.state.threshold else "failed"
                        await ws.send_json(tick)
                finally:
                    for task in (next_tick, end):
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(next_tick, end, return_exceptions=True)

        async def receive():
            while True:
                try:
                    message = json.loads(await ws.receive_text())
                except (ValueError, KeyError):
                    log.info("ignored malformed control")
                    continue
                if not isinstance(message, dict) or message.get("type") != "control":
                    log.info("ignored non-control message")
                    continue
                if message.get("reset") is True:
                    app.state.threshold = 70
                threshold = message.get("threshold")
                if (isinstance(threshold, (int, float)) and not isinstance(threshold, bool)
                        and 50 <= threshold <= 90):
                    app.state.threshold = threshold
                for field, current in (("mode", "live" if options.live else "replay"), ("app", options.app)):
                    if field in message and message[field] != current:
                        log.info("ignored input change: %s", field)

        sender, receiver = asyncio.create_task(send()), asyncio.create_task(receive())
        try:
            done, _ = await asyncio.wait((sender, receiver), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
        except (WebSocketDisconnect, WebSocketDisconnected, OSError):
            # sender가 close한 같은 루프 단계에서 receiver가 receive를 부르면 WebSocketDisconnected가 난다.
            pass
        finally:
            app.state.clients.pop(ws, None)
            app.state.handlers.discard(asyncio.current_task())
            sender.cancel()
            receiver.cancel()
            await asyncio.gather(sender, receiver, return_exceptions=True)

    return app


def main(argv=None):
    import importlib.util
    import uvicorn

    options = parse_args(argv)
    if not any(importlib.util.find_spec(name) for name in ("websockets", "wsproto")):
        raise SystemExit("WebSocket runtime missing: install websockets or wsproto before running the server")
    app = create_app(options)

    class Server(uvicorn.Server):
        async def shutdown(self, sockets=None):
            # Uvicorn 기본 shutdown(1012)보다 먼저 계약의 1001을 보낸다.
            await app.state.shutdown()
            await super().shutdown(sockets)

    server = Server(uvicorn.Config(app, host="127.0.0.1", port=options.port))

    def fail():
        server.should_exit = True

    app.state.on_fatal = fail
    server.run()
    if app.state.failure is not None or not server.started:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
