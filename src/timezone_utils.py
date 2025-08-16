"""
Timezone utilities for PST/PDT handling in the bathroom health monitoring system.
"""
import datetime
import pytz

# Define PST timezone
PST = pytz.timezone('US/Pacific')

def now_pst() -> datetime.datetime:
    """Get current time in PST/PDT timezone."""
    return datetime.datetime.now(PST)

def to_pst(dt: datetime.datetime) -> datetime.datetime:
    """Convert a datetime to PST/PDT timezone."""
    if dt.tzinfo is None:
        # Assume naive datetime is in system timezone, convert to PST
        system_tz = pytz.timezone('UTC')  # or get system timezone
        dt = system_tz.localize(dt)
    return dt.astimezone(PST)

def pst_from_naive(dt: datetime.datetime) -> datetime.datetime:
    """Convert a naive datetime (assuming it's already in PST) to PST-aware datetime."""
    return PST.localize(dt)

def pst_time(hour: int, minute: int = 0, second: int = 0) -> datetime.time:
    """Create a time object in PST for today."""
    return datetime.time(hour, minute, second, tzinfo=PST)

def pst_datetime_today(hour: int, minute: int = 0, second: int = 0) -> datetime.datetime:
    """Create a PST datetime for today at the specified time."""
    today = datetime.date.today()
    naive_dt = datetime.datetime.combine(today, datetime.time(hour, minute, second))
    return PST.localize(naive_dt)

def format_pst(dt: datetime.datetime, format_str: str = '%Y-%m-%d %H:%M:%S %Z') -> str:
    """Format a datetime in PST timezone."""
    if dt.tzinfo is None:
        dt = pst_from_naive(dt)
    else:
        dt = dt.astimezone(PST)
    return dt.strftime(format_str)
