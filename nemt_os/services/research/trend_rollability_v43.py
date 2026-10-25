"""Bayesian similarity-weighted permission layer for NEMT v4.3 pyramiding."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RollabilityObservation:
    features: tuple[float, ...]
    success: bool
    outcome_r: float


@dataclass(frozen=True)
class RollabilityConfig:
    bandwidth: float = 0.35
    minimum_effective_samples: float = 20.0
    confidence_z: float = 1.645
    minimum_probability_lower: float = 0.45
    minimum_marginal_expectancy_r: float = 0.05


@dataclass(frozen=True)
class RollabilityDecision:
    permitted: bool
    effective_samples: float
    probability_mean: float
    probability_lower: float
    expected_gain_r: float
    expected_loss_r: float
    marginal_expectancy_r: float
    reason: str


def assess_rollability(
    current_features: Sequence[float],
    observations: Sequence[RollabilityObservation],
    config: RollabilityConfig = RollabilityConfig(),
) -> RollabilityDecision:
    """Estimate whether a similar trend historically rewarded added risk."""

    if config.bandwidth <= 0:
        raise ValueError("bandwidth must be positive")
    current = tuple(float(value) for value in current_features)
    if any(not math.isfinite(value) for value in current):
        raise ValueError("features must be finite")
    weighted = []
    for observation in observations:
        if len(observation.features) != len(current):
            raise ValueError("feature dimensions must match")
        distance2 = sum((a - b) ** 2 for a, b in zip(current, observation.features))
        weight = math.exp(-distance2 / (2 * config.bandwidth ** 2))
        weighted.append((weight, observation))
    effective = sum(weight for weight, _ in weighted)
    alpha = 1.0 + sum(weight for weight, item in weighted if item.success)
    beta = 1.0 + sum(weight for weight, item in weighted if not item.success)
    mean = alpha / (alpha + beta)
    variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1))
    lower = max(0.0, mean - config.confidence_z * math.sqrt(variance))
    gain_weight = sum(weight for weight, item in weighted if item.success)
    loss_weight = sum(weight for weight, item in weighted if not item.success)
    gain = (2.0 + sum(weight * max(item.outcome_r, 0.0) for weight, item in weighted if item.success)) / (1.0 + gain_weight)
    loss = (1.0 + sum(weight * abs(min(item.outcome_r, 0.0)) for weight, item in weighted if not item.success)) / (1.0 + loss_weight)
    expectancy = lower * gain - (1.0 - lower) * loss
    if effective < config.minimum_effective_samples:
        reason = "insufficient_similar_history"
    elif lower < config.minimum_probability_lower:
        reason = "continuation_probability_too_low"
    elif expectancy < config.minimum_marginal_expectancy_r:
        reason = "negative_marginal_expectancy"
    else:
        reason = "permitted"
    return RollabilityDecision(reason == "permitted", effective, mean, lower, gain, loss, expectancy, reason)
