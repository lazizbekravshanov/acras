"""Timezone-aware datetime utilities."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(UTC)


def format_iso(dt: datetime) -> str:
    """Format a datetime as an ISO 8601 string."""
    return dt.isoformat()


def seconds_since(dt: datetime) -> float:
    """Return seconds elapsed since the given datetime."""
    return (utc_now() - dt).total_seconds()


def minutes_since(dt: datetime) -> float:
    """Return minutes elapsed since the given datetime."""
    return seconds_since(dt) / 60
