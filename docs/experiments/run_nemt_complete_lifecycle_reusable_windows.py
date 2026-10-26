"""Exploratory lifecycle runs on frequently reused BTC/ETH windows."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from run_nemt_complete_lifecycle_2023_regression import (
    CAPITAL,
    OUTPUT as _REGRESSION_OUTPUT,
    PROTOCOL,
    ZONE,
    Bar,
    LifecycleConfig,
    PLANS,
    assert_audit,
    compute_momentum_state,
    data_fingerprint,
    donchian_breakout,
    fetch_binance_spot_4h_archive,
    run_lifecycle,
    sha256,
    summarize,
)


del _REGRESSION_OUTPUT
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "reports" / "NEMT_COMPLETE_LIFECYCLE_REUSABLE_WINDOWS.json"
WINDOWS = (
    ("BTCUSDT", 2023),
    ("BTCUSDT", 2024),
    ("ETHUSDT", 2022),
    ("ETHUSDT", 2025),
)


def run_window(symbol: str, year: int) -> dict:
    start = datetime(year, 1, 1, tzinfo=ZONE)
    end = datetime(year + 1, 1, 1, tzinfo=ZONE)
    payloads = fetch_binance_spot_4h_archive(
        symbol=symbol,
        start_at=start.astimezone(timezone.utc) - timedelta(days=260),
        end_at=end.astimezone(timezone.utc) + timedelta(hours=4),
    )
    bars = [Bar.model_validate(item) for item in payloads]
    closes = [bar.close for bar in bars]
    start_index = next(
        index for index, bar in enumerate(bars)
        if bar.timestamp.astimezone(ZONE) >= start
    )
    end_index = next(
        index for index, bar in enumerate(bars)
        if bar.timestamp.astimezone(ZONE) >= end
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

    results: dict[str, dict] = {}
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
                results[key] = result
                summaries[key] = summarize(result)
    return {
        "symbol": symbol,
        "year": year,
        "start": start.isoformat(),
        "end_exclusive": end.isoformat(),
        "data_fingerprint": data_fingerprint(
            [bar.model_dump() for bar in bars]
        ),
        "summaries": summaries,
        "results": results,
    }


def main() -> None:
    windows = {
        f"{symbol}_{year}": run_window(symbol, year)
        for symbol, year in WINDOWS
    }
    payload = {
        "protocol": "nemt-complete-lifecycle-001",
        "protocol_sha256": sha256(PROTOCOL),
        "status": "REUSABLE_WINDOW_EXPLORATORY",
        "selection_allowed": False,
        "initial_equity": CAPITAL,
        "windows": windows,
        "safety": {"paper": 0, "testnet": 0, "live": 0},
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "status": payload["status"],
        "protocol_sha256": payload["protocol_sha256"],
        "window_count": len(windows),
        "base_cost": {
            window_key: {
                key: {
                    "final": round(value["final_equity"], 2),
                    "return_pct": round(value["total_return_pct"], 3),
                    "max_dd_pct": round(value["max_drawdown_pct"], 3),
                    "trades": value["trade_count"],
                    "adds": value["counters"]["adds"],
                    "partials": value["counters"]["partials"],
                }
                for key, value in window["summaries"].items()
                if key.endswith("base_cost")
            }
            for window_key, window in windows.items()
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
