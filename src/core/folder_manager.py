"""
core.folder_manager
====================
Ensures that all directories PROJECT ARGUS depends on (logs, journal
storage, config, docs) exist before the rest of the system boots.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, List

from src.core.logger import get_logger

logger = get_logger("FolderManager")


class FolderManager:
    """Creates and validates the on-disk folder layout for the project."""

    REQUIRED_FOLDERS: ClassVar[List[str]] = [
        "logs",
        "config",
        "docs",
        "journal_data",
    ]

    def __init__(self, base_path: str = ".") -> None:
        self.base_path = Path(base_path).resolve()

    def ensure_all(self) -> None:
        """Create every required folder if it does not already exist."""
        for folder in self.REQUIRED_FOLDERS:
            self.ensure(folder)
        logger.success("All required folders verified.")

    def ensure(self, relative_path: str) -> Path:
        """
        Ensure a single folder exists, creating it (and parents) if needed.

        Args:
            relative_path: Path relative to the project base directory.

        Returns:
            The absolute `Path` to the ensured folder.
        """
        target = self.base_path / relative_path
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created missing folder: {target}")
        return target
