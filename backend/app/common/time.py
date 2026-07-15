"""Timezone-aware clock helpers."""

from datetime import datetime
from zoneinfo import ZoneInfo

SEOUL_TIMEZONE = ZoneInfo("Asia/Seoul")


def now_seoul() -> datetime:
    """Return the current timezone-aware Asia/Seoul datetime."""
    return datetime.now(SEOUL_TIMEZONE)
