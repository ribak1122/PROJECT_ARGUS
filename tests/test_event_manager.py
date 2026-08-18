"""Unit tests for src.core.event_manager.EventManager."""

from __future__ import annotations

from typing import List

import pytest

from src.core.event_manager import Event, EventManager


@pytest.fixture(autouse=True)
def _reset_singleton():
    EventManager._instance = None
    yield
    EventManager._instance = None


def test_publish_invokes_subscriber() -> None:
    bus = EventManager()
    received: List[Event] = []

    def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("test.event", handler)
    bus.publish("test.event", {"foo": "bar"})

    assert len(received) == 1
    assert received[0].name == "test.event"
    assert received[0].payload == {"foo": "bar"}


def test_unsubscribe_stops_further_calls() -> None:
    bus = EventManager()
    call_count = {"count": 0}

    def handler(event: Event) -> None:
        call_count["count"] += 1

    bus.subscribe("test.event", handler)
    bus.publish("test.event")
    bus.unsubscribe("test.event", handler)
    bus.publish("test.event")

    assert call_count["count"] == 1


def test_publish_with_no_subscribers_does_not_raise() -> None:
    bus = EventManager()
    bus.publish("no.subscribers.event")  # Should not raise


def test_handler_exception_does_not_break_bus() -> None:
    bus = EventManager()
    results: List[str] = []

    def failing_handler(event: Event) -> None:
        raise RuntimeError("boom")

    def working_handler(event: Event) -> None:
        results.append("ok")

    bus.subscribe("test.event", failing_handler)
    bus.subscribe("test.event", working_handler)
    bus.publish("test.event")

    assert results == ["ok"]
