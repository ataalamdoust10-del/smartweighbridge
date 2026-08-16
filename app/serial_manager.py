import time
import threading
import re
from collections import deque
from dataclasses import dataclass
from typing import Optional, Callable

import serial
from serial.tools import list_ports


@dataclass
class DeviceConfig:
    enabled: bool = False
    port: str = ""          # مثال: COM3
    baud: int = 2400
    indicator: str = "GENERIC_SIGNED_5_6"
    stable_tol: float = 1.0
    stable_seconds: float = 1.2
    send_every_sec: float = 0.3
    scale_id: str = "SCALE-01"


class SerialManager:
    def __init__(self):
        self._cfg = DeviceConfig()
        self._t: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

        self.last_raw: str = ""
        self.last_weight: Optional[float] = None
        self.last_stable: bool = False
        self.last_seen_ts: float = 0.0
        self.last_error: str = ""          # NEW
        self.raw_lines = deque(maxlen=80)

    def list_ports(self):
        out = []
        for p in list_ports.comports():
            out.append({
                "device": p.device,
                "description": p.description,
                "hwid": p.hwid,
            })
        return out

    def auto_detect_port(self) -> str:
        ports = self.list_ports()
        if not ports:
            return ""
        for p in ports:
            d = (p.get("description") or "").lower()
            h = (p.get("hwid") or "").lower()
            if "cp210" in d or "silicon" in d or "cp210" in h or "silicon" in h:
                return p["device"]
        return ports[0]["device"]

    def set_config(self, cfg: DeviceConfig):
        with self._lock:
            self._cfg = cfg

    def get_config(self) -> DeviceConfig:
        with self._lock:
            return self._cfg

    def is_running(self) -> bool:
        return self._t is not None and self._t.is_alive()

    def stop(self):
        self._stop.set()
        t = self._t
        if t:
            t.join(timeout=3)
        self._t = None
        self._stop.clear()

    def start(self, on_weight: Callable[[float, bool, str], None]):
        if self.is_running():
            return
        self._stop.clear()
        self._t = threading.Thread(target=self._run, args=(on_weight,), daemon=True)
        self._t.start()

    # parser اندیکاتور شما (Generic signed 5/6 digits)
    def _parse_weight(self, line: str) -> Optional[float]:
        t = line.strip()
        if not t:
            return None
        neg = "-" in t
        digits = re.sub(r"[^0-9]", "", t)
        if not digits:
            return None
        if len(digits) < 5 or len(digits) > 6:
            return None
        w = int(digits)
        return float(-w if neg else w)

    def _split_lines(self, buf: bytearray):
        # خطوط را با \r یا \n جدا می‌کنیم (هر کدام)
        lines = []
        while True:
            npos = buf.find(b"\n")
            rpos = buf.find(b"\r")

            if npos == -1 and rpos == -1:
                break

            # نزدیک‌ترین جداکننده
            candidates = [p for p in [npos, rpos] if p != -1]
            pos = min(candidates)

            line = bytes(buf[:pos])
            del buf[:pos + 1]
            if line:
                lines.append(line)

        # جلوگیری از بزرگ شدن بافر اگر جداکننده نیامد
        if len(buf) > 4096:
            del buf[:-1024]

        return lines

    def _run(self, on_weight: Callable[[float, bool, str], None]):
        while not self._stop.is_set():
            cfg = self.get_config()

            if not cfg.enabled:
                time.sleep(0.3)
                continue
            if not cfg.port:
                time.sleep(0.3)
                continue

            try:
                self.last_error = ""
                with serial.Serial(cfg.port, cfg.baud, bytesize=8, parity="N", stopbits=1, timeout=0.2) as ser:
                    self.last_error = ""
                    buf = bytearray()

                    last_change = time.time()
                    last_w = None
                    last_send = 0.0

                    while not self._stop.is_set():
                        chunk = ser.read(128)
                        if not chunk:
                            continue

                        buf.extend(chunk)
                        for raw_line in self._split_lines(buf):
                            line = raw_line.decode("utf-8", errors="ignore")

                            w = self._parse_weight(line)
                            if w is None:
                                continue

                            now = time.time()
                            self.last_raw = line.strip()
                            self.raw_lines.appendleft(self.last_raw)
                            self.last_seen_ts = now

                            if last_w is None:
                                last_w = w
                                last_change = now
                            else:
                                if abs(w - last_w) > cfg.stable_tol:
                                    last_w = w
                                    last_change = now

                            stable = (now - last_change) >= cfg.stable_seconds

                            if now - last_send < cfg.send_every_sec:
                                continue
                            last_send = now

                            self.last_weight = last_w
                            self.last_stable = stable
                            self.last_error = ""

                            on_weight(last_w, stable, cfg.scale_id)

            except Exception as e:
                self.last_error = str(e)
                time.sleep(1)
