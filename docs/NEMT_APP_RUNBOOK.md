# NEMT App V0.1 — Runbook

Updated: 2026-10-17 · Mode covered: **DEMO** (verified), **TESTNET** (implemented, credentials pending), **LIVE** (write path intentionally absent).

## 1. What is in this delivery

| Layer | Path | Purpose |
|---|---|---|
| Mobile PWA | `web/` → `/trade` | Overview, market, order entry, orders, settings, admin kill switch |
| Cloud API | `backend/trade_app/` | Auth/RBAC/CSRF, market proxy, risk, orders, audit, system status |
| API entry | `backend/trade_main.py` | FastAPI + Uvicorn factory entry point |
| Persistence | `backend/.data/nemt_app.sqlite3` | Orders, fills, sessions, confirmations, audit, demo wallets |
| Binance adapter | `backend/trade_app/binance_spot.py` | Public market + read-only account + Spot Testnet orders (server only) |
| ADR | `docs/ADR-001-nemt-app-baseline.md` | Next.js-instead-of-Vite and SQLite/local baseline decisions |

The existing research dashboard and NEMT engine API (`backend/main.py`) are untouched.

## 2. Local DEMO (no exchange keys)

Prerequisites: Python 3.11+, Node.js 20.9+, npm.

```bash
# from the repository root
python -m venv venv                    # skip if venv exists
venv/Scripts/pip install -r backend/trade_requirements.txt

# Terminal 1 — cloud API (loopback only)
venv/Scripts/python backend/trade_main.py

# Terminal 2 — PWA
cd web
npm install
npm run build
npm start                              # http://localhost:3000/trade
```

On Linux/macOS use `venv/bin/python` and `venv/bin/pip`.

DEMO defaults:

| Account | Password | Roles |
|---|---|---|
| `demo` | `nemt-demo` | viewer, trader |
| `admin` | `nemt-admin` | viewer, trader, admin |
| `viewer` | `nemt-viewer` | viewer |

The login screen includes one-click DEMO access. These accounts exist only in
DEMO; non-DEMO modes never seed them.

DEMO behavior:
- Market data comes from Binance public REST (`c` = latest price, `p` = 24H change).
- If Binance is unreachable, the API returns deterministic simulated data and
  labels it `source: "demo"` in the UI. It is never presented as live.
- Market orders fill against the local simulated wallet; limit orders reserve
  funds and remain `NEW` until canceled. No request is sent to an exchange.
- The database starts with 10,000 USDT and 0.002 BTC per demo user.

Optional `backend/.env` (copy from `backend/.env.example`):
- set a long `NEMT_SESSION_SECRET` to keep sessions across restarts;
- change DEMO passwords if the phone/browser is reachable by other people.

## 3. Phone testing (Android, USB)

```bash
adb devices
adb reverse tcp:3000 tcp:3000
adb shell am start -a android.intent.action.VIEW \
  -d "http://localhost:3000/trade" com.android.chrome
```

`localhost` through `adb reverse` is a secure context, so the PWA service
worker and "Add to home screen" work. In Chrome: menu → **Add to home screen /
Install app**.

- The app never talks to Binance directly; it calls `/api/v1` through the Next
  proxy.
- The service worker never intercepts `/api/`; offline trading is impossible.
- The offline fallback is `web/public/offline.html`.
- Standalone mode removes the browser chrome; bottom navigation respects
  safe-area insets.

For testing over Wi-Fi on a local network, use HTTPS before relying on PWA
installation (or keep using `adb reverse`).

## 4. Environment isolation and gates

| Mode | Market | Account | Order path | Default |
|---|---|---|---|---|
| DEMO | Binance public or simulated fallback | Local simulated ledger | Local simulation only | yes |
| TESTNET | Binance Spot Testnet | Testnet read-only/trade key | Server-gated Testnet orders | requires explicit flags |
| LIVE | Binance public (read-only) | Read-only key | **No write path in V0.1** | disabled |

Switching modes is a server configuration change. A browser parameter or UI
switch cannot grant trading authority.

### Enabling TESTNET (after credentials are available)

1. Create a dedicated Binance **Spot Testnet** key. Disable withdrawals; use
   only the permissions required for Spot read/trade.
2. On the server (never in the repo or client bundle), set:
   ```ini
   NEMT_APP_MODE=TESTNET
   NEMT_MARKET_SOURCE=binance
   NEMT_SESSION_SECRET=<32+ random chars>
   NEMT_COOKIE_SECURE=true            # when served over HTTPS
   NEMT_BINANCE_API_KEY=<testnet key>
   NEMT_BINANCE_API_SECRET=<testnet secret>
   NEMT_ALLOW_TESTNET_TRADING=true
   # Operator login (minimum 12 characters); demo quick-login is disabled
   # outside DEMO. Only these hashed users are seeded into the local database.
   NEMT_TESTNET_TRADER_PASSWORD=<long random password>
   NEMT_TESTNET_ADMIN_PASSWORD=<long random password>
   NEMT_LIVE_TRADING_ENABLED=false
   ```
3. Restart the API. `/api/v1/system/status` must report `mode=TESTNET`,
   `trading_enabled=true`, and a connected account. If any credential is
   missing, trading stays disabled and orders are rejected.
4. Run the Testnet acceptance checklist in
   `docs/NEMT_APP_TESTNET_ACCEPTANCE.md`.

### LIVE

`NEMT_LIVE_TRADING_ENABLED=true` is deliberately ignored by V0.1:
`Settings.live_trading_available` is always `False`, and the risk engine
rejects LIVE order creation. Enabling real money requires the separate issue
#15 approval, review and a new release.

## 5. API surface

All endpoints are versioned under `/api/v1`; interactive OpenAPI docs are at
`/api/v1/docs` (FastAPI, direct port 8000).

| Method | Endpoint | Access |
|---|---|---|
| GET | `/health`, `/health/ready` | public |
| POST | `/auth/login` | public (rate limited) |
| POST | `/auth/demo` | DEMO only |
| GET | `/auth/me` | session |
| POST | `/auth/logout` | session + CSRF |
| GET | `/system/status` | viewer |
| GET | `/market/ticker`, `/market/klines` | viewer |
| GET | `/account/balances` | viewer |
| POST | `/orders/preview` | trader + CSRF |
| POST | `/orders` | trader + CSRF + confirmation token |
| GET | `/orders` | viewer (own orders) |
| POST | `/orders/{id}/cancel` | trader + CSRF |
| POST | `/admin/pause-new-orders`, `/admin/resume-new-orders` | admin + CSRF |
| POST | `/admin/cancel-open-orders` | admin + CSRF + `confirm=true` |
| GET | `/audit/events` | admin |

Trading writes also require a valid, unexpired, one-time confirmation token
issued by `/orders/preview`. A unique `clientOrderId` is derived from the
client idempotency key; retries return the existing order.

## 6. Risk controls (server-side, fail-closed)

Default limits (configurable only by environment):

- symbol allowlist: `BTCUSDT`;
- notional: 5–100 USDT per order, 1,000 USDT/day;
- max position value: 1,000 USDT; max 5 open orders; 10 orders/minute;
- stale market data (>20 s) or stale account snapshot (>60 s) blocks orders;
- global pause (`pause_new_orders`) persists and is checked inside the order
  transaction; resume and pause require admin + CSRF and are audited;
- bulk cancel requires explicit confirmation and never claims to close filled
  positions;
- DEMO orders update balances atomically; duplicate idempotency keys never
  create a second order.

The UI's kill switch is an operator convenience; the server is the control.

## 7. Operations

- **Health:** `GET http://127.0.0.1:8000/api/v1/health[/ready]`.
- **Pause all new orders:** app → 设置 (admin) → 全局新订单开关; or API. Filled
  positions are not closed.
- **Cancel all open orders:** app → 设置 (admin) → 确认撤销; result lists
  failures; filled positions are unchanged.
- **Audit:** `GET /audit/events` (admin) includes request ID, actor, mode and
  redacted details. API responses carry `X-Request-ID`.
- **Logs:** Uvicorn stdout. Credentials, signatures and auth headers are never
  logged. Do not enable request-body logging for `/auth/*` or `/orders`.
- **Backup (SQLite):** stop the API, copy `backend/.data/nemt_app.sqlite3`
  (plus `-wal`/`-shm` if present) to a private location; restart. Restore in a
  non-production environment first.
- **Reset DEMO:** stop the API and remove the SQLite file only if you accept
  losing demo orders and audit history. This is destructive; back up first.
- **Ports:** API binds `127.0.0.1:8000`; Next binds `:3000`. Do not expose
  Redis/PostgreSQL publicly. `quant-mvp` Redis is now bound to `127.0.0.1`.

## 8. Verification commands

```bash
# backend
cd backend && ../venv/Scripts/python -m pytest        # 20 tests
# frontend
cd web && npm run lint && npx tsc --noEmit && npm run build
```

Verified on 2026-10-17 with an Android device over `adb reverse`:
login → real BTCUSDT price → market preview → risk checks → confirmation →
simulated fill → balance update → order history. Evidence images are under
`docs/assets/nemt-app/`.

A local headless Chrome check captures every tab at 390 px and verifies the
manifest, an active service worker, zero horizontal overflow, an empty
localStorage, and the offline state:

```bash
# API and web must already be running; DEMO only
node scripts/nemt_app_ui_check.mjs
```

Result on 2026-10-17: passed (manifest + active SW controller; offline shell
shows `SERVER UNREACHABLE` and no order success).

## 9. Known gaps / follow-ups

- Binance User Data Stream and a periodic reconciliation worker (issue #13).
- Real Testnet order/partial-fill evidence requires Testnet credentials;
  the adapter and order state machine exist but have only been exercised with
  a mock transport so far.
- DEMO limit orders rest and can be canceled; there is no background matcher
  or simulated partial fill yet.
- MFA/re-authentication for admin actions, multi-user sessions, PostgreSQL,
  Alembic migrations, distributed rate limiting and alerts are not in V0.1.
- WebSocket/SSE market push is replaced by 5 s REST polling; freshness is
  explicit and orders are blocked when stale.
- Historical secrets in Git (COS keys, SSH private key) are tracked. See
  `docs/SECURITY_CLEANUP_PLAN.md`. Rotate credentials and clean history in a
  separately approved operation.
- Deployment, HTTPS reverse proxy, backup drills and GitHub Actions for the
  hosted staging environment remain issue #14 work.

## 10. Deployed DEMO environment (2026-10-17)

- **URL:** `https://postyouth.club/trade` (root redirects to `/trade`; `www` also works).
- **Fallback URL:** `https://103.144.246.242.sslip.io/trade` (temporary sslip.io host).
- **Access gate:** nginx HTTP Basic auth (username `nemt`). The password is
  stored only in `/root/nemt-app-access.txt` on the server and was handed to the
  owner directly; it is not in this repository. The app also has its own login.
- **Host:** 103.144.246.242 (Ubuntu 22.04). Existing sites on the server were
  left alone except for switching the `postyouth.club` public entry to NEMT.
- **Processes:** `nemt-api.service` (FastAPI on 127.0.0.1:8101) and
  `nemt-web.service` (Next.js on 127.0.0.1:3101); nginx terminates TLS.
- **Code:** `/opt/nemt-app` (owned by `nemtapp`); Python venv at
  `/opt/nemt-app/venv`.
- **Config:** `/etc/nemt-app/api.env` (mode 600, DEMO, Binance public market).
  It contains the session secret and is not in the repo.
- **Data:** `/var/lib/nemt-app/nemt_app.sqlite3` (orders, audit, demo ledger).
- **TLS:** `/etc/letsencrypt/live/postyouth.club/` (covers root + www).
  Certbot timer is active; renewal can be checked with:
  ```bash
  certbot renew --cert-name postyouth.club --dry-run
  ```
- **Previous postyouth site:** it was the Duoweilai app proxied from
  `127.0.0.1:8090`. That service and its data were **not stopped or deleted**;
  only the nginx hostname entry changed. Backups of the replaced nginx and
  renewal configs are in `/root/nemt-switch-backup-*/`. Restoring
  `postyouth.club.conf` there reverts the public entry.
- **Acceptance status:** HTTPS, basic gate and internal services were brought
  up; the final public end-to-end acceptance run after the domain switch was
  interrupted when work was paused. Re-run the checklist next session before
  calling Gate B/C complete.

Useful commands:

```bash
ssh -i ~/.ssh/moodify_cloud root@103.144.246.242   'systemctl status nemt-api nemt-web; journalctl -u nemt-api -u nemt-web -n 100'
# health from the server
ssh -i ~/.ssh/moodify_cloud root@103.144.246.242   'curl -s http://127.0.0.1:8101/api/v1/health'
```
