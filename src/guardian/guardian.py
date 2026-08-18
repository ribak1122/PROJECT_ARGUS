"""
guardian.guardian
==================
Guardian - the system's safety oversight layer.

The Guardian does not generate trading decisions; it supervises the rest
of the system and has authority to halt trading (a "kill switch") when
risk, connectivity, or data-quality conditions become unsafe. Phase 1
provides the architecture and basic monitoring hooks only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from src.core.config_manager import ConfigManager
from src.core.event_manager import EventManager
from src.core.logger import get_logger

logger = get_logger("Guardian")


@dataclass
class GuardianAlert:
    """A single safety alert raised by the Guardian."""

    reason: str
    severity: str  # "WARNING" | "CRITICAL"
    raised_at: datetime = field(default_factory=datetime.now)


class Guardian:
    """
    Monitors system health and enforces hard safety limits.

    Usage
    -----
    >>> guardian = Guardian()
    >>> guardian.check_spread(current_spread_points=420)
    >>> guardian.check_daily_loss(daily_loss=52.0)
    >>> if guardian.is_trading_halted:
    ...     print("Trading halted:", guardian.halt_reason)
    """

    def __init__(self, config: Optional[ConfigManager] = None) -> None:
        self.config = config or ConfigManager()
        self.event_bus = EventManager()

        self.spread_limit_points = float(self.config.get("mt5.spread_limit_points", 350))
        self.max_daily_loss = float(self.config.get("risk.max_daily_loss", 50.0))

        self._alerts: List[GuardianAlert] = []
        self._trading_halted: bool = False
        self._halt_reason: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Checks
    # ------------------------------------------------------------------ #
    def check_spread(self, current_spread_points: float) -> bool:
        """
        Verify the current spread is within acceptable limits.

        Returns:
            True if spread is acceptable; False if it breaches the limit.
        """
        if current_spread_points > self.spread_limit_points:
            self._raise_alert(
                f"Spread {current_spread_points} exceeds limit {self.spread_limit_points}",
                severity="WARNING",
            )
            return False
        return True

    def check_daily_loss(self, daily_loss: float) -> bool:
        """
        Verify accumulated daily loss has not breached the kill-switch
        threshold. Halts trading if it has.

        Returns:
            True if within limits; False if the kill-switch was triggered.
        """
        if daily_loss >= self.max_daily_loss:
            self.halt_trading(f"Daily loss limit breached: {daily_loss} >= {self.max_daily_loss}")
            return False
        return True

    def check_connection(self, is_connected: bool) -> bool:
        """Verify the MT5 connection is alive; raise an alert if not."""
        if not is_connected:
            self._raise_alert("MT5 connection lost.", severity="CRITICAL")
            return False
        return True

    # ------------------------------------------------------------------ #
    # Kill switch
    # ------------------------------------------------------------------ #
    def halt_trading(self, reason: str) -> None:
        """Immediately halt all trading activity system-wide."""
        self._trading_halted = True
        self._halt_reason = reason
        self._raise_alert(reason, severity="CRITICAL")
        self.event_bus.publish("guardian.halt", {"reason": reason})
        logger.error(f"TRADING HALTED: {reason}")

    def resume_trading(self) -> None:
        """Manually clear a halt state (e.g. after operator review)."""
        self._trading_halted = False
        self._halt_reason = None
        self.event_bus.publish("guardian.resume", {})
        logger.warning("Trading halt cleared by operator.")

    @property
    def is_trading_halted(self) -> bool:
        """Whether the Guardian has activated the kill switch."""
        return self._trading_halted

    @property
    def halt_reason(self) -> Optional[str]:
        """The reason trading was halted, if applicable."""
        return self._halt_reason

    @property
    def alerts(self) -> List[GuardianAlert]:
        """All alerts raised so far this session."""
        return list(self._alerts)

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #
    def _raise_alert(self, reason: str, severity: str) -> None:
        alert = GuardianAlert(reason=reason, severity=severity)
        self._alerts.append(alert)
        self.event_bus.publish("guardian.alert", {"reason": reason, "severity": severity})
        if severity == "CRITICAL":
            logger.error(f"[GUARDIAN ALERT] {reason}")
        else:
            logger.warning(f"[GUARDIAN ALERT] {reason}")
