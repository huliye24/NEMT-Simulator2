"""Run independent monthly NEMT v4 backtests for regime research."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Iterator


VARIANTS = ("v4a", "v4b", "v4c", "v41", "v42", "v43")


def iter_months(start: date, end_exclusive: date) -> Iterator[tuple[date, date]]:
    """Yield consecutive calendar-month boundaries."""
    current = start
    while current < end_exclusive:
        following = date(current.year + 1, 1, 1) if current.month == 12 else date(
            current.year, current.month + 1, 1
        )
        yield current, min(following, end_exclusive)
        current = following


def run_monthly_matrix(
    *, python: Path, runner: Path, start: date, end_exclusive: date,
    capital: float = 100.0, workers: int = 4,
) -> list[dict[str, object]]:
    """Run each v4 variant for every complete calendar month."""
    tasks = [
        (month_start, month_end, variant)
        for month_start, month_end in iter_months(start, end_exclusive)
        for variant in VARIANTS
    ]

    def execute(task: tuple[date, date, str]) -> dict[str, object]:
        month_start, month_end, variant = task
        process = subprocess.run(
            [
                str(python), str(runner), "--start", month_start.isoformat(),
                "--end", month_end.isoformat(), "--capital", str(capital),
                "--variant", variant,
            ],
            cwd=runner.parent.parent,
            capture_output=True,
            check=False,
            text=True,
        )
        output = process.stdout if process.stdout else process.stderr
        return {
            "start": month_start.isoformat(), "end": month_end.isoformat(),
            "variant": variant, "returncode": process.returncode,
            "last_output_line": output.splitlines()[-1] if output else "",
        }

    results: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(execute, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            completed = len(results)
            if completed % 12 == 0 or completed == len(tasks):
                failures = sum(item["returncode"] != 0 for item in results)
                print(json.dumps({"completed": completed, "total": len(tasks),
                                  "failures": failures}), flush=True)
    return sorted(results, key=lambda item: (item["start"], item["variant"]))


def main() -> None:
    """Run the monthly matrix from command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--runner", required=True, type=Path)
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2026-10-01")
    parser.add_argument("--capital", default=100.0, type=float)
    parser.add_argument("--workers", default=4, type=int)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    results = run_monthly_matrix(
        python=args.python,
        runner=args.runner,
        start=date.fromisoformat(args.start),
        end_exclusive=date.fromisoformat(args.end),
        capital=args.capital,
        workers=args.workers,
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    failures = [item for item in results if item["returncode"] != 0]
    print(json.dumps({"runs": len(results), "failures": failures}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
