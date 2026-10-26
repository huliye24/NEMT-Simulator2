"""Run the frozen 2023 BTC position-sizing comparison."""

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
OUTPUT = ROOT / "docs" / "reports" / "NEMT_BTCUSDT_2023_10K_POSITION_SIZING.json"
PROTOCOL = ROOT / "docs" / "experiments" / "NEMT_POSITION_SIZING_THREE_WAY_2023_FREEZE.md"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(STAGE))
os.environ["BINANCE_ARCHIVE_CACHE_DIR"] = str(CACHE)

from emergenzix_api.historical_data import fetch_binance_spot_4h_archive  # noqa: E402
from emergenzix_api.nemt_strategy.registry import data_fingerprint  # noqa: E402
from emergenzix_api.nemt_strategy.v522_ablation_cli import ARMS, run_arm  # noqa: E402
from emergenzix_api.schemas import Bar  # noqa: E402
from nemt_os.services.research.position_sizing import (  # noqa: E402
    SIZERS,
    SizingConfig,
    adaptive_drawdown_budget_kelly,
)


ZONE = ZoneInfo("Asia/Shanghai")
INITIAL_EQUITY = 10_000.0
FEE_RATE = 0.0005
LEVERAGE_CAP = 3.0
CONFIG = SizingConfig()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trade_r(trade: dict) -> float:
    stop_fraction = abs(trade["entry_price"] - trade["stop"]) / trade["entry_price"]
    net_per_notional = trade["net_pnl"] / trade["notional"]
    return net_per_notional / stop_fraction


def replay(name: str, trades: list[dict], bars: list[Bar], history: list[float]) -> dict:
    equity = INITIAL_EQUITY
    peak = equity
    maximum_drawdown = 0.0
    records = []
    risks = []

    for trade in trades:
        if name == "fixed_1pct":
            risk = 0.01
        elif name == "adaptive_drawdown_budget_kelly":
            current_drawdown = (peak - equity) / peak if peak else 0.0
            risk = adaptive_drawdown_budget_kelly(
                history, current_drawdown, CONFIG
            )
        else:
            risk = SIZERS[name](history, CONFIG)
        stop_fraction = abs(trade["entry_price"] - trade["stop"]) / trade["entry_price"]
        multiple = min(LEVERAGE_CAP, risk / stop_fraction) if risk > 0.0 else 0.0
        notional = equity * multiple
        quantity = notional / trade["entry_price"] if notional else 0.0
        entry_fee = notional * FEE_RATE

        entry_equity = equity
        for index in range(trade["entry_index"], trade["exit_index"]):
            mark = bars[index].close
            unrealized = quantity * (mark - trade["entry_price"]) * trade["direction"]
            marked_equity = equity + unrealized - entry_fee
            peak = max(peak, marked_equity)
            maximum_drawdown = max(
                maximum_drawdown, (peak - marked_equity) / peak if peak else 0.0
            )

        gross = quantity * (trade["exit_price"] - trade["entry_price"]) * trade["direction"]
        exit_fee = quantity * trade["exit_price"] * FEE_RATE
        pnl = gross - entry_fee - exit_fee
        equity += pnl
        peak = max(peak, equity)
        maximum_drawdown = max(
            maximum_drawdown, (peak - equity) / peak if peak else 0.0
        )
        realized_r = trade_r(trade)
        history.append(realized_r)
        risks.append(risk)
        records.append({
            "entry_at": trade["entry_at"],
            "exit_at": trade["exit_at"],
            "side": trade["side"],
            "risk_fraction": risk,
            "notional": notional,
            "leverage": multiple,
            "r_net": realized_r,
            "pnl": pnl,
            "equity_before": entry_equity,
            "equity_after": equity,
            "exit_reason": trade["exit_reason"],
        })

    largest_winner = max((row["pnl"] for row in records), default=0.0)
    total_return = (equity / INITIAL_EQUITY - 1.0) * 100.0
    return {
        "name": name,
        "initial_equity": INITIAL_EQUITY,
        "final_equity": equity,
        "total_return_pct": total_return,
        "max_drawdown_pct": maximum_drawdown * 100.0,
        "return_over_drawdown": (
            total_return / (maximum_drawdown * 100.0) if maximum_drawdown else None
        ),
        "trades_available": len(trades),
        "trades_participated": sum(row["risk_fraction"] > 0.0 for row in records),
        "average_risk_pct": statistics.mean(risks) * 100.0 if risks else 0.0,
        "minimum_risk_pct": min(risks) * 100.0 if risks else 0.0,
        "maximum_risk_pct": max(risks) * 100.0 if risks else 0.0,
        "delete_largest_winner_return_pct_diagnostic": (
            (equity - max(0.0, largest_winner)) / INITIAL_EQUITY - 1.0
        ) * 100.0,
        "records": records,
    }


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
        bars=bars, arm=ARMS["A"], zone=ZONE, start=train_start,
        end=test_start, capital=INITIAL_EQUITY, gate="nemt",
    )
    testing = run_arm(
        bars=bars, arm=ARMS["A"], zone=ZONE, start=test_start,
        end=test_end, capital=INITIAL_EQUITY, gate="nemt",
    )
    training_r = [trade_r(trade) for trade in training["trades"]]
    methods = ["fixed_1pct", *SIZERS]
    results = {
        method: replay(method, testing["trades"], bars, list(training_r))
        for method in methods
    }
    eligible = [value for value in results.values() if value["max_drawdown_pct"] <= 20.0]
    ranking = sorted(
        eligible,
        key=lambda value: (
            value["return_over_drawdown"] if value["return_over_drawdown"] is not None else -1e9,
            value["total_return_pct"],
        ),
        reverse=True,
    )
    payload = {
        "protocol": "nemt-position-sizing-three-way-2023-001",
        "protocol_sha256": sha256(PROTOCOL),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market": "BTCUSDT",
        "timeframe": "4h",
        "train_start": train_start.isoformat(),
        "test_start": test_start.isoformat(),
        "test_end_exclusive": test_end.isoformat(),
        "data_fingerprint": data_fingerprint([bar.model_dump() for bar in bars]),
        "training_trades": len(training["trades"]),
        "test_trades": len(testing["trades"]),
        "config": CONFIG.__dict__,
        "results": results,
        "ranking": [item["name"] for item in ranking],
        "safety": {"paper": 0, "testnet": 0, "live": 0, "telegram_signals": 0},
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
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
            }
            for key, value in results.items()
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
