"""Risk-budgeted NEMT v4 pyramiding and trailing-stop execution layer.

The module never generates entry direction.  It operates only after the NEMT
signal layer and v3 position controller have opened a position.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from .expectancy_optimizer import ExpectancyEstimate, optimize_expectancy

PyramidMode = Literal["v4_a_breakeven", "v4_b_atr_trailing", "v4_c_trailing_only"]


@dataclass(frozen=True)
class PyramidingV4Config:
    mode: PyramidMode = "v4_a_breakeven"
    add_at_r: tuple[float, float] = (1.0, 2.0)
    add_size_fractions: tuple[float, float] = (0.5, 0.25)
    break_even_buffer_bps: float = 15.0
    atr_trailing_multiple: float = 2.0
    max_total_notional_to_equity: float = 3.0

    def __post_init__(self) -> None:
        if len(self.add_at_r) != len(self.add_size_fractions):
            raise ValueError("add thresholds and size fractions must align")
        if any(value <= 0 for value in self.add_at_r):
            raise ValueError("add thresholds must be positive")
        if tuple(sorted(self.add_at_r)) != self.add_at_r:
            raise ValueError("add thresholds must be increasing")
        if any(not 0 < value < 1 for value in self.add_size_fractions):
            raise ValueError("add sizes must be fractions in (0, 1)")
        if any(a <= b for a, b in zip(self.add_size_fractions, self.add_size_fractions[1:])):
            raise ValueError("each pyramid addition must be smaller than the previous")
        if self.atr_trailing_multiple <= 0:
            raise ValueError("ATR trailing multiple must be positive")
        if self.max_total_notional_to_equity <= 0:
            raise ValueError("notional cap must be positive")


@dataclass
class PyramidPosition:
    side: int
    initial_entry: float
    initial_stop: float
    initial_notional: float
    total_quantity: float
    total_cost: float
    protective_stop: float
    add_count: int = 0
    best_price: Optional[float] = None

    @property
    def average_entry(self) -> float:
        return self.total_cost / self.total_quantity

    @property
    def initial_risk_distance(self) -> float:
        return abs(self.initial_entry - self.initial_stop)


@dataclass(frozen=True)
class PyramidDecision:
    add_notional: float
    new_stop: float
    add_index: Optional[int]
    reason: str


class PyramidingControllerV4:
    """Plan decreasing additions while enforcing monotonic protection."""

    def __init__(self, config: PyramidingV4Config = PyramidingV4Config()) -> None:
        self.config = config

    def evaluate(
        self,
        position: PyramidPosition,
        *,
        price: float,
        atr: float,
        equity: float,
        same_direction_confirmed: bool,
    ) -> PyramidDecision:
        if position.side not in (-1, 1):
            raise ValueError("side must be -1 or 1")
        if min(price, atr, equity, position.initial_entry, position.initial_stop) <= 0:
            raise ValueError("prices, ATR and equity must be positive")

        favorable = (price - position.initial_entry) * position.side
        r_multiple = favorable / position.initial_risk_distance
        best = position.best_price if position.best_price is not None else position.initial_entry
        best = max(best, price) if position.side == 1 else min(best, price)
        position.best_price = best

        add_notional = 0.0
        add_index: Optional[int] = None
        can_add = (
            self.config.mode != "v4_c_trailing_only"
            and same_direction_confirmed
            and favorable > 0
            and position.add_count < len(self.config.add_at_r)
            and r_multiple >= self.config.add_at_r[position.add_count]
        )
        if can_add:
            requested = position.initial_notional * self.config.add_size_fractions[position.add_count]
            current_notional = position.total_quantity * price
            cap = equity * self.config.max_total_notional_to_equity
            add_notional = max(0.0, min(requested, cap - current_notional))
            if add_notional > 0:
                add_index = position.add_count

        old_stop = position.protective_stop
        if self.config.mode == "v4_a_breakeven" and add_index is not None:
            buffer = position.average_entry * self.config.break_even_buffer_bps / 10_000.0
            candidate = position.average_entry + position.side * buffer
        else:
            candidate = best - position.side * self.config.atr_trailing_multiple * atr
        new_stop = max(old_stop, candidate) if position.side == 1 else min(old_stop, candidate)

        reason = "hold"
        if add_index is not None:
            reason = f"add_{add_index + 1}"
        elif new_stop != old_stop:
            reason = "tighten_stop"
        return PyramidDecision(add_notional, new_stop, add_index, reason)

    def apply_add(
        self,
        position: PyramidPosition,
        decision: PyramidDecision,
        *,
        fill_price: float,
    ) -> None:
        """Apply a previously approved addition; never accepts zero/loss adds."""

        if decision.add_index is None or decision.add_notional <= 0:
            raise ValueError("decision does not contain an addition")
        if (fill_price - position.initial_entry) * position.side <= 0:
            raise ValueError("pyramiding into a losing position is forbidden")
        quantity = decision.add_notional / fill_price
        position.total_quantity += quantity
        position.total_cost += decision.add_notional
        position.add_count += 1
        position.protective_stop = decision.new_stop


@dataclass(frozen=True)
class AdaptivePyramidingConfig:
    """Constraints for risk-budgeted fractional-Kelly pyramiding."""

    trade_risk_budget: float = 0.02
    kelly_fraction: float = 0.20
    max_total_notional_to_equity: float = 3.0
    minimum_nemt_quality: float = 0.60
    drawdown_shutdown: float = 0.20
    minimum_add_notional: float = 5.0
    cost_buffer_bps: float = 15.0

    def __post_init__(self) -> None:
        if not 0 < self.trade_risk_budget <= 0.1:
            raise ValueError("trade_risk_budget must be in (0, 0.1]")
        if not 0 < self.kelly_fraction <= 0.5:
            raise ValueError("kelly_fraction must be in (0, 0.5]")
        if not 0 <= self.minimum_nemt_quality <= 1:
            raise ValueError("minimum_nemt_quality must be in [0, 1]")
        if not 0 < self.drawdown_shutdown <= 1:
            raise ValueError("drawdown_shutdown must be in (0, 1]")


@dataclass(frozen=True)
class AdaptivePyramidInputs:
    equity: float
    price: float
    protective_stop: float
    current_quantity: float
    average_entry: float
    side: int
    win_probability: float
    payoff_ratio: float
    nemt_quality: float
    previous_nemt_quality: float
    regime_confidence: float
    drawdown_fraction: float
    same_direction_confirmed: bool


@dataclass(frozen=True)
class AdaptivePyramidDecision:
    add_notional: float
    remaining_risk_budget: float
    locked_profit: float
    open_stop_risk: float
    raw_kelly: float
    adjusted_kelly: float
    expected_edge: float
    reason: str


@dataclass(frozen=True)
class AdaptiveV42Decision:
    pyramid: AdaptivePyramidDecision
    expectancy: ExpectancyEstimate


def adaptive_pyramid_decision(
    inputs: AdaptivePyramidInputs,
    config: AdaptivePyramidingConfig = AdaptivePyramidingConfig(),
) -> AdaptivePyramidDecision:
    """Calculate marginal notional from risk headroom and fractional Kelly.

    The annual regime is not a direction gate. ``regime_confidence`` only
    shrinks uncertain sizing and must be an independently calibrated [0, 1]
    confidence value.
    """

    if inputs.side not in (-1, 1):
        raise ValueError("side must be -1 or 1")
    if inputs.equity <= 0 or min(inputs.price, inputs.protective_stop, inputs.average_entry) <= 0:
        raise ValueError("equity and prices must be positive")
    if inputs.current_quantity < 0 or inputs.payoff_ratio <= 0:
        raise ValueError("quantity must be non-negative and payoff positive")
    for name, value in (
        ("win_probability", inputs.win_probability),
        ("nemt_quality", inputs.nemt_quality),
        ("previous_nemt_quality", inputs.previous_nemt_quality),
        ("regime_confidence", inputs.regime_confidence),
        ("drawdown_fraction", inputs.drawdown_fraction),
    ):
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be in [0, 1]")

    p, payoff = inputs.win_probability, inputs.payoff_ratio
    edge = p * payoff - (1 - p)
    raw_kelly = max(0.0, edge / payoff)
    locked_per_unit = max(0.0, (inputs.protective_stop - inputs.average_entry) * inputs.side)
    locked_profit = locked_per_unit * inputs.current_quantity
    loss_per_unit = max(0.0, (inputs.average_entry - inputs.protective_stop) * inputs.side)
    open_stop_risk = loss_per_unit * inputs.current_quantity
    total_budget = inputs.equity * config.trade_risk_budget + locked_profit
    remaining = max(0.0, total_budget - open_stop_risk)

    if not inputs.same_direction_confirmed:
        reason = "nemt_direction_not_confirmed"
    elif inputs.nemt_quality < config.minimum_nemt_quality:
        reason = "nemt_quality_too_low"
    elif inputs.nemt_quality < inputs.previous_nemt_quality:
        reason = "nemt_quality_deteriorating"
    elif edge <= 0:
        reason = "non_positive_expected_edge"
    elif inputs.drawdown_fraction >= config.drawdown_shutdown:
        reason = "drawdown_shutdown"
    elif remaining <= 0:
        reason = "no_remaining_risk_budget"
    else:
        reason = "eligible"

    drawdown_scale = max(0.0, 1.0 - inputs.drawdown_fraction / config.drawdown_shutdown)
    adjusted_kelly = (
        raw_kelly
        * config.kelly_fraction
        * inputs.nemt_quality
        * inputs.regime_confidence
        * drawdown_scale
    )
    cost_per_unit = inputs.price * config.cost_buffer_bps / 10_000.0
    stop_distance = abs(inputs.price - inputs.protective_stop) + cost_per_unit
    risk_cap = remaining / stop_distance * inputs.price if stop_distance > 0 else 0.0
    kelly_cap = inputs.equity * config.max_total_notional_to_equity * adjusted_kelly
    current_notional = inputs.current_quantity * inputs.price
    margin_cap = max(0.0, inputs.equity * config.max_total_notional_to_equity - current_notional)
    add_notional = min(risk_cap, kelly_cap, margin_cap) if reason == "eligible" else 0.0
    if 0 < add_notional < config.minimum_add_notional:
        add_notional, reason = 0.0, "below_minimum_add_notional"
    return AdaptivePyramidDecision(
        add_notional=add_notional,
        remaining_risk_budget=remaining,
        locked_profit=locked_profit,
        open_stop_risk=open_stop_risk,
        raw_kelly=raw_kelly,
        adjusted_kelly=adjusted_kelly,
        expected_edge=edge,
        reason=reason,
    )


def adaptive_pyramid_decision_v42(
    inputs: AdaptivePyramidInputs,
    completed_trade_returns_r: list[float],
    config: AdaptivePyramidingConfig = AdaptivePyramidingConfig(),
) -> AdaptiveV42Decision:
    """Cap marginal pyramiding with robust Bayesian log-growth allocation."""

    base = adaptive_pyramid_decision(inputs, config)
    expectancy = optimize_expectancy(
        completed_trade_returns_r,
        current_drawdown=inputs.drawdown_fraction,
    )
    if base.add_notional <= 0:
        return AdaptiveV42Decision(base, expectancy)
    if not expectancy.eligible:
        return AdaptiveV42Decision(
            AdaptivePyramidDecision(
                0.0, base.remaining_risk_budget, base.locked_profit,
                base.open_stop_risk, base.raw_kelly, base.adjusted_kelly,
                base.expected_edge, f"robust_{expectancy.reason}",
            ),
            expectancy,
        )
    stop_pct = abs(inputs.price - inputs.protective_stop) / inputs.price
    robust_notional = (
        inputs.equity * expectancy.optimal_allocation_fraction / stop_pct
        if stop_pct > 0 else 0.0
    )
    capped = min(base.add_notional, robust_notional)
    reason = "eligible_v42" if capped >= config.minimum_add_notional else "below_minimum_add_notional"
    return AdaptiveV42Decision(
        AdaptivePyramidDecision(
            capped if reason == "eligible_v42" else 0.0,
            base.remaining_risk_budget, base.locked_profit,
            base.open_stop_risk, base.raw_kelly, base.adjusted_kelly,
            base.expected_edge, reason,
        ),
        expectancy,
    )
