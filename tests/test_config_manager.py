"""Unit tests for src.core.config_manager.ConfigManager."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.core.config_manager import ConfigError, ConfigManager


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Ensure each test gets a fresh ConfigManager singleton."""
    ConfigManager._instance = None
    ConfigManager._data = {}
    yield
    ConfigManager._instance = None
    ConfigManager._data = {}


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    config_content = textwrap.dedent(
        """
        mt5:
          symbol: "XAUUSD"
          lot: 0.01
        risk:
          reward_to_risk: 2.0
        """
    )
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content, encoding="utf-8")
    return config_file


def test_get_returns_nested_value(sample_config: Path) -> None:
    config = ConfigManager(str(sample_config))
    assert config.get("mt5.symbol") == "XAUUSD"
    assert config.get("mt5.lot") == 0.01


def test_get_returns_default_for_missing_key(sample_config: Path) -> None:
    config = ConfigManager(str(sample_config))
    assert config.get("mt5.nonexistent", default="fallback") == "fallback"


def test_require_raises_on_missing_key(sample_config: Path) -> None:
    config = ConfigManager(str(sample_config))
    with pytest.raises(ConfigError):
        config.require("mt5.nonexistent")


def test_missing_file_raises_config_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.yaml"
    with pytest.raises(ConfigError):
        ConfigManager(str(missing_path))


def test_as_dict_returns_full_config(sample_config: Path) -> None:
    config = ConfigManager(str(sample_config))
    data = config.as_dict
    assert "mt5" in data
    assert "risk" in data
