"""
utils.utils
============
Stateless helper functions shared across PROJECT ARGUS modules:
trading-session detection, number formatting, and small time helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

# Approximate trading session windows in UTC hours (used for display only;
# not a substitute for a broker's authoritative session calendar).
_SESSION_WINDOWS: Final[dict] = {
    "SYDNEY": (21, 6),
    "TOKYO": (0, 9),
    "LONDON": (7, 16),
    "NEW_YORK": (12, 21),
}


def get_current_session(now: datetime | None = None) -> str:
    """
    Return a best-effort label for the currently active trading session(s),
    based on UTC time.

    Args:
        now: Optional datetime override (defaults to `datetime.now(UTC)`).

    Returns:
        A comma-separated string of active sessions, or "OFF_HOURS".
    """
    current = now or datetime.now(timezone.utc)
    hour = current.hour

    active = []
    for session_name, (start, end) in _SESSION_WINDOWS.items():
        if start < end:
            in_session = start <= hour < end
        else:
            # Window wraps midnight (e.g. Sydney 21 -> 6)
            in_session = hour >= start or hour < end
        if in_session:
            active.append(session_name)

    return ", ".join(active) if active else "OFF_HOURS"


def format_price(value: float | None, decimals: int = 2) -> str:
    """Format a price for display, gracefully handling `None`."""
    if value is None:
        return "--"
    return f"{value:.{decimals}f}"


def format_pips(value: float | None, decimals: int = 1) -> str:
    """Format a pip/point value for display."""
    if value is None:
        return "--"
    return f"{value:.{decimals}f}"


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp `value` between `minimum` and `maximum`."""
    return max(minimum, min(value, maximum))


def percentage(part: float, whole: float) -> float:
    """Safely compute `part / whole * 100`, returning 0.0 if whole is 0."""
    if whole == 0:
        return 0.0
    return (part / whole) * 100.0


def utc_timestamp() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()
