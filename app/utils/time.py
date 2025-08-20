from datetime import datetime
from zoneinfo import ZoneInfo

EASTERN_TZ = ZoneInfo("America/New_York")


def now_eastern() -> datetime:
    """Return current time in US Eastern timezone."""
    return datetime.now(EASTERN_TZ)


def to_eastern(dt: datetime) -> datetime:
    """Convert a datetime to US Eastern timezone.

    Naive datetimes are assumed to be in UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(EASTERN_TZ)
