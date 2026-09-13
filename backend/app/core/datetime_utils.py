from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return timezone-naive UTC datetime for consistent storage across SQLite and PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
