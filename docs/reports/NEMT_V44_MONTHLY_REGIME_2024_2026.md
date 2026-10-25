# NEMT v4.4 monthly regime matrix and walk-forward router

- Complete months: 2024-01 to 2026-09 (33 months)
- Walk-forward warmup: 8 months
- Walk-forward evaluation: 25 months
- Router compounded return: +284.13%
- Router month-end maximum drawdown: 13.05%
- No binary pass/fail label and no win-rate threshold

## Market regime x strategy evidence

| Regime | Variant | Months | Average return | Median return | Positive months | Average drawdown | Average expectancy |
|---|---|---:|---:|---:|---:|---:|---:|
| calibration | v41 | 8 | +3.74% | +0.92% | 62% | 10.65% | +0.468R |
| calibration | v42 | 8 | +2.00% | -0.18% | 50% | 10.25% | +0.360R |
| calibration | v43 | 8 | +2.00% | -0.18% | 50% | 10.25% | +0.360R |
| calibration | v4a | 8 | +9.83% | +4.69% | 62% | 11.90% | +1.033R |
| calibration | v4b | 8 | +10.03% | +4.67% | 62% | 11.57% | +1.047R |
| calibration | v4c | 8 | +1.50% | -1.32% | 50% | 9.98% | +0.345R |
| range | v41 | 10 | +4.43% | +0.74% | 50% | 8.49% | +0.966R |
| range | v42 | 10 | +2.79% | +0.60% | 50% | 8.06% | +0.780R |
| range | v43 | 10 | +2.79% | +0.60% | 50% | 8.06% | +0.780R |
| range | v4a | 10 | +10.95% | +4.08% | 60% | 9.11% | +1.634R |
| range | v4b | 10 | +9.97% | +4.08% | 60% | 9.07% | +1.328R |
| range | v4c | 10 | +3.24% | +0.27% | 50% | 7.76% | +0.610R |
| strong_trend | v41 | 3 | +3.58% | +7.51% | 67% | 12.22% | +0.381R |
| strong_trend | v42 | 3 | -0.68% | -3.86% | 33% | 11.12% | +0.145R |
| strong_trend | v43 | 3 | -0.68% | -3.86% | 33% | 11.12% | +0.145R |
| strong_trend | v4a | 3 | +3.52% | +3.83% | 67% | 13.12% | +0.314R |
| strong_trend | v4b | 3 | +5.40% | +3.83% | 67% | 12.82% | +0.570R |
| strong_trend | v4c | 3 | -0.28% | -3.51% | 33% | 10.88% | +0.179R |
| turbulent | v41 | 3 | +2.30% | -7.52% | 33% | 9.34% | -0.116R |
| turbulent | v42 | 3 | -2.08% | -7.52% | 33% | 9.16% | -0.315R |
| turbulent | v43 | 3 | -2.08% | -7.52% | 33% | 9.16% | -0.315R |
| turbulent | v4a | 3 | +5.07% | -7.12% | 33% | 9.90% | +0.153R |
| turbulent | v4b | 3 | +5.07% | -7.12% | 33% | 9.90% | +0.153R |
| turbulent | v4c | 3 | -0.26% | -7.12% | 33% | 8.79% | -0.157R |
| weak_trend | v41 | 9 | +1.50% | -0.72% | 44% | 9.39% | +0.293R |
| weak_trend | v42 | 9 | -0.04% | -1.17% | 44% | 9.05% | +0.188R |
| weak_trend | v43 | 9 | -0.04% | -1.17% | 44% | 9.05% | +0.188R |
| weak_trend | v4a | 9 | +2.33% | +3.00% | 56% | 9.28% | +0.529R |
| weak_trend | v4b | 9 | +3.16% | +6.65% | 56% | 9.36% | +0.720R |
| weak_trend | v4c | 9 | -0.00% | -0.37% | 44% | 8.90% | +0.434R |

## Expanding-window router decisions

Each row was selected using only earlier months.

| Month | Pre-month regime | Selected | Estimated utility | Realized return | Realized drawdown |
|---|---|---|---:|---:|---:|
| 2024-09 | range | v4b | +1.47 | -4.37% | 6.42% |
| 2024-10 | range | v4b | -0.55 | +22.81% | 11.04% |
| 2024-11 | range | v4b | +2.97 | +25.37% | 7.90% |
| 2024-12 | strong_trend | v4b | -2.74 | -0.55% | 12.01% |
| 2025-01 | weak_trend | v4b | -2.21 | +6.65% | 8.48% |
| 2025-02 | weak_trend | v4b | -2.36 | +11.43% | 13.70% |
| 2025-03 | range | v4b | -0.80 | -2.01% | 12.42% |
| 2025-04 | range | v4b | +2.84 | -2.94% | 10.96% |
| 2025-05 | range | v4b | +0.58 | +2.12% | 12.61% |
| 2025-06 | weak_trend | v4a | +0.22 | -5.56% | 10.60% |
| 2025-07 | weak_trend | v4b | +5.97 | +14.42% | 8.08% |
| 2025-08 | weak_trend | v4b | +3.95 | -6.39% | 11.94% |
| 2025-09 | turbulent | v4b | +2.14 | -7.12% | 7.12% |
| 2025-10 | range | v4a | +1.52 | +11.06% | 11.12% |
| 2025-11 | turbulent | v4b | -0.10 | +33.67% | 9.87% |
| 2025-12 | weak_trend | v4b | +7.62 | -11.93% | 14.23% |
| 2026-01 | strong_trend | v4b | +3.35 | +12.93% | 8.01% |
| 2026-02 | strong_trend | v4a | +5.02 | +3.83% | 18.45% |
| 2026-03 | weak_trend | v4b | +6.06 | +13.85% | 4.16% |
| 2026-04 | weak_trend | v4b | -0.27 | -7.72% | 9.11% |
| 2026-05 | range | v4a | +0.13 | -2.14% | 4.79% |
| 2026-06 | range | v4b | -0.23 | +43.81% | 8.94% |
| 2026-07 | turbulent | v4b | +6.43 | -11.34% | 12.70% |
| 2026-08 | weak_trend | v4a | +3.03 | +13.55% | 4.06% |
| 2026-09 | range | v4a | +0.12 | +6.04% | 4.49% |

## Always-one-variant benchmarks over the same evaluation months

| Variant | Compounded return | Month-end max drawdown |
|---|---:|---:|
| v4a | +263.30% | 13.05% |
| v4b | +284.60% | 13.05% |
| v4c | +23.05% | 26.13% |
| v41 | +79.71% | 29.12% |
| v42 | +9.64% | 31.07% |
| v43 | +9.64% | 31.07% |

## Limitations

- Independent monthly runs close positions at month boundaries.
- Funding, liquidation tiers and order-book depth are not modeled.
- Regime thresholds are hypotheses and are not tuned on future months.
- Month-end drawdown can understate intramonth portfolio drawdown.
