# NEMT Strategy Asset Catalog

Updated: 2026-10-23

## Purpose

This catalog is the first screening pass over the external strategy assets in
`external/strategy-libraries`. It records what is already available before any
NEMT adapter or new strategy code is written. A listed strategy is research
material, not an approved trading system.

## Screening status

- Source repositories remain unchanged.
- Python syntax compilation passed for all Jesse and Freqtrade strategy files.
- No upstream performance claim has been independently reproduced yet.
- No strategy is approved for paper or live trading yet.
- StockSharp is catalog-only until its custom license is reviewed.

## First priority: Jesse trend and breakout strategies

### TurtleRules

Source: `external/strategy-libraries/jesse-example-strategies/TurtleRules/__init__.py`

| Field | Finding |
| --- | --- |
| Family | Trend following / Donchian breakout |
| Direction | Long and short |
| Entry | 20-period channel breakout by default; comments also describe 55-period System 2 |
| Exit | 10-period opposite channel by default |
| Volatility | ATR(20), called `N` in the Turtle rules |
| Position sizing | 1% of balance divided by ATR and dollars per point |
| Stop | Two ATR from entry |
| Scaling | Adds a unit each 0.5 ATR, nominal maximum four units |
| State required | Position direction, last added price, pyramid count and prior-trade result |
| NEMT migration difficulty | Medium |
| Decision | **Primary framework acceptance strategy, after defects are covered by tests** |

Static-review findings:

1. The strategy contains the complete shape needed to test the future NEMT contract:
   bidirectional signals, volatility sizing, protective stop, state, scaling and exits.
2. `last_was_profitable` is only set by `on_take_profit`, but this strategy does not
   define a take-profit order. The System 1 “skip after a winning trade” filter is
   therefore unlikely to work as intended.
3. Pyramid accounting depends on framework callbacks and must be tested for rejected,
   cancelled and partially filled orders.
4. The implementation does not model the original portfolio-level correlated-market
   unit limits. It is a single-strategy example, not a complete Turtle portfolio.
5. Channel calculations and decision timing must be checked bar by bar for look-ahead.

### Donchian

Source: `external/strategy-libraries/jesse-example-strategies/Donchian/__init__.py`

| Field | Finding |
| --- | --- |
| Family | Long-only trend following / channel breakout |
| Direction | Long only |
| Entry | Close above the previous Donchian upper band |
| Filter | Close above SMA(200) |
| Exit | Close below the previous Donchian lower band |
| Position sizing | Entire available balance |
| Stop | No independent protective stop |
| Tested upstream | Binance crypto examples, mostly 6-hour bars from 2019–2021 |
| NEMT migration difficulty | Low |
| Decision | **Use as the simplest signal-contract smoke test, never unchanged for live trading** |

The use of `candles[:-1]` deliberately excludes the current candle from the channel and
is a useful anti-look-ahead example. However, full-balance entry and the absence of a
protective stop make the upstream implementation unsuitable for deployment.

The included result files report attractive historical returns but also drawdowns around
33%–47% on the displayed markets. They are old, in-sample upstream artifacts and are not
accepted as NEMT evidence.

## Freqtrade inventory

The repository contains 27 direct strategy files. The first pass groups them by the
idea they can contribute, not by claimed profitability.

### Tier A — extract early

| Strategy | Family | Timeframe | Useful asset | Main caution |
| --- | --- | --- | --- | --- |
| `Strategy001` | EMA/Heikin-Ashi trend | 5m | Small, readable entry/exit contract | Long-only; exit condition needs independent review |
| `hlhb` | EMA + RSI + ADX trend | 4h | Simple multi-indicator trend confirmation | Very loose upstream stop and ROI parameters |
| `Supertrend` | Volatility-adjusted trend | 1h | Parameterized trend direction and exit | Source explicitly says indicator implementation is unvalidated |
| `Bandtastic` | Bollinger mean reversion | 15m | Multiple volatility bands plus RSI/MFI filters | Large hyperparameter space; high overfit risk |
| `multi_tf` | Multi-timeframe RSI | 5m plus informative frames | Tests multi-timeframe data contract | Requires informative-pair alignment and missing-data handling |
| `FixedRiskRewardLoss` | ATR risk/reward overlay | unspecified | Useful risk-management component | Entry is an always-buy placeholder; not a standalone strategy |

### Tier B — keep for later breadth

| Strategy | Family / use |
| --- | --- |
| `mabStra`, `MultiMa`, `PowerTower`, `UniversalMACD` | Moving-average and momentum variations |
| `Strategy002`–`Strategy005` | Composite indicator examples |
| `Heracles`, `SwingHighToSky`, `Diamond`, `GodStra` | Hyperoptimized rule combinations; useful after overfit controls exist |
| `PatternRecognition` | Daily candlestick-pattern experiment |
| `InformativeSample` | Informative-data plumbing example rather than a strategy candidate |
| `CustomStoplossWithPSAR`, `BreakEven` | Exit/risk examples rather than complete alpha strategies |
| `HourBasedStrategy` | Time/session rule example |

### Tier C — execution layer, not signal layer

| Strategy | Role | Decision |
| --- | --- | --- |
| `TWAPStrategy` | Time-sliced entry and exit execution | Preserve for future execution adapters; do not count as an alpha strategy |
| `AlmgrenChrissStrategy` | Market-impact/risk-aware execution slicing | Preserve for later order execution work; sample RSI signals are placeholders |
| `TrendRiderStrategy` | Large multi-timeframe composite | Defer until the minimal strategy contract and data alignment tests are stable |

## Proposed extraction sequence

This sequence intentionally starts with distinct levels of complexity:

1. **Donchian** — validate a minimal long/flat signal and eliminate look-ahead.
2. **TurtleRules** — validate long/short, ATR sizing, stop state and pyramiding.
3. **Strategy001** — validate a Freqtrade-style vectorized adapter.
4. **Bandtastic** — validate mean-reversion and parameter handling.
5. **multi_tf** — validate multi-timeframe data without contaminating earlier work.
6. **TWAP / Almgren-Chriss** — only after signal generation is separated from execution.

## Acceptance gates for every extracted strategy

1. License and exact upstream commit recorded.
2. Plain-language entry, exit, sizing and stop rules documented.
3. No future-candle or current-channel leakage.
4. Deterministic signal test on a small fixed candle fixture.
5. Backtest includes fees and slippage.
6. Same strategy logic can run one historical bar at a time.
7. At least one adverse test: gap, zero volume, missing bar or extreme volatility.
8. Paper-trading comparison before any live-execution consideration.

## Immediate conclusion

The repository already contains enough strategy material to stop inventing new alpha
code. The next engineering milestone should be a minimal adapter capable of running
Donchian and TurtleRules through the same NEMT backtest interface. Until that adapter
exists, collecting more framework code has lower value than cataloging and testing the
assets already present.

