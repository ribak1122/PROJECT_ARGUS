"""
core.event_manager
===================
A minimal, thread-safe publish/subscribe event bus used to decouple
PROJECT ARGUS subsystems (Scanner -> Engine -> Guardian -> Dashboard)
from one another.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, ClassVar, DefaultDict, Dict, List, Optional

from src.core.logger import get_logger

logger = get_logger("EventManager")

EventHandler = Callable[["Event"], None]


@dataclass
class Event:
    """A single event flowing through the system."""

    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventManager:
    """
    Simple singleton event bus.

    Usage
    -----
    >>> bus = EventManager()
    >>> def on_signal(event: Event) -> None:
    ...     print(event.payload)
    >>> bus.subscribe("signal.detected", on_signal)
    >>> bus.publish("signal.detected", {"symbol": "XAUUSD"})
    """

    _instance: ClassVar[Optional["EventManager"]] = None

    def __new__(cls) -> "EventManager":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._subscribers = defaultdict(list)  # type: DefaultDict[str, List[EventHandler]]
            instance._lock = threading.Lock()
            cls._instance = instance
        return cls._instance

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register `handler` to be invoked whenever `event_name` fires."""
        with self._lock:
            self._subscribers[event_name].append(handler)
        logger.info(f"Subscribed handler '{handler.__name__}' to event '{event_name}'")

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove a previously registered handler for `event_name`."""
        with self._lock:
            handlers = self._subscribers.get(event_name, [])
            if handler in handlers:
                handlers.remove(handler)
                logger.info(f"Unsubscribed handler '{handler.__name__}' from '{event_name}'")

    def publish(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """
        Publish an event to all subscribers, synchronously.

        Handler exceptions are caught and logged so one faulty subscriber
        cannot crash the rest of the system.
        """
        event = Event(name=event_name, payload=payload or {})
        with self._lock:
            handlers = list(self._subscribers.get(event_name, []))

        if not handlers:
            logger.info(f"Event '{event_name}' published with no subscribers.")
            return

        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001 - isolate subscriber failures
                logger.error(f"Handler '{handler.__name__}' failed on '{event_name}': {exc}")
