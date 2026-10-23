"""Backtest engine for simple strategies over Binance klines.

Design goals:

* Same cost model as the paper engine (taker fee + slippage), so a backtest
  number can be compared with what the auto trader would actually do.
* One position at a time, full equity notional, no leverage. That keeps the
  comparison between strategies about *the signal*, not about sizing.
* Float maths on purpose: this is research output, not the ledger (the paper
  engine is the one that must stay Decimal-exact).

Every strategy is a function of close prices producing a *target direction* per
bar (1 long, -1 short, 0 flat); the engine rebalances at the next bar's open, so
there is no look-ahead.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Literal, Sequence

import httpx

Direction = Literal[-1, 0, 1]

BARS_PER_YEAR = {
    "5m": 12 * 24 * 365,
    "15m": 4 * 24 * 365,
    "30m": 2 * 24 * 365,
    "1h": 24 * 365,
    "4h": 6 * 365,
    "1d": 365,
}


@dataclass(frozen=True)
class Bar:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def when(self) -> str:
        return datetime.fromtimestamp(self.open_time / 1000, tz=timezone.utc).isoformat(
            timespec="minutes"
        )


@dataclass
class Trade:
    direction: int
    entry_time: int
    entry_price: float
    exit_time: int
    exit_price: float
    pnl: float
    pnl_pct: float
    bars: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "side": "LONG" if self.direction > 0 else "SHORT",
            "entry_at": datetime.fromtimestamp(self.entry_time / 1000, tz=timezone.utc).isoformat(timespec="minutes"),
            "exit_at": datetime.fromtimestamp(self.exit_time / 1000, tz=timezone.utc).isoformat(timespec="minutes"),
            "entry_price": round(self.entry_price, 6),
            "exit_price": round(self.exit_price, 6),
            "pnl": round(self.pnl, 4),
            "pnl_pct": round(self.pnl_pct, 4),
            "bars": self.bars,
        }


@dataclass
class BacktestResult:
    strategy: str
    symbol: str
    interval: str
    bars: int
    starting_equity: float
    ending_equity: float
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "symbol": self.symbol,
            "interval": self.interval,
            "bars": self.bars,
            "params": self.params,
            "starting_equity": round(self.starting_equity, 2),
            "ending_equity": round(self.ending_equity, 2),
            "metrics": self.metrics,
            "trades": [trade.as_dict() for trade in self.trades[-50:]],
            "trade_count": len(self.trades),
            "equity_curve": self.equity_curve,
        }


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


def fetch_bars(
    symbol: str, interval: str = "15m", bars: int = 1000, *, base_url: str = "https://api.binance.com"
) -> list[Bar]:
    """Page through ``/api/v3/klines`` until ``bars`` closed candles are collected."""

    wanted = max(50, min(int(bars), 3000))
    collected: list[Bar] = []
    end_time: int | None = None
    with httpx.Client(timeout=httpx.Timeout(20.0, connect=10.0)) as client:
        while len(collected) < wanted:
            params: dict[str, Any] = {
                "symbol": symbol,
                "interval": interval,
                "limit": min(1000, wanted - len(collected)),
            }
            if end_time is not None:
                params["endTime"] = end_time
            response = client.get(f"{base_url}/api/v3/klines", params=params)
            response.raise_for_status()
            payload = response.json()
            if not payload:
                break
            chunk = [
                Bar(
                    open_time=int(item[0]),
                    open=float(item[1]),
                    high=float(item[2]),
                    low=float(item[3]),
                    close=float(item[4]),
                    volume=float(item[5]),
                )
                for item in payload
            ]
            collected = chunk + collected
            end_time = int(payload[0][0]) - 1
    # drop the last candle: it is still forming
    return collected[-wanted:-1] if len(collected) > wanted else collected[:-1]


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------


def sma(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if period <= 0:
        return out
    running = 0.0
    for index, value in enumerate(values):
        running += value
        if index >= period:
            running -= values[index - period]
        if index >= period - 1:
            out[index] = running / period
    return out


def ema(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if period <= 0 or not values:
        return out
    alpha = 2 / (period + 1)
    current = values[0]
    out[0] = current
    for index in range(1, len(values)):
        current = alpha * values[index] + (1 - alpha) * current
        out[index] = current
    return out


def rsi(values: Sequence[float], period: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return out
    gains = 0.0
    losses = 0.0
    for index in range(1, period + 1):
        change = values[index] - values[index - 1]
        gains += max(change, 0.0)
        losses += max(-change, 0.0)
    avg_gain = gains / period
    avg_loss = losses / period
    out[period] = 100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    for index in range(period + 1, len(values)):
        change = values[index] - values[index - 1]
        avg_gain = (avg_gain * (period - 1) + max(change, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-change, 0.0)) / period
        out[index] = 100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    return out


def bollinger(
    values: Sequence[float], period: int = 20, mult: float = 2.0
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    middle = sma(values, period)
    upper: list[float | None] = [None] * len(values)
    lower: list[float | None] = [None] * len(values)
    for index in range(len(values)):
        if middle[index] is None:
            continue
        window = values[index - period + 1 : index + 1]
        mean = middle[index] or 0.0
        variance = sum((item - mean) ** 2 for item in window) / len(window)
        deviation = math.sqrt(variance)
        upper[index] = mean + mult * deviation
        lower[index] = mean - mult * deviation
    return middle, upper, lower


# ---------------------------------------------------------------------------
# Strategies: close prices -> target direction per bar
# ---------------------------------------------------------------------------


def ma_cross_signals(closes: Sequence[float], *, fast: int = 9, slow: int = 21) -> list[int]:
    fast_ma = sma(closes, fast)
    slow_ma = sma(closes, slow)
    out: list[int] = []
    for index in range(len(closes)):
        a, b = fast_ma[index], slow_ma[index]
        if a is None or b is None:
            out.append(0)
        else:
            out.append(1 if a > b else -1)
    return out


def rsi_reversion_signals(
    closes: Sequence[float], *, period: int = 14, low: float = 30, high: float = 70
) -> list[int]:
    values = rsi(closes, period)
    out: list[int] = []
    state = 0
    for index in range(len(closes)):
        value = values[index]
        if value is None:
            out.append(0)
            continue
        if state == 0:
            if value < low:
                state = 1
            elif value > high:
                state = -1
        elif state == 1 and value >= 50:
            state = 0
        elif state == -1 and value <= 50:
            state = 0
        out.append(state)
    return out


def breakout_signals(
    closes: Sequence[float], *, period: int = 20, mult: float = 2.0
) -> list[int]:
    middle, upper, lower = bollinger(closes, period, mult)
    out: list[int] = []
    state = 0
    for index in range(len(closes)):
        mid, up, dn = middle[index], upper[index], lower[index]
        if mid is None or up is None or dn is None:
            out.append(0)
            continue
        close = closes[index]
        if close > up:
            state = 1
        elif close < dn:
            state = -1
        elif state == 1 and close < mid:
            state = 0
        elif state == -1 and close > mid:
            state = 0
        out.append(state)
    return out


def nemt_signals(
    closes: Sequence[float],
    *,
    window: int = 120,
    critical_entropy: float = 0.7,
    critical_psi: float = 0.5,
) -> list[int]:
    """Same NEMT rule as the live engine, evaluated bar by bar."""

    from .signals import NemtConfig, compute_state

    config = NemtConfig(
        critical_entropy=critical_entropy, critical_psi=critical_psi
    )
    out: list[int] = []
    state = 0
    for index in range(len(closes)):
        start = max(0, index - window + 1)
        if index - start + 1 < 30:
            out.append(0)
            continue
        try:
            current = compute_state(closes[start : index + 1], config)
        except Exception:  # noqa: BLE001 - not enough data
            out.append(0)
            continue
        if current.phase == "critical_up":
            state = 1
        elif current.phase == "critical_down":
            state = -1
        elif current.phase == "decay":
            state = 0
        out.append(state)
    return out


STRATEGIES: dict[str, Callable[..., list[int]]] = {
    "ma_cross": ma_cross_signals,
    "rsi_reversion": rsi_reversion_signals,
    "breakout": breakout_signals,
    "nemt": nemt_signals,
}

DEFAULT_PARAMS: dict[str, dict[str, Any]] = {
    "ma_cross": {"fast": 9, "slow": 21},
    "rsi_reversion": {"period": 14, "low": 30.0, "high": 70.0},
    "breakout": {"period": 20, "mult": 2.0},
    "nemt": {"window": 120, "critical_entropy": 0.7, "critical_psi": 0.5},
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def run_backtest(
    bars: Sequence[Bar],
    *,
    strategy: str,
    symbol: str,
    interval: str,
    fee_rate: float = 0.0005,
    slippage: float = 0.0005,
    starting_equity: float = 1000.0,
    params: dict[str, Any] | None = None,
) -> BacktestResult:
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy {strategy}")
    if len(bars) < 30:
        raise ValueError("not enough bars to backtest")

    spec = {**DEFAULT_PARAMS[strategy], **(params or {})}
    closes = [bar.close for bar in bars]
    targets = STRATEGIES[strategy](closes, **spec)

    cash = starting_equity
    units = 0.0
    direction = 0
    entry_price = 0.0
    entry_time = 0
    entry_index = 0

    trades: list[Trade] = []
    curve: list[dict[str, Any]] = []

    def fill(price: float, *, buying: bool) -> float:
        return price * (1 + slippage) if buying else price * (1 - slippage)

    for index in range(1, len(bars)):
        bar = bars[index]
        target = targets[index - 1]  # decided on the previous close
        price = bar.open

        # equity before any rebalance, marked at this bar's open
        equity_now = cash + units * price

        if target != direction:
            # close first
            if direction != 0:
                exit_price = fill(price, buying=direction < 0)
                fee = abs(units) * exit_price * fee_rate
                cash += units * exit_price - fee
                trades.append(
                    Trade(
                        direction=direction,
                        entry_time=entry_time,
                        entry_price=entry_price,
                        exit_time=bar.open_time,
                        exit_price=exit_price,
                        pnl=0.0,  # filled below once equity is known
                        pnl_pct=0.0,
                        bars=index - entry_index,
                    )
                )
                units = 0.0
                direction = 0
            if target != 0:
                notional = cash
                qty = notional / price
                entry_price = fill(price, buying=target > 0)
                fee = notional * fee_rate
                cash -= fee
                units = qty if target > 0 else -qty
                cash -= units * entry_price
                direction = target
                entry_time = bar.open_time
                entry_index = index

        equity_close = cash + units * bar.close
        curve.append({"t": bar.open_time, "equity": round(equity_close, 4)})

    # close whatever is left at the last close
    if direction != 0 and bars:
        last = bars[-1]
        exit_price = fill(last.close, buying=direction < 0)
        fee = abs(units) * exit_price * fee_rate
        cash += units * exit_price - fee
        trades.append(
            Trade(
                direction=direction,
                entry_time=entry_time,
                entry_price=entry_price,
                exit_time=last.open_time,
                exit_price=exit_price,
                pnl=0.0,
                pnl_pct=0.0,
                bars=len(bars) - 1 - entry_index,
            )
        )
        units = 0.0
        direction = 0
        if curve:
            curve[-1]["equity"] = round(cash, 4)

    ending = cash
    # realised PnL per trade: equity before entry vs after exit, reconstructed
    # from the compounding curve so fees are included exactly once.
    running = starting_equity
    for trade in trades:
        after = _equity_at(curve, trade.exit_time)
        trade.pnl = round(after - running, 4)
        trade.pnl_pct = round((after / running - 1) * 100, 4) if running else 0.0
        running = after

    metrics = compute_metrics(curve, trades, starting_equity, ending, interval)
    return BacktestResult(
        strategy=strategy,
        symbol=symbol,
        interval=interval,
        bars=len(bars),
        starting_equity=starting_equity,
        ending_equity=ending,
        trades=trades,
        equity_curve=_downsample(curve, 200),
        metrics=metrics,
        params=spec,
    )


def _equity_at(curve: list[dict[str, Any]], timestamp: int) -> float:
    for point in curve:
        if point["t"] >= timestamp:
            return float(point["equity"])
    return float(curve[-1]["equity"]) if curve else 0.0


def _downsample(curve: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(curve) <= limit:
        return curve
    step = len(curve) / limit
    return [curve[int(index * step)] for index in range(limit)]


def compute_metrics(    curve: list[dict[str, Any]],
    trades: list[Trade],
    starting: float,
    ending: float,
    interval: str,
) -> dict[str, Any]:
    equities = [float(point["equity"]) for point in curve] or [starting]
    total_return = (ending / starting - 1) * 100 if starting else 0.0

    peak = equities[0]
    max_drawdown = 0.0
    for value in equities:
        peak = max(peak, value)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - value) / peak * 100)

    returns = [
        equities[index] / equities[index - 1] - 1
        for index in range(1, len(equities))
        if equities[index - 1] > 0
    ]
    sharpe = 0.0
    if len(returns) > 2:
        mean = sum(returns) / len(returns)
        variance = sum((item - mean) ** 2 for item in returns) / len(returns)
        deviation = math.sqrt(variance)
        if deviation > 0:
            periods = BARS_PER_YEAR.get(interval, 4 * 24 * 365)
            sharpe = mean / deviation * math.sqrt(periods)

    wins = [trade for trade in trades if trade.pnl > 0]
    losses = [trade for trade in trades if trade.pnl <= 0]
    gross_win = sum(trade.pnl for trade in wins)
    gross_loss = abs(sum(trade.pnl for trade in losses))
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0
    profit_factor = gross_win / gross_loss if gross_loss > 0 else (999.0 if gross_win else 0.0)
    avg_bars = sum(trade.bars for trade in trades) / len(trades) if trades else 0.0

    return {
        "total_return_pct": round(total_return, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "sharpe": round(sharpe, 2),
        "trades": len(trades),
        "win_rate_pct": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "avg_bars_held": round(avg_bars, 1),
        "gross_win": round(gross_win, 2),
        "gross_loss": round(gross_loss, 2),
        "exposure_pct": round(
            sum(trade.bars for trade in trades) / max(1, len(equities)) * 100, 1
        ),
    }
