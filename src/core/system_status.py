"""
core.system_status
===================
Central, thread-safe state container describing the live status of
PROJECT ARGUS. The Dashboard reads from this object every render cycle;
the Scanner, MT5 bridge, and Engine write to it as conditions change.
"""

from __future__ import annotations

import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, Optional


class ConnectionState(str, Enum):
    """Possible states of the MT5 connection."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


class ScannerState(str, Enum):
    """Possible states of the market scanner."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class TrendState(str, Enum):
    """Higher-timeframe market structure bias."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"
    UNKNOWN = "UNKNOWN"


class DecisionState(str, Enum):
    """Latest decision produced by the Decision Engine."""

    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    NO_SIGNAL = "NO_SIGNAL"


@dataclass
class SystemStatus:
    """Snapshot of the entire system's live state."""

    version: str = "0.1.0"
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    scanner_state: ScannerState = ScannerState.IDLE
    symbol: str = "XAUUSD"
    current_price: Optional[float] = None
    spread: Optional[float] = None
    session: str = "UNKNOWN"
    trend: TrendState = TrendState.UNKNOWN
    decision: DecisionState = DecisionState.NO_SIGNAL
    confidence: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the status snapshot to a plain dictionary."""
        data = asdict(self)
        data["connection_state"] = self.connection_state.value
        data["scanner_state"] = self.scanner_state.value
        data["trend"] = self.trend.value
        data["decision"] = self.decision.value
        data["last_updated"] = self.last_updated.isoformat()
        return data


class SystemStatusManager:
    """
    Thread-safe singleton wrapper around `SystemStatus`.

    Usage
    -----
    >>> status = SystemStatusManager()
    >>> status.update(current_price=2415.32, spread=0.35)
    >>> snapshot = status.snapshot()
    """

    _instance: ClassVar[Optional["SystemStatusManager"]] = None

    def __new__(cls) -> "SystemStatusManager":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._status = SystemStatus()
            instance._lock = threading.Lock()
            cls._instance = instance
        return cls._instance

    def update(self, **kwargs: Any) -> None:
        """Update one or more fields of the status atomically."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self._status, key):
                    setattr(self._status, key, value)
            self._status.last_updated = datetime.now()

    def snapshot(self) -> SystemStatus:
        """Return a copy-safe reference to the current status."""
        with self._lock:
            return self._status
