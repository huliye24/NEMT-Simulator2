"""NEMT v5: causal weekly-value permission for NEMT critical events."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Literal, Sequence

from .nemt_momentum_v2 import MomentumState, compute_momentum_state

Direction = Literal["LONG", "SHORT", "NEUTRAL"]


@dataclass(frozen=True)
class WeeklyTrendConfig:
    horizons: tuple[int, ...] = (42, 84, 126, 252)
    longest_lookback_bars: int = 252
    neighbor_count: int = 48
    minimum_neighbors: int = 24
    event_separation_bars: int = 12
    fractional_risk: float = 0.25
    uncertainty_z: float = 0.84
    fee_rate_each_side: float = 0.0005
    slippage_rate_each_side: float = 0.0002
    stop_atr_multiple: float = 2.0
    maximum_leverage: int = 3


@dataclass(frozen=True)
class WeeklyTrendDecision:
    direction: Direction
    permitted: bool
    selected_horizon_bars: int
    expected_r: float
    conservative_log_growth: float
    payoff_ratio: float
    win_probability: float
    neighbor_count: int
    reason: str
    features: tuple[float, ...]


def _ret(closes: Sequence[float], index: int, bars: int) -> float:
    return closes[index] / closes[index - bars] - 1.0


def _efficiency(closes: Sequence[float], index: int, bars: int) -> float:
    window = closes[index - bars:index + 1]
    path = sum(abs(b - a) for a, b in zip(window, window[1:]))
    return abs(window[-1] - window[0]) / path if path else 0.0


def _volatility(closes: Sequence[float], index: int, bars: int) -> float:
    window = closes[index - bars:index + 1]
    values = [math.log(b / a) for a, b in zip(window, window[1:])]
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _atr(closes: Sequence[float], highs: Sequence[float], lows: Sequence[float], index: int) -> float:
    values = []
    for cursor in range(index - 13, index + 1):
        values.append(max(highs[cursor] - lows[cursor],
                          abs(highs[cursor] - closes[cursor - 1]),
                          abs(lows[cursor] - closes[cursor - 1])))
    return statistics.mean(values)


def _features(closes: Sequence[float], index: int, state: MomentumState) -> tuple[float, ...]:
    vol_42 = _volatility(closes, index, 42)
    return (_ret(closes, index, 18), _ret(closes, index, 42),
            _ret(closes, index, 126), _ret(closes, index, 252),
            _efficiency(closes, index, 42), _efficiency(closes, index, 126),
            vol_42, _volatility(closes, index, 18) / vol_42 if vol_42 else 1.0,
            state.psi / 100.0, state.entropy, state.score / 100.0)


def _direction(state: MomentumState) -> int:
    return 1 if state.phase == "critical_up" else -1 if state.phase == "critical_down" else 0


def _outcome_r(closes: Sequence[float], highs: Sequence[float], lows: Sequence[float],
               index: int, direction: int, horizon: int,
               config: WeeklyTrendConfig) -> float:
    entry = closes[index]
    risk_fraction = max(config.stop_atr_multiple * _atr(closes, highs, lows, index) / entry, 0.01)
    stop = entry * (1.0 - direction * risk_fraction)
    costs = 2 * config.fee_rate_each_side + 2 * config.slippage_rate_each_side
    for cursor in range(index + 1, index + horizon + 1):
        stopped = lows[cursor] <= stop if direction == 1 else highs[cursor] >= stop
        if stopped:
            return -1.0 - costs / risk_fraction
    directional_return = direction * (closes[index + horizon] / entry - 1.0)
    return (directional_return - costs) / risk_fraction


def _historical_events(closes: Sequence[float], index: int, direction: int,
                       config: WeeklyTrendConfig) -> list[tuple[int, tuple[float, ...]]]:
    events = []
    last_event = -config.event_separation_bars
    for cursor in range(config.longest_lookback_bars, index - max(config.horizons)):
        state = compute_momentum_state(closes[:cursor + 1])
        if _direction(state) != direction or cursor - last_event < config.event_separation_bars:
            continue
        events.append((cursor, _features(closes, cursor, state)))
        last_event = cursor
    return events


def _estimate(outcomes: Sequence[float], weights: Sequence[float],
              config: WeeklyTrendConfig) -> tuple[float, float]:
    total = sum(weights)
    mean_r = sum(w * r for w, r in zip(weights, outcomes)) / total
    utilities = [math.log(max(0.05, 1.0 + config.fractional_risk * r)) for r in outcomes]
    mean_u = sum(w * u for w, u in zip(weights, utilities)) / total
    variance = sum(w * (u - mean_u) ** 2 for w, u in zip(weights, utilities)) / total
    effective_n = total ** 2 / sum(w ** 2 for w in weights)
    lower_bound = mean_u - config.uncertainty_z * math.sqrt(variance / max(effective_n, 1.0))
    return mean_r, lower_bound


def assess_weekly_entry(*, closes: Sequence[float], highs: Sequence[float],
                        lows: Sequence[float], index: int,
                        config: WeeklyTrendConfig = WeeklyTrendConfig()) -> WeeklyTrendDecision:
    """Permit only NEMT critical events with positive conservative log-growth."""
    if not (len(closes) == len(highs) == len(lows)):
        raise ValueError("OHLC sequences must have equal length")
    if index < config.longest_lookback_bars:
        raise ValueError("insufficient feature history")
    state = compute_momentum_state(closes[:index + 1])
    direction = _direction(state)
    current = _features(closes, index, state)
    if direction == 0:
        return WeeklyTrendDecision("NEUTRAL", False, config.horizons[0], 0.0, 0.0,
                                   0.0, 0.0, 0, "not_nemt_critical", current)
    label: Direction = "LONG" if direction == 1 else "SHORT"
    events = _historical_events(closes, index, direction, config)
    if len(events) < config.minimum_neighbors:
        return WeeklyTrendDecision(label, False, config.horizons[0], 0.0, 0.0,
                                   0.0, 0.0, len(events), "insufficient_mature_events", current)
    columns = list(zip(*(features for _, features in events)))
    scales = [max(statistics.pstdev(column), 1e-8) for column in columns]
    distances = sorted((math.sqrt(sum(((a - b) / scale) ** 2
                                      for a, b, scale in zip(current, features, scales))), cursor)
                       for cursor, features in events)[:config.neighbor_count]
    positive = [distance for distance, _ in distances if distance > 0]
    bandwidth = statistics.median(positive) if positive else 1.0
    weights = [math.exp(-distance / max(bandwidth, 1e-8)) for distance, _ in distances]
    best = (config.horizons[0], -math.inf, -math.inf, [])
    for horizon in config.horizons:
        outcomes = [_outcome_r(closes, highs, lows, cursor, direction, horizon, config)
                    for _, cursor in distances]
        expected_r, lower_bound = _estimate(outcomes, weights, config)
        if lower_bound > best[2]:
            best = (horizon, expected_r, lower_bound, outcomes)
    horizon, expected_r, lower_bound, outcomes = best
    wins = [value for value in outcomes if value > 0]
    losses = [-value for value in outcomes if value <= 0]
    payoff = statistics.mean(wins) / statistics.mean(losses) if wins and losses else 0.0
    probability = len(wins) / len(outcomes)
    return WeeklyTrendDecision(
        label, lower_bound > 0.0, horizon, expected_r, lower_bound, payoff,
        probability, len(distances),
        "positive_conservative_log_growth" if lower_bound > 0 else "non_positive_conservative_log_growth",
        current,
    )
