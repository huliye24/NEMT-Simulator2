# ADR-001 — NEMT App V0.1 engineering baseline

- **Status:** Accepted for V0.1 development
- **Date:** 2026-10-17
- **Issues:** #5 (EPIC), #6 (baseline), #7 (cloud API), #12 (mobile PWA)
- **Owner:** huliye24

## Context

The EPIC describes extending a React 18 + Vite frontend and a Go collector.
The working `feature/mcp-quant-sync` branch has since moved `web/` to
Next.js 16 / React 19 (App Router, Tailwind v4) and already contains the
NEMT research dashboard, AI Council and an early Binance execution layer.
`backend/` also contains the research NEMT Engine API and prototype trading
classes. There is a second, stale full clone at `NEMT-Simulator2/` (pinned as
a gitlink) and a tracked `web/node_modules` directory from earlier work.

The app must ship a safe mobile terminal without destabilising the research
code or silently reusing unvalidated prototypes as production controls.

## Decisions

1. **Keep the existing Next.js app and add `/trade`.**
   The EPIC's "React + TypeScript + Vite" wording is implemented as the
   technically equivalent current stack: React 19 + TypeScript 5 in the
   existing App Router. Reverting to Vite would discard working UI, tests and
   routing. `/trade` is a self-contained mobile-first PWA shell; the existing
   dashboard, market, analysis and simulation pages remain untouched.
   PWA manifest, icons and a conservative service worker are added. Native
   Capacitor wrapping remains a later, separate decision.

2. **Separate the app API from the research engine.**
   The new service lives in `backend/trade_app/` with its own entry point
   (`backend/trade_main.py`), config and database. `backend/main.py` and
   `nemt_adapter` remain the research API. Sharing a process would couple
   order execution to numpy/pandas and NEMT engine imports, increasing
   blast radius and violating the "research is not an order-path control"
   boundary.

3. **DEMO is the default and is fully simulated.**
   DEMO uses an isolated SQLite ledger (`backend/.data/nemt_app.sqlite3`)
   with seeded demo users and balances. It fetches real public Binance
   market data when the network allows (source is always shown) and falls
   back to deterministic simulated data. DEMO orders never reach an exchange.

4. **TESTNET is server-gated, LIVE write is absent.**
   A TESTNET order can only be created when `NEMT_APP_MODE=TESTNET`,
   `NEMT_ALLOW_TESTNET_TRADING=true`, and credentials are present only in the
   server environment. `NEMT_LIVE_TRADING_ENABLED` exists but V0.1 has no
   executable LIVE order path; real-money trading requires the independent
   issue #15 approval. The frontend cannot grant capabilities.

5. **SQLite is the local/demo persistence baseline.**
   Money is stored as decimal TEXT, not float. Orders, confirmations, fills,
   audit events, risk flags and demo wallets have uniqueness constraints and
   transactions. Production/Testnet staging should migrate the repository
   layer to private PostgreSQL with backup/restore drills before onboarding
   users; no public database/Redis port is permitted.

6. **Redis exposure is fixed now.**
   `quant-mvp/docker-compose.yml` binds Redis and Redis Commander to
   `127.0.0.1` only.

## Consequences

- The PWA and API can be developed and demonstrated on a real phone without
  any exchange keys.
- Issue #12's routes and acceptance criteria apply; the implementation is
  Next.js rather than Vite and this ADR is the required technical-equivalent
  record.
- Testnet acceptance, User Data Stream reconciliation, partial-fill demo
  matching, MFA/passkey re-authentication, PostgreSQL migration and CI
  deployment remain follow-up work under #10, #13, #14 and #15.
- The stale nested clone and tracked `node_modules` are called out for a
  separate, approved cleanup; this ADR does not delete them.

## Security notes

- Exchange keys are read only from server environment variables; no key is
  ever returned by the API or placed in browser storage.
- Session cookies are HttpOnly/SameSite=Lax; mutating requests require a
  per-session CSRF token. Login is rate limited.
- Every mutation is audited with request ID, actor, mode and redacted detail.
- Unknown order outcomes become `PENDING_RECONCILIATION`; the server queries
  by stable `clientOrderId` instead of blindly resubmitting.
