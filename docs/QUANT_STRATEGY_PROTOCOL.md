# NEMT Quantitative Strategy Governance Protocol V1.0

**Status:** Normative | **Scope:** Research strategy proposals, AI publishers, reviews, PAPER runs, allocation and retirement

## 1. Principles
- Research generates hypotheses; experiments generate evidence; AI **proposes**; humans **approve**; the independent risk engine **controls execution**.
- A retained strategy is **not** an approved, running or profitable strategy.
- No strategy is presumed effective in every market regime. Dynamic switching is a new meta-strategy requiring independent validation.
- Default **PAPER ONLY**. No automatic transition to LIVE.

## 2. Artifact and provenance
Every candidate strategy version contains:
```text
strategy_id, version, hypothesis, research_id
code_repository, source_commit, artifact_sha256
markets, timeframe, parameters, execution_assumptions
dataset_ids and versions, experiment_ids
in_sample_metrics, out_of_sample_metrics, risk_metrics
fees/slippage/liquidity model, limitation notes
publisher_identity, submission_time, immutable_manifest
```
Scores or claims must link to actual experimental evidence. Treat submitted executable artifacts as untrusted until static review, signature/hash verification and isolated testing.

## 3. Controlled lifecycle
```text
DRAFT/RESEARCH
    ↓ experiments complete and evidence linked
SUBMITTED → VALIDATING → REVIEW_PENDING
                  ↘ VALIDATION_FAILED
REVIEW_PENDING → RETAINED | REJECTED
RETAINED → PAPER_ELIGIBLE (separate approval + risk checks)
PAPER_ELIGIBLE → PAPER_RUNNING (authorized start)
PAPER_RUNNING ↔ PAPER_PAUSED
PAPER_RUNNING → PAPER_STOPPED → RETIRED / ARCHIVED
```
Each transition records identity, timestamp, previous/next state, reason and strategy version. No silent edits or deleted audit history. Reject/archive is usually a soft status; physical deletion must preserve all trade, run and review references.

## 4. AI publishing and human review
- Publisher uses a dedicated least-privilege machine identity. Can submit/retrieve its own candidates but **cannot self-review, approve, deploy, change risk limits or access Binance secrets**.
- Submission API validates schema, evidence references, hashes, supported runtime interface, allowed markets/parameters, rate limits and idempotency.
- Reviewers may retain/reject with reasons. PAPER eligibility requires a separate explicit authorized decision with recorded risk budget and approved artifact.
- For unknown strategies, review no-lookahead implementation, data quality, costs, walk-forward/out-of-sample metrics, regime sensitivity, failure modes and comparison with simple baselines.

## 5. Strategy library and experiments
- Preserve all versions and experiment relationships. Do not replace old backtests after modifying strategy parameters.
- Maintain statuses such as candidate, retained, paper-eligible, running, paused, retired and archived; distinguish strategy lifecycle from individual `run_id` states.
- Candidate algorithms may come from MATLAB and/or appropriate GPU/CPU verification; GPU is not inherently mandatory.

## 6. PAPER execution and safety
- Shared market-data normalization → immutable strategy signal → independent risk check → paper matching engine → ledger → metrics.
- Assign every run a unique `run_id`, code/param/data versions and isolated paper account, unless explicitly authorized to use a shared test portfolio.
- Preserve idempotent signals/order IDs, atomic ledger entries, restart recovery, fee/slippage assumptions, stale-data blocking, exposure and loss limits, kill switch, errors and audit logs.
- Browser/UI cannot be responsible for long-running strategy execution or store exchange credentials.
- Connection to Binance real accounts, where authorized, is **read-only and separate from paper balances**. No live-order methods accessible to PAPER adapters.

## 7. Adaptive allocation / dynamic switching
- Allocator is a separately versioned strategy with documented market-regime model, feature availability, approved candidate universe, weight limits and turnover controls.
- Avoid using future prices, future regime labels or final test-period performance to choose strategy weights.
- Compare against fixed single-strategy, equal-weight and static-risk-weight baselines, including switching cost.
- Use walk-forward evaluation followed by shadow or PAPER observation. Strategy weights and regime decisions need timestamps, uncertainty, reasons and complete provenance.
- If regime confidence is low, data stale or risk service unavailable, fall back to predefined conservative/no-new-order state; never silently select a favorite strategy.

## 8. Separation of privileges and release gates
| Action | Allowed actor | Prerequisite |
| --- | --- | --- |
| Submit candidate | Authorized AI publisher/researcher | Signed-in identity, valid artifact |
| Retain/reject | Authorized human reviewer | Evidence and audit reason |
| Grant PAPER eligibility | Authorized reviewer/operator | Independent risk + evidence gate |
| Start/pause/stop PAPER | Authorized operator | Safe runtime, account isolation |
| Alter LIVE permissions/deploy | Separate explicit human approval | Dedicated security and rollout process |

No public registration by default. Backend enforces authorization independent of frontend visibility. No direct agent database writes or arbitrary uploaded code execution.

## 9. Monitoring and retirement
Persist signals, rejects, fills, position/equity snapshots, fees, drawdown, staleness, errors and strategy/allocation changes. Alert on data gaps, risk breaches and performance deterioration; use predeclared thresholds. A bad short-term return alone does not prove permanent failure, nor does a good short-term return prove validity.
Retire or pause with documented reason, preserve records, and send results back to Research and Experiments.

## 10. Micro-task implementation protocol
Separate schema → validation endpoint → human review state transition → PAPER eligibility gate → runtime attachment → audit/test into **15–30-minute micro-tasks**. Each task ends with focused tests and one commit. A broad “build strategy platform” request must be decomposed before execution.

**Related:** [SCIENTIFIC_EXPERIMENT_PROTOCOL.md](SCIENTIFIC_EXPERIMENT_PROTOCOL.md) · [ENGINEERING_PROTOCOL.md](ENGINEERING_PROTOCOL.md).
