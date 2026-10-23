"""Execute a user strategy module's run_backtest with CSV candles.

This script is intentionally small: the Next.js API writes the imported
repository files and OHLCV CSVs into a temporary directory, then runs this
file in a separate Python process. The module must expose
``run_backtest(hourly, four_hour, config)`` and may optionally expose
``Candle`` and ``StrategyConfig`` dataclasses.
"""

from __future__ import annotations

import csv
import dataclasses
import importlib.util
import inspect
import json
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace


def load_candles(path: str, factory):
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            values = {
                "open_time": int(row["open_time"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "close_time": int(row["close_time"]),
            }
            rows.append(factory(**values) if factory else SimpleNamespace(**values))
    return rows


def encode(value):
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, (set, tuple)):
        return list(value)
    return str(value)


def main() -> None:
    entry_path, hourly_path, four_path, config_path, output_path = sys.argv[1:6]
    try:
        config_data = json.loads(Path(config_path).read_text(encoding="utf-8"))
        entry_path_obj = Path(entry_path).resolve()
        sys.path.insert(0, str(entry_path_obj.parent))
        spec = importlib.util.spec_from_file_location("nemt_user_strategy", entry_path_obj)
        if spec is None or spec.loader is None:
            raise ValueError(f"cannot import strategy file: {entry_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        candle_factory = getattr(module, "Candle", None)
        hourly = load_candles(hourly_path, candle_factory)
        four_hour = load_candles(four_path, candle_factory)

        config_class = getattr(module, "StrategyConfig", None)
        if config_class is not None:
            allowed = set(inspect.signature(config_class).parameters)
            config = config_class(**{key: value for key, value in config_data.items() if key in allowed})
        else:
            config = SimpleNamespace(**config_data)

        run_backtest = getattr(module, "run_backtest", None)
        if not callable(run_backtest):
            raise ValueError("strategy module has no callable run_backtest()")

        parameters = inspect.signature(run_backtest).parameters
        kwargs = {}
        if "hourly" in parameters:
            kwargs["hourly"] = hourly
        if "four_hour" in parameters:
            kwargs["four_hour"] = four_hour
        if "config" in parameters:
            kwargs["config"] = config
        result = run_backtest(**kwargs) if kwargs else run_backtest(hourly, four_hour, config)

        payload = {
            "ok": True,
            "summary": result.get("summary", {}),
            "trades": result.get("trades", []),
            "equity_curve": result.get("equity_curve", []),
        }
        Path(output_path).write_text(
            json.dumps(payload, default=encode, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as exc:  # noqa: BLE001 - report the user strategy's failure
        payload = {"ok": False, "error": str(exc), "traceback": traceback.format_exc()}
        Path(output_path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        sys.exit(1)


if __name__ == "__main__":
    main()
