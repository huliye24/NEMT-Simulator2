"""Run the frozen iterative V2 position-sizing comparison for BTC 2023."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from run_nemt_position_sizing_three_way_2023 import (
    ARMS,
    CONFIG,
    INITIAL_EQUITY,
    ZONE,
    Bar,
    data_fingerprint,
    fetch_binance_spot_4h_archive,
    replay,
    run_arm,
    trade_r,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "reports" / "NEMT_BTCUSDT_2023_10K_POSITION_SIZING_V2.json"
PROTOCOL = ROOT / "docs" / "experiments" / "NEMT_POSITION_SIZING_V2_2023_FREEZE.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    train_start = datetime(2019, 1, 1, tzinfo=ZONE)
    test_start = datetime(2023, 1, 1, tzinfo=ZONE)
    test_end = datetime(2024, 1, 1, tzinfo=ZONE)
    payloads = fetch_binance_spot_4h_archive(
        symbol="BTCUSDT",
        start_at=train_start.astimezone(timezone.utc) - timedelta(days=260),
        end_at=test_end.astimezone(timezone.utc) + timedelta(hours=4),
    )
    bars = [Bar.model_validate(item) for item in payloads]
    training = run_arm(
        bars=bars,
        arm=ARMS["A"],
        zone=ZONE,
        start=train_start,
        end=test_start,
        capital=INITIAL_EQUITY,
        gate="nemt",
    )
    testing = run_arm(
        bars=bars,
        arm=ARMS["A"],
        zone=ZONE,
        start=test_start,
        end=test_end,
        capital=INITIAL_EQUITY,
        gate="nemt",
    )
    training_r = [trade_r(trade) for trade in training["trades"]]
    methods = [
        "fixed_1pct",
        "shrinkage_fractional_kelly",
        "distributionally_robust_kelly",
        "risk_constrained_kelly",
        "adaptive_drawdown_budget_kelly",
    ]
    results = {
        method: replay(method, testing["trades"], bars, list(training_r))
        for method in methods
    }
    eligible = [
        value for value in results.values()
        if value["max_drawdown_pct"] <= 20.0
    ]
    ranking = sorted(
        eligible,
        key=lambda value: (
            value["return_over_drawdown"]
            if value["return_over_drawdown"] is not None else -1e9,
            value["total_return_pct"],
        ),
        reverse=True,
    )
    payload = {
        "protocol": "nemt-position-sizing-v2-2023-001",
        "evidence": "ITERATIVE_EXPLORATORY",
        "protocol_sha256": sha256(PROTOCOL),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market": "BTCUSDT",
        "timeframe": "4h",
        "train_start": train_start.isoformat(),
        "test_start": test_start.isoformat(),
        "test_end_exclusive": test_end.isoformat(),
        "data_fingerprint": data_fingerprint(
            [bar.model_dump() for bar in bars]
        ),
        "training_trades": len(training["trades"]),
        "test_trades": len(testing["trades"]),
        "config": CONFIG.__dict__,
        "results": results,
        "ranking": [item["name"] for item in ranking],
        "safety": {
            "paper": 0,
            "testnet": 0,
            "live": 0,
            "telegram_signals": 0,
        },
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "status": "OK",
        "training_trades": len(training["trades"]),
        "test_trades": len(testing["trades"]),
        "ranking": payload["ranking"],
        "summary": {
            key: {
                "final": round(value["final_equity"], 2),
                "return_pct": round(value["total_return_pct"], 3),
                "max_dd_pct": round(value["max_drawdown_pct"], 3),
                "avg_risk_pct": round(value["average_risk_pct"], 3),
                "min_risk_pct": round(value["minimum_risk_pct"], 3),
                "max_risk_pct": round(value["maximum_risk_pct"], 3),
            }
            for key, value in results.items()
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
