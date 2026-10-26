"""BTC 2023 implementation regression for the frozen lifecycle engine.

This is an already revealed development window.  Its output may validate
accounting and execution semantics but must not select or tune an arm.
"""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / ".artifacts" / "multi" / "stage" / "backend"
CACHE = ROOT / ".artifacts" / "binance-cache"
OUTPUT = ROOT / "docs" / "reports" / "NEMT_COMPLETE_LIFECYCLE_2023_REGRESSION.json"
PROTOCOL = ROOT / "docs" / "experiments" / "NEMT_COMPLETE_TRADING_SYSTEM_LIFECYCLE_FREEZE_20261026.md"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(STAGE))
os.environ["BINANCE_ARCHIVE_CACHE_DIR"] = str(CACHE)

from emergenzix_api.historical_data import fetch_binance_spot_4h_archive  # noqa: E402
from emergenzix_api.nemt_strategy.nemt_momentum_v2 import (  # noqa: E402
    compute_momentum_state,
)
from emergenzix_api.nemt_strategy.registry import data_fingerprint  # noqa: E402
from emergenzix_api.schemas import Bar  # noqa: E402
from nemt_os.services.research.complete_lifecycle import (  # noqa: E402
    LifecycleConfig,
    PLANS,
    donchian_breakout,
    run_lifecycle,
)


ZONE = ZoneInfo("Asia/Shanghai")
CAPITAL = 10_000.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(result: dict) -> dict:
    trades = result["trades"]
    r_values = [trade["r_net"] for trade in trades]
    winners = sorted(
        (trade["net_pnl"] for trade in trades if trade["net_pnl"] > 0.0),
        reverse=True,
    )
    marks = [row for row in result["ledger"] if row["event"] == "mark"]
    largest_winner = winners[0] if winners else 0.0
    return {
        "final_equity": result["final_equity"],
        "total_return_pct": result["total_return_pct"],
        "max_drawdown_pct": result["max_drawdown_pct"],
        "trade_count": len(trades),
        "average_r": statistics.mean(r_values) if r_values else 0.0,
        "median_r": statistics.median(r_values) if r_values else 0.0,
        "delete_largest_winner_return_pct": (
            (result["final_equity"] - largest_winner) / CAPITAL - 1.0
        ) * 100.0,
        "maximum_leverage": max(
            (row["leverage"] for row in marks), default=0.0
        ),
        "maximum_open_risk_pct_of_plan": max(
            (
                row["open_risk"] / row["plan_budget"] * 100.0
                for row in marks if row["plan_budget"] > 0.0
            ),
            default=0.0,
        ),
        "counters": result["counters"],
    }


def assert_audit(result: dict) -> None:
    for row in result["ledger"]:
        if row["event"] != "mark" or row["plan_budget"] <= 0.0:
            continue
        if row["open_risk"] > row["plan_budget"] + 1e-7:
            raise AssertionError("open risk exceeded frozen plan budget")
        if row["leverage"] > 3.0 + 1e-9:
            raise AssertionError("leverage exceeded frozen cap")
    if result["safety"] != {"paper": 0, "testnet": 0, "live": 0}:
        raise AssertionError("unsafe execution path detected")


def main() -> None:
    test_start = datetime(2023, 1, 1, tzinfo=ZONE)
    test_end = datetime(2024, 1, 1, tzinfo=ZONE)
    payloads = fetch_binance_spot_4h_archive(
        symbol="BTCUSDT",
        start_at=test_start.astimezone(timezone.utc) - timedelta(days=260),
        end_at=test_end.astimezone(timezone.utc) + timedelta(hours=4),
    )
    bars = [Bar.model_validate(item) for item in payloads]
    closes = [bar.close for bar in bars]
    start_index = next(
        index for index, bar in enumerate(bars)
        if bar.timestamp.astimezone(ZONE) >= test_start
    )
    end_index = next(
        index for index, bar in enumerate(bars)
        if bar.timestamp.astimezone(ZONE) >= test_end
    )

    nemt = [0] * len(bars)
    breakout = [0] * len(bars)
    for index in range(121, len(bars)):
        state = compute_momentum_state(closes[:index + 1])
        nemt[index] = (
            1 if state.phase == "critical_up"
            else -1 if state.phase == "critical_down"
            else 0
        )
        breakout[index] = donchian_breakout(bars, index, 120)
    gated = [
        direction if direction != 0 and direction == nemt[index] else 0
        for index, direction in enumerate(breakout)
    ]

    full_results: dict[str, dict] = {}
    summaries: dict[str, dict] = {}
    for doubled_costs in (False, True):
        cost_label = "base_cost" if not doubled_costs else "double_cost"
        for gate_name, directions, require_nemt in (
            ("donchian", breakout, False),
            ("donchian_nemt", gated, True),
        ):
            for plan_name, plan in PLANS.items():
                key = f"{gate_name}_{plan_name}_{cost_label}"
                result = run_lifecycle(
                    bars=bars,
                    entry_directions=directions,
                    nemt_directions=nemt,
                    plan=plan,
                    capital=CAPITAL,
                    start_index=start_index,
                    end_index=end_index,
                    config=LifecycleConfig(doubled_costs=doubled_costs),
                    require_nemt_add_confirmation=require_nemt,
                )
                assert_audit(result)
                full_results[key] = result
                summaries[key] = summarize(result)

    output = {
        "protocol": "nemt-complete-lifecycle-001",
        "protocol_sha256": sha256(PROTOCOL),
        "status": "IMPLEMENTATION_REGRESSION_ONLY",
        "selection_allowed": False,
        "market": "BTCUSDT",
        "timeframe": "4h",
        "initial_equity": CAPITAL,
        "test_start": test_start.isoformat(),
        "test_end_exclusive": test_end.isoformat(),
        "data_fingerprint": data_fingerprint(
            [bar.model_dump() for bar in bars]
        ),
        "summaries": summaries,
        "results": full_results,
        "safety": {"paper": 0, "testnet": 0, "live": 0},
    }
    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "status": output["status"],
        "protocol_sha256": output["protocol_sha256"],
        "cells": len(summaries),
        "base_cost": {
            key: {
                "final": round(value["final_equity"], 2),
                "return_pct": round(value["total_return_pct"], 3),
                "max_dd_pct": round(value["max_drawdown_pct"], 3),
                "trades": value["trade_count"],
                "adds": value["counters"]["adds"],
                "partials": value["counters"]["partials"],
            }
            for key, value in summaries.items() if key.endswith("base_cost")
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
