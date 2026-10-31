"""Small shared helpers."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def uid() -> str:
    return uuid.uuid4().hex


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def local_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def short_date(value: str) -> str:
    dt = local_datetime(value)
    if not dt:
        return "--"
    return dt.strftime("%m/%d")


def full_date(value: str) -> str:
    dt = local_datetime(value)
    if not dt:
        return "--"
    return dt.strftime("%Y年%m月%d日 %H:%M")


def fmt_clock(total_seconds: float | int) -> str:
    seconds = max(0, int(total_seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def fmt_duration(total_seconds: float | int) -> str:
    seconds = max(0, int(total_seconds))
    minutes, secs = divmod(seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}小时{minutes:02d}分"
    return f"{minutes}分{secs:02d}秒"


def fmt_score(value: float | int) -> str:
    if abs(float(value) - round(float(value))) < 0.05:
        return str(int(round(float(value))))
    return f"{float(value):.1f}"


def percent(value: float | int, digits: int = 1) -> str:
    return f"{float(value):.{digits}f}%"
