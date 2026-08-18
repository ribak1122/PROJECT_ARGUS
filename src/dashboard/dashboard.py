"""
dashboard.dashboard
====================
Professional, auto-refreshing terminal dashboard for PROJECT ARGUS,
built on top of the `rich` library.

Displays: system identity/version, connection status, scanner status,
current price/spread, session, trend bias, decision, and confidence.
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.core.config_manager import ConfigManager
from src.core.logger import get_logger
from src.core.system_status import (
    ConnectionState,
    DecisionState,
    ScannerState,
    SystemStatus,
    SystemStatusManager,
    TrendState,
)
from src.utils.utils import format_price, get_current_session

logger = get_logger("Dashboard")

_STATE_STYLES = {
    ConnectionState.CONNECTED: "bold green",
    ConnectionState.CONNECTING: "bold yellow",
    ConnectionState.DISCONNECTED: "bold red",
    ConnectionState.ERROR: "bold red",
    ScannerState.RUNNING: "bold green",
    ScannerState.PAUSED: "bold yellow",
    ScannerState.IDLE: "grey62",
    ScannerState.STOPPED: "bold red",
    TrendState.BULLISH: "bold green",
    TrendState.BEARISH: "bold red",
    TrendState.RANGING: "bold yellow",
    TrendState.UNKNOWN: "grey62",
    DecisionState.BUY: "bold green",
    DecisionState.SELL: "bold red",
    DecisionState.WAIT: "bold yellow",
    DecisionState.NO_SIGNAL: "grey62",
}


class Dashboard:
    """
    Renders a live-updating terminal dashboard reflecting `SystemStatus`.

    Usage
    -----
    >>> dashboard = Dashboard()
    >>> dashboard.render_once()          # static single render
    >>> with dashboard.live():           # auto-refreshing context
    ...     while True:
    ...         dashboard.refresh()
    """

    def __init__(self, config: Optional[ConfigManager] = None) -> None:
        self.config = config or ConfigManager()
        self.status_manager = SystemStatusManager()
        self.console = Console()
        self.app_name = self.config.get("app.name", "PROJECT ARGUS")
        self.refresh_seconds = float(self.config.get("dashboard.refresh_seconds", 1))

    def _styled(self, value) -> Text:
        style = _STATE_STYLES.get(value, "white")
        return Text(str(getattr(value, "value", value)), style=style)

    def _build_header(self, status: SystemStatus) -> Panel:
        title = Text(f"{self.app_name}", style="bold cyan")
        subtitle = Text(f" v{status.version}  |  Adaptive Real-time Gold Understanding System", style="grey62")
        return Panel(Text.assemble(title, subtitle), border_style="cyan")

    def _build_status_table(self, status: SystemStatus) -> Table:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="bold white")
        table.add_column("Value")

        table.add_row("Symbol", status.symbol)
        table.add_row("Connection", self._styled(status.connection_state))
        table.add_row("Scanner", self._styled(status.scanner_state))
        table.add_row("Price", format_price(status.current_price, decimals=2))
        table.add_row("Spread", format_price(status.spread, decimals=2))
        table.add_row("Session", status.session or get_current_session())
        table.add_row("Trend", self._styled(status.trend))
        table.add_row("Decision", self._styled(status.decision))
        table.add_row("Confidence", f"{status.confidence * 100:.1f}%")
        table.add_row("Last Updated", status.last_updated.strftime("%Y-%m-%d %H:%M:%S"))
        return table

    def render(self) -> Panel:
        """Build the full dashboard renderable for the current status."""
        status = self.status_manager.snapshot()
        header = self._build_header(status)
        body = self._build_status_table(status)
        return Panel(Group(header, body), title="LIVE STATUS", border_style="blue")

    def render_once(self) -> None:
        """Print a single, static snapshot of the dashboard to the console."""
        self.console.clear()
        self.console.print(self.render())

    def live(self) -> Live:
        """
        Return a `rich.live.Live` context manager for continuous refresh.

        Usage
        -----
        >>> with dashboard.live() as live_view:
        ...     while running:
        ...         live_view.update(dashboard.render())
        ...         time.sleep(dashboard.refresh_seconds)
        """
        return Live(self.render(), console=self.console, refresh_per_second=4, screen=False)
