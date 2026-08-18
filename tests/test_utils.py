"""Unit tests for src.utils.utils."""

from __future__ import annotations

from datetime import datetime, timezone

from src.utils.utils import (
    clamp,
    format_pips,
    format_price,
    get_current_session,
    percentage,
)


def test_format_price_with_value() -> None:
    assert format_price(2415.678, decimals=2) == "2415.68"


def test_format_price_with_none() -> None:
    assert format_price(None) == "--"


def test_format_pips_with_none() -> None:
    assert format_pips(None) == "--"


def test_clamp_within_range() -> None:
    assert clamp(5, 0, 10) == 5


def test_clamp_below_minimum() -> None:
    assert clamp(-5, 0, 10) == 0


def test_clamp_above_maximum() -> None:
    assert clamp(15, 0, 10) == 10


def test_percentage_normal() -> None:
    assert percentage(50, 200) == 25.0


def test_percentage_zero_whole() -> None:
    assert percentage(50, 0) == 0.0


def test_get_current_session_returns_string() -> None:
    fixed_time = datetime(2026, 8, 17, 13, 0, tzinfo=timezone.utc)  # London+NY overlap
    session = get_current_session(fixed_time)
    assert isinstance(session, str)
    assert "LONDON" in session or "NEW_YORK" in session
