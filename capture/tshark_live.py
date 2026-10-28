"""tshark 실시간 캡처와 1초 추정. CLI는 scripts/pilot_live.py capture를 사용한다."""
import csv
import os
import pickle
import shutil
import subprocess
import threading
import time
import warnings
from pathlib import Path

OUT = Path("data/pilot")
METRICS = {"fps": "framesReceivedPerSecond", "bitrate": "bitrate",
           "frame_jitter": "frame_jitter", "frameHeight": "frameHeight"}
FIELDS = ["frame.time_relative", "frame.time_epoch", "ip.src", "ip.dst", "ip.proto", "ip.len",
          "udp.srcport", "udp.dstport", "udp.length", "rtp.ssrc", "rtp.timestamp", "rtp.seq",
          "rtp.p_type", "rtp.marker"]                     # vcaml pcap2csv와 같은 14필드
CALL_PROCS = {"chrome.exe", "zoom.exe"}


def core_util(percpu, cores):
    values = [percpu[i] for i in cores] if cores else percpu
    return sum(values) / len(values) if values else 0.0


def tshark_path():
    return shutil.which("tshark") or r"C:\Program Files\Wireshark\tshark.exe"


def load_models(folder="data/models"):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = {}
        for m in METRICS:
            with open(Path(folder) / f"meet_{m}_cv1.pkl", "rb") as f:
                obj = pickle.load(f)
            out[m] = (obj.estimator, list(obj.featureMatrix.columns))
    return out


class OsSampler(threading.Thread):
    """1초마다 CPU를 기록한다. 프로세스 CPU%는 전체 코어 대비(0–100)로 나눠 적는다."""

    def __init__(self, path, monitor_pids):
        super().__init__(daemon=True)
        import psutil
        self.ps, self.path, self.monitor_pids = psutil, path, set(monitor_pids)
        self.stop = threading.Event()
        self.ncpu = psutil.cpu_count() or 1
        self.procs = {}

    def _group_cpu(self):
        call = mon = 0.0
        for p in self.ps.process_iter(["name"]):
            name = (p.info["name"] or "").lower()
            if name not in CALL_PROCS and p.pid not in self.monitor_pids:
                continue
            q = self.procs.setdefault(p.pid, p)
            try:
                c = q.cpu_percent(None) / self.ncpu
            except self.ps.Error:
                continue
            if p.pid in self.monitor_pids:
                mon += c
            else:
                call += c
        return call, mon

    def call_core_pct(self):
        cores = set()
        for p in self.ps.process_iter(["name"]):
            if (p.info["name"] or "").lower() in CALL_PROCS:
                try:
                    cores.update(p.cpu_affinity())
                except self.ps.Error:
                    continue
        return core_util(self.ps.cpu_percent(None, percpu=True), cores)

    def run(self):
        self.ps.cpu_percent(None)
        self.ps.cpu_percent(None, percpu=True)
        self._group_cpu()
        with open(self.path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts", "cpu_pct", "call_proc_cpu_pct", "monitor_cpu_pct", "mem_pct",
                        "call_core_pct"])
            while not self.stop.wait(1.0):
                call, mon = self._group_cpu()
                w.writerow([round(time.time(), 3), self.ps.cpu_percent(None), round(call, 1),
                            round(mon, 1), self.ps.virtual_memory().percent,
                            round(self.call_core_pct(), 1)])
                f.flush()


def parse(fields):
    """readIpUdpFile과 같은 정리: proto가 비었거나 '17,17'처럼 여러 값이면 버린다."""
    rel, epoch, dst, proto, ulen = fields[0], fields[1], fields[3], fields[4], fields[8]
    if not proto or "," in proto or not dst or "," in dst:
        return None
    return float(epoch), float(rel), dst, int(proto), float(ulen) if ulen and "," not in ulen else 0.0


def tshark_cmd(iface, snaplen=0, duration=0):
    """capture()와 서버 live가 같이 쓰는 tshark 명령. snaplen > 0이면 패킷 앞 N바이트만 잡는다.

    vcaml 특징은 IP/UDP 헤더 길이만 쓰고 RTP 헤더는 앞 12바이트라, 96바이트면 14필드가 그대로 나온다.
    """
    # 1024-49152 밖 포트(P2P 흐름은 양쪽 모두 49152 초과일 수 있음, P2-1)는 휴리스틱으로 RTP를 해석한다
    cmd = [tshark_path(), "-i", iface, "-p", "-f", "udp", "-l", "-n"]
    if snaplen:
        cmd += ["-s", str(snaplen)]
    cmd += ["-d", "udp.port==1024-49152,rtp", "--enable-heuristic", "rtp_udp", "-T", "fields", "-E", "separator=/t"]
    for fld in FIELDS:
        cmd += ["-e", fld]
    if duration:
        cmd += ["-a", f"duration:{duration}"]
    return cmd


def process_lines(lines, models, emit, *, dst_ip=None, packet_writer=None, window_features=None,
                  feature_emit=None, every=1):
    """tshark 탭 구분 라인 iterable을 처리하고 윈도우마다 emit(row)을 호출한다.

    row는 et, n_pkts, METRICS의 원시 예측값, tick_ms를 담는다 (CSV 반올림은 호출자 담당).
    models는 load_models() 형식. packet_writer는 선택적인 csv.writer이며 원본 14필드를 쓴다.
    EOF·중단 시 마지막 윈도우도 내보낸다. 파일·프로세스는 열지 않는다.
    window_features를 주면 해당 인스턴스를 쓰고, 없으면 WindowFeatures를 만든다.
    feature_emit(row, w, flow)는 진단용 feature와 직전 창의 주 흐름을 받는다. None 라인은 idle flush 신호다.
    """
    if window_features is None:
        from server.features import WindowFeatures
        window_features = WindowFeatures(vca="meet", dst_ip=dst_ip)

    flows = {}
    windows = 0

    def estimate(w):
        nonlocal windows
        windows += 1
        if (windows - 1) % every:  # --every N: 캡처는 매 창 계속하고 모델 추론은 N창마다 한 번 (경량 모드)
            flows.clear()
            return
        t = time.perf_counter()
        pred = {m: float(est.predict(w[cols])[0]) for m, (est, cols) in models.items()}
        ms = (time.perf_counter() - t) * 1000
        row = {"et": int(w["et"].iloc[0]), "n_pkts": int(w["l_num_pkts"].iloc[0]),
               **pred, "tick_ms": ms}
        emit(row)
        if feature_emit is not None:
            feature_emit(row, w, max(flows, key=flows.get, default=None))
        flows.clear()

    try:
        for line in lines:
            if line is None:
                if (w := window_features.flush()) is not None:
                    estimate(w)
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < len(FIELDS):
                continue
            if packet_writer is not None:
                packet_writer.writerow(fields)
            r = parse(fields)
            if r is not None:
                if (w := window_features.push(*r)) is not None:
                    estimate(w)
                if (feature_emit is not None and r[3] == window_features.udp_proto
                        and r[4] > window_features.video_thresh):
                    target = window_features.receiver
                    source, port = fields[2], fields[6]
                    if r[2] == target and source and port and "," not in source and "," not in port:
                        flow = (source, int(port))
                        flows[flow] = flows.get(flow, 0.0) + r[4]
    finally:
        if (w := window_features.flush()) is not None:
            estimate(w)


def capture(a):
    from server.features import WindowFeatures
    OUT.mkdir(parents=True, exist_ok=True)
    models = load_models()
    wf = WindowFeatures(vca="meet", dst_ip=a.dst)
    cmd = tshark_cmd(a.iface, getattr(a, "snaplen", 0), a.duration)
    ts = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    samp = None
    if not a.no_os:
        samp = OsSampler(OUT / f"{a.name}_os.csv", [os.getpid(), ts.pid])
        samp.start()

    pk = open(OUT / f"{a.name}_pkts.csv", "w", newline="")
    es = open(OUT / f"{a.name}_est.csv", "w", newline="")
    pw, ew = csv.writer(pk), csv.writer(es)
    pw.writerow(FIELDS)
    ew.writerow(["et", "n_pkts", *METRICS, "tick_ms"])

    def emit(row):
        ms = row["tick_ms"]
        ew.writerow([row["et"], row["n_pkts"],
                     *(round(row[m], 2) for m in METRICS), round(ms, 1)])
        es.flush()
        print(f"{time.strftime('%H:%M:%S')} fps {row['fps']:5.1f}  kbps {row['bitrate'] / 1000:7.0f}  "
              f"h {row['frameHeight']:4.0f}  jit {row['frame_jitter']:5.1f}  ({ms:.0f} ms)", flush=True)

    print(f"capture → {OUT}/{a.name}_*.csv   (멈추기: Ctrl+C)", flush=True)
    try:
        process_lines(ts.stdout, models, emit, packet_writer=pw, window_features=wf,
                      every=getattr(a, "every", 1))
    except KeyboardInterrupt:
        pass
    finally:
        ts.terminate()
        if samp:
            samp.stop.set()
            samp.join(2)
        pk.close()
        es.close()
        print("dst ip:", wf.receiver)


