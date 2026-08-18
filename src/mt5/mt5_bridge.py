"""
mt5.mt5_bridge
==============
Thin, defensive wrapper around the `MetaTrader5` Python package.

Scope (Phase 1): connection lifecycle and read-only market data access.
NO order placement / modification logic lives here by design - this is
strictly a data/connection bridge until the Engine modules are implemented.

Note: The `MetaTrader5` package only functions on Windows with a running
MT5 terminal. Import is deferred/optional so the rest of the codebase can
still be imported and unit-tested on non-Windows machines.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from src.core.config_manager import ConfigManager
from src.core.logger import get_logger

logger = get_logger("MT5Bridge")

try:
    import MetaTrader5 as mt5  # type: ignore
    _MT5_AVAILABLE = True
except ImportError:  # pragma: no cover - expected on non-Windows dev machines
    mt5 = None
    _MT5_AVAILABLE = False

_TIMEFRAME_MAP: dict = {}
if _MT5_AVAILABLE:
    _TIMEFRAME_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "M3": mt5.TIMEFRAME_M3,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }


class MT5ConnectionError(Exception):
    """Raised when a connection or reconnection attempt fails."""


@dataclass
class TickData:
    """Normalized representation of an MT5 tick."""

    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    time: datetime

    @property
    def spread_points(self) -> float:
        """Return the current bid/ask spread expressed in raw price units."""
        return round(self.ask - self.bid, 8)


@dataclass
class CandleData:
    """Normalized representation of a single OHLCV candle."""

    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


class MT5Bridge:
    """
    Manages the lifecycle of the MetaTrader5 terminal connection and
    exposes read-only market data accessors.

    Usage
    -----
    >>> bridge = MT5Bridge()
    >>> bridge.connect()
    >>> tick = bridge.read_tick("XAUUSD")
    >>> candles = bridge.read_candles("XAUUSD", "M3", count=200)
    >>> bridge.shutdown()
    """

    def __init__(self, config: Optional[ConfigManager] = None) -> None:
        self.config = config or ConfigManager()
        self._connected: bool = False

    # ------------------------------------------------------------------ #
    # Connection lifecycle
    # ------------------------------------------------------------------ #
    def connect(self) -> bool:
        """
        Initialize the MT5 terminal connection and log in using the
        credentials defined in `config.yaml`.

        Returns:
            True if the connection succeeded.

        Raises:
            MT5ConnectionError: If MetaTrader5 is unavailable or login fails.
        """
        if not _MT5_AVAILABLE:
            logger.error("MetaTrader5 package is not available on this platform.")
            raise MT5ConnectionError("MetaTrader5 package not installed / unsupported OS.")

        account = int(self.config.get("mt5.account", 0))
        password = self.config.get("mt5.password", "")
        server = self.config.get("mt5.server", "")
        terminal_path = self.config.get("mt5.path", "") or None

        logger.info(f"Connecting to MT5 terminal (account={account}, server={server})...")

        initialized = (
            mt5.initialize(path=terminal_path) if terminal_path else mt5.initialize()
        )
        if not initialized:
            error = mt5.last_error()
            logger.error(f"MT5 initialize() failed: {error}")
            raise MT5ConnectionError(f"MT5 initialize() failed: {error}")

        authorized = mt5.login(account, password=password, server=server)
        if not authorized:
            error = mt5.last_error()
            logger.error(f"MT5 login() failed: {error}")
            mt5.shutdown()
            raise MT5ConnectionError(f"MT5 login() failed: {error}")

        self._connected = True
        logger.success(f"Connected to MT5 (account={account}, server={server}).")
        return True

    def reconnect(self, max_attempts: int = 3) -> bool:
        """
        Attempt to re-establish a lost MT5 connection.

        Args:
            max_attempts: Number of retry attempts before giving up.

        Returns:
            True if reconnection succeeded, False otherwise.
        """
        logger.warning("Attempting MT5 reconnection...")
        self.shutdown()

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Reconnect attempt {attempt}/{max_attempts}...")
                return self.connect()
            except MT5ConnectionError as exc:
                logger.error(f"Reconnect attempt {attempt} failed: {exc}")

        logger.error("All reconnection attempts exhausted.")
        return False

    def shutdown(self) -> None:
        """Gracefully close the MT5 terminal connection."""
        if _MT5_AVAILABLE and self._connected:
            mt5.shutdown()
            logger.info("MT5 connection closed.")
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Whether the bridge currently believes it holds a live connection."""
        return self._connected

    # ------------------------------------------------------------------ #
    # Read-only market data
    # ------------------------------------------------------------------ #
    def read_tick(self, symbol: str) -> Optional[TickData]:
        """
        Fetch the latest tick for `symbol`.

        Args:
            symbol: Trading symbol, e.g. "XAUUSD".

        Returns:
            A `TickData` instance, or None if unavailable.
        """
        self._require_connection()
        raw_tick = mt5.symbol_info_tick(symbol)
        if raw_tick is None:
            logger.warning(f"No tick data returned for {symbol}.")
            return None

        return TickData(
            symbol=symbol,
            bid=raw_tick.bid,
            ask=raw_tick.ask,
            last=raw_tick.last,
            volume=raw_tick.volume,
            time=datetime.fromtimestamp(raw_tick.time),
        )

    def read_candles(self, symbol: str, timeframe: str, count: int = 100) -> List[CandleData]:
        """
        Fetch the most recent `count` candles for `symbol` on `timeframe`.

        Args:
            symbol: Trading symbol, e.g. "XAUUSD".
            timeframe: One of "M1", "M3", "M5", "M15", "M30", "H1", "H4", "D1".
            count: Number of candles to retrieve.

        Returns:
            A list of `CandleData`, ordered oldest to newest.
        """
        self._require_connection()

        mt5_timeframe = _TIMEFRAME_MAP.get(timeframe.upper())
        if mt5_timeframe is None:
            logger.error(f"Unsupported timeframe requested: {timeframe}")
            return []

        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
        if rates is None or len(rates) == 0:
            logger.warning(f"No candle data returned for {symbol} [{timeframe}].")
            return []

        candles = [
            CandleData(
                time=datetime.fromtimestamp(row["time"]),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                tick_volume=int(row["tick_volume"]),
                spread=int(row["spread"]),
                real_volume=int(row["real_volume"]),
            )
            for row in rates
        ]
        return candles

    def read_symbol_info(self, symbol: str) -> Optional[Any]:
        """
        Fetch broker metadata for `symbol` (digits, point size, contract
        size, trading constraints, etc.).

        Args:
            symbol: Trading symbol, e.g. "XAUUSD".

        Returns:
            The raw `SymbolInfo` namedtuple from MetaTrader5, or None.
        """
        self._require_connection()
        info = mt5.symbol_info(symbol)
        if info is None:
            logger.warning(f"Symbol info not found for {symbol}.")
            return None
        if not info.visible:
            logger.info(f"Symbol {symbol} not visible in Market Watch; enabling...")
            mt5.symbol_select(symbol, True)
        return info

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _require_connection(self) -> None:
        if not self._connected:
            logger.error("Operation attempted without an active MT5 connection.")
            raise MT5ConnectionError("Not connected to MT5. Call connect() first.")
