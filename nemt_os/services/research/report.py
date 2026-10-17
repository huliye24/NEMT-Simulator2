"""实验报告生成 (canonical)。

纪律:
    - 必须如实输出，包括「不支持」的结论
    - 禁止只展示成功案例
    - 禁止把「回测盈利」描述为「理论已经证明」
    - 所有统计结论必须附带样本量与置信区间
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Sequence

from .backtest import BacktestResult
from .stats import StatConfig


def _fmt(v, nd: int = 4) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        if v != v:
            return "-"
        return f"{v:.{nd}f}"
    return str(v)


def _pct(v, nd: int = 2) -> str:
    if v is None or v != v:
        return "-"
    return f"{v * 100:.{nd}f}%"


def write_strategy_metrics_csv(results: Dict[str, BacktestResult], path: str) -> None:
    import csv

    if not results:
        return
    keys = ["symbol", "timeframe", "start_ms", "end_ms", "n_bars"]
    metric_keys = list(next(iter(results.values())).metrics.keys())
    header = ["strategy"] + keys + metric_keys
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for name, r in results.items():
            row = [name, r.symbol, r.timeframe, r.start_ms, r.end_ms, r.n_bars]
            row += [_fmt(r.metrics.get(k)) for k in metric_keys]
            w.writerow(row)


def write_trades_csv(results: Dict[str, BacktestResult], path: str) -> None:
    import csv

    rows: List[dict] = []
    for name, r in results.items():
        for t in r.trades:
            d = t.as_dict()
            d["strategy"] = name
            rows.append(d)
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("strategy\n")
        return
    header = ["strategy"] + [k for k in rows[0] if k != "strategy"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for d in rows:
            w.writerow(d)


def write_equity_curve_csv(results: Dict[str, BacktestResult], path: str) -> None:
    import csv

    if not results:
        return
    base = next(iter(results.values()))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp"] + list(results.keys()))
        for i, ts in enumerate(base.timestamps):
            row = [ts]
            for name in results:
                ec = results[name].equity_curve
                row.append(_fmt(ec[i], 6) if i < len(ec) else "")
            w.writerow(row)


def write_equity_curve_png(results: Dict[str, BacktestResult], path: str) -> Optional[str]:
    """绘制资金曲线。matplotlib 不可用时返回 None，不阻断流程。"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    if not results:
        return None
    base = next(iter(results.values()))
    if not base.equity_curve:
        return None

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 5))
    for name, r in results.items():
        ax.plot(r.timestamps[: len(r.equity_curve)], r.equity_curve, label=name, linewidth=1.2)
    ax.set_title("NEMT Research — Equity Curve (next-bar open, fees+slippage)")
    ax.set_xlabel("timestamp (UTC ms)")
    ax.set_ylabel("equity")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _metrics_table(results: Dict[str, BacktestResult]) -> List[str]:
    keys = [
        "total_return", "annualized_return", "max_drawdown", "sharpe_ratio",
        "sortino_ratio", "win_rate", "profit_factor", "average_win",
        "average_loss", "payoff_ratio", "maximum_consecutive_losses",
        "trade_count", "exposure", "benchmark_return",
    ]
    lines = [
        "| 指标 | " + " | ".join(results.keys()) + " |",
        "|" + "---|" * (len(results) + 1),
    ]
    for k in keys:
        row = [f"| {k}"]
        for name in results:
            v = results[name].metrics.get(k)
            row.append(_pct(v) if k in ("total_return", "annualized_return", "max_drawdown",
                                        "win_rate", "exposure", "benchmark_return") else _fmt(v, 3))
        lines.append(" | ".join(row) + " |")
    return lines


def build_experiment_report(
    config: dict,
    quality: dict,
    event_study_rows: List[dict],
    event_count: int,
    results: Dict[str, BacktestResult],
    verdict: str,
    split_info: Optional[dict] = None,
    degradation: Optional[List[dict]] = None,
    warnings: Optional[List[str]] = None,
) -> str:
    """生成 Markdown 实验报告。"""
    L: List[str] = []
    A = L.append

    A("# NEMT 实验报告")
    A("")
    A(f"- 标的: **{config.get('symbol')}**　周期: **{config.get('timeframe')}**")
    A(f"- 数据区间: `{config.get('start_ms')}` → `{config.get('end_ms')}` "
      f"（{config.get('n_bars')} 根 K 线）")
    A(f"- 数据源: {config.get('data_source')}")
    A("")

    A("## 1. 数据质量")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    for k in ("total_rows", "kept_rows", "duplicate_timestamps", "missing_bars",
              "non_positive_price", "negative_volume", "ohlc_violations",
              "unclosed_last_bar_dropped", "is_clean"):
        if k in quality:
            A(f"| {k} | {quality[k]} |")
    A("")

    if warnings:
        A("### 警告")
        A("")
        for w in warnings:
            A(f"- ⚠️ {w}")
        A("")

    A("## 2. 命题")
    A("")
    A("> 当 BTC 市场进入低谱宽、波动收缩且 DCI 开始上升的临界状态后，")
    A("> 未来 24、48、72 小时发生趋势扩张的概率显著高于随机时点和简单波动率收缩基准。")
    A("")
    A(f"**结论：{verdict}**")
    A("")
    A(f"检测到临界事件 **{event_count}** 个。")
    A("")

    if event_study_rows:
        A("## 3. 事件研究结果")
        A("")
        cols = [c for c in event_study_rows[0].keys()]
        A("| " + " | ".join(cols) + " |")
        A("|" + "---|" * len(cols))
        for r in event_study_rows:
            A("| " + " | ".join(_fmt(r.get(c), 4) for c in cols) + " |")
        A("")

    A("## 4. 策略对比")
    A("")
    if results:
        L.extend(_metrics_table(results))
    else:
        A("（无策略结果）")
    A("")

    if split_info:
        A("## 5. 样本外验证")
        A("")
        A("| 区间 | 起 | 止 | 根数 |")
        A("|---|---|---|---|")
        for k in ("train", "val", "test"):
            if k in split_info:
                a, b = split_info[k]
                A(f"| {k} | {a} | {b} | {b - a} |")
        A("")
        if degradation:
            A("| 指标 | 训练 | 验证 | 测试 | 相对验证下降 | 判定 |")
            A("|---|---|---|---|---|---|")
            for d in degradation:
                A(f"| {d.get('metric')} | {_fmt(d.get('train_value'), 4)} | "
                  f"{_fmt(d.get('val_value'), 4)} | {_fmt(d.get('test_value'), 4)} | "
                  f"{_pct(d.get('drop_vs_val'))} | {d.get('verdict')} |")
            A("")

    A("## 6. 解读限制（必须随结论一起阅读）")
    A("")
    A("- 本报告**不构成**对 NEMT 理论是否正确的证明。回测盈利不等于理论被证明。")
    A("- 涡旋与共振条件的 OI、资金费率、链上指标**无法从 OHLCV 计算**，"
      "本报告使用的是替代代理量，结论适用范围受限。")
    A("- alpha / beta 目前为配置常数，尚未从数据估计。")
    A("- 若测试集表现显著衰减，已按规则判定为疑似过拟合，该结果不可用于决策。")
    A("- 本研究不做实盘下单，全部结论仅限历史研究。")
    A("")

    return "\n".join(L)
