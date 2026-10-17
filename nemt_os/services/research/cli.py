"""NEMT 研究唯一命令入口 (canonical)。

用法:
    python -m nemt_os.services.research.cli experiment \
        --symbol BTCUSDT \
        --timeframe 1h \
        --strategy all \
        --data-source csv \
        --data-path btc_data.csv \
        --output output/research

所有其它入口（main.py / nemt_controller.py / quant-mvp 等）均为 non-canonical。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from typing import Dict, List, Optional

from .backtest import BacktestConfig, run_backtest
from .candles import CandleSeries, write_quality_report
from .data_sources import (
    DataSourceError,
    load_binance,
    load_csv,
    load_or_download,
    make_synthetic_series,
)
from .events import (
    EventConfig,
    RegimeConfig,
    classify_regimes,
    compute_outcomes,
    detect_bbw_contraction_events,
    detect_critical_events,
    sample_random_indices,
)
from .report import (
    build_experiment_report,
    write_equity_curve_csv,
    write_equity_curve_png,
    write_strategy_metrics_csv,
    write_trades_csv,
)
from .stats import StatConfig, compare_to_control, describe, overall_verdict
from .strategies import ALL_STRATEGIES, build_strategy, run_strategy
from .validation import SplitConfig, judge_degradation, split_by_time, walk_forward_folds
from .variables import NEMTConfig, compute_nemt_states, states_to_csv


# ---------------------------------------------------------------- 事件研究


OUTCOME_FIELDS = ["fwd_return", "fwd_abs_return", "mfe", "mae", "fwd_rvol", "trend_duration"]
PRIMARY_OUTCOME = "fwd_abs_return"


def run_event_study(
    series: CandleSeries,
    states: list,
    event_cfg: EventConfig,
    stat_cfg: StatConfig,
    max_control_samples: int = 3000,
) -> tuple:
    """运行事件研究，返回 (rows, event_indices, overall_verdict)。

    对照组:
        - random        随机时点（与事件数相同，固定种子）
        - bbw_contract  单独的布林带宽度收缩
        - all_bars      全样本（等价于 Buy & Hold 的结果分布）
    """
    events = detect_critical_events(states, event_cfg)
    n = len(series)

    n_random = len(events)
    rng_seed = stat_cfg.seed
    rand_idx = sample_random_indices(n, n_random, seed=rng_seed,
                                     min_index=0, max_index=n - 1)
    bbw_idx = detect_bbw_contraction_events(
        states,
        percentile_max=event_cfg.vol_percentile_max,
        cooldown_bars=event_cfg.cooldown_bars,
    )

    # 全样本对照组可能高达数万，bootstrap 成本会爆炸。
    # 用确定性等距抽样把它压到 max_control_samples，
    # 这只影响对照组的估计精度，不影响事件组统计量。
    all_idx = list(range(0, n))
    if len(all_idx) > max_control_samples:
        step = len(all_idx) / max_control_samples
        all_idx = [all_idx[int(k * step)] for k in range(max_control_samples)]
    if len(bbw_idx) > max_control_samples:
        step = len(bbw_idx) / max_control_samples
        bbw_idx = [bbw_idx[int(k * step)] for k in range(max_control_samples)]

    groups = {
        "event": events,
        "random": rand_idx,
        "bbw_contract": bbw_idx,
        "all_bars": all_idx,
    }

    rows: List[dict] = []
    verdict_inputs: List[dict] = []

    for h in event_cfg.horizons:
        vals: Dict[str, Dict[str, List[float]]] = {}
        for gname, idxs in groups.items():
            bucket: Dict[str, List[float]] = {f: [] for f in OUTCOME_FIELDS}
            for i in idxs:
                o = compute_outcomes(series, i, int(h))
                if o is None:
                    continue
                for f in OUTCOME_FIELDS:
                    bucket[f].append(o[f])
            vals[gname] = bucket

        for f in OUTCOME_FIELDS:
            for gname in groups:
                d = describe(vals[gname][f], stat_cfg, label=f"{gname}")
                rows.append({
                    "horizon": h,
                    "outcome": f,
                    "group": gname,
                    "n": d["n"],
                    "mean": d["mean"],
                    "median": d["median"],
                    "win_rate": d["win_rate"],
                    "ci_low": d["ci_low"],
                    "ci_high": d["ci_high"],
                })

            # 事件组 vs 各对照
            for ctrl in ("random", "bbw_contract", "all_bars"):
                cmp_ = compare_to_control(
                    vals["event"][f], vals[ctrl][f], stat_cfg
                )
                rows.append({
                    "horizon": h,
                    "outcome": f,
                    "group": f"event_vs_{ctrl}",
                    "n": cmp_["event_n"],
                    "mean": cmp_.get("diff", float("nan")),
                    "median": float("nan"),
                    "win_rate": float("nan"),
                    "ci_low": cmp_.get("diff_ci_low", float("nan")),
                    "ci_high": cmp_.get("diff_ci_high", float("nan")),
                    "verdict": cmp_.get("verdict_text", ""),
                })
                if f == PRIMARY_OUTCOME and ctrl in ("random", "bbw_contract"):
                    verdict_inputs.append(cmp_)

    return rows, events, overall_verdict(verdict_inputs)


def _write_csv_rows(rows: List[dict], path: str) -> None:
    import csv

    if not rows:
        return
    header: List[str] = []
    for r in rows:
        for k in r:
            if k not in header:
                header.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ---------------------------------------------------------------- CLI


def _load_series(args) -> CandleSeries:
    if args.data_source == "csv":
        if not args.data_path:
            raise ValueError("--data-source csv 时必须提供 --data-path")
        if not os.path.exists(args.data_path):
            raise FileNotFoundError(f"数据文件不存在: {args.data_path}")
        return load_csv(args.data_path, symbol=args.symbol, timeframe=args.timeframe)
    if args.data_source == "binance":
        return load_or_download(
            symbol=args.symbol,
            timeframe=args.timeframe,
            cache_dir=args.cache_dir,
            refresh=args.refresh,
        )
    if args.data_source == "synthetic":
        # 仅供冒烟测试，**严禁**用于任何理论结论
        return make_synthetic_series(n=args.synthetic_bars,
                                     symbol=args.symbol, timeframe=args.timeframe)
    raise ValueError(f"未知 data-source: {args.data_source}")


def cmd_experiment(args) -> int:
    out_dir = args.output
    os.makedirs(out_dir, exist_ok=True)

    warnings: List[str] = []

    print("[1/9] 读取与校验数据 ...")
    series = _load_series(args)
    if len(series) < 50:
        raise ValueError(f"数据量过少（{len(series)} 根），无法进行实验")

    q = series.quality
    write_quality_report(q, os.path.join(out_dir, "data_quality.json"))

    days = series.coverage_days()
    if days < 365:
        warnings.append(
            f"数据仅覆盖 {days:.0f} 天（约 {days/30.4:.1f} 个月），"
            f"**不足一个完整牛熊周期**，事件研究的统计功效与外推性受限"
        )
    if not q.is_clean():
        warnings.append("数据质量检查未通过（见 data_quality.json），结果需谨慎解读")

    print(f"      共 {len(series)} 根 K 线，覆盖 {days:.0f} 天")

    print("[2/9] 计算 NEMT 状态变量 ...")
    nemt_cfg = NEMTConfig()
    states = compute_nemt_states(series, nemt_cfg)
    states_to_csv(states, os.path.join(out_dir, "nemt_states.csv"))

    print("[3/9] 运行理论事件研究 ...")
    event_cfg = EventConfig()
    stat_cfg = StatConfig(n_bootstrap=args.n_bootstrap)
    study_rows, events, verdict = run_event_study(series, states, event_cfg, stat_cfg)
    _write_csv_rows(study_rows, os.path.join(out_dir, "event_study.csv"))

    ev_rows = [{
        "event_id": k + 1,
        "index": i,
        "timestamp": series.candles[i].timestamp,
        "dci": states[i].dci,
        "spectral_width": states[i].spectral_width,
        "sw_percentile": states[i].sw_percentile,
        "bbw_percentile": states[i].bbw_percentile,
        "rvol_percentile": states[i].rvol_percentile,
        "dci_slope": states[i].dci_slope,
        "vortex_score": states[i].vortex_score,
        "resonance_score": states[i].resonance_score,
        "market_phase": states[i].market_phase,
    } for k, i in enumerate(events)]
    _write_csv_rows(ev_rows, os.path.join(out_dir, "nemt_events.csv"))
    print(f"      检出 {len(events)} 个临界事件；命题结论: {verdict}")

    print("[4/9] 运行策略 ...")
    strategies = ALL_STRATEGIES if args.strategy == "all" else \
        [s.strip() for s in args.strategy.split(",")]
    bt_cfg = BacktestConfig(
        initial_capital=args.initial_capital,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        seed=args.seed,
    )

    results: Dict[str, object] = {}
    for name in strategies:
        strat = build_strategy(name)
        signals = run_strategy(strat, series, states)
        res = run_backtest(series, signals, bt_cfg, states=states)
        results[name] = res
        print(f"      {name}: 交易 {len(res.trades)} 笔, "
              f"收益 {res.metrics['total_return']*100:.2f}%, "
              f"回撤 {res.metrics['max_drawdown']*100:.2f}%")

    print("[5/9] 样本外验证 ...")
    split_cfg = SplitConfig()
    split = split_by_time(len(series), split_cfg)
    split_info = split.as_dict()
    degradation: List[dict] = []

    if len(series) >= 200:
        # 在全样本上已跑过；这里对 NEMT 策略做分段评估
        target = "nemt_critical_state" if "nemt_critical_state" in results else \
            next(iter(results))
        seg_metrics: Dict[str, Dict[str, float]] = {}
        for seg in ("train", "val", "test"):
            a, b = split.range_for(seg)
            if b - a < 30:
                seg_metrics[seg] = {}
                continue
            sub = series.slice(start_ms=series.candles[a].timestamp,
                               end_ms=(series.candles[b].timestamp
                                       if b < len(series) else None))
            sub_states = states[a:b]
            strat = build_strategy(target)
            sig = run_strategy(strat, sub, sub_states)
            r = run_backtest(sub, sig, bt_cfg, states=sub_states)
            seg_metrics[seg] = r.metrics

        for metric in ("total_return", "sharpe_ratio", "profit_factor"):
            tv = seg_metrics.get("train", {}).get(metric)
            vv = seg_metrics.get("val", {}).get(metric)
            sv = seg_metrics.get("test", {}).get(metric)
            if tv is None or vv is None or sv is None:
                continue
            d = judge_degradation(metric, tv, vv, sv, split_cfg.degradation_threshold)
            degradation.append(d.as_dict())
            if d.verdict == "疑似过拟合":
                warnings.append(
                    f"{target} 在 {metric} 上测试集相对验证集衰减 "
                    f"{(d.drop_vs_val or 0)*100:.1f}%，判定为疑似过拟合"
                )
    else:
        warnings.append("样本量不足 200 根，跳过分段样本外验证")

    print("[6/9] 生成策略比较表 ...")
    write_strategy_metrics_csv(results, os.path.join(out_dir, "strategy_metrics.csv"))

    print("[7/9] 生成资金曲线 ...")
    write_equity_curve_csv(results, os.path.join(out_dir, "equity_curve.csv"))
    png = write_equity_curve_png(results, os.path.join(out_dir, "equity_curve.png"))
    if png is None:
        warnings.append("matplotlib 不可用，未生成 equity_curve.png（不影响其它产物）")

    print("[8/9] 保存交易与配置 ...")
    write_trades_csv(results, os.path.join(out_dir, "trades.csv"))

    config = {
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "data_source": args.data_source,
        "data_path": args.data_path,
        "n_bars": len(series),
        "start_ms": series.start_ms(),
        "end_ms": series.end_ms(),
        "coverage_days": round(days, 2),
        "strategies": strategies,
        "seed": args.seed,
        "nemt_config": nemt_cfg.to_dict(),
        "event_config": event_cfg.to_dict(),
        "stat_config": stat_cfg.to_dict(),
        "backtest_config": bt_cfg.to_dict(),
        "split_config": split_cfg.to_dict(),
        "split": split_info,
        "primary_outcome": PRIMARY_OUTCOME,
        "verdict": verdict,
    }
    with open(os.path.join(out_dir, "experiment_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("[9/9] 生成 Markdown 报告 ...")
    md = build_experiment_report(
        config=config,
        quality=q.to_dict(),
        event_study_rows=study_rows,
        event_count=len(events),
        results=results,
        verdict=verdict,
        split_info=split_info,
        degradation=degradation,
        warnings=warnings,
    )
    with open(os.path.join(out_dir, "experiment_report.md"), "w", encoding="utf-8") as f:
        f.write(md)

    print("")
    print(f"完成。产物目录: {os.path.abspath(out_dir)}")
    print(f"命题结论: {verdict}")
    for w in warnings:
        print(f"⚠️  {w}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nemt_os.services.research.cli",
        description="NEMT 个人 BTC 量化研究系统 — 唯一命令入口",
    )
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("experiment", help="运行完整实验")
    e.add_argument("--symbol", default="BTCUSDT")
    e.add_argument("--timeframe", default="1h")
    e.add_argument("--strategy", default="all",
                   help="all 或逗号分隔的策略名")
    e.add_argument("--data-source", default="csv",
                   choices=["csv", "binance", "synthetic"])
    e.add_argument("--data-path", default="btc_data.csv")
    e.add_argument("--output", default="output/research")
    e.add_argument("--cache-dir", default="data/cache")
    e.add_argument("--refresh", action="store_true", help="忽略缓存重新下载")
    e.add_argument("--initial-capital", type=float, default=10_000.0)
    e.add_argument("--fee-bps", type=float, default=10.0)
    e.add_argument("--slippage-bps", type=float, default=5.0)
    e.add_argument("--seed", type=int, default=20240101)
    e.add_argument("--n-bootstrap", type=int, default=2000)
    e.add_argument("--synthetic-bars", type=int, default=1500,
                   help="仅 data-source=synthetic 时使用")
    e.set_defaults(func=cmd_experiment)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, DataSourceError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"未预期的错误: {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
