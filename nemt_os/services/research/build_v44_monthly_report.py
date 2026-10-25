"""Build the v4.4 regime matrix and causal walk-forward routing report."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from nemt_os.services.research.regime_router_v44 import (
    MonthlyPerformance,
    compound_return,
    compute_regime_snapshot,
    walk_forward_route,
)


VARIANTS = ("v4a", "v4b", "v4c", "v41", "v42", "v43")


def load_performance(report_dir: Path) -> list[MonthlyPerformance]:
    """Load the completed independent monthly backtest records."""
    rows: list[MonthlyPerformance] = []
    for path in sorted(report_dir.glob("nemt-v4*-continuous-*-01-to-*-01.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        start = datetime.fromisoformat(payload["start_local"])
        end = datetime.fromisoformat(payload["end_local_exclusive"])
        if end.day != 1 or (end.year * 12 + end.month) - (start.year * 12 + start.month) != 1:
            continue
        variant = payload["record_type"].removeprefix("nemt_").removesuffix("_continuous_backtest")
        if variant not in VARIANTS:
            continue
        metrics = payload["metrics"]
        ratio = metrics.get("expectancy_over_average_loss")
        if ratio is None:
            trades = payload.get("trades", [])
            pnl = [float(item["net_pnl"]) for item in trades]
            losses = [-value for value in pnl if value <= 0]
            average_loss = statistics.mean(losses) if losses else 0.0
            ratio = statistics.mean(pnl) / average_loss if pnl and average_loss else 0.0
        rows.append(MonthlyPerformance(
            month=start.strftime("%Y-%m"),
            variant=variant,
            return_pct=float(metrics["total_return_pct"]),
            max_drawdown_pct=float(metrics["max_drawdown_pct"]),
            trades=int(metrics["trades"]),
            expectancy_ratio=float(ratio),
        ))
    return rows


def monthly_drawdown(returns_pct: list[float]) -> float:
    """Calculate drawdown from month-end compounded equity observations."""
    equity = peak = 1.0
    maximum = 0.0
    for value in returns_pct:
        equity *= 1.0 + value / 100.0
        peak = max(peak, equity)
        maximum = max(maximum, (peak - equity) / peak)
    return maximum * 100.0


def main() -> None:
    """Create JSON, CSV-like Markdown, and walk-forward evidence artifacts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", required=True, type=Path)
    parser.add_argument("--backend-root", required=True, type=Path)
    parser.add_argument("--output-prefix", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.backend_root))
    from emergenzix_api.historical_data import fetch_binance_btc_4h_archive
    from emergenzix_api.schemas import Bar

    performance = load_performance(args.report_dir)
    months = sorted({item.month for item in performance})
    complete_months = [
        month for month in months
        if {item.variant for item in performance if item.month == month} == set(VARIANTS)
    ]
    performance = [item for item in performance if item.month in complete_months]
    if not complete_months:
        raise ValueError("no complete six-variant months found")

    zone = ZoneInfo("Asia/Shanghai")
    first = datetime.strptime(complete_months[0] + "-01", "%Y-%m-%d").replace(tzinfo=zone)
    last = datetime.strptime(complete_months[-1] + "-01", "%Y-%m-%d").replace(tzinfo=zone)
    payloads = fetch_binance_btc_4h_archive(
        start_at=first.astimezone(timezone.utc) - timedelta(days=100),
        end_at=last.astimezone(timezone.utc),
    )
    bars = [Bar.model_validate(item) for item in payloads]
    snapshots = []
    for month in complete_months:
        boundary = datetime.strptime(month + "-01", "%Y-%m-%d").replace(tzinfo=zone)
        closes = [bar.close for bar in bars if bar.timestamp < boundary.astimezone(timezone.utc)]
        snapshots.append(compute_regime_snapshot(month=month, closes=closes))

    decisions = walk_forward_route(
        snapshots=snapshots,
        performance=performance,
        variants=VARIANTS,
        min_history_months=8,
        fallback_variant="v4c",
    )
    evaluation_decisions = [item for item in decisions if item.history_months >= 8]
    evaluation_months = {item.month for item in evaluation_decisions}
    router_returns = [item.realized_return_pct for item in evaluation_decisions]

    benchmarks = {}
    for variant in VARIANTS:
        values = [
            item.return_pct for item in performance
            if item.variant == variant and item.month in evaluation_months
        ]
        benchmarks[variant] = {
            "compound_return_pct": compound_return(values),
            "month_end_max_drawdown_pct": monthly_drawdown(values),
        }
    grouped: dict[tuple[str, str], list[MonthlyPerformance]] = defaultdict(list)
    snapshot_by_month = {item.month: item for item in snapshots}
    for item in performance:
        grouped[(snapshot_by_month[item.month].regime, item.variant)].append(item)
    regime_matrix = []
    for (regime, variant), rows in sorted(grouped.items()):
        regime_matrix.append({
            "regime": regime,
            "variant": variant,
            "months": len(rows),
            "average_return_pct": statistics.mean(item.return_pct for item in rows),
            "median_return_pct": statistics.median(item.return_pct for item in rows),
            "positive_month_ratio": sum(item.return_pct > 0 for item in rows) / len(rows),
            "average_drawdown_pct": statistics.mean(item.max_drawdown_pct for item in rows),
            "average_expectancy_ratio": statistics.mean(item.expectancy_ratio for item in rows),
        })

    matrix_rows = []
    performance_by_key = {(item.month, item.variant): item for item in performance}
    for snapshot in snapshots:
        row = {"month": snapshot.month, "regime": snapshot.regime,
               "direction": snapshot.direction, "features": snapshot.__dict__}
        row["strategies"] = {
            variant: performance_by_key[(snapshot.month, variant)].__dict__
            for variant in VARIANTS
        }
        matrix_rows.append(row)

    artifact = {
        "protocol": "nemt-v4.4-regime-router-monthly-001",
        "causality": "regime features use only candles completed before each month; router uses only earlier monthly outcomes",
        "months": matrix_rows,
        "regime_matrix": regime_matrix,
        "walk_forward": {
            "warmup_months": 8,
            "evaluation_months": len(evaluation_decisions),
            "compound_return_pct": compound_return(router_returns),
            "month_end_max_drawdown_pct": monthly_drawdown(router_returns),
            "decisions": [item.__dict__ for item in decisions],
        },
        "always_variant_benchmarks": benchmarks,
        "limitations": [
            "independent monthly runs close positions at month boundaries",
            "funding, liquidation tiers and order-book depth are not modeled",
            "regime thresholds are hypotheses and are not tuned on future months",
            "month-end drawdown understates possible intramonth portfolio drawdown",
        ],
    }
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = args.output_prefix.with_suffix(".json")
    md_path = args.output_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_lines = []
    for row in regime_matrix:
        summary_lines.append(
            f"| {row['regime']} | {row['variant']} | {row['months']} | "
            f"{row['average_return_pct']:+.2f}% | {row['median_return_pct']:+.2f}% | "
            f"{row['positive_month_ratio']:.0%} | {row['average_drawdown_pct']:.2f}% | "
            f"{row['average_expectancy_ratio']:+.3f}R |"
        )
    benchmark_lines = [
        f"| {variant} | {values['compound_return_pct']:+.2f}% | "
        f"{values['month_end_max_drawdown_pct']:.2f}% |"
        for variant, values in benchmarks.items()
    ]
    decision_lines = [
        f"| {item.month} | {item.regime} | {item.selected_variant} | "
        f"{item.estimated_utility:+.2f} | {item.realized_return_pct:+.2f}% | "
        f"{item.realized_drawdown_pct:.2f}% |"
        for item in evaluation_decisions
    ]
    md_path.write_text(f"""# NEMT v4.4 monthly regime matrix and walk-forward router

- Complete months: {complete_months[0]} to {complete_months[-1]} ({len(complete_months)} months)
- Walk-forward warmup: 8 months
- Walk-forward evaluation: {len(evaluation_decisions)} months
- Router compounded return: {compound_return(router_returns):+.2f}%
- Router month-end maximum drawdown: {monthly_drawdown(router_returns):.2f}%
- No binary pass/fail label and no win-rate threshold

## Market regime x strategy evidence

| Regime | Variant | Months | Average return | Median return | Positive months | Average drawdown | Average expectancy |
|---|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(summary_lines)}

## Expanding-window router decisions

Each row was selected using only earlier months.

| Month | Pre-month regime | Selected | Estimated utility | Realized return | Realized drawdown |
|---|---|---|---:|---:|---:|
{chr(10).join(decision_lines)}

## Always-one-variant benchmarks over the same evaluation months

| Variant | Compounded return | Month-end max drawdown |
|---|---:|---:|
{chr(10).join(benchmark_lines)}

## Limitations

- Independent monthly runs close positions at month boundaries.
- Funding, liquidation tiers and order-book depth are not modeled.
- Regime thresholds are hypotheses and are not tuned on future months.
- Month-end drawdown can understate intramonth portfolio drawdown.
""", encoding="utf-8")
    print(json.dumps({"json": str(json_path), "markdown": str(md_path),
                      "months": len(complete_months),
                      "router_return_pct": compound_return(router_returns)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
