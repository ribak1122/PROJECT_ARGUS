"""
engine.evidence_engine
=======================
Evidence Engine (Phase 1 skeleton).

Responsible - once implemented - for detecting raw market "evidence":
liquidity sweeps, Fair Value Gaps, RSI confirmation states, and market
structure shifts. This module intentionally contains NO strategy logic
yet; it only defines the architecture/contract that later phases will
fill in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.logger import get_logger
from src.mt5.mt5_bridge import CandleData

logger = get_logger("EvidenceEngine")


@dataclass
class EvidenceItem:
    """A single piece of detected market evidence."""

    kind: str  # e.g. "LIQUIDITY_SWEEP", "FVG", "RSI_CONFIRMATION"
    detected_at: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


class EvidenceEngine:
    """
    Aggregates raw evidence detectors and produces a normalized list of
    `EvidenceItem` objects for the Decision Engine to consume.

    NOTE: Detection methods are placeholders for Phase 2 implementation.
    """

    def __init__(self) -> None:
        self._evidence_log: List[EvidenceItem] = []

    def analyze(
        self,
        entry_candles: List[CandleData],
        structure_candles: List[CandleData],
        rsi_values: Optional[List[float]] = None,
    ) -> List[EvidenceItem]:
        """
        Run all evidence detectors against the supplied candle data.

        Args:
            entry_candles: Recent candles on the entry timeframe (e.g. M3).
            structure_candles: Recent candles on the structure timeframe (e.g. M15).
            rsi_values: Optional pre-computed RSI series aligned to entry_candles.

        Returns:
            A list of detected `EvidenceItem` objects (empty until Phase 2).
        """
        logger.info(
            f"EvidenceEngine.analyze() called with {len(entry_candles)} entry candles "
            f"and {len(structure_candles)} structure candles."
        )

        evidence: List[EvidenceItem] = []
        evidence.extend(self.detect_liquidity_sweep(entry_candles))
        evidence.extend(self.detect_fair_value_gap(entry_candles))
        evidence.extend(self.detect_rsi_confirmation(rsi_values or []))

        self._evidence_log.extend(evidence)
        return evidence

    def detect_liquidity_sweep(self, candles: List[CandleData]) -> List[EvidenceItem]:
        """
        Detect liquidity sweep patterns (stop-hunt beyond a prior high/low
        followed by rejection).

        NOT YET IMPLEMENTED - placeholder for Phase 2.
        """
        logger.info("detect_liquidity_sweep() not yet implemented.")
        return []

    def detect_fair_value_gap(self, candles: List[CandleData]) -> List[EvidenceItem]:
        """
        Detect Fair Value Gaps (3-candle imbalance patterns) and their
        subsequent rejection/fill behaviour.

        NOT YET IMPLEMENTED - placeholder for Phase 2.
        """
        logger.info("detect_fair_value_gap() not yet implemented.")
        return []

    def detect_rsi_confirmation(self, rsi_values: List[float]) -> List[EvidenceItem]:
        """
        Detect RSI overbought/oversold confirmation aligned with price
        action evidence.

        NOT YET IMPLEMENTED - placeholder for Phase 2.
        """
        logger.info("detect_rsi_confirmation() not yet implemented.")
        return []

    @property
    def history(self) -> List[EvidenceItem]:
        """Return all evidence collected so far this session."""
        return list(self._evidence_log)
