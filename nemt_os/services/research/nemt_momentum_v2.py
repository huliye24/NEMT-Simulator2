"""NEMT momentum strategy v2: causal signal state plus position intent.

The v2 upgrade is intentionally conservative.  It keeps the measured psi and
entropy equations intact, removes the lagging annual-trend hard gate, and
turns repeated directional phases into HOLD semantics for one position.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Literal, Optional, Sequence

from .trend_regime import TrendRegime

Phase = Literal["stable", "critical", "critical_up", "critical_down", "decay"]


@dataclass(frozen=True)
class MomentumV2Config:
    window: int = 120
    critical_entropy: float = 0.7
    critical_psi: float = 0.5
    low_entropy: float = 0.15
    stable_psi: float = 0.3
    ema_alpha: float = 0.3
    base_leverage: int = 3
    strong_leverage: int = 5
    strong_score: int = 85
    aligned_risk_scale: float = 1.0
    neutral_risk_scale: float = 0.75
    countertrend_risk_scale: float = 0.5


@dataclass(frozen=True)
class MomentumState:
    psi: float
    entropy: float
    phase: Phase
    score: int


@dataclass(frozen=True)
class PositionIntent:
    target: int
    action: Literal["OPEN", "HOLD", "CLOSE", "REVERSE", "FLAT"]
    leverage: int
    risk_scale: float
    state: MomentumState


def _entropy(values: Sequence[float]) -> float:
    low, high = min(values), max(values)
    if high <= low:
        return 0.0
    bins = max(2, min(10, len(values) // 5))
    counts = [0] * bins
    width = (high - low) / bins
    for value in values:
        counts[min(int((value - low) / width), bins - 1)] += 1
    total = len(values)
    return -sum((n / total) * math.log2(n / total) for n in counts if n) / math.log2(bins)


def compute_momentum_state(
    closes: Sequence[float], config: MomentumV2Config = MomentumV2Config()
) -> MomentumState:
    """Compute the unchanged repository psi/entropy state from trailing data."""

    if len(closes) < 5:
        raise ValueError("at least five closes are required")
    window = list(closes[-config.window:])
    returns = [(window[i] - window[i - 1]) / window[i - 1] for i in range(1, len(window))]
    ema = returns[0]
    for value in returns[1:]:
        ema = config.ema_alpha * value + (1.0 - config.ema_alpha) * ema
    psi = ema * 100.0
    entropy = _entropy(window)
    if entropy > config.critical_entropy:
        phase: Phase = "critical_up" if psi > config.critical_psi else (
            "critical_down" if psi < -config.critical_psi else "critical"
        )
    elif entropy < config.low_entropy and abs(psi) <= config.stable_psi:
        phase = "decay"
    else:
        phase = "stable"
    score = round(min(1.0, 0.6 * abs(psi) / config.critical_psi + 0.4 * entropy / config.critical_entropy) * 100)
    return MomentumState(psi, entropy, phase, score)


def _risk_scale(target: int, regime: TrendRegime, config: MomentumV2Config) -> float:
    if regime in ("unknown", "neutral"):
        return config.neutral_risk_scale
    aligned = (regime == "bull" and target == 1) or (regime == "bear" and target == -1)
    return config.aligned_risk_scale if aligned else config.countertrend_risk_scale


def next_intent(
    state: MomentumState,
    current_target: int,
    annual_regime: TrendRegime = "unknown",
    config: MomentumV2Config = MomentumV2Config(),
) -> PositionIntent:
    """Convert state into a one-position intent without duplicate entries."""

    signal = 1 if state.phase == "critical_up" else -1 if state.phase == "critical_down" else None
    if state.phase == "decay":
        target = 0
    elif signal is not None:
        target = signal
    else:
        target = current_target
    if target == current_target:
        action = "HOLD" if target else "FLAT"
    elif target == 0:
        action = "CLOSE"
    elif current_target == 0:
        action = "OPEN"
    else:
        action = "REVERSE"
    leverage = config.strong_leverage if state.score >= config.strong_score else config.base_leverage
    scale = _risk_scale(target, annual_regime, config) if target else 0.0
    return PositionIntent(target, action, leverage, scale, state)


def generate_targets(
    closes: Sequence[float],
    regimes: Optional[Sequence[TrendRegime]] = None,
    config: MomentumV2Config = MomentumV2Config(),
) -> List[PositionIntent]:
    """Generate causal persistent position intents for a complete series."""

    if regimes is not None and len(regimes) != len(closes):
        raise ValueError("regimes and closes must have equal length")
    out: List[PositionIntent] = []
    target = 0
    for index in range(len(closes)):
        if index + 1 < 5:
            state = MomentumState(0.0, 0.0, "stable", 0)
        else:
            state = compute_momentum_state(closes[: index + 1], config)
        regime = regimes[index] if regimes is not None else "unknown"
        intent = next_intent(state, target, regime, config)
        target = intent.target
        out.append(intent)
    return out
