from __future__ import annotations

import math

import pytest

from nemt_os.services.research.regime_router_v44 import (
    MonthlyPerformance,
    RegimeSnapshot,
    classify_regimes_causally,
    compound_return,
    compute_regime_snapshot,
    walk_forward_route,
)


def test_regime_features_use_supplied_pre_month_closes() -> None:
    closes = [100.0 * math.exp(index * 0.002) for index in range(541)]
    snapshot = compute_regime_snapshot(month="2025-01", closes=closes)
    assert snapshot.direction == 1
    assert snapshot.trailing_return > 0
    assert snapshot.directional_efficiency == pytest.approx(1.0)
    assert snapshot.regime == "strong_trend"


def test_walk_forward_decisions_do_not_change_when_future_results_change() -> None:
    snapshots = [
        RegimeSnapshot(f"2025-{month:02d}", 0.1, 1.2, 0.3, 0.5, 1.0, 1, "weak_trend")
        for month in range(1, 11)
    ]
    performance = [
        MonthlyPerformance(snapshot.month, variant, 2.0 if variant == "v4b" else 0.0,
                           1.0, 3, 0.1)
        for snapshot in snapshots for variant in ("v4b", "v4c")
    ]
    original = walk_forward_route(
        snapshots=snapshots, performance=performance,
        variants=("v4b", "v4c"), min_history_months=3,
    )
    changed = performance[:-2] + [
        MonthlyPerformance("2025-10", "v4b", -99.0, 99.0, 3, -1.0),
        MonthlyPerformance("2025-10", "v4c", 99.0, 1.0, 3, 1.0),
    ]
    rerun = walk_forward_route(
        snapshots=snapshots, performance=changed,
        variants=("v4b", "v4c"), min_history_months=3,
    )
    assert original[-1].selected_variant == rerun[-1].selected_variant
    assert original[-1].estimated_utility == rerun[-1].estimated_utility


def test_compound_return() -> None:
    assert compound_return([10.0, -10.0]) == pytest.approx(-1.0)


def test_causal_regime_labels_ignore_future_features() -> None:
    snapshots = [
        RegimeSnapshot(
            f"2025-{month:02d}", 0.01 * month, 0.1 * month,
            0.01 * month, 0.4, 0.8 + 0.01 * month, 1, "range",
        )
        for month in range(1, 11)
    ]
    original = classify_regimes_causally(snapshots, calibration_months=3)
    changed = snapshots[:-1] + [
        RegimeSnapshot("2025-10", -0.9, 99.0, 0.99, 2.0, 9.0, -1, "range")
    ]
    rerun = classify_regimes_causally(changed, calibration_months=3)
    assert [item.regime for item in original[:-1]] == [item.regime for item in rerun[:-1]]
