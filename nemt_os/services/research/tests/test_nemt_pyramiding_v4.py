import pytest

from nemt_os.services.research.nemt_pyramiding_v4 import (
    AdaptivePyramidInputs,
    AdaptivePyramidingConfig,
    PyramidPosition,
    PyramidingControllerV4,
    PyramidingV4Config,
    adaptive_pyramid_decision,
    adaptive_pyramid_decision_v42,
)


def long_position() -> PyramidPosition:
    return PyramidPosition(1, 100.0, 98.0, 100.0, 1.0, 100.0, 98.0)


def test_first_and_second_additions_decrease() -> None:
    controller = PyramidingControllerV4()
    position = long_position()
    first = controller.evaluate(position, price=102.0, atr=1.0, equity=100.0, same_direction_confirmed=True)
    assert first.add_notional == 50.0
    controller.apply_add(position, first, fill_price=102.0)
    second = controller.evaluate(position, price=104.0, atr=1.0, equity=100.0, same_direction_confirmed=True)
    assert second.add_notional == 25.0


def test_never_adds_to_loss_or_without_nemt_confirmation() -> None:
    controller = PyramidingControllerV4()
    position = long_position()
    assert controller.evaluate(position, price=99.0, atr=1.0, equity=100.0, same_direction_confirmed=True).add_notional == 0
    assert controller.evaluate(position, price=104.0, atr=1.0, equity=100.0, same_direction_confirmed=False).add_notional == 0


def test_trailing_stop_never_loosens() -> None:
    controller = PyramidingControllerV4(PyramidingV4Config(mode="v4_b_atr_trailing"))
    position = long_position()
    first = controller.evaluate(position, price=105.0, atr=1.0, equity=100.0, same_direction_confirmed=True)
    position.protective_stop = first.new_stop
    second = controller.evaluate(position, price=103.0, atr=2.0, equity=100.0, same_direction_confirmed=True)
    assert second.new_stop >= first.new_stop


def test_trailing_only_never_adds() -> None:
    controller = PyramidingControllerV4(PyramidingV4Config(mode="v4_c_trailing_only"))
    decision = controller.evaluate(long_position(), price=110.0, atr=1.0, equity=100.0, same_direction_confirmed=True)
    assert decision.add_notional == 0
    assert decision.add_index is None


def test_apply_add_rejects_loss_fill() -> None:
    controller = PyramidingControllerV4()
    position = long_position()
    decision = controller.evaluate(position, price=102.0, atr=1.0, equity=100.0, same_direction_confirmed=True)
    with pytest.raises(ValueError):
        controller.apply_add(position, decision, fill_price=99.0)


def adaptive_inputs(**overrides: object) -> AdaptivePyramidInputs:
    values = dict(
        equity=100.0, price=110.0, protective_stop=102.0,
        current_quantity=1.0, average_entry=100.0, side=1,
        win_probability=0.55, payoff_ratio=2.0, nemt_quality=0.8,
        previous_nemt_quality=0.7, regime_confidence=0.8,
        drawdown_fraction=0.02, same_direction_confirmed=True,
    )
    values.update(overrides)
    return AdaptivePyramidInputs(**values)  # type: ignore[arg-type]


def test_adaptive_size_is_positive_only_with_edge_and_risk_headroom() -> None:
    decision = adaptive_pyramid_decision(adaptive_inputs())
    assert decision.add_notional > 0
    assert decision.expected_edge > 0
    assert decision.locked_profit == 2.0


def test_adaptive_size_rejects_deteriorating_nemt() -> None:
    decision = adaptive_pyramid_decision(
        adaptive_inputs(nemt_quality=0.65, previous_nemt_quality=0.8)
    )
    assert decision.add_notional == 0
    assert decision.reason == "nemt_quality_deteriorating"


def test_adaptive_size_shuts_down_at_drawdown_limit() -> None:
    decision = adaptive_pyramid_decision(adaptive_inputs(drawdown_fraction=0.2))
    assert decision.add_notional == 0
    assert decision.reason == "drawdown_shutdown"


def test_more_locked_profit_releases_more_risk_budget() -> None:
    low = adaptive_pyramid_decision(adaptive_inputs(protective_stop=100.5))
    high = adaptive_pyramid_decision(adaptive_inputs(protective_stop=104.0))
    assert high.remaining_risk_budget > low.remaining_risk_budget


def test_fractional_kelly_and_notional_cap_bound_addition() -> None:
    config = AdaptivePyramidingConfig(max_total_notional_to_equity=1.5)
    decision = adaptive_pyramid_decision(adaptive_inputs(current_quantity=1.3), config)
    assert decision.add_notional <= 7.0 + 1e-9


def test_v42_refuses_pyramiding_without_robust_trade_history() -> None:
    decision = adaptive_pyramid_decision_v42(adaptive_inputs(), [100.0])
    assert decision.pyramid.add_notional == 0
    assert decision.expectancy.reason == "insufficient_observations"


def test_v42_allows_low_win_rate_when_robust_expectancy_is_positive() -> None:
    history = [-1.0] * 90 + [100.0] * 10
    decision = adaptive_pyramid_decision_v42(adaptive_inputs(), history)
    assert decision.expectancy.eligible is True
    assert decision.pyramid.add_notional > 0
