"""Timezone utility functions."""
from datetime import datetime, timezone, timedelta
from typing import Optional


# Beijing timezone (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def to_beijing_time(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to Beijing time string.

    Args:
        dt: Datetime object (should be timezone-aware)

    Returns:
        ISO 8601 formatted string in Beijing time, or None if dt is None
    """
    if dt is None:
        return None

    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to Beijing time
    beijing_dt = dt.astimezone(BEIJING_TZ)

    # Format as "YYYY-MM-DD HH:MM:SS"
    return beijing_dt.strftime("%Y-%m-%d %H:%M:%S")


def get_current_beijing_time() -> datetime:
    """Get current time in Beijing timezone."""
    return datetime.now(BEIJING_TZ)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def current_beijing_period() -> str:
    """Get current period string (YYYY-MM) in Beijing timezone."""
    now = get_current_beijing_time()
    return now.strftime("%Y-%m")
