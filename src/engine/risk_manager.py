"""
engine.risk_manager
====================
Risk Manager (Phase 1 skeleton).

Responsible - once implemented - for translating a `Decision` into a
concrete order plan: lot size, stop loss (derived from a fixed floating
loss in account currency), and take profit (1:2 reward-to-risk by
default). No order execution occurs here or anywhere yet in Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.config_manager import ConfigManager
from src.core.logger import get_logger

logger = get_logger("RiskManager")


@dataclass
class OrderPlan:
    """A fully-specified, not-yet-executed order plan."""

    symbol: str
    direction: str  # "BUY" | "SELL"
    lot: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    risk_amount: float
    reward_to_risk: float


class RiskManager:
    """
    Computes position sizing and SL/TP levels from configuration and
    live price/symbol data. Placeholder implementation for Phase 1 -
    calculation logic (point value, contract size lookups) arrives in
    a later phase once the MT5 symbol-info bridge is wired in.
    """

    def __init__(self, config: Optional[ConfigManager] = None) -> None:
        self.config = config or ConfigManager()
        self.fixed_loss = float(self.config.get("risk.fixed_loss_per_trade", 5.0))
        self.reward_to_risk = float(self.config.get("risk.reward_to_risk", 2.0))
        self.lot = float(self.config.get("mt5.lot", 0.01))
        self.max_open_positions = int(self.config.get("risk.max_open_positions", 1))

    def build_order_plan(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
    ) -> OrderPlan:
        """
        Build an `OrderPlan` for a given direction and entry price.

        Args:
            symbol: Trading symbol, e.g. "XAUUSD".
            direction: "BUY" or "SELL".
            entry_price: The proposed entry price.

        Returns:
            An `OrderPlan`. SL/TP prices are `None` until the point-value
            based calculation is implemented in a later phase.
        """
        logger.info(
            f"RiskManager.build_order_plan() called: {direction} {symbol} @ {entry_price} "
            f"(fixed_loss={self.fixed_loss}, RR={self.reward_to_risk})"
        )
        logger.info("SL/TP price calculation not yet implemented - returning plan with prices=None.")

        return OrderPlan(
            symbol=symbol,
            direction=direction,
            lot=self.lot,
            stop_loss_price=None,
            take_profit_price=None,
            risk_amount=self.fixed_loss,
            reward_to_risk=self.reward_to_risk,
        )

    def is_within_risk_limits(self, daily_loss_so_far: float, open_positions: int) -> bool:
        """
        Check whether a new trade would violate configured risk limits.

        Args:
            daily_loss_so_far: Realized + floating loss for the day so far.
            open_positions: Number of currently open positions.

        Returns:
            True if a new trade is permitted under current risk limits.
        """
        max_daily_loss = float(self.config.get("risk.max_daily_loss", 50.0))

        if daily_loss_so_far >= max_daily_loss:
            logger.warning(f"Daily loss limit reached: {daily_loss_so_far} >= {max_daily_loss}")
            return False

        if open_positions >= self.max_open_positions:
            logger.warning(f"Max open positions reached: {open_positions} >= {self.max_open_positions}")
            return False

        return True
