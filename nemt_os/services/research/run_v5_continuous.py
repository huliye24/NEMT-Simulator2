"""Continuous single-account backtest for NEMT v5 weekly trend value."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from emergenzix_api.historical_data import fetch_binance_btc_4h_archive
from emergenzix_api.schemas import Bar

from .nemt_momentum_v2 import compute_momentum_state
from .nemt_strategy_v3 import PositionControllerV3, StrategyV3Config
from .nemt_weekly_trend_v5 import WeeklyTrendConfig, assess_weekly_entry


def _atr(bars: list[Bar], index: int, period: int = 14) -> float:
    values = []
    for cursor in range(index - period + 1, index + 1):
        previous = bars[cursor - 1].close
        values.append(max(bars[cursor].high - bars[cursor].low,
                          abs(bars[cursor].high - previous),
                          abs(bars[cursor].low - previous)))
    return statistics.mean(values)


def _drawdown(equities: list[float]) -> float:
    peak = equities[0]
    maximum = 0.0
    for equity in equities:
        peak = max(peak, equity)
        maximum = max(maximum, (peak - equity) / peak if peak else 0.0)
    return maximum


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--capital", type=float, default=100.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    zone = ZoneInfo("Asia/Shanghai")
    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=zone)
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=zone)
    payloads = fetch_binance_btc_4h_archive(
        start_at=start.astimezone(timezone.utc) - timedelta(days=900),
        end_at=end.astimezone(timezone.utc) + timedelta(hours=4),
    )
    bars = [Bar.model_validate(item) for item in payloads]
    closes, highs, lows = ([bar.close for bar in bars], [bar.high for bar in bars],
                           [bar.low for bar in bars])
    weekly_config = WeeklyTrendConfig()
    controller = PositionControllerV3(StrategyV3Config(base_leverage=3, strong_leverage=3))
    fee_rate, slippage = 0.0005, 0.0002
    cash = args.capital
    position = None
    trades = []
    curve = []
    audits = []
    last_candidate_index = -10_000

    for index in range(253, len(bars)):
        bar = bars[index]
        local_open = bar.timestamp.astimezone(zone)
        if local_open < start or local_open >= end:
            continue
        decision_index = index - 1
        state = compute_momentum_state(closes[:decision_index + 1])
        current_target = position["direction"] if position else 0
        intent = controller.decide(state, current_target)

        if position:
            side = position["direction"]
            stop_hit = bar.low <= position["stop"] if side == 1 else bar.high >= position["stop"]
            held_bars = index - position["entry_index"]
            signal_exit = held_bars >= position["planned_horizon_bars"] and intent.target != side
            if stop_hit or signal_exit:
                raw_exit = position["stop"] if stop_hit else bar.open
                exit_price = raw_exit * (1 - side * slippage)
                gross = position["quantity"] * (exit_price - position["entry_price"]) * side
                exit_fee = position["quantity"] * exit_price * fee_rate
                net = gross - position["entry_fee"] - exit_fee
                cash += net
                trades.append({**position, "exit_at": bar.timestamp.isoformat(),
                               "exit_price": exit_price,
                               "exit_reason": "protective_stop" if stop_hit else "weekly_edge_expired",
                               "holding_bars": held_bars, "holding_days": held_bars * 4 / 24,
                               "net_pnl": net, "equity_after": cash})
                position = None
                if stop_hit:
                    controller.on_stop()

        # Only a fresh, deduplicated NEMT critical event may request a new position.
        if (position is None and intent.target != 0
                and decision_index - last_candidate_index >= weekly_config.event_separation_bars):
            last_candidate_index = decision_index
            weekly = assess_weekly_entry(
                closes=closes, highs=highs, lows=lows, index=decision_index,
                config=weekly_config,
            )
            audits.append({"at": bars[decision_index].timestamp.isoformat(), **asdict(weekly)})
            expected_target = 1 if weekly.direction == "LONG" else -1 if weekly.direction == "SHORT" else 0
            if weekly.permitted and expected_target == intent.target and cash > 0:
                side = intent.target
                entry = bar.open * (1 + side * slippage)
                stop_distance = max(2.0 * _atr(bars, decision_index), entry * 0.01)
                stop_fraction = stop_distance / entry
                notional = min(cash * weekly_config.maximum_leverage, cash * 0.01 / stop_fraction)
                quantity = notional / entry
                entry_fee = notional * fee_rate
                position = {
                    "direction": side, "side": "LONG" if side == 1 else "SHORT",
                    "entry_index": index, "entry_at": bar.timestamp.isoformat(),
                    "entry_price": entry, "quantity": quantity, "notional": notional,
                    "leverage": min(weekly_config.maximum_leverage, notional / cash),
                    "entry_fee": entry_fee, "stop": entry - side * stop_distance,
                    "initial_risk_usdt": cash * 0.01,
                    "planned_horizon_bars": weekly.selected_horizon_bars,
                    "expected_r": weekly.expected_r,
                    "conservative_log_growth": weekly.conservative_log_growth,
                    "model_payoff_ratio": weekly.payoff_ratio,
                    "model_win_probability": weekly.win_probability,
                }

        if position:
            # V4-B protection: trail only after one full week, never widen the stop.
            held_bars = index - position["entry_index"]
            if held_bars >= 42:
                trail = bar.close - position["direction"] * 2.0 * _atr(bars, index)
                position["stop"] = (max(position["stop"], trail) if position["direction"] == 1
                                    else min(position["stop"], trail))
            unrealized = position["quantity"] * (bar.close - position["entry_price"]) * position["direction"]
            equity = cash + unrealized - position["entry_fee"]
        else:
            equity = cash
        curve.append({"time": bar.timestamp.isoformat(), "equity": equity})

    if position:
        last = next(bar for bar in reversed(bars) if bar.timestamp.astimezone(zone) < end)
        side = position["direction"]
        exit_price = last.close * (1 - side * slippage)
        gross = position["quantity"] * (exit_price - position["entry_price"]) * side
        exit_fee = position["quantity"] * exit_price * fee_rate
        net = gross - position["entry_fee"] - exit_fee
        cash += net
        held_bars = len(curve) - position["entry_index"]
        trades.append({**position, "exit_at": (last.timestamp + timedelta(hours=4)).isoformat(),
                       "exit_price": exit_price, "exit_reason": "end_of_period",
                       "holding_bars": held_bars, "holding_days": held_bars * 4 / 24,
                       "net_pnl": net, "equity_after": cash})
        if curve:
            curve[-1]["equity"] = cash

    equities = [args.capital] + [item["equity"] for item in curve]
    wins = [trade for trade in trades if trade["net_pnl"] > 0]
    losses = [trade for trade in trades if trade["net_pnl"] <= 0]
    gross_win = sum(trade["net_pnl"] for trade in wins)
    gross_loss = abs(sum(trade["net_pnl"] for trade in losses))
    metrics = {
        "initial_equity": args.capital, "final_equity": cash,
        "total_return_pct": (cash / args.capital - 1) * 100,
        "max_drawdown_pct": _drawdown(equities) * 100,
        "trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate_pct": len(wins) / len(trades) * 100 if trades else 0.0,
        "profit_factor": gross_win / gross_loss if gross_loss else None,
        "payoff_ratio": ((gross_win / len(wins)) / (gross_loss / len(losses))) if wins and losses else None,
        "average_holding_days": statistics.mean(t["holding_days"] for t in trades) if trades else 0.0,
        "longs": sum(t["side"] == "LONG" for t in trades),
        "shorts": sum(t["side"] == "SHORT" for t in trades),
        "candidate_events": len(audits),
        "permitted_events": sum(item["permitted"] for item in audits),
    }
    report = {
        "protocol": "nemt-v5-4h-weekly-value-001",
        "start_local": start.isoformat(), "end_local_exclusive": end.isoformat(),
        "mathematics": {
            "direction_source": "NEMT critical_up/critical_down only",
            "objective": "maximize uncertainty-adjusted expected fractional log growth",
            "permission": "conservative_log_growth > 0",
            "win_rate_gate": False,
        },
        "config": asdict(weekly_config), "metrics": metrics,
        "trades": trades, "candidate_audit": audits, "equity_curve": curve,
        "limitations": ["Historical simulation only; no orders were created.",
                        "Funding, liquidation tiers, latency and depth are not modeled."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "metrics": metrics}, ensure_ascii=False))


if __name__ == "__main__":
    main()
