"""실제 캡처·모델·WebSocket 연결 없이 ASGI Replay 계약을 검증한다."""
import asyncio
import csv
import json
import socket
import sys
import threading
from contextlib import asynccontextmanager
from functools import partial

import pandas as pd
import pytest

from capture.tshark_live import FIELDS
from server import app as ws_app
from test_schema_contract import check


def _socketpair_with_retry(make_pair, *args, **kwargs):
    # shortcut: 테스트의 10014만 최대 5회 시도; Winsock 원인 해결 뒤 제거한다.
    for attempt in range(5):
        try:
            return make_pair(*args, **kwargs)
        except OSError as exc:
            if getattr(exc, "winerror", None) != 10014 or attempt == 4:
                raise


@pytest.fixture(autouse=True)
def retry_windows_socketpair(monkeypatch):
    if sys.platform == "win32":
        monkeypatch.setattr(socket, "socketpair",
                            partial(_socketpair_with_retry, socket.socketpair))


@pytest.mark.parametrize("winerror,failures,expected_calls", [
    (10014, 0, 1), (10014, 1, 2), (10014, 4, 5),
    (10014, 5, 5), (10013, 1, 1), (None, 1, 1),
])
def test_socketpair_retry_is_bounded_and_preserves_errors(winerror, failures, expected_calls):
    calls = []
    pair = (object(), object())
    error = OSError(10014, "synthetic socketpair failure")
    error.winerror = winerror

    def make_pair(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) <= failures:
            raise error
        return pair

    if expected_calls > failures:
        assert _socketpair_with_retry(make_pair, socket.AF_INET, proto=0) is pair
    else:
        with pytest.raises(OSError) as caught:
            _socketpair_with_retry(make_pair, socket.AF_INET, proto=0)
        assert caught.value is error
    assert calls == [((socket.AF_INET,), {"proto": 0})] * expected_calls


class FakeModel:
    def __init__(self, value, gates=None):
        self.value, self.gates, self.calls = value, gates or {}, 0

    def predict(self, frame):
        assert list(frame.columns) == ["l_num_pkts"]
        self.calls += 1
        if self.calls in self.gates:
            assert self.gates[self.calls].wait(5), "test did not release prediction"
        return [self.value]


def models(gates=None):
    return {metric: (FakeModel(value, gates if metric == "fps" else None), ["l_num_pkts"])
            for metric, value in {"fps": 20.04, "bitrate": 123456,
                                  "frame_jitter": 12.5, "frameHeight": 720}.items()}


def write_packets(path, count=8):
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        for i in range(count):
            rel = i * 0.6
            writer.writerow([rel, 1000 + rel, "sender", "receiver", 17, 1028,
                             5000, 5001, 1000, "", "", "", "", ""])
    return path


@pytest.fixture
def packets(tmp_path):
    return write_packets(tmp_path / "synthetic_pkts.csv")


class Socket:
    def __init__(self, app, outgoing_limit=0):
        self.incoming, self.outgoing = asyncio.Queue(), asyncio.Queue(maxsize=outgoing_limit)
        self.incoming.put_nowait({"type": "websocket.connect"})
        self.task = asyncio.create_task(app(
            {"type": "websocket", "asgi": {"version": "3.0"}, "scheme": "ws",
             "path": "/ws", "raw_path": b"/ws", "root_path": "", "query_string": b"",
             "headers": [], "client": ("127.0.0.1", 1234),
             "server": ("127.0.0.1", 8000), "subprotocols": [], "state": {}},
            self.incoming.get, self.outgoing.put))

    async def next(self):
        return await asyncio.wait_for(self.outgoing.get(), 5)

    async def accepted(self):
        assert (await self.next())["type"] == "websocket.accept"

    async def tick(self):
        message = await self.next()
        assert message["type"] == "websocket.send"
        return json.loads(message["text"])

    async def rest(self):
        ticks = []
        while True:
            message = await self.next()
            if message["type"] == "websocket.close":
                assert message["code"] == 1000
                assert message.get("reason") == "replay finished"
                await asyncio.wait_for(self.task, 5)
                return ticks
            assert message["type"] == "websocket.send"
            ticks.append(json.loads(message["text"]))

    async def disconnect(self):
        if not self.task.done():
            self.incoming.put_nowait({"type": "websocket.disconnect", "code": 1000})
        await asyncio.wait_for(self.task, 5)


@asynccontextmanager
async def session(packets, *extra, gates=None):
    app = ws_app.create_app(ws_app.parse_args(
        ["--replay", str(packets), "--speed", "0", *extra]), models=models(gates))
    sockets = []
    async with app.router.lifespan_context(app):
        try:
            yield app, sockets
        finally:
            for gate in (gates or {}).values():
                gate.set()
            for socket in sockets:
                await socket.disconnect()
    assert app.state.failure is None


async def until(predicate):
    async def wait():
        while not predicate():
            await asyncio.sleep(0)
    await asyncio.wait_for(wait(), 5)


@pytest.mark.parametrize("schema", ["v1", "v1.2"])
def test_teams_live_tick_is_unvalidated(schema):
    options = ws_app.parse_args(["--live", "--app", "teams", "--schema", schema])
    assert options.app == "teams"
    row = {"et": 1001, "fps": 30, "bitrate": 1500000,
           "frame_jitter": 10, "frameHeight": 720}
    features = dict.fromkeys(("l_num_bytes", "l_num_pkts", "t_q1", "t_q2", "t_std", "t_max"), 1)
    tick = ws_app.build_tick(row, features, options, ws_app.JudgeState(),
                             ws_app.Diagnoser(), 70, truth=ws_app._metrics(row))
    assert tick["app"] == "teams" and tick["mode"] == "live"
    assert tick["truth"] is None and tick["validated"] is False
    if schema == "v1":
        check(tick)
    else:
        expected = ws_app.judge(row, "meet", ws_app.JudgeState())
        expected.pop("validated")
        assert tick["judgement"] == expected


def test_replay_ticks_match_v1_and_truth_uses_exact_epoch(packets, monkeypatch):
    truth = pd.DataFrame({"ts": [1000, 1001, 1002, 1004],
                          "framesReceivedPerSecond": [99, 29.5, 30, 28],
                          "bitrate": [999000, 234500, 240000, 220000],
                          "frame_jitter": [1, 8.5, float("nan"), 9],
                          "frameHeight": [1080, 1080, 1080, 720]})
    calls = []

    def select_truth(path, epochs):
        calls.append((path, list(epochs)))
        return truth

    monkeypatch.setattr(ws_app, "select_truth", select_truth)

    async def run():
        async with session(packets, "--truth", "synthetic_dump.json") as (app, sockets):
            socket = Socket(app)
            sockets.append(socket)
            await socket.accepted()
            ticks = await socket.rest()
        assert [tick["ts"] for tick in ticks] == [1001, 1002, 1003, 1004]
        for tick in ticks:
            check(tick)
            assert tick["mode"] == "replay"
            assert tick["est"] == {"fps": 20.0, "bitrate_kbps": 123.456,
                                   "frame_jitter_ms": 12.5, "height": 720}
        assert ticks[0]["truth"] == {"fps": 29.5, "bitrate_kbps": 234.5,
                                     "frame_jitter_ms": 8.5, "height": 1080}
        assert ticks[1]["truth"] is None  # 일부가 NaN인 truth는 쓰지 않는다.
        assert ticks[2]["truth"] is None  # 가까운 초의 정답으로 채우지 않는다.
        assert ticks[3]["truth"]["fps"] == 28
        assert calls and {1001, 1002, 1003, 1004} <= set(calls[0][1])

    asyncio.run(run())


def test_control_changes_next_tick_and_reset_restores_default(packets):
    gates = {2: threading.Event(), 3: threading.Event()}

    async def run():
        async with session(packets, gates=gates) as (app, sockets):
            socket = Socket(app)
            sockets.append(socket)
            await socket.accepted()
            first = await socket.tick()
            assert first["qoe"] == 75 and first["verdict"] == "passed"
            for text in ("invalid json", "[]", '{"type":"other","threshold":90}',
                         '{"type":"control","threshold":99}'):
                socket.incoming.put_nowait({"type": "websocket.receive", "text": text})
            await until(socket.incoming.empty)
            assert app.state.threshold == 70
            socket.incoming.put_nowait({"type": "websocket.receive", "text":
                                      json.dumps({"type": "control", "threshold": 80})})
            await until(lambda: app.state.threshold == 80)
            gates[2].set()
            second = await socket.tick()
            assert second["qoe"] == 75 and second["verdict"] == "failed"
            socket.incoming.put_nowait({"type": "websocket.receive", "text":
                                      json.dumps({"type": "control", "reset": True})})
            await until(lambda: app.state.threshold == 70)
            gates[3].set()
            rest = await socket.rest()
            assert rest and all(tick["verdict"] == "passed" for tick in rest)
            for tick in [first, second, *rest]:
                check(tick)

    asyncio.run(run())


def test_broadcast_runs_once_and_survives_one_disconnect(packets):
    gates = {1: threading.Event(), 2: threading.Event()}
    fake = models(gates)

    async def run():
        app = ws_app.create_app(ws_app.parse_args(
            ["--replay", str(packets), "--speed", "0"]), models=fake)
        async with app.router.lifespan_context(app):
            one, two = Socket(app), Socket(app)
            try:
                await one.accepted()
                await two.accepted()
                gates[1].set()
                first, second = await one.tick(), await two.tick()
                assert first == second
                await one.disconnect()
                gates[2].set()
                rest = await two.rest()
                assert [tick["ts"] for tick in [second, *rest]] == [1001, 1002, 1003, 1004]
                assert all(tick["truth"] is None and not tick["validated"] for tick in rest)
                for tick in [first, *rest]:
                    check(tick)
            finally:
                for gate in gates.values():
                    gate.set()
                await one.disconnect()
                await two.disconnect()
        assert app.state.failure is None
        assert all(model.calls == 4 for model, _ in fake.values())

    asyncio.run(run())


def test_v12_os_uses_latest_past_sample_and_expires_after_two_seconds(packets, tmp_path):
    os_csv = tmp_path / "synthetic_os.csv"
    os_csv.write_text("ts,cpu_pct,call_proc_cpu_pct,monitor_cpu_pct,mem_pct,call_core_pct\n"
                      "1000,10,2,1,50,10\n1001,20,3,1,60,20\n1005,99,99,99,99,99\n")

    async def run():
        async with session(packets, "--schema", "v1.2", "--os", str(os_csv)) as (app, sockets):
            socket = Socket(app)
            sockets.append(socket)
            await socket.accepted()
            ticks = await socket.rest()
        assert len(ticks) == 4
        for tick in ticks:
            v1 = {key: value for key, value in tick.items()
                  if key not in {"judgement", "device", "diagnosis"}}
            check(v1)
            assert "validated" not in tick["judgement"]
            assert {"cause", "confidence"} <= tick["diagnosis"].keys()
        expected = {"cpu_pct": 20, "proc_cpu_pct": 3, "mem_pct": 60, "call_core_pct": 20}
        assert [tick["device"] for tick in ticks] == [expected, expected, expected, None]

    asyncio.run(run())


def test_v12_old_os_csv_sets_device_to_none(packets, tmp_path):
    os_csv = tmp_path / "old_os.csv"
    os_csv.write_text("ts,cpu_pct,call_proc_cpu_pct,monitor_cpu_pct,mem_pct\n"
                      "1000,10,2,1,50\n", encoding="utf-8")

    async def run():
        async with session(packets, "--schema", "v1.2", "--os", str(os_csv)) as (app, sockets):
            socket = Socket(app)
            sockets.append(socket)
            await socket.accepted()
            ticks = await socket.rest()
        assert ticks and all(tick["device"] is None for tick in ticks)
        assert all(tick["diagnosis"]["cause"] != "device_cpu" for tick in ticks)

    asyncio.run(run())


def test_replay_passes_flow_and_call_core_pct_to_diagnoser(tmp_path):
    packets = tmp_path / "cpu_pkts.csv"
    with packets.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for i in range(300):
            rel = i / 10
            writer.writerow([rel, 1000 + rel, "sender", "receiver", 17, 1028,
                             5000, 5001, 1000, "123", 100, i, 96, 0])
    os_csv = tmp_path / "cpu_os.csv"
    os_csv.write_text("ts,cpu_pct,call_proc_cpu_pct,monitor_cpu_pct,mem_pct,call_core_pct\n"
                      + "".join(f"{1000 + i},25,10,1,50,95\n" for i in range(31)), encoding="utf-8")

    async def run():
        async with session(packets, "--schema", "v1.2", "--os", str(os_csv)) as (app, sockets):
            socket = Socket(app)
            sockets.append(socket)
            await socket.accepted()
            ticks = await socket.rest()
        assert len(ticks) >= 20
        cpu_ticks = [tick for tick in ticks if tick["diagnosis"]["cause"] == "device_cpu"]
        assert cpu_ticks
        assert all(tick["device"]["call_core_pct"] == 95 for tick in ticks)
        assert all(tick["device"]["proc_cpu_pct"] == 10 for tick in ticks)
        assert all(tick["diagnosis"]["confidence"] > 0 for tick in cpu_ticks)

    asyncio.run(run())


def test_shutdown_closes_connection_with_1001_and_stops_worker(packets):
    async def run():
        # 다음 패킷 대기는 stop Event로 즉시 끊어져야 한다.
        app = ws_app.create_app(ws_app.parse_args(
            ["--replay", str(packets), "--speed", "0.001", "--loop"]), models=models())
        async with app.router.lifespan_context(app):
            socket = Socket(app)
            await socket.accepted()
        message = await socket.next()
        assert message == {"type": "websocket.close", "code": 1001,
                           "reason": "server shutdown"}
        await socket.disconnect()
        assert app.state.worker.done() and app.state.failure is None
        assert not app.state.clients

    asyncio.run(run())


def test_live_capture_start_failure_closes_with_1011(monkeypatch):
    def fail_capture(*args, **kwargs):
        raise OSError("synthetic")

    monkeypatch.setattr(ws_app.subprocess, "Popen", fail_capture)

    async def run():
        fake = models()
        app = ws_app.create_app(ws_app.parse_args(["--live"]), models=fake)
        async with app.router.lifespan_context(app):
            socket = Socket(app)
            await socket.accepted()
            message = await socket.next()
            assert message == {"type": "websocket.close", "code": 1011,
                               "reason": "capture failed: synthetic"}
            await socket.disconnect()
        assert isinstance(app.state.failure, OSError)
        assert app.state.worker.done()
        assert all(model.calls == 0 for model, _ in fake.values())

    asyncio.run(run())


def test_slow_client_drops_old_ticks_without_blocking_replay(tmp_path):
    packets = write_packets(tmp_path / "long_pkts.csv", count=40)
    gates = {2: threading.Event()}

    async def run():
        async with session(packets, gates=gates) as (app, sockets):
            socket = Socket(app, outgoing_limit=1)
            sockets.append(socket)
            await socket.accepted()
            await until(lambda: socket.outgoing.qsize() == 1)
            gates[2].set()
            await asyncio.wait_for(app.state.worker, 5)
            pending, _ = next(iter(app.state.clients.values()))
            assert pending.qsize() == pending.maxsize == 10
            ticks = await socket.rest()
            expected = [int(1000 + i * 0.6) for i in range(2, 40, 2)] + [1023]
            assert [tick["ts"] for tick in ticks[-10:]] == expected[-10:]
            assert len(ticks) < len(expected)
            for tick in ticks:
                check(tick)

    asyncio.run(run())
