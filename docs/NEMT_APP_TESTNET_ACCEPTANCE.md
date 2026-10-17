# NEMT App V0.1 — Testnet acceptance checklist

Last updated: **2026-10-17**
Scope: Spot **Testnet** only. This document does not authorize real-money trading.

Legend: ✅ verified · 🟡 implemented, not yet verified against the venue · ⬜ not implemented · — not in V0.1.

## Gate A — Market data + read-only account

| Item | Status | Evidence / note |
|---|---|---|
| DEMO starts without exchange keys | ✅ | `backend/tests/test_trade_app.py`; DEMO smoke |
| DEMO/Testnet/LIVE config isolation, LIVE default off | ✅ | `test_environment_isolation_fails_closed`; `/system/status` |
| Unknown/invalid mode fails closed | ✅ | `ConfigError` tests |
| Public BTCUSDT latest price uses `c`, change uses `p` | ✅ | `test_parser_uses_latest_price_not_price_change`; live Binance data observed |
| Kline parsing (REST + raw/combined `@kline` event) | ✅ | parser unit tests; REST chart verified |
| Feed staleness is exposed and blocks orders | ✅ | risk checks + UI banners |
| Auth rate limit, RBAC viewer/trader/admin, CSRF | ✅ | `test_login_session_and_logout`, `test_rbac_viewer_cannot_trade_and_csrf_is_required` |
| TESTNET operator accounts (no demo login outside DEMO) | ✅ | `test_testnet_operator_login_and_demo_endpoint_disabled`; password hashes only |
| Binance Spot adapter signing/time sync/error mapping | 🟡 | mock transport tests (`test_binance_adapter_signs_requests_and_parses_account`) |
| Read-only account balances against real Testnet | ⬜/🟡 | adapter implemented; needs dedicated Testnet keys and a real `GET /api/v3/account` |
| No exchange keys in browser/localStorage/logs | ✅ | design + audit tests; server env only |

**Gate A status: DEMO portion passed; Testnet account verification pending credentials.**

## Gate B — Testnet trading loop

| Item | Status | Evidence / note |
|---|---|---|
| Server-side risk gate before every order | ✅ | `risk.py`; preview + create re-check; tests |
| Minimum/maximum notional, daily budget, position, open orders, rate | ✅ | preview rejection test; settings limits |
| Global pause (Kill Switch) persists across restart | ✅ | `test_pause_survives_restart` |
| Pause is checked again between preview and confirmation | ✅ | `test_pause_between_preview_and_confirm_fails_closed` |
| One-time preview → confirmation flow | ✅ | DEMO phone flow; `confirmations` table |
| Idempotent `clientOrderId` / no duplicate on retry | ✅ | `test_market_order_fills_once_and_is_idempotent` |
| Market and limit order paths | ✅ DEMO | market fills locally; limit reserves/cancels |
| Cancel + reserved funds release | ✅ DEMO | `test_limit_order_reserves_then_cancel_releases` |
| Admin bulk cancel does not claim to close positions | ✅ | `test_admin_bulk_cancel_does_not_claim_positions_closed` |
| Testnet limit order create/cancel/fill | 🟡 | adapter + state machine written; cannot log in without TESTNET operator passwords; **no real Testnet evidence yet** |
| Venue filters fail closed outside DEMO | ✅ | `test_exchange_rules_fail_closed_outside_demo` |
| Partial fill / remainder cancel | ⬜ | state enum supports it; no demo matcher or venue evidence |
| Timeout / unknown outcome → query, never blind resubmit | ✅ code path 🟡 | adapter mock timeout test; needs Testnet proof |
| 429/418/5xx bounded backoff | ✅ code | adapter unit path; needs recorded Testnet evidence |
| User Data Stream + reconciliation | ⬜ | issue #13 follow-up |
| Audit for every mutation with request IDs | ✅ | `audit_events`; tests |

**Gate B status: DEMO risk/idempotency/cancel verified. Testnet order loop not yet accepted.**

## Gate C — Mobile PWA + operations

| Item | Status | Evidence / note |
|---|---|---|
| Mobile-first `/trade` route, 375 px layout | ✅ | Android Chrome screenshots; bottom nav safe areas |
| Five distinct statuses | ✅ | 服务端 / 登录 / 行情 / 账户 / 交易 |
| DEMO vs LIVE visual distinction, LIVE non-executable | ✅ | amber DEMO watermark; LIVE chip; no write route |
| Overview, market chart, order entry, order history, settings | ✅ | phone verification; screenshots in `docs/assets/nemt-app/` |
| Preview → explicit confirmation sheet | ✅ | phone flow, risk checks visible |
| Offline blocks trading and never reports success | ✅ | online gate + no API caching; SW review |
| PWA manifest, icons, service worker | ✅ | `/manifest.webmanifest`, `/sw.js`, `/icons/*`; install requires HTTPS/localhost |
| No Binance keys in Network/localStorage | ✅ | architecture; cookie-only session |
| Admin pause/resume + bulk cancel UI | 🟡 | implemented, API tested; UI not yet exercised on device |
| MFA/re-auth for admin actions | ⬜ | V0.1 uses admin role + CSRF + audited reason |
| CI lint/typecheck/pytest/frontend build | ✅ | `.github/workflows/nemt-app-ci.yml` (run after push) |
| PWA manifest + active service worker | ✅ | headless: manifest `/manifest.webmanifest`, SW scope `/`, controller active |
| 390 px no horizontal overflow; empty localStorage | ✅ | headless DOM assertions (`scripts/nemt_app_ui_check.mjs`) |
| Hosted DEMO staging, HTTPS, basic gate | ✅ | `https://postyouth.club/trade` (nginx TLS, Let's Encrypt); final public acceptance run was interrupted and remains to be repeated |
| Hosted TESTNET staging, monitoring, backups | ⬜ | issue #14 follow-up |
| Real phone PWA install (standalone) | 🟡 | service worker registration is production-only; verify on installed app |

**Gate C status: DEMO mobile PWA delivered and exercised on an Android device.**

## Evidence collected (2026-10-17, DEMO)

- Backend: 20 pytest tests passing (DEMO + adapter mocks + fail-closed filters).
- Frontend: ESLint 0 errors, TypeScript clean, Next.js production build succeeds.
- Phone (Xiaomi M2102J2SC, Android, Chrome via `adb reverse`):
  login, real Binance BTCUSDT feed, order entry, server risk preview,
  confirmation sheet, simulated fill, balance update, order history.
- Headless Chrome 390 px: PWA manifest present, service worker active and
  controlling the page, no horizontal overflow, no localStorage keys; offline
  reload shows the network/login error without any order success.
- Screenshots (`docs/assets/nemt-app/`):
  - headless 390 px: `login.png`, `overview.png`, `market.png`, `trade.png`,
    `orders.png`, `settings-trader.png`, `settings-admin.png`,
    `settings-admin-controls.png`, `offline.png`;
  - desktop: `desktop-overview.png`;
  - Android device: `device-overview.png`, `device-confirm-sheet.png`,
    `device-order-filled.png`, `device-orders.png`.

## Required to close Gate B

1. Provide dedicated Spot Testnet credentials **server-side only** and set the
   flags from the runbook. Never commit or paste secrets into an issue/chat.
2. Record a Testnet market buy, a limit order + cancel, and (if available) a
   partial fill; export redacted order/audit JSON as evidence.
3. Confirm timeout/429 behavior with a controlled network fault and show that
   no duplicate `clientOrderId` exists.
4. Implement reconciliation for `PENDING_RECONCILIATION` and restart recovery
   (issue #13) before calling the loop closed.
