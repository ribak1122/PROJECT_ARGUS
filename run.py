"""
PROJECT ARGUS - Adaptive Real-time Gold Understanding System
==============================================================
Main application entry point.

Phase 1 scope: bootstraps core services (logger, config, folders, event
bus, status manager), initializes the MT5 bridge and scanner framework,
and runs the live terminal dashboard. No trading logic executes yet.
"""

from __future__ import annotations

import sys
import time

from src.core.config_manager import ConfigError, ConfigManager
from src.core.event_manager import EventManager
from src.core.folder_manager import FolderManager
from src.core.logger import ArgusLogger, get_logger
from src.core.system_status import ConnectionState, SystemStatusManager
from src.dashboard.dashboard import Dashboard
from src.engine.decision_engine import DecisionEngine
from src.engine.evidence_engine import EvidenceEngine
from src.engine.risk_manager import RiskManager
from src.guardian.guardian import Guardian
from src.journal.daily_journal import DailyJournal
from src.mt5.mt5_bridge import MT5Bridge, MT5ConnectionError
from src.scanner.scanner import Scanner


def bootstrap() -> ConfigManager:
    """Initialize folders, logging, and configuration. Returns the config."""
    folder_manager = FolderManager()
    folder_manager.ensure_all()

    config = ConfigManager()
    ArgusLogger.configure(
        log_dir=config.get("logging.directory", "logs"),
        level=config.get("logging.level", "INFO"),
    )
    return config


def main() -> int:
    """Application entry point. Returns a process exit code."""
    try:
        config = bootstrap()
    except ConfigError as exc:
        print(f"[FATAL] Configuration error: {exc}")
        return 1

    logger = get_logger("Main")
    logger.success(f"{config.get('app.name', 'PROJECT ARGUS')} v{config.get('app.version', '0.1.0')} booting...")

    event_bus = EventManager()
    status_manager = SystemStatusManager()
    status_manager.update(version=config.get("app.version", "0.1.0"), symbol=config.get("mt5.symbol", "XAUUSD"))

    journal = DailyJournal(config)
    journal.log("SYSTEM", "PROJECT ARGUS booting", {"version": config.get("app.version")})

    guardian = Guardian(config)
    evidence_engine = EvidenceEngine()
    decision_engine = DecisionEngine()
    risk_manager = RiskManager(config)

    mt5_bridge = MT5Bridge(config)
    status_manager.update(connection_state=ConnectionState.CONNECTING)

    try:
        mt5_bridge.connect()
        status_manager.update(connection_state=ConnectionState.CONNECTED)
        journal.log("SYSTEM", "MT5 connection established")
    except MT5ConnectionError as exc:
        status_manager.update(connection_state=ConnectionState.ERROR)
        logger.warning(f"MT5 connection unavailable in this environment: {exc}")
        logger.warning("Continuing in OFFLINE mode - dashboard and architecture only.")
        journal.log("SYSTEM", "MT5 connection unavailable", {"error": str(exc)})

    scanner = Scanner(mt5_bridge, config)

    def on_scan() -> None:
        """Strategy hook placeholder - wired to Evidence/Decision Engine in Phase 2."""
        logger.info("Scan cycle executed (strategy logic pending Phase 2).")

    scanner.set_scan_callback(on_scan)

    if mt5_bridge.is_connected:
        scanner.start()

    dashboard = Dashboard(config)
    logger.success("PROJECT ARGUS boot sequence complete.")

    try:
        with dashboard.live() as live_view:
            while True:
                live_view.update(dashboard.render())
                time.sleep(dashboard.refresh_seconds)
    except KeyboardInterrupt:
        logger.warning("Shutdown requested by user (Ctrl+C).")
    finally:
        scanner.stop()
        mt5_bridge.shutdown()
        journal.log("SYSTEM", "PROJECT ARGUS shutdown complete")
        logger.success("PROJECT ARGUS shutdown complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
