"""NEMT v3 position controller and stop-risk sizing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from .nemt_momentum_v2 import MomentumState

Action = Literal["OPEN", "HOLD", "CLOSE", "REVERSE", "FLAT", "WAIT_REVERSAL", "COOLDOWN"]


@dataclass(frozen=True)
class StrategyV3Config:
    reversal_confirmation_bars: int = 2
    stop_cooldown_bars: int = 2
    risk_per_trade: float = 0.02
    base_leverage: int = 3
    strong_leverage: int = 5
    strong_score: int = 85

    def __post_init__(self) -> None:
        if self.reversal_confirmation_bars < 1:
            raise ValueError("reversal_confirmation_bars must be >= 1")
        if self.stop_cooldown_bars < 0:
            raise ValueError("stop_cooldown_bars must be >= 0")
        if not 0.0 < self.risk_per_trade <= 0.1:
            raise ValueError("risk_per_trade must be in (0, 0.1]")
        if not 1 <= self.base_leverage <= self.strong_leverage <= 5:
            raise ValueError("v3 leverage must satisfy 1 <= base <= strong <= 5")


@dataclass(frozen=True)
class V3Decision:
    target: int
    action: Action
    leverage: int
    reversal_count: int


def risk_sized_notional(
    equity: float,
    stop_pct: float,
    leverage: int,
    config: StrategyV3Config = StrategyV3Config(),
) -> float:
    """Size notional so the modeled stop risks at most 2% by default."""

    if equity <= 0.0 or stop_pct <= 0.0:
        return 0.0
    risk_notional = equity * config.risk_per_trade / stop_pct
    carrying_cap = equity * leverage * 0.95
    return min(risk_notional, carrying_cap)


class PositionControllerV3:
    """Causal one-position state machine with confirmed reversals."""

    def __init__(self, config: StrategyV3Config = StrategyV3Config()) -> None:
        self.config = config
        self._pending_direction: Optional[int] = None
        self._pending_count = 0
        self._cooldown = 0

    def on_stop(self) -> None:
        """Start a cooldown after a protective stop."""

        self._cooldown = self.config.stop_cooldown_bars
        self._pending_direction = None
        self._pending_count = 0

    def decide(self, state: MomentumState, current_target: int) -> V3Decision:
        """Return the next target using current and retained past state only."""

        leverage = self.config.strong_leverage if state.score >= self.config.strong_score else self.config.base_leverage
        signal = 1 if state.phase == "critical_up" else -1 if state.phase == "critical_down" else None
        if current_target == 0 and self._cooldown > 0:
            self._cooldown -= 1
            return V3Decision(0, "COOLDOWN", leverage, 0)
        if state.phase == "decay":
            self._pending_direction, self._pending_count = None, 0
            return V3Decision(0, "CLOSE" if current_target else "FLAT", leverage, 0)
        if current_target == 0:
            self._pending_direction, self._pending_count = None, 0
            return V3Decision(signal or 0, "OPEN" if signal else "FLAT", leverage, 0)
        if signal is None or signal == current_target:
            self._pending_direction, self._pending_count = None, 0
            return V3Decision(current_target, "HOLD", leverage, 0)
        if self._pending_direction == signal:
            self._pending_count += 1
        else:
            self._pending_direction, self._pending_count = signal, 1
        if self._pending_count >= self.config.reversal_confirmation_bars:
            count = self._pending_count
            self._pending_direction, self._pending_count = None, 0
            return V3Decision(signal, "REVERSE", leverage, count)
        return V3Decision(current_target, "WAIT_REVERSAL", leverage, self._pending_count)
