"""Causal long-horizon trend regime overlay for NEMT experiments.

This module deliberately does not change the NEMT state equations.  It only
labels the long-horizon price regime and raises the momentum requirement for a
counter-trend entry.  Keeping the overlay separate makes A/B attribution
possible and prevents an experimental rule from silently becoming theory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Sequence


TrendRegime = Literal["bull", "neutral", "bear", "unknown"]
TradeDirection = Literal["LONG", "SHORT"]


@dataclass(frozen=True)
class AnnualTrendConfig:
    """Configuration for a trailing-price annual trend label.

    ``lookback_bars`` defaults to 365 days of 4-hour candles.  The price at
    ``index`` and the price exactly ``lookback_bars`` earlier are the only
    inputs, so the result is causal and reproducible.
    """

    lookback_bars: int = 365 * 6
    neutral_band: float = 0.15
    countertrend_psi_multiplier: float = 1.5

    def __post_init__(self) -> None:
        if self.lookback_bars < 2:
            raise ValueError("lookback_bars must be >= 2")
        if not 0.0 <= self.neutral_band < 1.0:
            raise ValueError("neutral_band must be in [0, 1)")
        if self.countertrend_psi_multiplier < 1.0:
            raise ValueError("countertrend_psi_multiplier must be >= 1")


@dataclass(frozen=True)
class AnnualTrendState:
    """Long-horizon regime and its trailing return at one decision point."""

    regime: TrendRegime
    trailing_return: Optional[float]


def classify_annual_trend(
    closes: Sequence[float],
    index: int,
    config: AnnualTrendConfig = AnnualTrendConfig(),
) -> AnnualTrendState:
    """Classify bull/neutral/bear using data available at ``index`` only."""

    if index < 0 or index >= len(closes):
        raise IndexError("index is outside closes")
    prior_index = index - config.lookback_bars
    if prior_index < 0:
        return AnnualTrendState("unknown", None)
    prior = float(closes[prior_index])
    current = float(closes[index])
    if prior <= 0.0 or current <= 0.0:
        raise ValueError("prices must be positive")
    trailing_return = current / prior - 1.0
    if trailing_return > config.neutral_band:
        regime: TrendRegime = "bull"
    elif trailing_return < -config.neutral_band:
        regime = "bear"
    else:
        regime = "neutral"
    return AnnualTrendState(regime, trailing_return)


def permits_nemt_entry(
    direction: TradeDirection,
    psi: float,
    regime: TrendRegime,
    *,
    critical_psi: float = 0.5,
    config: AnnualTrendConfig = AnnualTrendConfig(),
) -> bool:
    """Apply a small asymmetric threshold without changing NEMT state math.

    Trend-aligned and neutral entries retain the original ``critical_psi``.
    Counter-trend entries require ``countertrend_psi_multiplier`` times that
    momentum.  ``unknown`` rejects entry because the annual context is absent.
    """

    if critical_psi <= 0.0:
        raise ValueError("critical_psi must be positive")
    if regime == "unknown":
        return False
    countertrend = (regime == "bull" and direction == "SHORT") or (
        regime == "bear" and direction == "LONG"
    )
    threshold = critical_psi * (
        config.countertrend_psi_multiplier if countertrend else 1.0
    )
    return psi > threshold if direction == "LONG" else psi < -threshold


def is_new_directional_event(
    direction: TradeDirection,
    previous_direction: Optional[TradeDirection],
) -> bool:
    """Return true only on first entry into a directional critical phase."""

    return direction != previous_direction
