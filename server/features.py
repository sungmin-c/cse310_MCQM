"""스트리밍 1초 윈도우 feature 추출 — vcaml 배치(ip-udp-ml 경로)와 같은 값을 낸다.

vcaml 배치 규칙 (net_utils.readIpUdpFile, feature_extraction._buildIntervals):
- 패킷 필터: UDP, 수신 dst IP 하나(UDP 바이트 합이 가장 큰 것), udp.length > video_thresh(306)
- 윈도우 경계: 윈도우 첫 패킷 시각 + prediction_window(1s)를 '초과'한 패킷이 새 윈도우를 연다
  (고정 1초 격자가 아니라 패킷이 경계를 정한다)
- IAT: 전역 연속 간격. 윈도우 첫 패킷의 IAT = 직전 윈도우 마지막 패킷과의 간격,
  맨 첫 패킷은 캡처 시작(time_relative 0)부터의 간격
- et: 다음 윈도우를 연 패킷의 epoch, 마지막 윈도우는 마지막 패킷 epoch (int로 자름)

통계 계산 자체는 vcaml FeatureExtractor를 그대로 호출한다 (재구현하지 않음).
"""
import math
from collections import defaultdict

import pandas as pd

from vcaml.config import project_config
from vcaml.feature_extraction import FeatureExtractor


class WindowFeatures:
    """패킷을 하나씩 push하면 윈도우가 닫힐 때마다 feature 1행(DataFrame)을 돌려준다."""

    def __init__(self, vca="meet", dataset="in_lab_data", dst_ip=None,
                 feature_subset=("LSTATS", "TSTATS"), config=project_config):
        self.fe = FeatureExtractor(list(feature_subset), config, vca, dataset)
        self.window_s = config["prediction_window"]
        self.video_thresh = config["video_thresh"]
        self.udp_proto = config["udp_proto"]
        # dst_ip=None이면 지금까지 UDP 바이트가 가장 많은 dst를 수신자로 본다 (배치는 파일 전체 기준).
        # ponytail: 초반 몇 초는 배치와 다른 dst를 고를 수 있음. Live에서는 폰 IP를 넘기는 쪽이 정확.
        self.dst_ip = dst_ip
        self._dst_bytes = defaultdict(float)
        self._rows = []          # 현재 윈도우: (epoch, rel, length)
        self._start = None       # 현재 윈도우 첫 패킷 rel
        self._prev_rel = 0.0     # 직전 수락 패킷 rel (캡처 시작 = 0)
        self._win_prev = 0.0     # 현재 윈도우 시작 직전 패킷 rel
        self.last_epoch = None   # 마지막 수락 패킷 epoch (Live에서 무패킷 감지용)

    def push(self, epoch, rel, ip_dst, ip_proto, udp_length):
        """패킷 1개. 이 패킷이 직전 윈도우를 닫으면 그 윈도우의 feature를, 아니면 None."""
        if ip_proto != self.udp_proto:
            return None
        if self.dst_ip is None:
            self._dst_bytes[ip_dst] += udp_length
            if ip_dst != max(self._dst_bytes, key=self._dst_bytes.get):
                return None
        elif ip_dst != self.dst_ip:
            return None
        if not udp_length > self.video_thresh:
            return None

        out = None
        if self._start is not None and rel - self._start > self.window_s:
            out = self._emit(et=epoch)
        if self._start is None:
            self._start = rel
            self._win_prev = self._prev_rel
        self._rows.append((epoch, rel, udp_length))
        self._prev_rel = rel
        self.last_epoch = epoch
        return out

    def flush(self):
        """열려 있는 윈도우를 강제로 닫는다 (파일 끝, 또는 Live에서 패킷이 끊겼을 때)."""
        if not self._rows:
            return None
        return self._emit(et=self._rows[-1][0])

    def _emit(self, et):
        df = pd.DataFrame(self._rows, columns=["time", "time_normed", "length"])
        # 첫 IAT가 '직전 패킷과의 간격'이 되도록 기준점을 옮긴다 (간격 자체는 그대로).
        df["time_normed"] = df["time_normed"] - self._win_prev
        feats = self.fe.extract_features(df)
        feats["et"] = int(et)
        self._rows, self._start = [], None
        return feats


class RtpSeqLoss:
    """RTP 순번 빈칸으로 본 손실률. RTP 헤더는 SRTP에서도 평문이라 네트워크에서 보인다.

    RTP를 해석할 수 없는 앱(예: 확인 전의 Kakao)에서는 쓰지 않는다 → 진단은 IP/UDP 규칙만 사용.
    순서가 뒤바뀐 패킷(diff ≤ 0)은 무시한다. diff가 3000을 넘으면 순번 재시작으로 보고 무시한다.
    """

    def __init__(self):
        self._last = {}
        self._recv = 0
        self._gaps = 0

    def push(self, ssrc, seq):
        if ssrc is None or seq is None:
            return
        last = self._last.get(ssrc)
        if last is not None:
            diff = (seq - last) % 65536
            if diff == 0 or diff > 3000:
                return
            self._gaps += diff - 1
        self._last[ssrc] = seq
        self._recv += 1

    def take(self):
        """직전 take 이후의 손실률. 받은 RTP 패킷이 없으면 None."""
        n = self._recv + self._gaps
        out = self._gaps / n if self._recv else None
        self._recv = self._gaps = 0
        return out


def rows_from_csv(path):
    """vcaml 형식 CSV(tshark 14필드)를 push 인자 튜플로 순서대로 낸다.

    readIpUdpFile과 같은 정리: ip.proto가 비었거나 '17,17'처럼 여러 값이면 버린다.
    """
    df = pd.read_csv(path, usecols=["frame.time_relative", "frame.time_epoch",
                                    "ip.dst", "ip.proto", "udp.length"])
    for rel, epoch, dst, proto, ulen in df.itertuples(index=False):
        if isinstance(proto, float) and math.isnan(proto):
            continue
        proto = str(proto)
        if "," in proto:
            continue
        ulen = 0.0 if isinstance(ulen, float) and math.isnan(ulen) else ulen
        yield epoch, rel, dst, int(float(proto)), ulen


def stream_csv(path, vca="meet", dataset="in_lab_data", dst_ip=None):
    """CSV 하나를 처음부터 끝까지 스트리밍으로 처리한 feature 표 (Replay·검증용)."""
    wf = WindowFeatures(vca=vca, dataset=dataset, dst_ip=dst_ip)
    parts = [f for r in rows_from_csv(path) if (f := wf.push(*r)) is not None]
    last = wf.flush()
    if last is not None:
        parts.append(last)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
