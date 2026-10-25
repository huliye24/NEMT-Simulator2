"""Causal monthly market-regime features and a walk-forward strategy router."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class RegimeSnapshot:
    """Features known before a monthly strategy decision."""

    month: str
    trailing_return: float
    trend_z: float
    directional_efficiency: float
    realized_volatility: float
    volatility_ratio: float
    direction: int
    regime: str

    def vector(self) -> tuple[float, float, float, float]:
        """Return the numerical feature vector used by the router."""
        return (
            self.trend_z,
            self.directional_efficiency,
            self.realized_volatility,
            self.volatility_ratio,
        )


@dataclass(frozen=True)
class MonthlyPerformance:
    """One strategy's realized result for one month."""

    month: str
    variant: str
    return_pct: float
    max_drawdown_pct: float
    trades: int
    expectancy_ratio: float

    @property
    def utility(self) -> float:
        """Risk-adjusted monthly utility used for strategy selection."""
        return self.return_pct - 0.50 * self.max_drawdown_pct


@dataclass(frozen=True)
class RouterDecision:
    """A strategy choice made using earlier months only."""

    month: str
    regime: str
    selected_variant: str
    estimated_utility: float
    realized_return_pct: float
    realized_drawdown_pct: float
    history_months: int


def _standard_deviation(values: Sequence[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def compute_regime_snapshot(
    *, month: str, closes: Sequence[float], bars_per_day: int = 6,
    long_days: int = 90, short_days: int = 20,
) -> RegimeSnapshot:
    """Classify a month from candles completed before that month begins."""
    long_count = long_days * bars_per_day
    short_count = short_days * bars_per_day
    if len(closes) < long_count + 1:
        raise ValueError("insufficient pre-month history for regime classification")
    window = [float(value) for value in closes[-(long_count + 1):]]
    if any(not math.isfinite(value) or value <= 0 for value in window):
        raise ValueError("closes must be finite and positive")
    log_returns = [math.log(current / previous) for previous, current in zip(window, window[1:])]
    trailing_return = math.exp(sum(log_returns)) - 1.0
    volatility = _standard_deviation(log_returns)
    short_volatility = _standard_deviation(log_returns[-short_count:])
    annualizer = math.sqrt(bars_per_day * 365)
    realized_volatility = volatility * annualizer
    volatility_ratio = short_volatility / volatility if volatility > 0 else 1.0
    path = sum(abs(current - previous) for previous, current in zip(window, window[1:]))
    directional_efficiency = abs(window[-1] - window[0]) / path if path > 0 else 0.0
    trend_z = abs(statistics.mean(log_returns)) * math.sqrt(len(log_returns)) / volatility if volatility > 0 else 0.0
    direction = 1 if trailing_return > 0 else -1 if trailing_return < 0 else 0

    if volatility_ratio >= 1.45 and directional_efficiency < 0.20:
        regime = "turbulent"
    elif trend_z >= 1.50 and directional_efficiency >= 0.30:
        regime = "strong_trend"
    elif trend_z >= 0.75 and directional_efficiency >= 0.16:
        regime = "weak_trend"
    else:
        regime = "range"
    return RegimeSnapshot(
        month=month,
        trailing_return=trailing_return,
        trend_z=trend_z,
        directional_efficiency=directional_efficiency,
        realized_volatility=realized_volatility,
        volatility_ratio=volatility_ratio,
        direction=direction,
        regime=regime,
    )


def _scaled_distance(
    left: RegimeSnapshot, right: RegimeSnapshot, history: Sequence[RegimeSnapshot]
) -> float:
    columns = list(zip(*(item.vector() for item in history)))
    scales = [max(_standard_deviation(column), 1e-6) for column in columns]
    return math.sqrt(sum(
        ((a - b) / scale) ** 2
        for a, b, scale in zip(left.vector(), right.vector(), scales)
    ))


def select_variant(
    *, target: RegimeSnapshot, history_snapshots: Sequence[RegimeSnapshot],
    history_performance: Sequence[MonthlyPerformance], variants: Sequence[str],
    neighbors: int = 8, conservative_penalty: float = 0.50,
) -> tuple[str, float]:
    """Select a variant from similar past months without future observations."""
    if not history_snapshots:
        raise ValueError("router needs at least one historical month")
    snapshots_by_month = {item.month: item for item in history_snapshots}
    distances = sorted(
        (
            (_scaled_distance(target, snapshot, history_snapshots), snapshot.month)
            for snapshot in history_snapshots
        ),
        key=lambda item: item[0],
    )[:neighbors]
    selected_months = {month for _, month in distances}
    distance_by_month = {month: distance for distance, month in distances}
    positive_distances = [distance for distance, _ in distances if distance > 0]
    bandwidth = statistics.median(positive_distances) if positive_distances else 1.0
    best_variant = variants[0]
    best_score = -math.inf
    for variant in variants:
        observations = [
            item for item in history_performance
            if item.variant == variant and item.month in selected_months
            and item.month in snapshots_by_month
        ]
        if not observations:
            continue
        weights = [math.exp(-distance_by_month[item.month] / max(bandwidth, 1e-6))
                   for item in observations]
        total_weight = sum(weights)
        mean = sum(weight * item.utility for weight, item in zip(weights, observations)) / total_weight
        variance = sum(
            weight * (item.utility - mean) ** 2
            for weight, item in zip(weights, observations)
        ) / total_weight
        effective_n = total_weight ** 2 / sum(weight ** 2 for weight in weights)
        score = mean - conservative_penalty * math.sqrt(variance / max(effective_n, 1.0))
        if score > best_score:
            best_variant, best_score = variant, score
    return best_variant, best_score


def walk_forward_route(
    *, snapshots: Sequence[RegimeSnapshot], performance: Sequence[MonthlyPerformance],
    variants: Sequence[str], min_history_months: int = 8,
    fallback_variant: str = "v4c",
) -> list[RouterDecision]:
    """Produce expanding-window decisions; each decision sees only earlier months."""
    ordered = sorted(snapshots, key=lambda item: item.month)
    performance_by_key = {(item.month, item.variant): item for item in performance}
    decisions: list[RouterDecision] = []
    for index, target in enumerate(ordered):
        history = ordered[:index]
        if len(history) < min_history_months:
            selected, estimate = fallback_variant, 0.0
        else:
            history_months = {item.month for item in history}
            eligible = [item for item in performance if item.month in history_months]
            selected, estimate = select_variant(
                target=target,
                history_snapshots=history,
                history_performance=eligible,
                variants=variants,
            )
        realized = performance_by_key.get((target.month, selected))
        if realized is None:
            continue
        decisions.append(RouterDecision(
            month=target.month,
            regime=target.regime,
            selected_variant=selected,
            estimated_utility=estimate,
            realized_return_pct=realized.return_pct,
            realized_drawdown_pct=realized.max_drawdown_pct,
            history_months=len(history),
        ))
    return decisions


def compound_return(returns_pct: Iterable[float]) -> float:
    """Compound a sequence of percentage returns."""
    equity = 1.0
    for value in returns_pct:
        equity *= 1.0 + value / 100.0
    return (equity - 1.0) * 100.0
