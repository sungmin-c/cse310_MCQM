"""W1 파일럿 P3 (H1) — 모니터가 통화를 망치는가. 모니터 끔/켬을 번갈아 돌리고 단계 시각을 기록한다.

순서: warm(끔, Meet 연결 전환 대기) → --modes 의 단계들을 한 바퀴로 하고 --pairs 바퀴, 바퀴마다 시작 단계를 돌린다(시간 drift 상쇄).
  --modes 기본 off,on (P3와 같음). 단계 종류 (P5, docs/design/overhead_weekend.md):
    off      아무것도 안 함
    on       `pilot_live.py capture --duration step --name <name>_onK` (tshark + 모델 + psutil)
    capture  tshark만 (출력 버림)
    server   `python -m server.app --live` (tshark + 모델 + WS) + 화면 없는 WS 클라이언트, 포트 8000
    widget   server와 같되 포트 8001. widget_proxy.html(PiP)을 미리 열어 두면 그 페이지가 이 포트에 붙는다
    os       psutil 1 Hz 기록만 (tshark·모델 없음)
  --snaplen/--every 는 on·capture·server·widget 에 적용, --pin-monitor N 은 모니터 프로세스 트리를 코어 0..N-1에 묶는다
  (모니터는 단계가 끝나면 종료되므로 되돌릴 affinity가 남지 않는다. Chrome 코어 고정은 cpu_load.py --pin이 담당)
  전체 구간: psutil 1 Hz 기록 → data/pilot/<name>_os.csv (총 CPU, Chrome CPU)
  단계 시각: data/pilot/<name>_phase.csv (ts, phase)
  메모리: data/pilot/<name>_mem.csv (가용 MB, 시스템 %, Chrome RSS, 모니터 RSS). 단계별 평균은 phase.csv로 나눠 비교
통화 쪽 영향(수신·디코드·freeze·송신 fps)은 끝난 뒤 webrtc-internals dump로 단계별 비교한다.

실행 (repo 루트):
  uv run --with psutil python scripts/overhead_ab.py --name p3_meet1 --dst 172.30.1.51
"""
import argparse
import csv
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture.tshark_live import CALL_PROCS, OUT, OsSampler, tshark_cmd  # noqa: E402


def sample_mem(path, stop, mon):
    """1 Hz 메모리 기록 → <name>_mem.csv. 시스템 가용 MB, 통화 프로세스(chrome.exe 등) RSS 합,
    모니터(켬 단계의 pilot_live 프로세스 + 자식 tshark) RSS 합. RSS 합은 공유 페이지를 중복 세므로 과대 [가정]이고,
    프로세스 간 비교보다 끔/켬 단계 간 차이와 가용 MB 변화를 본다."""
    import psutil
    mb = 2**20
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "avail_mb", "mem_pct", "call_rss_mb", "monitor_rss_mb", "monitor_cpu_pct"])
        procs, ncpu = {}, psutil.cpu_count() or 1   # cpu_percent는 이전 호출 이후 평균이라 Process 객체를 유지한다
        while not stop.wait(1.0):
            call = 0
            for p in psutil.process_iter(["name", "memory_info"]):
                if (p.info["name"] or "").lower() in CALL_PROCS and p.info["memory_info"]:
                    call += p.info["memory_info"].rss
            monitor = mcpu = 0
            if mon["proc"] is not None and mon["proc"].poll() is None:
                try:
                    root = psutil.Process(mon["proc"].pid)
                    for q in [root, *root.children(recursive=True)]:
                        q = procs.setdefault(q.pid, q)
                        monitor += q.memory_info().rss
                        mcpu += q.cpu_percent(None) / ncpu
                except psutil.Error:
                    pass
            vm = psutil.virtual_memory()
            w.writerow([round(time.time(), 3), round(vm.available / mb), vm.percent,
                        round(call / mb), round(monitor / mb), round(mcpu, 2)])
            f.flush()


def pin_tree(proc, cores, stop):
    """proc와 자손(tshark 등, 나중에 뜨는 것 포함)을 cores에 묶는다. 0.5초마다 다시 적용."""
    import psutil
    while not stop.wait(0.5):
        try:
            root = psutil.Process(proc.pid)
            for q in [root, *root.children(recursive=True)]:
                try:
                    q.cpu_affinity(cores)
                except psutil.Error:
                    pass
        except psutil.Error:
            return


def drain_ws(port, stop):
    """서버는 첫 WS 클라이언트가 붙어야 입력을 시작한다. 화면 없이 메시지만 버리는 클라이언트."""
    from websockets.sync.client import connect
    deadline = time.time() + 30
    while not stop.is_set() and time.time() < deadline:
        try:
            with connect(f"ws://127.0.0.1:{port}/ws", open_timeout=2) as ws:
                while not stop.is_set():
                    try:
                        ws.recv(timeout=1)
                    except TimeoutError:
                        pass
            return
        except Exception:
            stop.wait(1.0)


def start_monitor(mode, a, sec, k):
    """모드별 모니터 프로세스를 띄워 Popen을 돌려준다 (off는 None)."""
    here = Path(__file__).parent
    tune = (["--snaplen", str(a.snaplen)] if a.snaplen else []) + (["--every", str(a.every)] if a.every > 1 else [])
    if mode == "on":
        return subprocess.Popen(
            [sys.executable, str(here / "pilot_live.py"), "capture", "--name", f"{a.name}_on{k}",
             "--iface", a.iface, "--dst", a.dst, "--duration", str(sec), *tune], stdout=subprocess.DEVNULL)
    if mode == "capture":
        return subprocess.Popen(tshark_cmd(a.iface, a.snaplen, sec), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
    if mode in ("server", "widget"):
        port = 8000 if mode == "server" else 8001
        return subprocess.Popen(
            [sys.executable, "-m", "server.app", "--live", "--iface", a.iface, "--dst", a.dst,
             "--port", str(port), *tune], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if mode == "os":
        return subprocess.Popen([sys.executable, str(here / "pilot_live.py"), "osonly", "--duration", str(sec)],
                                stdout=subprocess.DEVNULL)
    raise SystemExit(f"알 수 없는 단계: {mode}")


def stop_tree(proc):
    import psutil
    try:
        root = psutil.Process(proc.pid)
        for q in [*root.children(recursive=True), root]:
            try:
                q.terminate()
            except psutil.Error:
                pass
    except psutil.Error:
        pass
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        proc.kill()


def run_phase(mode, a, sec, k, mon):
    if mode == "off":
        time.sleep(sec)
        return
    mon["proc"] = start_monitor(mode, a, sec, k)
    stop = threading.Event()
    if a.pin_monitor:
        threading.Thread(target=pin_tree, args=(mon["proc"], list(range(a.pin_monitor)), stop), daemon=True).start()
    if mode in ("server", "widget"):
        threading.Thread(target=drain_ws, args=(8000 if mode == "server" else 8001, stop), daemon=True).start()
    try:
        if mode in ("on", "capture", "os"):
            mon["proc"].wait()          # duration으로 스스로 끝난다
        else:
            time.sleep(sec)             # 서버는 끝이 없어 시간이 되면 끈다
    finally:
        stop.set()
        stop_tree(mon["proc"])
        mon["proc"] = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--dst", required=True, help="노트북 IP")
    ap.add_argument("--iface", default="Wi-Fi")
    ap.add_argument("--step", type=int, default=50, help="단계당 초")
    ap.add_argument("--warm", type=int, default=150, help="시작 전 대기 초 (Meet PeerConnection 전환)")
    ap.add_argument("--pairs", type=int, default=3, help="바퀴 수 (모든 단계를 한 번씩 도는 것이 한 바퀴)")
    ap.add_argument("--modes", default="off,on", help="쉼표 구분: off,on,capture,server,widget,os")
    ap.add_argument("--snaplen", type=int, default=0)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--pin-monitor", type=int, default=0, help="모니터를 코어 0..N-1에 묶음 (0이면 끔)")
    a = ap.parse_args()
    modes = a.modes.split(",")

    OUT.mkdir(parents=True, exist_ok=True)
    samp = OsSampler(OUT / f"{a.name}_os.csv", [])
    samp.start()
    mon = {"proc": None}
    mem = threading.Thread(target=sample_mem, args=(OUT / f"{a.name}_mem.csv", samp.stop, mon), daemon=True)
    mem.start()
    phases = [("warm", a.warm)] + [(modes[(i + r) % len(modes)], a.step)
                                    for r in range(a.pairs) for i in range(len(modes))]
    k = 0
    with open(OUT / f"{a.name}_phase.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "phase"])
        try:
            for phase, sec in phases:
                w.writerow([round(time.time(), 3), phase])
                f.flush()
                print(f"{time.strftime('%H:%M:%S')} {phase} {sec}초", flush=True)
                if phase == "warm":
                    time.sleep(sec)
                    continue
                if phase == "widget":
                    print("  위젯 단계: widget_proxy.html의 PiP 창이 통화 창 위에 떠 있어야 한다 (포트 8001)", flush=True)
                if phase == "on":
                    k += 1
                run_phase(phase, a, sec, k, mon)
        except KeyboardInterrupt:
            pass
        finally:
            w.writerow([round(time.time(), 3), "end"])
            samp.stop.set()
            samp.join(2)
            mem.join(2)
            print("끝", flush=True)


if __name__ == "__main__":
    main()
