# NEMT Engineering Development Protocol V1.0

**Status:** Normative | **Scope:** All human and AI contributors | **Owner:** NEMT maintainers

## 1. Purpose and precedence
Build NEMT through small, testable, reviewable increments; prevent unapproved scope drift and protect financial systems.

Before acting, read `AGENTS.md`, `docs/MICRO_TASK_PROTOCOL.md`, and applicable direction-lock rules. This protocol **supplements**, not overrides, stricter repository protections. If a referenced lock file is missing, report the gap instead of assuming unrestricted permissions. Access to protected paths (such as `/core`, `/database`, `/auth`) requires an explicit, separately approved scope/lock change.

## 2. Mandatory 15–30-minute micro-tasks
- One task = one narrowly defined goal, one verifiable result, one logical commit.
- Timebox is a planning target, not a reason to skip tests or rush.
- Split work exceeding 30 minutes **before** implementation; separate schema, API, runtime and UI work.
- Each task names: ID, objective, evidence/current state, allowed paths, forbidden paths, 3–5 steps, tests, acceptance criteria, stop conditions, deliverables.
- Do not start the next task automatically. Discoveries outside scope go into a follow-up backlog.
- Before edits: inspect branch, `git status`, existing tests and the real codebase. Do not assume local and GitHub versions match.

## 3. Implementation discipline
1. Choose the smallest safe edit; prefer reuse over parallel implementations.
2. Keep scientific models, exchange adapters, execution, risk, auth and UI separated.
3. Prohibit hidden network calls, silent fallback to mock results, or hardcoded return/performance data.
4. Add or adjust focused unit/integration tests for changed behavior; run only relevant checks first, expanding as risk requires.
5. Review `git diff` for unintended file changes and leaked secrets.
6. Use a descriptive Conventional Commit on an authorized working branch. No force-push and no unrelated edits.
7. Report test evidence honestly, including commands not run or environmental blockers.

## 4. Review gates
- **Documentation/UI (low risk):** scope review, relevant validation, reviewable commit.
- **Data models/API:** schema compatibility, migration plan, rollback/recovery strategy, auth tests.
- **Strategy/runtime/risk:** deterministic simulation tests, idempotency, event replay and fail-safe behavior.
- **Credentials, exchange access, production deployment:** explicit human approval and separate task; no AI self-approval.
- Every gate must preserve PAPER vs LIVE isolation, least privilege and an audit trail.

## 5. Security and deployment
- PAPER/DEMO is the default; never create Binance live orders without a separately approved workflow.
- Do not disclose API keys in source, logs, issues, screenshots, or client bundles. Use approved secret injection.
- No unauthorized IAM, network, production DB, account, balance or broker permission changes.
- Confirm target host/branch/database; back up state before approved migration; define rollback, health check and owner.
- If secrets or unsafe live-order pathways are found, stop and escalate.

## 6. Definition of Done
- Acceptance criteria proven by artifacts/test output.
- No unrelated files or unexplained dependencies; preserved baseline and backward compatibility.
- Risk and documentation implications recorded.
- Git commit SHA and branch captured, with a concise report:
```text
Task ID / Status (PASS|PARTIAL|BLOCKED|FAIL)
Actual elapsed / Files changed / Commit SHA & branch
Tests run and results / Tests not run
Scope deviations / Risks & blockers / Next one proposed task
```
- Stop and await the next instruction.

## 7. Continuous improvement
Retrospect on recurring test failures, cycle time and revert causes. Change this protocol through a dedicated documentation micro-task and review. Never weaken critical controls merely to meet a timebox.

**Canonical micro-task template:** [MICRO_TASK_PROTOCOL.md](MICRO_TASK_PROTOCOL.md).
