# External Strategy Libraries

This inventory records upstream strategy repositories kept as read-only research assets.
They are not integrated into the NEMT runtime, and their presence does not mean that a
strategy has passed correctness, profitability, security, or licensing review.

All repositories were cloned with `--depth 1` on 2026-10-23 into
`external/strategy-libraries/`.

| Local directory | Upstream | Branch | Commit | Strategy inventory | License note |
| --- | --- | --- | --- | --- | --- |
| `freqtrade-strategies` | `https://github.com/freqtrade/freqtrade-strategies.git` | `main` | `f3340ce11f5bdf62f598522e64d1f5638eaa13f5` | 27 files under `user_data/strategies`; 69 Python files overall | GPL-3.0; review copyleft obligations before copying or distributing code |
| `stocksharp-algotrading` | `https://github.com/StockSharp/AlgoTrading.git` | `main` | `d841aed60dc90942783a452d8a505ee01219c418` | 3,811 numbered strategy directories; 3,815 Python files | StockSharp Custom License; treat as reference-only until a dedicated license review approves reuse |
| `jesse-example-strategies` | `https://github.com/jesse-ai/example-strategies.git` | `master` | `7c91e0a37bf62165790120d730442e4f6eb00364` | 11 top-level strategy directories, including `TurtleRules` and `Donchian` | MIT |

## Handling rules

1. Preserve each upstream repository unchanged during the collection phase.
2. Do not import a strategy into NEMT merely because it is present here.
3. Before adaptation, record the source path, upstream commit, license, expected market,
   timeframe, long/short behavior, data dependencies, and risk rules.
4. Run static review and isolated backtests before paper trading.
5. Never promote a strategy to live execution solely on an upstream backtest claim.

## Initial extraction order

1. Jesse `TurtleRules` and `Donchian` for the first end-to-end strategy-container test.
2. Freqtrade trend, breakout, and mean-reversion strategies for crypto-focused breadth.
3. StockSharp catalog discovery and taxonomy only; no code reuse before license review.

