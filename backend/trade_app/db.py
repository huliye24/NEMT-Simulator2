"""SQLite persistence for the NEMT App V0.1 cloud API.

DEMO uses a local SQLite file. The schema deliberately keeps money as TEXT
decimals (never floats) and records every state transition. A production
deployment can migrate this repository layer to PostgreSQL without changing
the API contract; see docs/ADR-001-nemt-app-baseline.md.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

from .config import AppMode, Settings
from .security import hash_password

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    roles TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    csrf_token TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_username ON sessions(username);

CREATE TABLE IF NOT EXISTS confirmations (
    token_hash TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    draft_json TEXT NOT NULL,
    draft_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    client_order_id TEXT NOT NULL UNIQUE,
    idempotency_key TEXT NOT NULL,
    username TEXT NOT NULL,
    mode TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    type TEXT NOT NULL,
    time_in_force TEXT,
    price TEXT,
    quantity TEXT NOT NULL,
    notional TEXT NOT NULL DEFAULT '0',
    filled_qty TEXT NOT NULL DEFAULT '0',
    avg_fill_price TEXT,
    status TEXT NOT NULL,
    fee TEXT NOT NULL DEFAULT '0',
    fee_asset TEXT,
    exchange_order_id TEXT,
    reserved_amount TEXT NOT NULL DEFAULT '0',
    reserved_asset TEXT,
    risk_json TEXT,
    error_code TEXT,
    error_message TEXT,
    request_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    submitted_at TEXT,
    UNIQUE(username, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(username, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(username, status);

CREATE TABLE IF NOT EXISTS fills (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    exchange_trade_id TEXT,
    price TEXT NOT NULL,
    quantity TEXT NOT NULL,
    commission TEXT NOT NULL DEFAULT '0',
    commission_asset TEXT,
    filled_at TEXT NOT NULL,
    UNIQUE(order_id, exchange_trade_id)
);
CREATE INDEX IF NOT EXISTS idx_fills_order ON fills(order_id);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    actor TEXT,
    action TEXT NOT NULL,
    mode TEXT NOT NULL,
    request_id TEXT,
    entity_type TEXT,
    entity_id TEXT,
    detail_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_events(ts DESC);

CREATE TABLE IF NOT EXISTS system_flags (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT
);

CREATE TABLE IF NOT EXISTS demo_wallets (
    username TEXT NOT NULL,
    asset TEXT NOT NULL,
    free TEXT NOT NULL,
    locked TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (username, asset)
);

CREATE TABLE IF NOT EXISTS account_snapshots (
    account_key TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    balances_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    source TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Paper trading (纸上交易): real quotes, simulated money. Completely separate
-- from the live order tables above; nothing here can reach an exchange.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS paper_accounts (
    username TEXT PRIMARY KEY,
    initial_equity TEXT NOT NULL,
    cash TEXT NOT NULL,
    realized_pnl TEXT NOT NULL DEFAULT '0',
    fees_paid TEXT NOT NULL DEFAULT '0',
    funding_paid TEXT NOT NULL DEFAULT '0',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_positions (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    strategy TEXT NOT NULL DEFAULT 'NEMT',
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    side TEXT NOT NULL,
    qty TEXT NOT NULL,
    entry_price TEXT NOT NULL,
    leverage INTEGER NOT NULL DEFAULT 1,
    margin TEXT NOT NULL DEFAULT '0',
    realized_pnl TEXT NOT NULL DEFAULT '0',
    fees TEXT NOT NULL DEFAULT '0',
    funding TEXT NOT NULL DEFAULT '0',
    last_funding_at TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN',
    opened_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_paper_positions_user
    ON paper_positions(username, status);

CREATE TABLE IF NOT EXISTS paper_fills (
    id TEXT PRIMARY KEY,
    position_id TEXT NOT NULL,
    username TEXT NOT NULL,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    side TEXT NOT NULL,
    action TEXT NOT NULL,
    qty TEXT NOT NULL,
    price TEXT NOT NULL,
    fee TEXT NOT NULL DEFAULT '0',
    realized_pnl TEXT NOT NULL DEFAULT '0',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_paper_fills_user
    ON paper_fills(username, created_at DESC);

CREATE TABLE IF NOT EXISTS paper_equity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    at TEXT NOT NULL,
    equity TEXT NOT NULL,
    cash TEXT NOT NULL,
    unrealized TEXT NOT NULL,
    realized TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_paper_equity_user
    ON paper_equity(username, at DESC);

-- ---------------------------------------------------------------------------
-- Auto trading loop (NEMT signal -> paper position). Human approval is not part
-- of this path; every decision is journalled here for the UI.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS auto_trade_flags (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT
);

CREATE TABLE IF NOT EXISTS auto_trade_state (
    symbol TEXT PRIMARY KEY,
    last_phase TEXT,
    last_signal TEXT,
    last_action TEXT,
    last_action_at TEXT
);

CREATE TABLE IF NOT EXISTS auto_trade_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    position_id TEXT,
    detail_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_auto_trade_events_ts ON auto_trade_events(ts DESC);
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime | None = None) -> str:
    current = value or utc_now()
    return current.astimezone(timezone.utc).isoformat(timespec="seconds")


def iso_after(seconds: int) -> str:
    return iso(utc_now() + timedelta(seconds=seconds))


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def decimal_str(value: Decimal) -> str:
    return format(value, "f")


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=10,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    @contextmanager
    def tx(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        """Transaction scope. Use immediate for read-modify-write flows."""

        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def query_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        connection = self.connect()
        try:
            return list(connection.execute(sql, params).fetchall())
        finally:
            connection.close()

    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        connection = self.connect()
        try:
            return connection.execute(sql, params).fetchone()
        finally:
            connection.close()

    def _migrate_columns(self, connection: sqlite3.Connection) -> None:
        """Additive column migrations for tables that already exist on disk.

        SQLite has no "ADD COLUMN IF NOT EXISTS", and the deployed database keeps
        its paper positions, so new columns are added only when missing.
        """

        wanted = {
            "paper_positions": (
                ("stop_price", "TEXT"),
                ("take_price", "TEXT"),
                ("opened_reason", "TEXT"),
            ),
        }
        for table, columns in wanted.items():
            existing = {
                str(row[1])
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            for name, ddl in columns:
                if name not in existing:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")

    def initialize(self, settings: Settings) -> None:
        # executescript() manages its own transaction, so schema creation is
        # kept outside the explicit BEGIN/COMMIT used for seeding.
        connection = self.connect()
        try:
            connection.executescript(SCHEMA_SQL)
            self._migrate_columns(connection)
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT MAX(version) AS version FROM schema_migrations"
                ).fetchone()
                current_version = int(row["version"] or 0) if row else 0
                if current_version < SCHEMA_VERSION:
                    connection.execute(
                        "INSERT OR REPLACE INTO schema_migrations(version, applied_at)"
                        " VALUES (?, ?)",
                        (SCHEMA_VERSION, iso()),
                    )

                connection.execute(
                    "INSERT OR IGNORE INTO system_flags(key, value, updated_at, updated_by)"
                    " VALUES ('pause_new_orders', '0', ?, 'system')",
                    (iso(),),
                )

                if settings.is_demo:
                    self._seed_demo(connection, settings)
                for username, (password, roles) in settings.operator_users.items():
                    # Upsert, never INSERT OR IGNORE: a leftover DEMO row with
                    # the same username must not keep its weak DEMO password.
                    connection.execute(
                        "INSERT INTO users"
                        " (username, password_hash, roles, enabled, created_at)"
                        " VALUES (?, ?, ?, 1, ?)"
                        " ON CONFLICT(username) DO UPDATE SET"
                        " password_hash = excluded.password_hash,"
                        " roles = excluded.roles,"
                        " enabled = 1",
                        (username, hash_password(password), ",".join(roles), iso()),
                    )
                if settings.mode is AppMode.LIVE:
                    self._disable_legacy_demo_accounts(connection, settings)
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        finally:
            connection.close()


    def _disable_legacy_demo_accounts(
        self, connection: sqlite3.Connection, settings: Settings
    ) -> None:
        """LIVE must not inherit DEMO logins from an earlier deployment.

        The DEMO seed accounts stay in the database when the mode is switched.
        Anyone who knows ``nemt-demo`` would otherwise keep a trading session on
        a real-money deployment, so they are disabled unless the operator
        deliberately named one of them as the new operator account.
        """

        legacy = sorted({"demo", "viewer", "admin"} - set(settings.operator_users))
        if not legacy:
            return
        placeholders = ",".join("?" for _ in legacy)
        connection.execute(
            f"UPDATE users SET enabled = 0 WHERE username IN ({placeholders})",
            tuple(legacy),
        )

    def _seed_demo(self, connection: sqlite3.Connection, settings: Settings) -> None:
        now = iso()
        seeded_users = {
            "viewer": ("viewer", settings.demo_passwords.get("viewer", "")),
            "demo": ("viewer,trader", settings.demo_passwords.get("demo", "")),
            "admin": ("viewer,trader,admin", settings.demo_passwords.get("admin", "")),
        }
        for username, (roles, password) in seeded_users.items():
            connection.execute(
                "INSERT OR IGNORE INTO users(username, password_hash, roles, enabled, created_at)"
                " VALUES (?, ?, ?, 1, ?)",
                (username, hash_password(password), roles, now),
            )
            for asset, amount in (
                ("USDT", settings.demo_initial_usdt),
                ("BTC", settings.demo_initial_btc),
            ):
                connection.execute(
                    "INSERT OR IGNORE INTO demo_wallets(username, asset, free, locked, updated_at)"
                    " VALUES (?, ?, ?, '0', ?)",
                    (username, asset, decimal_str(amount), now),
                )

    def log_audit(
        self,
        connection: sqlite3.Connection,
        *,
        action: str,
        mode: str,
        actor: str | None = None,
        request_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        from .security import redact

        connection.execute(
            "INSERT INTO audit_events"
            " (ts, actor, action, mode, request_id, entity_type, entity_id, detail_json)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                iso(),
                actor,
                action,
                mode,
                request_id,
                entity_type,
                entity_id,
                json.dumps(redact(detail or {}), ensure_ascii=False, sort_keys=True),
            ),
        )
