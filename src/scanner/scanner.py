"""
scanner.scanner
================
Scanner framework for PROJECT ARGUS.

This module owns the polling loop that periodically pulls fresh market
data from the MT5 bridge and hands it off to the (not-yet-implemented)
Evidence/Decision Engine. Strategy logic is intentionally NOT implemented
here - Phase 1 only prepares the architecture and lifecycle management.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from src.core.config_manager import ConfigManager
from src.core.event_manager import EventManager
from src.core.logger import get_logger
from src.core.system_status import ScannerState, SystemStatusManager
from src.mt5.mt5_bridge import MT5Bridge

logger = get_logger("Scanner")

ScanCallback = Callable[[], None]


class Scanner:
    """
    Periodically triggers a market scan on a background thread.

    The actual analysis (liquidity sweeps, FVGs, RSI confirmation) is
    delegated to a pluggable callback so this class stays a pure
    scheduling/lifecycle component.

    Usage
    -----
    >>> scanner = Scanner(mt5_bridge=bridge)
    >>> scanner.set_scan_callback(my_strategy_function)
    >>> scanner.start()
    ...
    >>> scanner.stop()
    """

    def __init__(
        self,
        mt5_bridge: MT5Bridge,
        config: Optional[ConfigManager] = None,
    ) -> None:
        self.mt5_bridge = mt5_bridge
        self.config = config or ConfigManager()
        self.event_bus = EventManager()
        self.status = SystemStatusManager()

        self.symbol: str = self.config.get("mt5.symbol", "XAUUSD")
        self.interval_seconds: float = float(self.config.get("scanner.interval_seconds", 5))

        self._scan_callback: Optional[ScanCallback] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

    def set_scan_callback(self, callback: ScanCallback) -> None:
        """Register the function invoked on every scan tick (strategy hook)."""
        self._scan_callback = callback
        logger.info(f"Scan callback registered: {callback.__name__}")

    def start(self) -> None:
        """Start the scanner loop on a dedicated daemon thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Scanner already running.")
            return

        if not self.config.get("scanner.enabled", True):
            logger.warning("Scanner is disabled in configuration; not starting.")
            return

        self._stop_event.clear()
        self._pause_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="ArgusScannerThread", daemon=True)
        self._thread.start()

        self.status.update(scanner_state=ScannerState.RUNNING)
        self.event_bus.publish("scanner.started", {"symbol": self.symbol})
        logger.success(f"Scanner started for {self.symbol} (interval={self.interval_seconds}s).")

    def pause(self) -> None:
        """Pause scanning without terminating the background thread."""
        self._pause_event.set()
        self.status.update(scanner_state=ScannerState.PAUSED)
        self.event_bus.publish("scanner.paused", {})
        logger.warning("Scanner paused.")

    def resume(self) -> None:
        """Resume scanning after a `pause()` call."""
        self._pause_event.clear()
        self.status.update(scanner_state=ScannerState.RUNNING)
        self.event_bus.publish("scanner.resumed", {})
        logger.info("Scanner resumed.")

    def stop(self) -> None:
        """Stop the scanner loop and join the background thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval_seconds + 2)
        self.status.update(scanner_state=ScannerState.STOPPED)
        self.event_bus.publish("scanner.stopped", {})
        logger.info("Scanner stopped.")

    def _run_loop(self) -> None:
        """Internal polling loop executed on the background thread."""
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.5)
                continue

            try:
                self._tick()
            except Exception as exc:  # noqa: BLE001 - keep the loop alive
                logger.error(f"Scanner tick failed: {exc}")

            self._stop_event.wait(self.interval_seconds)

    def _tick(self) -> None:
        """Execute a single scan cycle."""
        if not self.mt5_bridge.is_connected:
            logger.warning("Scanner tick skipped: MT5 bridge not connected.")
            return

        tick = self.mt5_bridge.read_tick(self.symbol)
        if tick is not None:
            self.status.update(current_price=tick.last or tick.bid, spread=tick.spread_points)
            self.event_bus.publish("scanner.tick", {"symbol": self.symbol, "price": tick.bid})

        if self._scan_callback is not None:
            self._scan_callback()
