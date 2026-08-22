from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import jdatetime


TEHRAN_TZ = ZoneInfo("Asia/Tehran")


PERSIAN_DIGITS = str.maketrans(
    "0123456789",
    "۰۱۲۳۴۵۶۷۸۹",
)


def parse_utc(value):
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00",
            )
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt

    except Exception:
        return None


def to_tehran(value):
    dt = parse_utc(value)

    if not dt:
        return None

    return dt.astimezone(
        TEHRAN_TZ
    )


def jalali_datetime(value):
    dt = to_tehran(value)

    if not dt:
        return "—"

    jalali = jdatetime.datetime.fromgregorian(
        datetime=dt
    )

    result = (
        f"{jalali.year:04d}/"
        f"{jalali.month:02d}/"
        f"{jalali.day:02d}"
        " - "
        f"{dt.hour:02d}:"
        f"{dt.minute:02d}:"
        f"{dt.second:02d}"
    )

    return result.translate(
        PERSIAN_DIGITS
    )


def jalali_date(value):
    dt = to_tehran(value)

    if not dt:
        return "—"

    jalali = jdatetime.datetime.fromgregorian(
        datetime=dt
    )

    result = (
        f"{jalali.year:04d}/"
        f"{jalali.month:02d}/"
        f"{jalali.day:02d}"
    )

    return result.translate(
        PERSIAN_DIGITS
    )


def iran_time(value):
    dt = to_tehran(value)

    if not dt:
        return "—"

    result = (
        f"{dt.hour:02d}:"
        f"{dt.minute:02d}:"
        f"{dt.second:02d}"
    )

    return result.translate(
        PERSIAN_DIGITS
    )
