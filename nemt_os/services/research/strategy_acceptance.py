"""Acceptance policy for asymmetric-payoff trend strategies.

Win rate is reported for diagnosis but is intentionally not a gate.  A low
win-rate system may be valid when its payoff distribution produces positive
expectancy without violating survival constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping


@dataclass(frozen=True)
class AcceptanceThresholds:
    minimum_trades: int = 20
    minimum_profit_factor: float = 1.20
    minimum_payoff_ratio: float = 1.20
    minimum_expectancy_ratio: float = 0.05
    minimum_sharpe: float = 1.50
    maximum_drawdown: float = 0.20


def assess_strategy(
    metrics: Mapping[str, float],
    thresholds: AcceptanceThresholds = AcceptanceThresholds(),
) -> dict[str, object]:
    """Evaluate growth and survival; never reject solely for low win rate."""

    checks = {
        "enough_trades": metrics.get("trade_count", 0.0) >= thresholds.minimum_trades,
        "positive_total_return": metrics.get("total_return", 0.0) > 0.0,
        "positive_expectancy": metrics.get("expectancy_ratio", 0.0) >= thresholds.minimum_expectancy_ratio,
        "profit_factor": metrics.get("profit_factor", 0.0) >= thresholds.minimum_profit_factor,
        "payoff_ratio": metrics.get("payoff_ratio", 0.0) >= thresholds.minimum_payoff_ratio,
        "sharpe": metrics.get("sharpe_ratio", 0.0) >= thresholds.minimum_sharpe,
        "drawdown": metrics.get("max_drawdown", 1.0) <= thresholds.maximum_drawdown,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "thresholds": asdict(thresholds),
        "diagnostics": {"win_rate": metrics.get("win_rate", 0.0)},
        "policy": "positive_expectancy_and_survival",
    }
