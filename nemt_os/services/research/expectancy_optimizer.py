"""Robust expectancy and log-growth optimizer for asymmetric trend systems."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ExpectancyOptimizerConfig:
    prior_wins: float = 1.0
    prior_losses: float = 1.0
    prior_win_r: float = 2.0
    prior_loss_r: float = 1.0
    payoff_prior_strength: float = 5.0
    confidence_z: float = 1.645
    tail_fraction: float = 0.10
    maximum_risk_fraction: float = 0.02
    maximum_cvar_fraction: float = 0.03
    maximum_allocation_fraction: float = 0.50
    grid_steps: int = 500
    minimum_observations: int = 20


@dataclass(frozen=True)
class ExpectancyEstimate:
    observations: int
    posterior_win_probability: float
    conservative_win_probability: float
    shrunk_average_win_r: float
    conservative_average_loss_r: float
    payoff_ratio: float
    robust_expectancy_r: float
    loss_cvar_r: float
    optimal_allocation_fraction: float
    expected_log_growth: float
    eligible: bool
    reason: str


def optimize_expectancy(
    trade_returns_r: Sequence[float],
    *,
    current_drawdown: float = 0.0,
    drawdown_limit: float = 0.20,
    config: ExpectancyOptimizerConfig = ExpectancyOptimizerConfig(),
) -> ExpectancyEstimate:
    """Estimate conservative edge and maximize constrained expected log growth.

    Inputs are completed-trade returns measured in initial-risk units (R).
    No current or future trade outcome may be included.
    """

    if not 0 <= current_drawdown <= 1 or not 0 < drawdown_limit <= 1:
        raise ValueError("drawdown values must be valid fractions")
    values = [float(value) for value in trade_returns_r]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("trade returns must be finite")
    wins = [value for value in values if value > 0]
    losses = [-value for value in values if value <= 0]
    alpha = config.prior_wins + len(wins)
    beta = config.prior_losses + len(losses)
    posterior_p = alpha / (alpha + beta)
    variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1))
    conservative_p = max(0.0, posterior_p - config.confidence_z * math.sqrt(variance))

    strength = config.payoff_prior_strength
    average_win = (sum(wins) + strength * config.prior_win_r) / (len(wins) + strength)
    average_loss = (sum(losses) + strength * config.prior_loss_r) / (len(losses) + strength)
    conservative_loss = average_loss * (1.0 + config.confidence_z / math.sqrt(len(losses) + strength))
    payoff = average_win / conservative_loss if conservative_loss > 0 else 0.0
    expectancy = conservative_p * average_win - (1.0 - conservative_p) * conservative_loss

    sorted_losses = sorted(losses or [config.prior_loss_r], reverse=True)
    tail_count = max(1, math.ceil(len(sorted_losses) * config.tail_fraction))
    loss_cvar = sum(sorted_losses[:tail_count]) / tail_count
    drawdown_scale = max(0.0, 1.0 - current_drawdown / drawdown_limit)
    allocation_cap = config.maximum_allocation_fraction * drawdown_scale
    best_fraction, best_growth = 0.0, 0.0
    if len(values) >= config.minimum_observations and expectancy > 0 and allocation_cap > 0:
        for step in range(1, config.grid_steps + 1):
            fraction = allocation_cap * step / config.grid_steps
            if fraction * conservative_loss > config.maximum_risk_fraction:
                break
            if fraction * loss_cvar > config.maximum_cvar_fraction:
                break
            if fraction * conservative_loss >= 1.0:
                break
            growth = (
                conservative_p * math.log1p(fraction * average_win)
                + (1.0 - conservative_p) * math.log1p(-fraction * conservative_loss)
            )
            if growth > best_growth:
                best_fraction, best_growth = fraction, growth

    eligible = best_fraction > 0
    if len(values) < config.minimum_observations:
        reason = "insufficient_observations"
    elif expectancy <= 0:
        reason = "non_positive_robust_expectancy"
    elif allocation_cap <= 0:
        reason = "drawdown_shutdown"
    elif not eligible:
        reason = "risk_or_cvar_constraint"
    else:
        reason = "eligible"
    return ExpectancyEstimate(
        len(values), posterior_p, conservative_p, average_win, conservative_loss,
        payoff, expectancy, loss_cvar, best_fraction, best_growth, eligible, reason,
    )
