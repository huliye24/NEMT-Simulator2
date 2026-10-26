"""Execute the frozen NEMT three-arm cross-asset protocol.

This is an orchestration-only research script. It imports the frozen strategy
implementation by hash, changes no trading rule, and creates no order.
"""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / ".artifacts" / "multi" / "stage" / "backend"
CACHE = ROOT / ".artifacts" / "binance-cache"
OUTPUT = ROOT / "docs" / "reports" / "NEMT_THREE_ARM_CROSS_ASSET_20261026.json"
PROTOCOL = ROOT / "docs" / "experiments" / "NEMT_THREE_ARM_CROSS_ASSET_FREEZE_20261026.md"

sys.path.insert(0, str(STAGE))
os.environ["BINANCE_ARCHIVE_CACHE_DIR"] = str(CACHE)

from emergenzix_api.historical_data import fetch_binance_spot_4h_archive  # noqa: E402
from emergenzix_api.nemt_strategy.registry import data_fingerprint  # noqa: E402
from emergenzix_api.nemt_strategy.v522_ablation_cli import (  # noqa: E402
    ARMS,
    run_arm,
)
from emergenzix_api.nemt_strategy.v526_incremental_information_cli import (  # noqa: E402
    delta_r,
)
from emergenzix_api.nemt_strategy.v527_entropy_cli import (  # noqa: E402
    build_psi_ledger,
    dedupe_events,
    delta_s,
    synthetic_validation,
)
from emergenzix_api.schemas import Bar  # noqa: E402


CELLS = (
    ("ETHUSDT", "2021-01-01", "2022-01-01", "PRIMARY"),
    ("ETHUSDT", "2023-01-01", "2024-01-01", "PRIMARY"),
    ("ETHUSDT", "2025-01-01", "2026-01-01", "PRIMARY"),
    ("BNBUSDT", "2022-01-01", "2023-01-01", "SECONDARY"),
    ("BNBUSDT", "2024-01-01", "2025-01-01", "SECONDARY"),
    ("SOLUSDT", "2022-01-01", "2023-01-01", "SECONDARY"),
    ("SOLUSDT", "2024-01-01", "2025-01-01", "SECONDARY"),
    ("XRPUSDT", "2022-01-01", "2023-01-01", "SECONDARY"),
    ("XRPUSDT", "2024-01-01", "2025-01-01", "SECONDARY"),
)
GATES = ("none", "psi", "nemt")
FEE_BPS = (2.0, 5.0, 10.0)
SLIPPAGE_BPS = (2.0, 5.0, 10.0)
CAPITAL = 100.0
BOOTSTRAP_ROUNDS = 2000
ZONE = ZoneInfo("Asia/Shanghai")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def enrich_arm(report: dict) -> dict:
    trades = report["trades"]
    r_values = [
        trade["net_pnl"] / trade["initial_risk_usdt"]
        for trade in trades
        if trade["initial_risk_usdt"] > 0
    ]
    largest_winner = max((trade["net_pnl"] for trade in trades), default=0.0)
    metrics = dict(report["metrics"])
    metrics["median_r_multiple"] = statistics.median(r_values) if r_values else None
    metrics["delete_largest_winner_return_pct_diagnostic"] = (
        (metrics["final_equity"] - max(0.0, largest_winner)) / CAPITAL - 1.0
    ) * 100.0
    return {
        "metrics": metrics,
        "counters": report["counters"],
        "exit_reasons": dict(Counter(t["exit_reason"] for t in trades)),
        "trades": trades,
        "equity_curve": report["equity_curve"],
    }


def cost_grid(bars: list[Bar], start: datetime, end: datetime, gate: str) -> list[dict]:
    rows = []
    for fee_bps in FEE_BPS:
        for slippage_bps in SLIPPAGE_BPS:
            result = run_arm(
                bars=bars,
                arm=ARMS["A"],
                zone=ZONE,
                start=start,
                end=end,
                capital=CAPITAL,
                fee_rate=fee_bps / 10_000.0,
                slippage_rate=slippage_bps / 10_000.0,
                gate=gate,
            )
            rows.append(
                {
                    "fee_bps_each_side": fee_bps,
                    "slippage_bps_each_side": slippage_bps,
                    "total_return_pct": result["metrics"]["total_return_pct"],
                    "max_drawdown_pct": result["metrics"]["max_drawdown_pct"],
                    "trades": result["metrics"]["trades"],
                }
            )
    return rows


def run_cell(symbol: str, start_text: str, end_text: str, tier: str) -> dict:
    start = datetime.strptime(start_text, "%Y-%m-%d").replace(tzinfo=ZONE)
    end = datetime.strptime(end_text, "%Y-%m-%d").replace(tzinfo=ZONE)
    warmup = start.astimezone(timezone.utc) - timedelta(days=260)
    payloads = fetch_binance_spot_4h_archive(
        symbol=symbol,
        start_at=warmup,
        end_at=end.astimezone(timezone.utc) + timedelta(hours=4),
    )
    bars = [Bar.model_validate(item) for item in payloads]
    in_window = [bar for bar in bars if start <= bar.timestamp.astimezone(ZONE) < end]
    expected = int((end - start).total_seconds() // (4 * 3600))
    if len(in_window) != expected:
        return {
            "cell": f"{symbol}-{start.year}",
            "symbol": symbol,
            "tier": tier,
            "status": "DATA_UNAVAILABLE",
            "reason": f"expected {expected} bars, got {len(in_window)}",
        }

    arms = {}
    stress = {}
    for gate in GATES:
        arms[gate] = enrich_arm(
            run_arm(
                bars=bars,
                arm=ARMS["A"],
                zone=ZONE,
                start=start,
                end=end,
                capital=CAPITAL,
                gate=gate,
            )
        )
        stress[gate] = cost_grid(bars, start, end, gate)

    events = build_psi_ledger(bars=bars, zone=ZONE, start=start, end=end)
    psi_events = []
    cell_id = f"{symbol}-{start.year}"
    for event in events:
        copied = dict(event)
        copied["g"] = copied["m"]
        copied["month"] = f"{cell_id}-{copied['month']}"
        psi_events.append(copied)
    entropy_candidates = [dict(event) for event in events if event["m"] == 1]
    for event in entropy_candidates:
        event["month"] = f"{cell_id}-{event['month']}"

    return {
        "cell": cell_id,
        "symbol": symbol,
        "tier": tier,
        "start_local": start.isoformat(),
        "end_local_exclusive": end.isoformat(),
        "status": "OK",
        "bars_in_window": len(in_window),
        "data_fingerprint": data_fingerprint([bar.model_dump() for bar in bars]),
        "arms": arms,
        "cost_stress": stress,
        "event_tests": {
            "psi_raw": delta_r(psi_events, bootstrap_rounds=BOOTSTRAP_ROUNDS),
            "psi_deduped": delta_r(
                dedupe_events(psi_events), bootstrap_rounds=BOOTSTRAP_ROUNDS
            ),
            "entropy_raw": delta_s(events, bootstrap_rounds=BOOTSTRAP_ROUNDS),
            "entropy_deduped": delta_s(
                dedupe_events(entropy_candidates), bootstrap_rounds=BOOTSTRAP_ROUNDS
            ),
        },
        "events": events,
    }


def pooled_tests(cells: list[dict]) -> dict:
    all_events = []
    for cell in cells:
        if cell.get("status") != "OK":
            continue
        for event in cell["events"]:
            copied = dict(event)
            copied["month"] = f"{cell['cell']}-{copied['month']}"
            copied["g"] = copied["m"]
            all_events.append(copied)
    entropy_candidates = [event for event in all_events if event["m"] == 1]
    return {
        "psi_raw": delta_r(all_events, bootstrap_rounds=BOOTSTRAP_ROUNDS),
        "psi_deduped": delta_r(
            dedupe_events(all_events), bootstrap_rounds=BOOTSTRAP_ROUNDS
        ),
        "entropy_raw": delta_s(all_events, bootstrap_rounds=BOOTSTRAP_ROUNDS),
        "entropy_deduped": delta_s(
            dedupe_events(entropy_candidates), bootstrap_rounds=BOOTSTRAP_ROUNDS
        ),
    }


def main() -> None:
    validations = synthetic_validation()
    if any(not check["passed"] for check in validations):
        raise SystemExit("Synthetic validation failed; results remain sealed")

    results = []
    for symbol, start, end, tier in CELLS:
        print(f"RUN {symbol} {start} {end}", flush=True)
        try:
            results.append(run_cell(symbol, start, end, tier))
        except Exception as exc:  # Preserve the complete preregistered matrix.
            results.append(
                {
                    "cell": f"{symbol}-{start[:4]}",
                    "symbol": symbol,
                    "tier": tier,
                    "status": "DATA_UNAVAILABLE",
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            )

    payload = {
        "protocol": "nemt-three-arm-cross-asset-001",
        "protocol_sha256": sha256(PROTOCOL),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "capital": CAPITAL,
        "arms": {"A": "none", "B": "psi", "C": "nemt"},
        "cost_grid_bps_each_side": {
            "fee": FEE_BPS,
            "slippage": SLIPPAGE_BPS,
        },
        "synthetic_validation": validations,
        "cells": results,
        "pooled_event_tests": pooled_tests(results),
        "safety": {
            "paper_orders": 0,
            "testnet_orders": 0,
            "live_orders": 0,
            "telegram_open_signals": 0,
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "OK", "output": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
