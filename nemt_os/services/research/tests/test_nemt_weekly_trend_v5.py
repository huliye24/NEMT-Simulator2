import math

from nemt_os.services.research.nemt_weekly_trend_v5 import assess_weekly_entry


def _series(count: int) -> tuple[list[float], list[float], list[float]]:
    closes = [100.0 * math.exp(0.001 * i + 0.02 * math.sin(i / 11)) for i in range(count)]
    return closes, [value * 1.004 for value in closes], [value * 0.996 for value in closes]


def test_noncritical_state_fails_closed() -> None:
    closes = [100.0] * 1000
    decision = assess_weekly_entry(closes=closes, highs=closes, lows=closes, index=900)
    assert decision.permitted is False
    assert decision.reason == "not_nemt_critical"


def test_future_changes_do_not_change_current_decision() -> None:
    closes, highs, lows = _series(1800)
    index = 1600
    before = assess_weekly_entry(closes=closes, highs=highs, lows=lows, index=index)
    changed_closes, changed_highs, changed_lows = closes[:], highs[:], lows[:]
    for offset in range(index + 1, len(closes)):
        changed_closes[offset] *= 3.0
        changed_highs[offset] *= 3.0
        changed_lows[offset] *= 0.2
    after = assess_weekly_entry(
        closes=changed_closes, highs=changed_highs, lows=changed_lows, index=index
    )
    assert after == before


def test_horizons_begin_at_one_week_of_four_hour_bars() -> None:
    closes, highs, lows = _series(1200)
    decision = assess_weekly_entry(closes=closes, highs=highs, lows=lows, index=1000)
    assert decision.selected_horizon_bars in {42, 84, 126, 252}
    assert decision.direction in {"LONG", "SHORT", "NEUTRAL"}
