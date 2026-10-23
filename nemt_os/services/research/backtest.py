"""可信回测引擎 (canonical)。

与仓库历史实现的关键差异（均为审计发现的问题）:
    1. **信号在第 i 根收盘后确认，在第 i+1 根的 open 成交**
       —— `nemt_os/nemt/backtest.py:190` 用 `closes[-1]` 当根成交，存在前视
    2. **买入端与卖出端都计手续费**
       —— 旧实现的 pnl 用 `qty*entry_price` 作成本基础，漏算买入端费用
    3. **滑点使用确定性种子**
       —— `nemt_os/nemt/execution.py:261` 用无种子的 `random.uniform`，不可复现
    4. 每根 K 线 mark-to-market；结束时按最后收盘价结算未平仓头寸
    5. 禁止负现金、禁止重复开仓
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from .candles import CandleSeries, bars_per_year


# ---------------------------------------------------------------- 配置


@dataclass
class BacktestConfig:
    initial_capital: float = 10_000.0
    fee_bps: float = 10.0            # 单边手续费（基点）
    slippage_bps: float = 5.0        # 单边滑点（基点）
    slippage_jitter: float = 0.0     # 滑点随机扰动比例（0 = 完全确定）
    seed: int = 20240101
    position_fraction: float = 1.0   # 单次开仓使用的资金比例
    risk_free_rate: float = 0.0      # 年化无风险利率

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Trade:
    """单笔交易记录。所有字段都可追溯到具体 K 线。"""

    trade_id: int
    entry_index: int
    entry_timestamp: int
    entry_price: float
    entry_fee: float
    entry_reason: str
    exit_index: int
    exit_timestamp: int
    exit_price: float
    exit_fee: float
    exit_reason: str
    quantity: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    holding_bars: int
    entry_phase: str = ""
    entry_dci: Optional[float] = None
    entry_spectral_width: Optional[float] = None
    entry_vortex_score: Optional[float] = None
    entry_resonance_score: Optional[float] = None
    side: str = "LONG"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class BacktestResult:
    config: BacktestConfig
    symbol: str
    timeframe: str
    start_ms: int
    end_ms: int
    n_bars: int
    trades: List[Trade]
    equity_curve: List[float]
    timestamps: List[int]

    # 绩效指标
    metrics: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "n_bars": self.n_bars,
            "config": self.config.to_dict(),
            "metrics": self.metrics,
        }


# ---------------------------------------------------------------- 指标


def max_drawdown(equity: List[float]) -> float:
    """最大回撤（正值）。"""
    if not equity:
        return 0.0
    peak = equity[0]
    mdd = 0.0
    for v in equity:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak
            if dd > mdd:
                mdd = dd
    return mdd


def _per_bar_returns(equity: List[float]) -> List[float]:
    out: List[float] = []
    for i in range(1, len(equity)):
        p0 = equity[i - 1]
        if p0 > 0:
            out.append(equity[i] / p0 - 1.0)
        else:
            out.append(0.0)
    return out


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _stdev(xs: List[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((v - m) ** 2 for v in xs) / (n - 1))


def compute_metrics(
    equity: List[float],
    trades: List[Trade],
    n_bars: int,
    timeframe: str,
    cfg: BacktestConfig,
    benchmark_return: float,
    in_position_flags: Optional[List[bool]] = None,
) -> Dict[str, float]:
    """计算全部绩效指标。"""
    init = cfg.initial_capital
    final = equity[-1] if equity else init
    total_return = (final - init) / init if init else 0.0

    bpy = bars_per_year(timeframe)
    years = (n_bars / bpy) if bpy > 0 and n_bars > 0 else 0.0
    if years > 0 and final > 0 and init > 0:
        annualized_return = (final / init) ** (1.0 / years) - 1.0
    else:
        annualized_return = 0.0

    mdd = max_drawdown(equity)
    rets = _per_bar_returns(equity)

    sharpe = 0.0
    sortino = 0.0
    if len(rets) >= 2:
        sd = _stdev(rets)
        mr = _mean(rets)
        if sd > 0:
            sharpe = (mr - cfg.risk_free_rate / bpy) / sd * math.sqrt(bpy)
        downside = [r for r in rets if r < 0]
        dd_dev = math.sqrt(sum(r * r for r in downside) / len(rets)) if downside else 0.0
        if dd_dev > 0:
            sortino = (mr - cfg.risk_free_rate / bpy) / dd_dev * math.sqrt(bpy)

    pnls = [t.net_pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    win_rate = (len(wins) / len(pnls)) if pnls else 0.0
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (float("inf") if gross_win > 0 else 0.0)
    avg_win = _mean(wins) if wins else 0.0
    avg_loss = abs(_mean(losses)) if losses else 0.0
    payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else (float("inf") if avg_win > 0 else 0.0)

    max_consec = 0
    streak = 0
    for p in pnls:
        if p <= 0:
            streak += 1
            max_consec = max(max_consec, streak)
        else:
            streak = 0

    if in_position_flags:
        exposure = sum(1 for v in in_position_flags if v) / len(in_position_flags)
    else:
        exposure = 0.0

    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "max_drawdown": mdd,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "win_rate": win_rate,
        "profit_factor": profit_factor if profit_factor != float("inf") else 9999.0,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "payoff_ratio": payoff_ratio if payoff_ratio != float("inf") else 9999.0,
        "maximum_consecutive_losses": float(max_consec),
        "trade_count": float(len(trades)),
        "exposure": exposure,
        "benchmark_return": benchmark_return,
        "final_equity": final,
        "excess_return": total_return - benchmark_return,
    }


# ---------------------------------------------------------------- 引擎


def run_backtest(
    series: CandleSeries,
    signals: List[float],
    cfg: Optional[BacktestConfig] = None,
    phases: Optional[List[str]] = None,
    states: Optional[list] = None,
) -> BacktestResult:
    """执行回测。

    时间线（关键）:
        第 i 根: 先执行"上一根收盘产生的订单"（用第 i 根的 open 成交）
                → 再按第 i 根 close 做 mark-to-market
                → 再依据 signals[i] 产生下一根的订单

    这样保证信号只用到了 i 及之前的信息，成交价是 i+1 的开盘价。
    """
    cfg = cfg or BacktestConfig()
    if len(series) != len(signals):
        raise ValueError(
            f"signals 长度 ({len(signals)}) 与 K 线数 ({len(series)}) 不一致"
        )
    invalid = [signal for signal in signals if signal not in (-1.0, 0.0, 1.0)]
    if invalid:
        raise ValueError(
            f"signals 只允许 -1.0、0.0、1.0，收到 {invalid[0]!r}"
        )

    rng = random.Random(cfg.seed)
    opens = series.opens
    closes = series.closes
    n = len(series)

    cash = cfg.initial_capital
    qty = 0.0
    direction = 0
    entry_index = -1
    entry_price = 0.0
    entry_fee_total = 0.0
    entry_reason = ""

    trades: List[Trade] = []
    equity: List[float] = []
    in_pos_flags: List[bool] = []

    pending_target: Optional[int] = None
    pending_reason: str = ""

    def slip(price: float, side: str) -> float:
        s = cfg.slippage_bps / 10_000.0
        if cfg.slippage_jitter > 0:
            s *= (1.0 + rng.uniform(-cfg.slippage_jitter, cfg.slippage_jitter))
        if side == "BUY":
            return price * (1.0 + s)
        return price * (1.0 - s)

    for i in range(n):
        # --- 1) 执行上一根收盘产生的目标，在当前 open 先平后开 ---
        if pending_target is not None and pending_target != direction:
            if direction != 0 and qty > 0:
                close_side = "SELL" if direction == 1 else "BUY"
                px = slip(opens[i], close_side)
                notional = qty * px
                fee = notional * cfg.fee_bps / 10_000.0
                gross = direction * (px - entry_price) * qty
                if direction == 1:
                    cash += notional - fee
                else:
                    cash += gross - fee
                net = gross - entry_fee_total - fee
                st = states[entry_index] if (states and 0 <= entry_index < len(states)) else None
                trades.append(Trade(
                    trade_id=len(trades) + 1,
                    entry_index=entry_index,
                    entry_timestamp=series.candles[entry_index].timestamp,
                    entry_price=entry_price,
                    entry_fee=entry_fee_total,
                    entry_reason=entry_reason,
                    exit_index=i,
                    exit_timestamp=series.candles[i].timestamp,
                    exit_price=px,
                    exit_fee=fee,
                    exit_reason=pending_reason,
                    quantity=qty,
                    gross_pnl=gross,
                    net_pnl=net,
                    return_pct=(direction * (px - entry_price) / entry_price)
                    if entry_price > 0 else 0.0,
                    holding_bars=i - entry_index,
                    entry_phase=(st.market_phase if st else ""),
                    entry_dci=(st.dci if st else None),
                    entry_spectral_width=(st.spectral_width if st else None),
                    entry_vortex_score=(st.vortex_score if st else None),
                    entry_resonance_score=(st.resonance_score if st else None),
                    side="LONG" if direction == 1 else "SHORT",
                ))
                qty = 0.0
                direction = 0
                entry_index = -1

            if pending_target != 0 and cash > 0:
                open_side = "BUY" if pending_target == 1 else "SELL"
                px = slip(opens[i], open_side)
                budget = cash * cfg.position_fraction
                if budget > 0 and px > 0:
                    fee_rate = cfg.fee_bps / 10_000.0
                    if pending_target == 1:
                        open_qty = budget / (px * (1.0 + fee_rate))
                        cost = open_qty * px
                        fee = cost * fee_rate
                        if cost + fee <= cash + 1e-9:
                            cash -= cost + fee
                        else:
                            open_qty = 0.0
                    else:
                        open_qty = budget / px
                        fee = open_qty * px * fee_rate
                        cash -= fee
                    if open_qty > 0:
                        qty = open_qty
                        direction = pending_target
                        entry_index = i
                        entry_price = px
                        entry_fee_total = fee
                        entry_reason = pending_reason
        pending_target = None

        # --- 2) mark-to-market ---
        if direction == 1:
            marked_equity = cash + qty * closes[i]
        elif direction == -1:
            marked_equity = cash + (entry_price - closes[i]) * qty
        else:
            marked_equity = cash
        equity.append(marked_equity)
        in_pos_flags.append(direction != 0)

        # --- 3) 依据本根收盘信号，产生下一根的订单 ---
        target = int(signals[i])
        if target != direction:
            pending_target = target
            pending_reason = "signal"

    # --- 结束：未平仓头寸按最后一根收盘价结算 ---
    if direction != 0 and qty > 0:
        i = n - 1
        close_side = "SELL" if direction == 1 else "BUY"
        px = slip(closes[i], close_side)
        notional = qty * px
        fee = notional * cfg.fee_bps / 10_000.0
        gross = direction * (px - entry_price) * qty
        if direction == 1:
            cash += notional - fee
        else:
            cash += gross - fee
        net = gross - entry_fee_total - fee
        st = states[entry_index] if (states and 0 <= entry_index < len(states)) else None
        trades.append(Trade(
            trade_id=len(trades) + 1,
            entry_index=entry_index,
            entry_timestamp=series.candles[entry_index].timestamp,
            entry_price=entry_price,
            entry_fee=entry_fee_total,
            entry_reason=entry_reason,
            exit_index=i,
            exit_timestamp=series.candles[i].timestamp,
            exit_price=px,
            exit_fee=fee,
            exit_reason="end_of_data",
            quantity=qty,
            gross_pnl=gross,
            net_pnl=net,
            return_pct=(direction * (px - entry_price) / entry_price)
            if entry_price > 0 else 0.0,
            holding_bars=i - entry_index,
            entry_phase=(st.market_phase if st else ""),
            entry_dci=(st.dci if st else None),
            entry_spectral_width=(st.spectral_width if st else None),
            entry_vortex_score=(st.vortex_score if st else None),
            entry_resonance_score=(st.resonance_score if st else None),
            side="LONG" if direction == 1 else "SHORT",
        ))
        qty = 0.0
        direction = 0
        if equity:
            equity[-1] = cash

    # --- 基准：同区间 Buy & Hold ---
    bench = 0.0
    if n >= 2 and closes[0] > 0:
        bench = closes[-1] / closes[0] - 1.0

    metrics = compute_metrics(
        equity, trades, n, series.timeframe, cfg, bench, in_pos_flags
    )

    return BacktestResult(
        config=cfg,
        symbol=series.symbol,
        timeframe=series.timeframe,
        start_ms=series.candles[0].timestamp if n else 0,
        end_ms=series.candles[-1].timestamp if n else 0,
        n_bars=n,
        trades=trades,
        equity_curve=equity,
        timestamps=series.timestamps,
        metrics=metrics,
    )
