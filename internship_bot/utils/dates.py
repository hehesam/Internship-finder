"""Date parsing helpers."""

from datetime import datetime, timezone

from dateutil import parser as date_parser


def parse_datetime(value: str | None) -> datetime | None:
    """Parse a date string to timezone-aware UTC datetime when possible."""
    if not value or not value.strip():
        return None

    try:
        parsed = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
