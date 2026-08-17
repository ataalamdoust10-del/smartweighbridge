import re
import time
import requests
import serial

SERVER_BASE = "https://smartweighbridge-production.up.railway.app"

CONFIG_URL = SERVER_BASE + "/api/agent/config"
WEIGHT_URL = SERVER_BASE + "/api/scale/weight"
STATUS_URL = SERVER_BASE + "/api/agent/status"

# باید دقیقاً با SWB_DEVICE_TOKEN در Railway یکی باشد
DEVICE_TOKEN = "SWB-DEV-9f3a1c7b-2e4d-4b1f-9a12-7c3d9e5a1f22"

HEADERS = {"X-Device-Token": DEVICE_TOKEN}


def extract_signed_weight(line: str):
    t = line.strip()

    if not t:
        return None

    neg = "-" in t
    digits = re.sub(r"[^0-9]", "", t)

    if not digits:
        return None

    if len(digits) < 5 or len(digits) > 6:
        return None

    value = int(digits)

    return -value if neg else value


def get_config(session):
    r = session.get(CONFIG_URL, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def send_weight(session, scale_id, weight, stable, raw):
    payload = {
        "scale_id": scale_id,
        "weight": float(weight),
        "stable": bool(stable),
        "raw": raw,
    }

    r = session.post(
        WEIGHT_URL,
        json=payload,
        headers=HEADERS,
        timeout=10,
    )

    r.raise_for_status()


def send_status(session, running, error="", raw="", weight=None, stable=False):
    try:
        payload = {
            "running": running,
            "error": error,
            "raw": raw,
            "weight": weight,
            "stable": stable,
        }

        session.post(
            STATUS_URL,
            json=payload,
            headers=HEADERS,
            timeout=5,
        )
    except Exception:
        pass


def main():

    print("================================")
    print(" Smart Weighbridge Scale Agent")
    print("================================")
    print("Server:", SERVER_BASE)
    print()

    session = requests.Session()

    while True:

        try:
            cfg = get_config(session)

        except Exception as e:
            print("Config error:", e)
            time.sleep(3)
            continue

        enabled = bool(cfg.get("enabled", False))

        if not enabled:
            print("Device is OFF - waiting...")
            send_status(session, False)
            time.sleep(2)
            continue

        port = str(cfg.get("port") or "").strip()
        baud = int(cfg.get("baud", 9600))

        stable_tol = float(cfg.get("stable_tol", 1.0))
        stable_seconds = float(cfg.get("stable_seconds", 1.2))
        send_every = float(cfg.get("send_every_sec", 0.3))
        scale_id = str(cfg.get("scale_id", "SCALE-01"))

        if not port:
            print("No COM port selected.")
            send_status(session, False, "No COM port selected")
            time.sleep(2)
            continue

        print()
        print("Connecting:")
        print(" Port :", port)
        print(" Baud :", baud)
        print(" Scale:", scale_id)

        try:

            with serial.Serial(
                port,
                baud,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=0.2,
            ) as ser:

                print("CONNECTED:", port, "@", baud)

                send_status(session, True)

                buf = bytearray()

                last_weight = None
                last_change = time.time()
                last_send = 0.0

                config_check = time.time()

                while True:

                    # هر 2 ثانیه بررسی کن تنظیم سایت تغییر کرده یا نه
                    if time.time() - config_check >= 2:

                        config_check = time.time()

                        try:
                            new_cfg = get_config(session)

                            new_enabled = bool(new_cfg.get("enabled", False))
                            new_port = str(new_cfg.get("port") or "").strip()
                            new_baud = int(new_cfg.get("baud", baud))

                            if (
                                not new_enabled
                                or new_port != port
                                or new_baud != baud
                            ):
                                print("Configuration changed. Reconnecting...")
                                break

                            stable_tol = float(
                                new_cfg.get("stable_tol", stable_tol)
                            )
                            stable_seconds = float(
                                new_cfg.get("stable_seconds", stable_seconds)
                            )
                            send_every = float(
                                new_cfg.get("send_every_sec", send_every)
                            )
                            scale_id = str(
                                new_cfg.get("scale_id", scale_id)
                            )

                        except Exception as e:
                            print("Config refresh error:", e)

                    chunk = ser.read(128)

                    if not chunk:
                        continue

                    buf.extend(chunk)

                    while True:

                        npos = buf.find(b"\n")
                        rpos = buf.find(b"\r")

                        positions = [
                            p for p in (npos, rpos)
                            if p != -1
                        ]

                        if not positions:
                            break

                        pos = min(positions)

                        raw_line = bytes(buf[:pos])
                        del buf[:pos + 1]

                        if not raw_line:
                            continue

                        text = raw_line.decode(
                            "utf-8",
                            errors="ignore"
                        ).strip()

                        weight = extract_signed_weight(text)

                        if weight is None:
                            continue

                        now = time.time()

                        if last_weight is None:
                            last_weight = weight
                            last_change = now

                        elif abs(weight - last_weight) > stable_tol:
                            last_weight = weight
                            last_change = now

                        stable = (
                            now - last_change
                        ) >= stable_seconds

                        if now - last_send < send_every:
                            continue

                        try:

                            send_weight(
                                session,
                                scale_id,
                                last_weight,
                                stable,
                                text,
                            )

                            send_status(
                                session,
                                True,
                                "",
                                text,
                                last_weight,
                                stable,
                            )

                            last_send = now

                            print(
                                "POST",
                                last_weight,
                                "stable=",
                                stable,
                                "raw=",
                                repr(text),
                            )

                        except Exception as e:
                            print("POST error:", e)

        except serial.SerialException as e:

            msg = str(e)

            print("Serial error:", msg)

            send_status(
                session,
                False,
                msg,
            )

            time.sleep(2)

        except Exception as e:

            msg = str(e)

            print("Agent error:", msg)

            send_status(
                session,
                False,
                msg,
            )

            time.sleep(2)


if __name__ == "__main__":
    main()
