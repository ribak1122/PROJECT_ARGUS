"""
engine.decision_engine
=======================
Decision Engine (Phase 1 skeleton).

Responsible - once implemented - for synthesizing `EvidenceItem` objects
from the Evidence Engine into a final trading decision (BUY / SELL / WAIT)
with an associated confidence score. No decision logic is implemented yet;
this module defines the contract only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from src.core.logger import get_logger
from src.core.system_status import DecisionState
from src.engine.evidence_engine import EvidenceItem

logger = get_logger("DecisionEngine")


@dataclass
class Decision:
    """The final output of the Decision Engine for a single scan cycle."""

    state: DecisionState = DecisionState.NO_SIGNAL
    confidence: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


class DecisionEngine:
    """
    Consumes evidence and produces a final, confidence-weighted trading
    decision. Placeholder implementation for Phase 1.
    """

    def __init__(self, min_confidence: float = 0.6) -> None:
        self.min_confidence = min_confidence

    def decide(self, evidence: List[EvidenceItem]) -> Decision:
        """
        Evaluate a batch of evidence and produce a `Decision`.

        Args:
            evidence: Evidence items produced by the `EvidenceEngine`.

        Returns:
            A `Decision` object. Always `NO_SIGNAL` until Phase 2 logic
            is implemented.
        """
        logger.info(f"DecisionEngine.decide() called with {len(evidence)} evidence item(s).")

        if not evidence:
            return Decision(state=DecisionState.NO_SIGNAL, confidence=0.0, reasoning=["No evidence available."])

        # Placeholder: real scoring/weighting logic arrives in Phase 2.
        logger.info("Decision logic not yet implemented - returning NO_SIGNAL.")
        return Decision(
            state=DecisionState.NO_SIGNAL,
            confidence=0.0,
            reasoning=["Decision logic not yet implemented."],
        )
