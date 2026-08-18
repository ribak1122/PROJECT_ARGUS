"""
core.config_manager
====================
Loads and exposes PROJECT ARGUS configuration from `config/config.yaml`.

The ConfigManager is implemented as a lazily-initialized singleton so that
every module in the system shares one consistent, in-memory view of the
configuration without repeatedly touching disk.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Optional

import yaml

from src.core.logger import get_logger

logger = get_logger("ConfigManager")


class ConfigError(Exception):
    """Raised when configuration cannot be loaded or a key is missing."""


class ConfigManager:
    """
    Singleton configuration manager backed by a YAML file.

    Usage
    -----
    >>> cfg = ConfigManager()
    >>> cfg.get("mt5.symbol")
    'XAUUSD'
    >>> cfg.get("mt5.lot", default=0.01)
    """

    _instance: ClassVar[Optional["ConfigManager"]] = None
    _data: ClassVar[dict] = {}
    _config_path: ClassVar[Optional[Path]] = None

    def __new__(cls, config_path: str = "config/config.yaml") -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load(config_path)
        return cls._instance

    def _load(self, config_path: str) -> None:
        """Read the YAML configuration file into memory."""
        path = Path(config_path)
        self.__class__._config_path = path

        if not path.exists():
            logger.error(f"Configuration file not found: {path}")
            raise ConfigError(f"Configuration file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as file_handle:
                self.__class__._data = yaml.safe_load(file_handle) or {}
            logger.success(f"Configuration loaded from {path}")
        except yaml.YAMLError as exc:
            logger.error(f"Failed to parse YAML configuration: {exc}")
            raise ConfigError(f"Failed to parse YAML configuration: {exc}") from exc

    def reload(self) -> None:
        """Force a re-read of the configuration file from disk."""
        if self._config_path is None:
            raise ConfigError("Cannot reload: config path unknown.")
        logger.info("Reloading configuration from disk...")
        self._load(str(self._config_path))

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value using dot notation.

        Args:
            dotted_key: e.g. "mt5.symbol" or "scanner.interval_seconds".
            default: Value returned if the key path does not exist.

        Returns:
            The configuration value, or `default` if not found.
        """
        node: Any = self._data
        for part in dotted_key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def require(self, dotted_key: str) -> Any:
        """Same as `get`, but raises `ConfigError` if the key is missing."""
        sentinel = object()
        value = self.get(dotted_key, default=sentinel)
        if value is sentinel:
            logger.error(f"Missing required configuration key: {dotted_key}")
            raise ConfigError(f"Missing required configuration key: {dotted_key}")
        return value

    @property
    def as_dict(self) -> dict:
        """Return the full configuration as a plain dictionary."""
        return dict(self._data)
