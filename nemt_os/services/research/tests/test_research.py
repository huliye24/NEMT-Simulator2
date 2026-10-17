"""NEMT 研究主链路测试。

覆盖验收清单要求:
    Candle 数据校验 / 指标无未来数据泄漏 / next-bar open 成交 /
    买卖双边手续费 / 滑点 / mark-to-market / 未平仓结算 /
    最大回撤 / profit factor / 时间序列切分 / 同配置结果可复现
"""

from __future__ import annotations

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from nemt_os.services.research.backtest import (  # noqa: E402
    BacktestConfig,
    compute_metrics,
    max_drawdown,
    run_backtest,
)
from nemt_os.services.research.candles import (  # noqa: E402
    Candle,
    CandleSeries,
    load_csv,
    validate_and_build,
)
from nemt_os.services.research.data_sources import make_synthetic_series  # noqa: E402
from nemt_os.services.research.strategies import (  # noqa: E402
    BuyAndHold,
    build_strategy,
    run_strategy,
)
from nemt_os.services.research.validation import (  # noqa: E402
    SplitConfig,
    judge_degradation,
    split_by_time,
    walk_forward_folds,
)
from nemt_os.services.research.variables import (  # noqa: E402
    NEMTConfig,
    compute_nemt_states,
)


def _flat_series(n: int = 60, price: float = 100.0) -> CandleSeries:
    """价格恒定（除微小 spread）的序列，用于隔离费用与滑点效应。"""
    rows = [
        Candle(1_600_000_000_000 + i * 3_600_000,
               price, price * 1.001, price * 0.999, price, 100.0, "TEST", "1h")
        for i in range(n)
    ]
    return validate_and_build(rows, "TEST", "1h", drop_unclosed_last=False)


def _signals_buy_at(idx: int, n: int) -> list:
    s = [0.0] * n
    for i in range(idx, n):
        s[i] = 1.0
    return s


# ---------------------------------------------------------------- 数据校验


def test_candle_validation_detects_duplicates_and_bad_values():
    base = make_synthetic_series(n=40, seed=1)
    rows = list(base.candles[:10])
    rows.append(rows[3])                                    # 重复时间戳
    # 两类违规分别用两根 K 线：清洗按"首个命中的问题"归类，
    # 塞进同一根会导致第二类不被计数（这是设计，不是缺陷）
    rows.append(Candle(rows[0].timestamp - 3_600_000, -5.0, 2.0, 0.5, 1.0, 9.0, "X", "1h"))
    rows.append(Candle(rows[0].timestamp - 7_200_000, 10.0, 11.0, 9.0, 10.5, -9.0, "X", "1h"))
    s = validate_and_build(rows, "X", "1h", drop_unclosed_last=False)

    assert s.quality.duplicate_timestamps == 1
    assert s.quality.unsorted_input is True
    assert s.quality.non_positive_price == 1
    assert s.quality.negative_volume == 1
    ts = s.timestamps
    assert all(ts[i] < ts[i + 1] for i in range(len(ts) - 1)), "输出必须严格升序"


def test_candle_validation_detects_missing_bars():
    rows = [
        Candle(1_600_000_000_000 + i * 3_600_000, 10.0, 11.0, 9.0, 10.5, 1.0, "T", "1h")
        for i in range(10)
    ]
    rows = [r for r in rows if r.timestamp != 1_600_000_000_000 + 3 * 3_600_000]
    s = validate_and_build(rows, "T", "1h", drop_unclosed_last=False)
    assert s.quality.missing_bars == 1
    assert s.quality.is_clean() is False


def test_unclosed_last_bar_is_dropped():
    import time

    now = int(time.time() * 1000)
    tf = 3_600_000
    # 最后一根的开盘时间必须落在"当前尚未走完"的那一格内：
    # 即 last.timestamp + tf > now
    rows = [
        Candle(now - (9 - i) * tf, 10.0, 11.0, 9.0, 10.5, 1.0, "T", "1h")
        for i in range(10)
    ]
    s = validate_and_build(rows, "T", "1h", drop_unclosed_last=True, now_ms=now)
    assert s.quality.unclosed_last_bar_dropped is True
    assert len(s) == 9


def test_csv_roundtrip(tmp_path):
    s = make_synthetic_series(n=50, seed=2)
    p = tmp_path / "c.csv"
    s.to_csv(str(p))
    s2 = load_csv(str(p))
    assert len(s2) == len(s)
    assert s2.timestamps == s.timestamps
    assert abs(s2.closes[10] - s.closes[10]) < 1e-12


# ---------------------------------------------------------------- 无未来数据泄漏


def test_nemt_states_have_no_lookahead():
    """用截断序列计算，前 k 根的状态必须与全序列前 k 根逐项一致。"""
    full = make_synthetic_series(n=420, seed=3)
    cfg = NEMTConfig()
    st_full = compute_nemt_states(full, cfg)

    k = 380
    prefix = full.slice(end_ms=full.candles[k].timestamp + 1)
    st_pre = compute_nemt_states(prefix, cfg)

    assert len(st_pre) == k + 1
    checked = 0
    for i in range(len(st_pre)):
        a, b = st_full[i], st_pre[i]
        if a.dci is None or b.dci is None:
            assert a.dci is None and b.dci is None
            continue
        assert abs(a.dci - b.dci) < 1e-12, f"DCI 在 {i} 处不一致"
        if a.spectral_width is not None and b.spectral_width is not None:
            assert abs(a.spectral_width - b.spectral_width) < 1e-12, \
                f"谱宽在 {i} 处不一致（存在未来数据依赖）"
        checked += 1
    assert checked > 0


@pytest.mark.parametrize("name", ["sma_baseline", "bollinger_squeeze_breakout",
                                  "nemt_critical_state", "buy_and_hold"])
def test_strategy_signal_prefix_equivalence(name):
    full = make_synthetic_series(n=300, seed=4)
    states = compute_nemt_states(full, NEMTConfig())
    sig_full = run_strategy(build_strategy(name), full, states)

    k = 250
    prefix = full.slice(end_ms=full.candles[k].timestamp + 1)
    sig_pre = run_strategy(build_strategy(name), prefix, states[: k + 1])
    assert sig_pre == sig_full[: k + 1], f"{name} 的信号依赖了未来数据"


# ---------------------------------------------------------------- 成交时机


def test_fill_uses_next_bar_open():
    s = _flat_series(60)
    n = len(s)
    sig = _signals_buy_at(10, n)
    cfg = BacktestConfig(fee_bps=0.0, slippage_bps=0.0)
    r = run_backtest(s, sig, cfg)

    assert len(r.trades) == 1
    t = r.trades[0]
    assert t.entry_index == 11, "必须在信号产生的下一根成交"
    assert t.entry_timestamp == s.candles[11].timestamp
    assert abs(t.entry_price - s.opens[11]) < 1e-9, "成交价必须是下一根的 open"


# ---------------------------------------------------------------- 手续费


def test_fees_charged_on_both_sides():
    s = _flat_series(60)
    n = len(s)
    sig = _signals_buy_at(10, n)
    cfg = BacktestConfig(fee_bps=10.0, slippage_bps=0.0)
    r = run_backtest(s, sig, cfg)

    t = r.trades[0]
    assert t.entry_fee > 0, "买入端必须计手续费"
    assert t.exit_fee > 0, "卖出端必须计手续费"
    # 价格恒定 → 净亏损应等于双边费用
    assert t.net_pnl < 0
    expected = -(t.entry_fee + t.exit_fee)
    assert abs(t.net_pnl - expected) < 1e-6, "净盈亏应恰好等于双边手续费之和"


def test_zero_fee_flat_price_has_zero_pnl():
    s = _flat_series(60)
    sig = _signals_buy_at(10, len(s))
    cfg = BacktestConfig(fee_bps=0.0, slippage_bps=0.0)
    r = run_backtest(s, sig, cfg)
    assert abs(r.trades[0].net_pnl) < 1e-9


# ---------------------------------------------------------------- 滑点


def test_slippage_direction():
    s = _flat_series(60)
    sig = _signals_buy_at(10, len(s))
    cfg = BacktestConfig(fee_bps=0.0, slippage_bps=100.0)  # 1%
    r = run_backtest(s, sig, cfg)
    t = r.trades[0]
    assert t.entry_price > s.opens[11], "买入滑点必须抬高成交价"
    assert t.exit_price < s.closes[-1], "卖出滑点必须压低成交价"


# ---------------------------------------------------------------- mark-to-market


def test_mark_to_market_equity_tracks_position():
    s = make_synthetic_series(n=80, seed=5)
    sig = [1.0] * len(s)
    cfg = BacktestConfig(fee_bps=0.0, slippage_bps=0.0)
    r = run_backtest(s, sig, cfg)

    # 持仓期间，相邻两根的权益变化应等于持仓量 × 价格变化
    i, j = 40, 41
    qty = None
    for t in r.trades:
        if t.entry_index <= i and (t.exit_index is None or t.exit_index > i):
            qty = t.quantity
    assert qty is not None and qty > 0
    delta_equity = r.equity_curve[j] - r.equity_curve[i]
    delta_price = s.closes[j] - s.closes[i]
    assert abs(delta_equity - qty * delta_price) < 1e-6, "权益未按市价估值"


# ---------------------------------------------------------------- 未平仓结算


def test_open_position_is_settled_at_end():
    s = make_synthetic_series(n=80, seed=6)
    sig = [1.0] * len(s)   # 一直持有，信号从不转平
    cfg = BacktestConfig(fee_bps=5.0, slippage_bps=0.0)
    r = run_backtest(s, sig, cfg)

    assert len(r.trades) == 1
    assert r.trades[0].exit_reason == "end_of_data"
    assert r.trades[0].exit_index == len(s) - 1


# ---------------------------------------------------------------- 指标


def test_max_drawdown_known_value():
    eq = [100.0, 110.0, 55.0, 80.0, 200.0]
    # 峰值 110 → 55，回撤 50%
    assert abs(max_drawdown(eq) - 0.5) < 1e-12


def test_profit_factor_known_value():
    from nemt_os.services.research.backtest import Trade

    mk = lambda pnl: Trade(  # noqa: E731
        trade_id=1, entry_index=0, entry_timestamp=0, entry_price=1.0, entry_fee=0.0,
        entry_reason="", exit_index=1, exit_timestamp=1, exit_price=1.0, exit_fee=0.0,
        exit_reason="", quantity=1.0, gross_pnl=pnl, net_pnl=pnl, return_pct=0.0,
        holding_bars=1)
    trades = [mk(10.0), mk(20.0), mk(-5.0), mk(-5.0)]
    m = compute_metrics([100.0, 110.0], trades, 2, "1h", BacktestConfig(), 0.0)
    assert abs(m["profit_factor"] - 3.0) < 1e-12      # 30 / 10
    assert abs(m["average_win"] - 15.0) < 1e-12
    assert abs(m["average_loss"] - 5.0) < 1e-12
    assert abs(m["payoff_ratio"] - 3.0) < 1e-12
    assert m["maximum_consecutive_losses"] == 2
    assert m["win_rate"] == 0.5


# ---------------------------------------------------------------- 时间序列切分


def test_time_split_is_ordered_and_contiguous():
    n = 1000
    sp = split_by_time(n, SplitConfig(train_ratio=0.6, val_ratio=0.2))
    assert sp.train[0] == 0
    assert sp.train[1] == sp.val[0]
    assert sp.val[1] == sp.test[0]
    assert sp.test[1] == n
    assert sp.train[1] > 0 and sp.val[1] > sp.val[0] and sp.test[1] > sp.test[0]


def test_walk_forward_train_always_precedes_test():
    folds = walk_forward_folds(1000, SplitConfig(n_walk_forward_folds=4))
    assert len(folds) >= 2
    for f in folds:
        assert f.train[1] <= f.test[0], "训练集必须完全位于测试集之前"


def test_degradation_verdict():
    d = judge_degradation("sharpe_ratio", 2.0, 1.8, 0.5, threshold=0.4)
    assert d.verdict == "疑似过拟合"
    d2 = judge_degradation("sharpe_ratio", 2.0, 1.8, 1.7, threshold=0.4)
    assert d2.verdict in ("无显著衰减", "轻度衰减")


# ---------------------------------------------------------------- 可复现性


def test_same_config_is_reproducible():
    s = make_synthetic_series(n=200, seed=7)
    states = compute_nemt_states(s, NEMTConfig())
    sig = run_strategy(build_strategy("sma_baseline"), s, states)
    cfg = BacktestConfig(fee_bps=10.0, slippage_bps=5.0, slippage_jitter=0.5)

    r1 = run_backtest(s, sig, cfg, states=states)
    r2 = run_backtest(s, sig, cfg, states=states)

    assert r1.metrics == r2.metrics, "同配置两次运行的指标必须完全一致"
    assert r1.equity_curve == r2.equity_curve, "同配置两次运行的资金曲线必须完全一致"
    assert [t.net_pnl for t in r1.trades] == [t.net_pnl for t in r2.trades]


# ---------------------------------------------------------------- 防重复开仓 / 负现金


def test_no_duplicate_entry_and_no_negative_cash():
    s = make_synthetic_series(n=200, seed=8)
    # 信号在 1 / 0 之间反复跳变，检验不会重复开仓
    sig = [1.0 if (i // 7) % 2 == 0 else 0.0 for i in range(len(s))]
    cfg = BacktestConfig(fee_bps=5.0, slippage_bps=2.0, slippage_jitter=0.3)
    r = run_backtest(s, sig, cfg)

    # 交易必须严格交替：任一笔的入场必须晚于上一笔的出场
    for k in range(1, len(r.trades)):
        assert r.trades[k].entry_index > r.trades[k - 1].exit_index, "出现重复开仓"
    # 权益始终非负
    assert all(e >= -1e-6 for e in r.equity_curve), "出现负权益"
