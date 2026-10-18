# NEMT App V0.1 — Engineering Baseline Acceptance (issue #6)

- **Date:** 2026-10-18
- **Parent:** #5 (EPIC) · **Issue:** #6 · **Governance:** #20/#21
- **Status:** baseline hardening implemented in one scoped PR; CI is the clean
  environment used for Docker/Redis health evidence.
- **Scope authorization:** the maintainer approved the remaining baseline paths
  for this task (root Compose, `.gitignore`, `.github/`, README/docs, backend
  config/tests). `/core`, `/database`, `/auth`, `/.git`, trading/risk behavior
  and credentials were **not** modified.

## 1. Deliverables

| Item | Path | Result |
|---|---|---|
| Architecture decision | `docs/ADR-001-nemt-app-baseline.md` | Next.js baseline, DEMO/TESTNET/LIVE isolation, SQLite, Docker boundary and CI gates recorded |
| Development / deployment instructions | `README.md`, `docs/NEMT_APP_RUNBOOK.md` | Clean-clone DEMO quick start, health checks, Docker relationship, config gates |
| Configuration sample | `backend/.env.example` | Placeholders only; DEMO default; LIVE disabled; exchange placeholders empty; loopback API host/port |
| App API | `backend/trade_app/` + `backend/trade_main.py` | Existing service; mode/config and health endpoints verified |
| App tests | `backend/tests/` | Includes new `test_baseline.py` safety/health tests |
| Compose hardening | `docker-compose.yml` | Redis `127.0.0.1:6379`; Redis Commander `127.0.0.1:8081`; obsolete `version` removed |
| Compose hardening | `quant-mvp/docker-compose.yml` | Redis/Commander already bound to `127.0.0.1`; left intact |
| CI gates | `.github/workflows/nemt-app-ci.yml` | pytest + DEMO health smoke, web lint/typecheck/build, secret/config guard, baseline format check, Compose config + Redis loopback health |
| Ignore guardrails | `.gitignore` | `*.env` / `.env.*` ignored; `.env.example` retained |

## 2. Configuration and service boundaries

| Layer | Path / service | Exposure |
|---|---|---|
| App API | `backend/trade_main.py` (FastAPI/uvicorn) | `127.0.0.1:8000` by default |
| Web PWA | `web/` (Next.js 16 / React 19) | `:3000`; calls App API only |
| Persistence | `backend/.data/*.sqlite3` (SQLite, `schema_migrations` v1) | local file; no public DB service |
| Redis / collector | root `docker-compose.yml`, `quant-mvp/docker-compose.yml` | legacy/quant stack; Redis + Commander loopback only |
| Exchange adapter | `backend/trade_app/binance_spot.py` | server-only; DEMO needs no key |

Mode matrix:

| Mode | Default | Trading | Requirements |
|---|---|---|---|
| DEMO | **yes** | local simulated ledger | no exchange key, no Redis, no Docker |
| TESTNET | no | server-gated | explicit mode/flag + server-only Testnet credentials + operator passwords |
| LIVE | no | **no order path in V0.1** | separate issue #15 approval, not implemented |

`NEMT_LIVE_TRADING_ENABLED=false` is the sample/default; the code ignores LIVE
enablement for order creation and `live_trading_available` stays false.

## 3. Verification evidence (local, 2026-10-18)

Environment: Windows, Python 3.11.9, Node 24.14.0, Docker CLI 29.3.1 /
Compose v5.1.1. Docker Desktop daemon could not start on this workstation
(`Docker Desktop is unable to start`), so local runtime container health was
not claimed; the CI `compose` job performs the clean Redis health check.

| Check | Command | Result |
|---|---|---|
| Backend tests | `cd backend && python -m pytest -q` | **23 passed** (includes 3 new baseline tests) |
| New baseline tests | `python -m pytest tests/test_baseline.py -q` | **3 passed** |
| Baseline format | `ruff format --check backend/trade_app/config.py backend/trade_main.py backend/tests/test_baseline.py` | **3 files already formatted** |
| DEMO API health | `curl http://127.0.0.1:8011/api/v1/health` | `{"status":"ok","mode":"DEMO",...}` |
| DEMO readiness | `curl http://127.0.0.1:8011/api/v1/health/ready` | `{"status":"ready","database":"ok","market_source":"demo","trading_enabled":true}` |
| Root Compose config | `docker compose -f docker-compose.yml --profile quant --profile full --profile tools --profile web config -q` | exit 0 |
| Quant Compose config | `docker compose -f quant-mvp/docker-compose.yml --profile tools --profile backtest config -q` | exit 0 |
| Port bindings | effective Compose config | Redis `host_ip=127.0.0.1`, port 6379; Commander `host_ip=127.0.0.1`, port 8081 |
| Web lint/typecheck/build | `npm ci && npm run lint && npx tsc --noEmit && npm run build` | exit 0; 0 lint errors (12 pre-existing warnings) |
| Redis runtime health | CI `Compose config and Redis loopback health` | checked in the clean CI environment; see PR checks |

## 4. CI gates

The workflow runs on push and pull request:

1. **Backend tests (DEMO, no secrets)** — pytest, then starts
   `backend/trade_main.py` and asserts `/api/v1/health` and
   `/api/v1/health/ready`.
2. **Web lint, typecheck, build** — `npm ci` from `web/package-lock.json`.
3. **Python format check (baseline)** — Ruff `0.6.9` on the baseline config,
   entry point and baseline tests. Legacy app modules are formatted in #14.
4. **Compose config and Redis loopback health** — validates both Compose
   projects, starts root Redis, asserts healthy, `127.0.0.1:6379`, and
   `redis-cli ping`.
5. **New-source secret guard + baseline configuration defaults** — no obvious
   app-source secrets; DEMO default; LIVE=false; exchange placeholders empty.

The external Cloudflare Workers build check is pre-existing and can fail
independently of this PR; it is not part of the NEMT App CI matrix.

## 5. Known follow-ups

- App container stack (Dockerfiles/Compose for API + web), PostgreSQL/Alembic
  migration, hosted staging deployment and backup drills: issue #14.
- Testnet order/partial-fill/reconciliation evidence: issues #10/#13.
- Real-money enablement: issue #15, separate approval; do not enable from this
  baseline.
- Historical COS/SSH credential rotation and any Git-history remediation:
  issue #18, separate approval; this PR reads no credential contents and
  rewrites no history.
- Full-backend Ruff formatting is intentionally deferred; the CI format gate
  currently covers the baseline files only.
- MATLAB/NEMT research code (`matlab/`, root `nemt_*.py`) was not moved or
  modified; no directory migration was performed.
