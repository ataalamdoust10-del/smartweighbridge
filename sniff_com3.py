import re
import serial
import time

PORT = "COM3"
BAUD = 2400

# تبدیل ارقام فارسی/عربی به انگلیسی (اگر لازم شد)
TRANS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def extract_weight(text: str):
    text = text.translate(TRANS)
    digits = re.sub(r"[^0-9]", "", text)
    # بعضی اندیکاتورها 5 رقم می‌فرستن، بعضی 6 رقم:
    if 5 <= len(digits) <= 6:
        digits = digits.zfill(6)  # به 6 رقم تبدیلش می‌کنیم
        return int(digits)
    return None

ser = serial.Serial(PORT, BAUD, bytesize=8, parity="N", stopbits=1, timeout=1)

print("Listening:", PORT, "baud:", BAUD)
buf = b""

try:
    while True:
        chunk = ser.read(64)
        if not chunk:
            continue
        buf += chunk

        # جدا کردن بر اساس CR/LF (هر دو را ساپورت می‌کنیم)
        while b"\n" in buf or b"\r" in buf:
            # نزدیک‌ترین جداکننده
            npos = buf.find(b"\n") if b"\n" in buf else 10**9
            rpos = buf.find(b"\r") if b"\r" in buf else 10**9
            pos = min(npos, rpos)

            line, buf = buf[:pos], buf[pos+1:]
            text = line.decode("utf-8", errors="ignore").strip()

            w = extract_weight(text)
            if w is not None:
                print("WEIGHT =", w, "  raw =", repr(text))
except KeyboardInterrupt:
    pass
finally:
    ser.close()
