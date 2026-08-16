import re
import time
import requests
import serial

# =========================
# 1) تنظیمات سریال (طبق TeraTerm شما)
# =========================
SERIAL_PORT = "COM3"
SERIAL_BAUD = 2400
BYTESIZE = 8
PARITY = "N"
STOPBITS = 1
TIMEOUT = 1

# =========================
# 2) تنظیمات سرور Railway (سایت اصلی)
# =========================
SERVER_URL = "https://smartweighbridge-production.up.railway.app/api/scale/weight"
DEVICE_TOKEN = "SWB-DEV-9f3a1c7b-2e4d-4b1f-9a12-7c3d9e5a1f22"
SCALE_ID = "SCALE-01"

# =========================
# 3) تنظیمات ارسال و تشخیص پایداری
# =========================
# هر چند ثانیه یکبار ارسال کند (حتی اگر وزن ثابت است، تا stable هم آپدیت شود)
SEND_EVERY_SEC = 0.5

# تلورانس تغییر وزن برای درنظر گرفتن نویز (اگر نویز داری 1 یا 2 بگذار)
# اگر دقیق و بدون نویز است 0 بگذار
STABLE_TOL = 1

# اگر وزن حداقل این مدت داخل تلورانس بود => stable=True
STABLE_SECONDS = 1.2

# =========================
# Helpers
# =========================
def extract_signed_weight(line: str):
    """
    نمونه ورودی از اندیکاتور شما:
      -01645
    اینجا:
    - اگر '-' داخل خط باشد => وزن منفی
    - فقط رقم‌ها را جدا می‌کنیم (5 یا 6 رقم)
    """
    t = line.strip()
    if not t:
        return None

    neg = "-" in t
    digits = re.sub(r"[^0-9]", "", t)

    if not digits:
        return None

    if len(digits) < 5 or len(digits) > 6:
        return None

    w = int(digits)  # "01645" -> 1645
    return -w if neg else w


def post_weight(session: requests.Session, weight: float, stable: bool):
    headers = {"X-Device-Token": DEVICE_TOKEN}
    payload = {"scale_id": SCALE_ID, "weight": float(weight), "stable": stable}
    r = session.post(SERVER_URL, json=payload, headers=headers, timeout=10)
    r.raise_for_status()


def main():
    print("=== Scale Agent (Railway) ===")
    print("Serial :", SERIAL_PORT, "baud:", SERIAL_BAUD)
    print("Server :", SERVER_URL)
    print("ScaleID:", SCALE_ID)
    print("Stable tol:", STABLE_TOL, "Stable sec:", STABLE_SECONDS)
    print("Send every:", SEND_EVERY_SEC, "sec")
    print("=============================")

    session = requests.Session()

    last_weight = None
    last_change_ts = time.time()
    last_send_ts = 0.0

    while True:
        try:
            with serial.Serial(
                SERIAL_PORT,
                SERIAL_BAUD,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=TIMEOUT,
            ) as ser:
                print("Connected to serial:", SERIAL_PORT)

                while True:
                    raw = ser.readline()
                    if not raw:
                        continue

                    text = raw.decode("utf-8", errors="ignore")
                    w = extract_signed_weight(text)
                    if w is None:
                        continue

                    now = time.time()

                    # تشخیص تغییر وزن با تلورانس
                    if last_weight is None:
                        last_weight = w
                        last_change_ts = now
                    else:
                        if abs(w - last_weight) > STABLE_TOL:
                            last_weight = w
                            last_change_ts = now

                    stable = (now - last_change_ts) >= STABLE_SECONDS

                    # محدود کردن تعداد ارسال
                    if now - last_send_ts < SEND_EVERY_SEC:
                        continue

                    try:
                        post_weight(session, last_weight, stable)
                        last_send_ts = now
                        print("POST", last_weight, "stable=", stable, "raw=", repr(text.strip()))
                    except requests.HTTPError as e:
                        print("HTTP error:", e, "resp:", getattr(e.response, "text", None))
                        time.sleep(1)
                    except Exception as e:
                        print("POST failed:", e)
                        time.sleep(1)

        except serial.SerialException as e:
            print("Serial error:", e)
            time.sleep(2)
        except Exception as e:
            print("Agent error:", e)
            time.sleep(2)


if __name__ == "__main__":
    main()
