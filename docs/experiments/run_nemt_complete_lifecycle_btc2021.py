"""Exploratory BTCUSDT 2021 lifecycle run with 10,000 USDT capital."""

from __future__ import annotations

import json
from pathlib import Path

from run_nemt_complete_lifecycle_reusable_windows import (
    PROTOCOL,
    run_window,
    sha256,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "reports" / "NEMT_COMPLETE_LIFECYCLE_BTC2021_10K.json"


def main() -> None:
    window = run_window("BTCUSDT", 2021)
    payload = {
        "protocol": "nemt-complete-lifecycle-001",
        "protocol_sha256": sha256(PROTOCOL),
        "status": "REUSABLE_WINDOW_EXPLORATORY",
        "selection_allowed": False,
        "initial_equity": 10_000.0,
        "window": window,
        "safety": {"paper": 0, "testnet": 0, "live": 0},
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "status": payload["status"],
        "protocol_sha256": payload["protocol_sha256"],
        "base_cost": {
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
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
