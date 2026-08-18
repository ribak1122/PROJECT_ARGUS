"""
core.logger
============
Professional logging subsystem for PROJECT ARGUS.

Provides a singleton-style logger factory that writes:
    - Daily rotating log files under /logs (one file per calendar day)
    - Colored, level-aware output to the terminal

A custom SUCCESS level (25, between INFO and WARNING) is added so the
system can clearly report successful operations (connections, trades,
scans) without abusing INFO or WARNING.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Optional

# --------------------------------------------------------------------------- #
# Custom SUCCESS log level
# --------------------------------------------------------------------------- #
SUCCESS_LEVEL_NUM: int = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


def _success(self: logging.Logger, message: str, *args, **kwargs) -> None:
    """Log a message with severity 'SUCCESS' (between INFO and WARNING)."""
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)


logging.Logger.success = _success  # type: ignore[attr-defined]


class _AnsiColors:
    """ANSI escape codes used for terminal coloring."""

    RESET: str = "\033[0m"
    BOLD: str = "\033[1m"
    GREY: str = "\033[90m"
    BLUE: str = "\033[94m"
    GREEN: str = "\033[92m"
    YELLOW: str = "\033[93m"
    RED: str = "\033[91m"
    BOLD_RED: str = "\033[1;91m"
    CYAN: str = "\033[96m"


class ColoredFormatter(logging.Formatter):
    """A `logging.Formatter` that colorizes output based on log level."""

    _LEVEL_COLORS: ClassVar[dict] = {
        logging.DEBUG: _AnsiColors.GREY,
        logging.INFO: _AnsiColors.BLUE,
        SUCCESS_LEVEL_NUM: _AnsiColors.GREEN,
        logging.WARNING: _AnsiColors.YELLOW,
        logging.ERROR: _AnsiColors.RED,
        logging.CRITICAL: _AnsiColors.BOLD_RED,
    }

    _BASE_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)-18s | %(message)s"
    _DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        color = self._LEVEL_COLORS.get(record.levelno, _AnsiColors.RESET)
        formatter = logging.Formatter(
            f"{_AnsiColors.CYAN}%(asctime)s{_AnsiColors.RESET} | "
            f"{color}{_AnsiColors.BOLD}%(levelname)-8s{_AnsiColors.RESET} | "
            f"{_AnsiColors.GREY}%(name)-18s{_AnsiColors.RESET} | "
            f"{color}%(message)s{_AnsiColors.RESET}",
            datefmt=self._DATE_FORMAT,
        )
        return formatter.format(record)


class PlainFormatter(logging.Formatter):
    """Non-colored formatter used for the file handler."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-18s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class ArgusLogger:
    """
    Factory / manager for all PROJECT ARGUS loggers.

    Usage
    -----
    >>> logger = ArgusLogger.get_logger("Scanner")
    >>> logger.info("Scanner initialized")
    >>> logger.success("Connected to MT5")
    >>> logger.warning("Spread above limit")
    >>> logger.error("Failed to fetch candle data")
    """

    _initialized: ClassVar[bool] = False
    _log_dir: ClassVar[Path] = Path("logs")
    _level: ClassVar[int] = logging.INFO

    @classmethod
    def configure(cls, log_dir: str = "logs", level: str = "INFO") -> None:
        """
        Configure global logging behaviour. Must be called once at startup
        (idempotent - safe to call multiple times).

        Args:
            log_dir: Directory in which daily log files are stored.
            level: Minimum log level name (DEBUG, INFO, WARNING, ERROR).
        """
        cls._log_dir = Path(log_dir)
        cls._log_dir.mkdir(parents=True, exist_ok=True)
        cls._level = getattr(logging, level.upper(), logging.INFO)
        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str = "ARGUS") -> logging.Logger:
        """
        Retrieve (or create) a configured logger instance.

        Args:
            name: Logical component name, e.g. 'Scanner', 'MT5Bridge'.

        Returns:
            A fully configured `logging.Logger` instance.
        """
        if not cls._initialized:
            cls.configure()

        logger = logging.getLogger(name)

        if logger.handlers:
            # Already configured - avoid duplicate handlers.
            return logger

        logger.setLevel(cls._level)
        logger.propagate = False

        # --- Console handler (colored) ---
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        console_handler.setLevel(cls._level)
        logger.addHandler(console_handler)

        # --- Daily rotating file handler ---
        log_file = cls._log_dir / f"argus_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(PlainFormatter())
        file_handler.setLevel(cls._level)
        logger.addHandler(file_handler)

        return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Convenience module-level accessor for `ArgusLogger.get_logger`."""
    return ArgusLogger.get_logger(name or "ARGUS")
