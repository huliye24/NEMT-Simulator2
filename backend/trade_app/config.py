"""Configuration and environment isolation for the NEMT App V0.1 cloud API.

The server -- never the browser -- decides which environment is active.
Unknown or inconsistent configuration fails closed rather than falling
back to a more permissive mode.
"""

from __future__ import annotations

import os
import secrets
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Mapping

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class ConfigError(RuntimeError):
    """Raised when the environment configuration is unsafe or invalid."""


class AppMode(str, Enum):
    DEMO = "DEMO"
    TESTNET = "TESTNET"
    LIVE = "LIVE"


def _load_dotenv() -> None:
    """Load backend/.env then repo .env without overriding real env vars.

    This intentionally implements only the small subset the service needs;
    secrets are never written to logs.
    """

    for candidate in (BACKEND_DIR / ".env", REPO_ROOT / ".env"):
        if not candidate.is_file():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration for one API process."""

    mode: AppMode
    database_path: Path
    session_secret: str = field(repr=False)
    session_ttl_seconds: int = 12 * 60 * 60
    confirmation_ttl_seconds: int = 90
    cookie_name: str = "nemt_session"
    cookie_secure: bool = False

    allowed_symbols: tuple[str, ...] = ("BTCUSDT",)
    market_source: str = "binance"
    market_stale_seconds: int = 20
    account_stale_seconds: int = 60

    allow_testnet_trading: bool = False
    live_trading_enabled: bool = False
    binance_api_key: str | None = field(default=None, repr=False)
    binance_api_secret: str | None = field(default=None, repr=False)
    binance_recv_window_ms: int = 5000

    min_order_notional: Decimal = Decimal("5")
    max_order_notional: Decimal = Decimal("100")
    max_daily_notional: Decimal = Decimal("1000")
    max_position_notional: Decimal = Decimal("1000")
    max_open_orders: int = 5
    max_orders_per_minute: int = 10
    trading_fee_rate: Decimal = Decimal("0.001")

    demo_initial_usdt: Decimal = Decimal("10000")
    demo_initial_btc: Decimal = Decimal("0.002")

    # --- Paper trading (纸上交易: real quotes, simulated money) --------------
    paper_initial_equity: Decimal = Decimal("2000")
    paper_symbols: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    paper_taker_fee_spot: Decimal = Decimal("0.001")
    paper_taker_fee_perp: Decimal = Decimal("0.0005")
    paper_slippage_bps: Decimal = Decimal("5")
    paper_maintenance_margin_rate: Decimal = Decimal("0.004")
    paper_funding_interval_hours: int = 8
    paper_max_leverage: int = 10
    paper_min_notional: Decimal = Decimal("5")

    # --- NEMT signal engine (相位/动量), mirrors nemtCalculator.ts -----------
    nemt_critical_entropy: Decimal = Decimal("0.7")
    nemt_critical_psi: Decimal = Decimal("0.5")
    nemt_stable_psi: Decimal = Decimal("0.3")
    nemt_ema_alpha: Decimal = Decimal("0.3")
    nemt_low_entropy: Decimal = Decimal("0.15")
    nemt_atr_period: int = 14
    nemt_bars: int = 120
    nemt_risk_per_trade_pct: Decimal = Decimal("1")

    # --- Auto trading loop: NEMT signal -> paper position, no human click ----
    auto_trade_enabled: bool = True
    auto_trade_username: str = "demo"
    auto_trade_interval_seconds: int = 60
    auto_trade_interval: str = "15m"
    auto_trade_max_positions: int = 3
    auto_trade_cooldown_minutes: int = 15

    demo_passwords: Mapping[str, str] = field(default_factory=dict, repr=False)
    # username -> (password, roles). Passwords stay repr=False and are only
    # hashed into the local user table; they are never returned by the API.
    operator_users: Mapping[str, tuple[str, tuple[str, ...]]] = field(
        default_factory=dict, repr=False
    )

    allowed_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )
    api_prefix: str = "/api/v1"
    app_version: str = "0.1.0"

    @property
    def is_demo(self) -> bool:
        return self.mode is AppMode.DEMO

    @property
    def market_symbols(self) -> tuple[str, ...]:
        """Symbols the market service may quote.

        Paper trading needs ETH/SOL even when live order routing is limited to
        the ``allowed_symbols`` allowlist, so quoting is a superset. Order
        routing still uses ``allowed_symbols`` only.
        """

        merged: dict[str, None] = {}
        for symbol in (*self.allowed_symbols, *self.paper_symbols):
            merged[str(symbol).upper()] = None
        return tuple(merged)

    @property
    def binance_credentials_configured(self) -> bool:
        return bool(self.binance_api_key and self.binance_api_secret)

    @property
    def testnet_credentials_configured(self) -> bool:
        return self.binance_credentials_configured

    @property
    def live_trading_available(self) -> bool:
        """Whether the operator opened the real-money order path.

        This is now driven by ``NEMT_LIVE_TRADING_ENABLED`` instead of being
        hard-wired off. The path is only usable when *all* of these hold:

        * ``NEMT_APP_MODE=LIVE``
        * ``NEMT_LIVE_TRADING_ENABLED=true``
        * server-side Binance credentials are present
        * at least one non-DEMO operator account was configured (load_settings
          refuses to build LIVE settings without one)
        * the per-order/day/month risk limits in this file

        Enabling it moves real money. The demo accounts are disabled on
        startup in LIVE mode so a public visitor cannot inherit trading rights.
        """

        return self.live_trading_enabled

    @property
    def live_trading_ready(self) -> bool:
        """LIVE is selected, switched on, and has credentials to sign with."""

        return (
            self.mode is AppMode.LIVE
            and self.live_trading_enabled
            and self.binance_credentials_configured
        )

    @property
    def trading_enabled(self) -> bool:
        if self.mode is AppMode.DEMO:
            return True
        if self.mode is AppMode.TESTNET:
            return self.allow_testnet_trading and self.testnet_credentials_configured
        return self.live_trading_ready

    def public_status(self) -> dict[str, object]:
        """Non-secret capability summary for /system/status and the UI."""

        return {
            "mode": self.mode.value,
            "trading_enabled": self.trading_enabled,
            "live_trading_enabled": self.live_trading_enabled,
            "live_trading_available": self.live_trading_available,
            "live_trading_ready": self.live_trading_ready,
            "testnet_credentials_configured": self.testnet_credentials_configured,
            "binance_credentials_configured": self.binance_credentials_configured,
            "allowed_symbols": list(self.allowed_symbols),
            "market_source": self.market_source,
            "limits": {
                "min_order_notional": str(self.min_order_notional),
                "max_order_notional": str(self.max_order_notional),
                "max_daily_notional": str(self.max_daily_notional),
                "max_position_notional": str(self.max_position_notional),
                "max_open_orders": self.max_open_orders,
                "max_orders_per_minute": self.max_orders_per_minute,
                "market_stale_seconds": self.market_stale_seconds,
                "account_stale_seconds": self.account_stale_seconds,
            },
        }


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Build settings from environment variables.

    ``environ`` exists so tests can supply an isolated mapping. Values in it
    take precedence over the process environment.
    """

    if environ is not None:
        # Merge without mutating the caller's mapping.
        merged = dict(os.environ)
        merged.update(environ)
        source = merged
    else:
        _load_dotenv()
        source = os.environ

    def env(name: str, default: str | None = None) -> str | None:
        value = source.get(name)
        return default if value is None or value == "" else value

    def env_bool(name: str, default: bool) -> bool:
        raw = env(name)
        if raw is None:
            return default
        normalized = raw.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ConfigError(f"{name} must be one of true/false/1/0/yes/no")

    def env_int(name: str, default: int, *, minimum: int = 1) -> int:
        raw = env(name)
        if raw is None:
            return default
        try:
            value = int(raw)
        except ValueError as exc:
            raise ConfigError(f"{name} must be an integer") from exc
        if value < minimum:
            raise ConfigError(f"{name} must be >= {minimum}")
        return value

    def env_decimal(name: str, default: str) -> Decimal:
        raw = env(name, default) or default
        try:
            value = Decimal(raw)
        except InvalidOperation as exc:
            raise ConfigError(f"{name} must be a decimal number") from exc
        if value <= 0:
            raise ConfigError(f"{name} must be > 0")
        return value

    def env_csv(name: str, default: str) -> tuple[str, ...]:
        raw = env(name, default) or default
        return tuple(item.strip() for item in raw.split(",") if item.strip())

    raw_mode = (env("NEMT_APP_MODE", "DEMO") or "DEMO").strip().upper()
    try:
        mode = AppMode(raw_mode)
    except ValueError as exc:
        raise ConfigError("NEMT_APP_MODE must be DEMO, TESTNET or LIVE") from exc

    market_source = (env("NEMT_MARKET_SOURCE", "binance") or "binance").strip().lower()
    if market_source not in {"binance", "demo"}:
        raise ConfigError("NEMT_MARKET_SOURCE must be binance or demo")
    if market_source == "demo" and mode is not AppMode.DEMO:
        raise ConfigError("NEMT_MARKET_SOURCE=demo is only allowed in DEMO mode")

    allowed_symbols = tuple(s.upper() for s in env_csv("NEMT_ALLOWED_SYMBOLS", "BTCUSDT"))
    if not allowed_symbols:
        raise ConfigError("NEMT_ALLOWED_SYMBOLS must not be empty")

    session_secret = env("NEMT_SESSION_SECRET")
    if session_secret is None:
        if mode is not AppMode.DEMO:
            raise ConfigError("NEMT_SESSION_SECRET is required outside DEMO mode")
        session_secret = secrets.token_urlsafe(48)
        print(
            "WARNING: NEMT_SESSION_SECRET not set; using an ephemeral DEMO secret. "
            "Sessions will not survive a restart.",
            file=sys.stderr,
        )
    if mode is not AppMode.DEMO and len(session_secret) < 32:
        raise ConfigError("NEMT_SESSION_SECRET must be at least 32 characters")

    cookie_secure = env_bool("NEMT_COOKIE_SECURE", mode is AppMode.LIVE)
    if mode is AppMode.LIVE and not cookie_secure:
        raise ConfigError("NEMT_COOKIE_SECURE must be true in LIVE mode")

    database_path = Path(
        env("NEMT_DATABASE_PATH", str(BACKEND_DIR / ".data" / "nemt_app.sqlite3")) or ""
    ).expanduser()
    if not database_path.is_absolute():
        database_path = (REPO_ROOT / database_path).resolve()

    demo_passwords: dict[str, str] = {}
    if mode is AppMode.DEMO:
        demo_passwords = {
            "viewer": env("NEMT_VIEWER_PASSWORD", "nemt-viewer") or "nemt-viewer",
            "demo": env("NEMT_DEMO_PASSWORD", "nemt-demo") or "nemt-demo",
            "admin": env("NEMT_ADMIN_PASSWORD", "nemt-admin") or "nemt-admin",
        }

    operator_users: dict[str, tuple[str, tuple[str, ...]]] = {}
    if mode in (AppMode.TESTNET, AppMode.LIVE):
        prefix = "TESTNET" if mode is AppMode.TESTNET else "LIVE"
        trader_password = env(f"NEMT_{prefix}_TRADER_PASSWORD")
        admin_password = env(f"NEMT_{prefix}_ADMIN_PASSWORD")
        if trader_password:
            if len(trader_password) < 12:
                raise ConfigError(
                    f"NEMT_{prefix}_TRADER_PASSWORD must be at least 12 characters"
                )
            operator_users[
                env(f"NEMT_{prefix}_TRADER_USERNAME", "trader") or "trader"
            ] = (trader_password, ("viewer", "trader"))
        if admin_password:
            if len(admin_password) < 12:
                raise ConfigError(
                    f"NEMT_{prefix}_ADMIN_PASSWORD must be at least 12 characters"
                )
            operator_users[
                env(f"NEMT_{prefix}_ADMIN_USERNAME", "admin") or "admin"
            ] = (admin_password, ("viewer", "trader", "admin"))
        if not operator_users:
            if mode is AppMode.LIVE:
                # Fail closed: LIVE without a real operator account would leave
                # only the leftover DEMO logins able to reach the order path.
                raise ConfigError(
                    "LIVE mode requires an operator account: set"
                    " NEMT_LIVE_TRADER_PASSWORD and/or NEMT_LIVE_ADMIN_PASSWORD"
                    " (minimum 12 characters). Demo accounts are disabled in LIVE."
                )
            print(
                "WARNING: TESTNET mode has no operator users. Set"
                " NEMT_TESTNET_TRADER_PASSWORD and/or NEMT_TESTNET_ADMIN_PASSWORD"
                " before signing in. Demo accounts are not seeded outside DEMO.",
                file=sys.stderr,
            )

    settings = Settings(
        mode=mode,
        database_path=database_path,
        session_secret=session_secret,
        session_ttl_seconds=env_int("NEMT_SESSION_TTL_SECONDS", 12 * 60 * 60, minimum=300),
        confirmation_ttl_seconds=env_int("NEMT_CONFIRMATION_TTL_SECONDS", 90, minimum=15),
        cookie_secure=cookie_secure,
        allowed_symbols=allowed_symbols,
        market_source=market_source,
        market_stale_seconds=env_int("NEMT_MARKET_STALE_SECONDS", 20, minimum=5),
        account_stale_seconds=env_int("NEMT_ACCOUNT_STALE_SECONDS", 60, minimum=10),
        allow_testnet_trading=env_bool("NEMT_ALLOW_TESTNET_TRADING", False),
        live_trading_enabled=env_bool("NEMT_LIVE_TRADING_ENABLED", False),
        binance_api_key=env("NEMT_BINANCE_API_KEY"),
        binance_api_secret=env("NEMT_BINANCE_API_SECRET"),
        binance_recv_window_ms=env_int("NEMT_BINANCE_RECV_WINDOW_MS", 5000, minimum=1000),
        min_order_notional=env_decimal("NEMT_MIN_ORDER_NOTIONAL", "5"),
        max_order_notional=env_decimal("NEMT_MAX_ORDER_NOTIONAL", "100"),
        max_daily_notional=env_decimal("NEMT_MAX_DAILY_NOTIONAL", "1000"),
        max_position_notional=env_decimal("NEMT_MAX_POSITION_NOTIONAL", "1000"),
        max_open_orders=env_int("NEMT_MAX_OPEN_ORDERS", 5),
        max_orders_per_minute=env_int("NEMT_MAX_ORDERS_PER_MINUTE", 10),
        trading_fee_rate=env_decimal("NEMT_TRADING_FEE_RATE", "0.001"),
        demo_initial_usdt=env_decimal("NEMT_DEMO_INITIAL_USDT", "10000"),
        demo_initial_btc=env_decimal("NEMT_DEMO_INITIAL_BTC", "0.002"),
        paper_initial_equity=env_decimal("NEMT_PAPER_INITIAL_EQUITY", "2000"),
        paper_symbols=tuple(
            s.upper() for s in env_csv("NEMT_PAPER_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT")
        ),
        paper_taker_fee_spot=env_decimal("NEMT_PAPER_TAKER_FEE_SPOT", "0.001"),
        paper_taker_fee_perp=env_decimal("NEMT_PAPER_TAKER_FEE_PERP", "0.0005"),
        paper_slippage_bps=env_decimal("NEMT_PAPER_SLIPPAGE_BPS", "5"),
        paper_maintenance_margin_rate=env_decimal(
            "NEMT_PAPER_MAINTENANCE_MARGIN_RATE", "0.004"
        ),
        paper_funding_interval_hours=env_int("NEMT_PAPER_FUNDING_INTERVAL_HOURS", 8),
        paper_max_leverage=env_int("NEMT_PAPER_MAX_LEVERAGE", 10),
        paper_min_notional=env_decimal("NEMT_PAPER_MIN_NOTIONAL", "5"),
        nemt_critical_entropy=env_decimal("NEMT_NEMT_CRITICAL_ENTROPY", "0.7"),
        nemt_critical_psi=env_decimal("NEMT_NEMT_CRITICAL_PSI", "0.5"),
        nemt_stable_psi=env_decimal("NEMT_NEMT_STABLE_PSI", "0.3"),
        nemt_ema_alpha=env_decimal("NEMT_NEMT_EMA_ALPHA", "0.3"),
        nemt_low_entropy=env_decimal("NEMT_NEMT_LOW_ENTROPY", "0.15"),
        nemt_atr_period=env_int("NEMT_NEMT_ATR_PERIOD", 14),
        nemt_bars=env_int("NEMT_NEMT_BARS", 120, minimum=30),
        nemt_risk_per_trade_pct=env_decimal("NEMT_NEMT_RISK_PER_TRADE_PCT", "1"),
        auto_trade_enabled=env_bool("NEMT_AUTO_TRADE_ENABLED", True),
        auto_trade_username=env("NEMT_AUTO_TRADE_USERNAME", "demo") or "demo",
        auto_trade_interval_seconds=env_int(
            "NEMT_AUTO_TRADE_INTERVAL_SECONDS", 60, minimum=10
        ),
        auto_trade_interval=env("NEMT_AUTO_TRADE_INTERVAL", "15m") or "15m",
        auto_trade_max_positions=env_int("NEMT_AUTO_TRADE_MAX_POSITIONS", 3),
        auto_trade_cooldown_minutes=env_int("NEMT_AUTO_TRADE_COOLDOWN_MINUTES", 15),
        demo_passwords=demo_passwords,
        operator_users=operator_users,
        allowed_origins=env_csv(
            "NEMT_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ),
    )

    if settings.live_trading_enabled and mode is AppMode.LIVE:
        print(
            "WARNING: NEMT_LIVE_TRADING_ENABLED is on. Orders are submitted to"
            " the Binance production venue and spend real money."
            f" operator accounts={sorted(settings.operator_users)};"
            f" max order={settings.max_order_notional} USDT;"
            f" max daily={settings.max_daily_notional} USDT.",
            file=sys.stderr,
        )
    elif settings.live_trading_enabled:
        print(
            "WARNING: NEMT_LIVE_TRADING_ENABLED is set but NEMT_APP_MODE is not"
            " LIVE; no real-money order path is active.",
            file=sys.stderr,
        )

    return settings
