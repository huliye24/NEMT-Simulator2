"""Tests for the experimental annual trend overlay."""

from __future__ import annotations

from nemt_os.services.research.trend_regime import (
    AnnualTrendConfig,
    classify_annual_trend,
    is_new_directional_event,
    permits_nemt_entry,
)


def test_annual_trend_classification_is_causal() -> None:
    config = AnnualTrendConfig(lookback_bars=4, neutral_band=0.15)
    prefix = [100.0, 101.0, 102.0, 103.0, 120.0]
    full = prefix + [1.0, 9999.0]

    assert classify_annual_trend(prefix, 4, config) == classify_annual_trend(
        full, 4, config
    )
    assert classify_annual_trend(full, 4, config).regime == "bull"


def test_annual_trend_has_neutral_and_bear_states() -> None:
    config = AnnualTrendConfig(lookback_bars=2, neutral_band=0.15)

    assert classify_annual_trend([100.0, 100.0, 95.0], 2, config).regime == "neutral"
    assert classify_annual_trend([100.0, 100.0, 80.0], 2, config).regime == "bear"
    assert classify_annual_trend([100.0, 101.0], 1, config).regime == "unknown"


def test_countertrend_requires_stronger_psi() -> None:
    config = AnnualTrendConfig(countertrend_psi_multiplier=1.5)

    assert permits_nemt_entry("LONG", 0.55, "bull", config=config)
    assert not permits_nemt_entry("SHORT", -0.70, "bull", config=config)
    assert permits_nemt_entry("SHORT", -0.80, "bull", config=config)
    assert permits_nemt_entry("SHORT", -0.55, "bear", config=config)
    assert not permits_nemt_entry("LONG", 0.70, "bear", config=config)
    assert permits_nemt_entry("LONG", 0.80, "bear", config=config)


def test_directional_event_is_not_repeated_each_bar() -> None:
    assert is_new_directional_event("LONG", None)
    assert not is_new_directional_event("LONG", "LONG")
    assert is_new_directional_event("SHORT", "LONG")
