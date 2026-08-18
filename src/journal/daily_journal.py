"""
journal.daily_journal
======================
Persists a daily record of system events and (eventually) trade outcomes
to disk, so every trading day can be reviewed and audited independently.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.config_manager import ConfigManager
from src.core.logger import get_logger

logger = get_logger("DailyJournal")


@dataclass
class JournalEntry:
    """A single journal entry (a system event, decision, or trade note)."""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    category: str = "INFO"  # e.g. "SYSTEM", "DECISION", "TRADE", "GUARDIAN"
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


class DailyJournal:
    """
    Writes structured journal entries to a per-day file (CSV or JSON,
    configurable) under the configured journal directory.

    Usage
    -----
    >>> journal = DailyJournal()
    >>> journal.log("SYSTEM", "Scanner started", {"symbol": "XAUUSD"})
    """

    def __init__(self, config: Optional[ConfigManager] = None) -> None:
        self.config = config or ConfigManager()
        self.directory = Path(self.config.get("journal.directory", "journal_data"))
        self.file_format = str(self.config.get("journal.format", "csv")).lower()
        self.directory.mkdir(parents=True, exist_ok=True)

    def _today_path(self) -> Path:
        filename = f"journal_{datetime.now().strftime('%Y-%m-%d')}.{self.file_format}"
        return self.directory / filename

    def log(self, category: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Append a new entry to today's journal file.

        Args:
            category: Logical grouping, e.g. "SYSTEM", "DECISION", "TRADE".
            message: Human-readable description of the event.
            data: Optional structured payload (evidence, prices, etc.).
        """
        entry = JournalEntry(category=category, message=message, data=data or {})

        try:
            if self.file_format == "json":
                self._append_json(entry)
            else:
                self._append_csv(entry)
            logger.info(f"Journal entry recorded: [{category}] {message}")
        except OSError as exc:
            logger.error(f"Failed to write journal entry: {exc}")

    def read_today(self) -> List[Dict[str, Any]]:
        """Read and return all journal entries recorded today."""
        path = self._today_path()
        if not path.exists():
            return []

        if self.file_format == "json":
            with path.open("r", encoding="utf-8") as file_handle:
                return json.load(file_handle)

        entries: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8", newline="") as file_handle:
            reader = csv.DictReader(file_handle)
            for row in reader:
                entries.append(dict(row))
        return entries

    # ------------------------------------------------------------------ #
    # Internal writers
    # ------------------------------------------------------------------ #
    def _append_csv(self, entry: JournalEntry) -> None:
        path = self._today_path()
        file_exists = path.exists()

        with path.open("a", encoding="utf-8", newline="") as file_handle:
            fieldnames = ["timestamp", "category", "message", "data"]
            writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            row = asdict(entry)
            row["data"] = json.dumps(row["data"])
            writer.writerow(row)

    def _append_json(self, entry: JournalEntry) -> None:
        path = self._today_path()
        entries: List[Dict[str, Any]] = []
        if path.exists():
            with path.open("r", encoding="utf-8") as file_handle:
                try:
                    entries = json.load(file_handle)
                except json.JSONDecodeError:
                    entries = []

        entries.append(asdict(entry))
        with path.open("w", encoding="utf-8") as file_handle:
            json.dump(entries, file_handle, indent=2)
