# NEMT Scientific Experiment Protocol V1.0

**Status:** Normative | **Scope:** MATLAB, Python, CPU/GPU experiments, backtests and simulation research

## 1. Scientific principle
A research claim must be traceable from a hypothesis through data, code, parameters, execution environment, metrics and reproducible artifacts. **A faster GPU experiment is not automatically a better or more valid experiment.** No fabricated numbers or retroactive rewriting of results.

## 2. Experiment lifecycle
`QUESTION → HYPOTHESIS → PROTOCOL → DATASET LOCK → RUN → VALIDATE → REPORT → REPLICATE / REVISE`

- Register a unique `research_id` and `experiment_id` before execution.
- State null/alternative hypotheses, target market, timeframe, outcome metrics and failure criteria **before** inspecting evaluation results.
- Define baseline(s), control comparisons, and a fixed training/validation/test split. Use chronological splits for market data.
- Record whether work is exploratory or confirmatory; do not relabel exploratory findings as preregistered confirmation.
- MATLAB and GPU runs are separate compute methods; assign hardware by demonstrated need, not ceremony.

## 3. Dataset governance
For each dataset record: source/licence, symbol, market type, timezone UTC, acquisition time, event-time field, interval/granularity, raw/adjusted flag, missing/duplicate/outlier policy, and immutable dataset version/checksum.
- Enforce no future leakage, survivorship or look-ahead bias; log corporate actions or exchange-specific adjustments where relevant.
- For live feeds, preserve event time and receipt time, gaps, reconnections, market-data staleness and provenance.
- Never overwrite raw source files. Derived datasets reference raw hashes and transformation code/versions.
- Distinguish real market data from synthetic/test fixtures visibly.

## 4. Minimal immutable experiment manifest
Store the manifest alongside all outputs, e.g.:
```json
{
  "schema_version": "1.0",
  "research_id": "R-001",
  "experiment_id": "EXP-001",
  "hypothesis": "predeclared falsifiable claim",
  "run_type": "backtest",
  "source_commit": "<git_sha>",
  "code_artifact_sha256": "<hash>",
  "dataset_id": "BTCUSDT-1m",
  "dataset_version": "<immutable_version>",
  "dataset_sha256": "<hash>",
  "time_range_utc": {"start": "<ISO8601>", "end": "<ISO8601>"},
  "split_definition": "<chronological split policy>",
  "parameters": {},
  "random_seed": 42,
  "engine": {"name": "MATLAB", "version": "<version>"},
  "compute": {"provider": "AWS", "instance_type": "<type>", "gpu_model": null},
  "cost_model": {"fee_bps": null, "slippage_model": "<version>"},
  "started_at": "<ISO8601>",
  "completed_at": "<ISO8601>",
  "status": "COMPLETED",
  "artifacts": []
}
```
Placeholder values must be replaced by genuine run metadata. Record MATLAB toolboxes or Python packages, CUDA/driver versions when used, container/image digest, OS, GPU determinism constraints and hardware availability.

## 5. Execution and evidence
- Run with pinned parameters, dependencies and datasets; store stdout/stderr logs, machine-readable metrics, charts and a human-readable conclusion.
- Recommended artifact layout:
```text
experiments/{experiment_id}/
  manifest.json
  parameters.json
  metrics.json
  report.md
  logs/
  plots/
  artifacts.sha256
```
- Store large artifacts in permission-controlled S3 or existing storage; Git contains code/schema/docs and immutable artifact references, not large datasets or secrets.
- Job states: `QUEUED / RUNNING / COMPLETED / FAILED / CANCELLED`. Failures must retain diagnostic logs.
- Compare CPU/GPU results with tolerance and numerics noted; nondeterministic operations require repeated runs and variation reporting, not claimed bit-for-bit equivalence.

## 6. Quantitative validation
- Define metrics in advance (returns, drawdown, risk-adjusted performance, turnover, order/fill error and stability as relevant).
- Apply transaction fees, realistic slippage, execution latency, liquidity/volume constraints and funding where applicable; never report frictionless PnL as realized results.
- Use out-of-sample and walk-forward validation; prevent parameter selection on final holdout.
- Record multiple-testing/selection bias, confidence intervals or uncertainty where credible; report negative results and regime sensitivity.
- Separate historical backtest, replay, shadow live feed, paper trading and real executions as distinct evidence classes.

## 7. Acceptance and publication
Review checklist:
- [ ] Hypothesis and acceptance criteria predeclared
- [ ] Dataset identity/version/hash and split documented
- [ ] Code and configuration pinned; run logs retained
- [ ] Environment and random seeds recorded
- [ ] Metrics with costs, uncertainty and baseline comparisons
- [ ] Artifacts checksummed and accessible to authorized reviewers
- [ ] Re-run or clear reason reproduction was not possible
- [ ] Conclusion distinguishes observations from interpretations
Only validated evidence may support a strategy recommendation; experiment completion does not grant execution approval.

## 8. Micro-task rhythm
Work in 15–30-minute tasks: manifest schema → dataset validator → local deterministic smoke run → artifact upload → metric checker → replication report. One task, one testable result, one commit; stop after each review gate.

**Related:** [ENGINEERING_PROTOCOL.md](ENGINEERING_PROTOCOL.md) · [QUANT_STRATEGY_PROTOCOL.md](QUANT_STRATEGY_PROTOCOL.md).
