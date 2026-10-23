"""NEMT signal engine (相位 / 动量) for live klines.

Formulas are the ones already used by this repository in
``src/web/strategy/nemt/nemtCalculator.ts`` so the server and the old dashboard
agree on the numbers:

    returns_i = (close_i - close_{i-1}) / close_{i-1}
    ψ  psi    = EMA(returns, α=0.3) × 100                  (percent per bar)
    φ  phi    = stdev(returns) × sqrt(24×365) × 100        (annualised vol, %)
    S  entropy= H(price histogram) / log2(bins), bins = min(10, n // 5)

Phase rules (criticalEntropy=0.7, criticalPsi=0.5, stablePsi=0.3):

    S > 0.7 and ψ >  0.5 -> critical_up    -> LONG
    S > 0.7 and ψ < -0.5 -> critical_down  -> SHORT
    S > 0.7 otherwise    -> critical       -> WAIT (方向不明)
    S < 0.15 and |ψ| > 0.3 -> stable       -> no new entry
    S < 0.15 otherwise     -> decay        -> EXIT (相位衰竭)
    otherwise              -> stable       -> no new entry

Only public klines are read here. Nothing in this module trades.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Iterable, Literal, Sequence

from .config import Settings
from .errors import ApiException
from .market import Kline, MarketService

Phase = Literal["stable", "critical", "critical_up", "critical_down", "decay"]
Direction = Literal["LONG", "SHORT", "WAIT", "EXIT", "HOLD"]

PHASE_LABELS: dict[str, str] = {
    "stable": "稳定期",
    "critical": "临界·方向不明",
    "critical_up": "临界上涨",
    "critical_down": "临界下跌",
    "decay": "衰减期",
}

PHASE_MEANING: dict[str, str] = {
    "stable": "波动收敛、动量不足，不开新仓",
    "critical": "熵已经拉高但 ψ 不够，方向不明，等待",
    "critical_up": "高熵 + 正动量，临界突破向上",
    "critical_down": "高熵 + 负动量，临界突破向下",
    "decay": "低熵且动量消失，趋势已经衰竭，离场",
}

TRADING_DAYS_PER_YEAR = 365
HOURS_PER_DAY = 24


@dataclass(frozen=True)
class NemtConfig:
    critical_entropy: float = 0.7
    critical_psi: float = 0.5
    stable_psi: float = 0.3
    ema_alpha: float = 0.3
    low_entropy: float = 0.15
    atr_period: int = 14
    bars: int = 120

    @classmethod
    def from_settings(cls, settings: Settings) -> "NemtConfig":
        return cls(
            critical_entropy=float(settings.nemt_critical_entropy),
            critical_psi=float(settings.nemt_critical_psi),
            stable_psi=float(settings.nemt_stable_psi),
            ema_alpha=float(settings.nemt_ema_alpha),
            low_entropy=float(settings.nemt_low_entropy),
            atr_period=int(settings.nemt_atr_period),
            bars=int(settings.nemt_bars),
        )


@dataclass(frozen=True)
class NemtState:
    psi: float
    phi: float
    entropy: float
    phase: Phase
    wave_amplitude: float
    wave_frequency: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "psi": round(self.psi, 6),
            "phi": round(self.phi, 4),
            "entropy": round(self.entropy, 6),
            "phase": self.phase,
            "phase_label": PHASE_LABELS[self.phase],
            "wave_amplitude": round(self.wave_amplitude, 6),
            "wave_frequency": round(self.wave_frequency, 6),
        }


def _returns(closes: Sequence[float]) -> list[float]:
    return [
        (closes[index] - closes[index - 1]) / closes[index - 1]
        for index in range(1, len(closes))
        if closes[index - 1] != 0
    ]


def ema(values: Sequence[float], alpha: float) -> float:
    if not values:
        return 0.0
    current = values[0]
    for value in values[1:]:
        current = alpha * value + (1 - alpha) * current
    return current


def stdev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(max(0.0, variance))


def price_entropy(closes: Sequence[float]) -> float:
    """Normalised Shannon entropy of the price histogram, in [0, 1]."""

    if len(closes) < 5:
        return 0.5
    low = min(closes)
    high = max(closes)
    span = high - low
    if span <= 0:
        return 0.0
    bins = max(2, min(10, len(closes) // 5))
    width = span / bins
    counts = [0] * bins
    for price in closes:
        index = min(int((price - low) / width), bins - 1)
        counts[index] += 1
    total = len(closes)
    entropy = 0.0
    for count in counts:
        if count:
            probability = count / total
            entropy -= probability * math.log2(probability)
    max_entropy = math.log2(bins)
    return entropy / max_entropy if max_entropy > 0 else 0.0


def determine_phase(psi: float, entropy: float, config: NemtConfig) -> Phase:
    if entropy > config.critical_entropy:
        if psi > config.critical_psi:
            return "critical_up"
        if psi < -config.critical_psi:
            return "critical_down"
        return "critical"
    if entropy < config.low_entropy:
        if abs(psi) > config.stable_psi:
            return "stable"
        return "decay"
    return "stable"


def wave_shape(closes: Sequence[float]) -> tuple[float, float]:
    """Amplitude relative to the mean, and sign-change frequency."""

    if len(closes) < 2:
        return 0.0, 0.0
    mean = sum(closes) / len(closes)
    if mean <= 0:
        return 0.0, 0.0
    amplitude = (max(closes) - min(closes)) / mean
    centred = [price - mean for price in closes]
    crossings = sum(
        1
        for index in range(1, len(centred))
        if (centred[index] >= 0) != (centred[index - 1] >= 0)
    )
    return amplitude, crossings / len(centred)


def compute_state(closes: Sequence[float], config: NemtConfig) -> NemtState:
    if len(closes) < 5:
        raise ApiException(422, "nemt_not_enough_data", "K 线数量不足以计算 NEMT 状态")
    returns = _returns(closes)
    psi = ema(returns, config.ema_alpha) * 100
    phi = (
        stdev(returns) * math.sqrt(HOURS_PER_DAY * TRADING_DAYS_PER_YEAR) * 100
        if returns
        else 0.0
    )
    entropy = price_entropy(closes)
    amplitude, frequency = wave_shape(closes)
    return NemtState(
        psi=psi,
        phi=phi,
        entropy=entropy,
        phase=determine_phase(psi, entropy, config),
        wave_amplitude=amplitude,
        wave_frequency=frequency,
    )


def atr(klines: Sequence[Kline], period: int = 14) -> float:
    """Average true range in quote currency; 0 when there is not enough data."""

    if len(klines) < 2:
        return 0.0
    window = list(klines)[-(period + 1) :]
    ranges: list[float] = []
    for index in range(1, len(window)):
        high = float(window[index].high)
        low = float(window[index].low)
        previous_close = float(window[index - 1].close)
        ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    if not ranges:
        return 0.0
    return sum(ranges) / len(ranges)


def strength(psi: float, entropy: float, config: NemtConfig) -> int:
    """0-100 confidence for the UI. Momentum carries more weight than entropy."""

    momentum = min(1.0, abs(psi) / max(config.critical_psi, 1e-9))
    spread = min(1.0, entropy / max(config.critical_entropy, 1e-9))
    score = 0.6 * momentum + 0.4 * spread
    return int(round(max(0.0, min(1.0, score)) * 100))


@dataclass
class SignalCard:
    symbol: str
    interval: str
    mark_price: Decimal
    state: NemtState
    direction: Direction
    strength: int
    reasons: list[str] = field(default_factory=list)
    entry: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    stop_pct: float = 0.0
    risk_usdt: Decimal | None = None
    suggested_notional: Decimal | None = None
    suggested_leverage: int = 1
    action_label: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "mark_price": self.mark_price,
            "direction": self.direction,
            "strength": self.strength,
            "action_label": self.action_label,
            "reasons": self.reasons,
            "entry": self.entry,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "stop_pct": round(self.stop_pct, 6),
            "risk_usdt": self.risk_usdt,
            "suggested_notional": self.suggested_notional,
            "suggested_leverage": self.suggested_leverage,
            **self.state.as_dict(),
        }


ACTION_LABELS: dict[str, str] = {
    "LONG": "可以做多",
    "SHORT": "可以做空",
    "WAIT": "等待",
    "EXIT": "离场",
    "HOLD": "不操作",
}


class NemtSignalService:
    """Turns klines into an actionable card. Read-only, no order routing."""

    def __init__(self, settings: Settings, market: MarketService):
        self.settings = settings
        self.market = market
        self.config = NemtConfig.from_settings(settings)

    async def card(
        self,
        symbol: str,
        interval: str = "15m",
        *,
        equity: Decimal | None = None,
    ) -> SignalCard:
        symbol = symbol.strip().upper()
        try:
            series = await self.market.klines(symbol, interval, self.config.bars)
        except Exception as exc:  # noqa: BLE001
            raise ApiException(503, "market_unavailable", f"{symbol} 行情不可用") from exc
        if not series.items:
            raise ApiException(503, "market_unavailable", f"{symbol} 没有可用 K 线")

        closes = [float(item.close) for item in series.items]
        state = compute_state(closes, self.config)
        mark = series.items[-1].close
        score = strength(state.psi, state.entropy, self.config)

        direction: Direction
        reasons: list[str] = []
        if state.phase == "critical_up":
            direction = "LONG"
            reasons.append(
                f"熵 {state.entropy:.2f} 高于临界值 {self.config.critical_entropy}，"
                f"动量 ψ={state.psi:+.3f}% 为正"
            )
        elif state.phase == "critical_down":
            direction = "SHORT"
            reasons.append(
                f"熵 {state.entropy:.2f} 高于临界值 {self.config.critical_entropy}，"
                f"动量 ψ={state.psi:+.3f}% 为负"
            )
        elif state.phase == "critical":
            direction = "WAIT"
            reasons.append(
                f"熵 {state.entropy:.2f} 已进入临界区，但 |ψ|={abs(state.psi):.3f}% "
                f"不足 {self.config.critical_psi}%，方向未定"
            )
        elif state.phase == "decay":
            direction = "EXIT"
            reasons.append(
                f"熵 {state.entropy:.2f} 很低且 |ψ|={abs(state.psi):.3f}% "
                f"低于 {self.config.stable_psi}%，趋势已衰竭"
            )
        else:
            direction = "HOLD"
            reasons.append(
                f"熵 {state.entropy:.2f} 不在临界区（>{self.config.critical_entropy}），"
                "NEMT 不给出新仓信号"
            )

        card = SignalCard(
            symbol=symbol,
            interval=interval,
            mark_price=mark,
            state=state,
            direction=direction,
            strength=score,
            reasons=reasons,
            action_label=ACTION_LABELS[direction],
        )

        if direction in ("LONG", "SHORT"):
            atr_value = atr(series.items, self.config.atr_period)
            price = float(mark)
            stop_pct = (atr_value * 1.5 / price) if price > 0 else 0.02
            stop_pct = max(0.01, min(0.05, stop_pct or 0.02))
            sign = 1 if direction == "LONG" else -1
            stop = price * (1 - sign * stop_pct)
            target = price * (1 + sign * stop_pct * 2)
            card.stop_pct = stop_pct
            card.entry = mark
            card.stop_loss = Decimal(f"{stop:.8f}")
            card.take_profit = Decimal(f"{target:.8f}")

            base_equity = equity if equity is not None else self.settings.paper_initial_equity
            risk_rate = Decimal(str(self.settings.nemt_risk_per_trade_pct)) / Decimal("100")
            risk_usdt = (base_equity * risk_rate).quantize(Decimal("0.00000001"))
            notional = (risk_usdt / Decimal(str(stop_pct))).quantize(Decimal("0.01"))

            # Risk sizing can ask for more notional than the account can carry.
            # 95% of equity is spendable so the taker fee always fits, and the
            # leverage is what makes the rest affordable.
            usable = (base_equity * Decimal("0.95")).quantize(Decimal("0.01"))
            max_leverage = int(self.settings.paper_max_leverage)
            leverage = max(
                1, min(max_leverage, int(math.ceil(float(notional) / max(float(usable), 1e-9))))
            )
            ceiling = (usable * leverage).quantize(Decimal("0.01"))
            if notional > ceiling:
                notional = ceiling
                reasons.append(
                    f"按风险算出的仓位 {risk_usdt}/{stop_pct:.2%} 超过账户承受能力，已压到 {ceiling} USDT"
                )

            minimum = self.settings.paper_min_notional
            if notional < minimum:
                notional = minimum
                reasons.append(
                    f"按 {risk_rate * 100:.1f}% 风险算出的仓位小于最小下单额，已抬到 {minimum} USDT"
                )
            card.risk_usdt = risk_usdt
            card.suggested_notional = notional
            card.suggested_leverage = leverage
            reasons.append(
                f"止损 {stop_pct * 100:.2f}%（1.5×ATR），盈亏比 1:2，"
                f"风险 {risk_usdt} USDT ≈ 权益的 {risk_rate * 100:.1f}%"
            )
        else:
            reasons.append(f"相位结论：{PHASE_MEANING[state.phase]}")

        return card

    async def board(
        self,
        symbols: Iterable[str],
        interval: str = "15m",
        *,
        equity: Decimal | None = None,
    ) -> list[SignalCard]:
        cards: list[SignalCard] = []
        for symbol in symbols:
            try:
                cards.append(await self.card(symbol, interval, equity=equity))
            except ApiException:
                continue
        return cards
