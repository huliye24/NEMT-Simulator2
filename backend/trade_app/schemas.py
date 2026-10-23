"""Versioned API contracts. These models generate the OpenAPI document."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    PENDING_RECONCILIATION = "PENDING_RECONCILIATION"


PositiveDecimal = Annotated[Decimal, Field(gt=0)]
IdempotencyKey = Annotated[
    str, Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
]


class ApiError(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ApiError


class UserOut(BaseModel):
    username: str
    roles: list[str]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class DemoLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account: Literal["viewer", "demo", "admin"] = "demo"


class SessionOut(BaseModel):
    authenticated: bool = True
    user: UserOut
    csrf_token: str
    expires_at: str
    mode: str


class LogoutOut(BaseModel):
    ok: bool = True


class TickerOut(BaseModel):
    symbol: str
    last_price: Decimal
    price_change: Decimal
    price_change_percent: Decimal
    high_price: Decimal
    low_price: Decimal
    volume: Decimal
    quote_volume: Decimal
    event_time: str | None
    fetched_at: str
    source: Literal["binance", "demo"]
    stale: bool


class KlineOut(BaseModel):
    open_time: int
    open_time_iso: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time: int
    is_closed: bool


class KlinesOut(BaseModel):
    symbol: str
    interval: str
    source: Literal["binance", "demo"]
    stale: bool
    fetched_at: str
    items: list[KlineOut]


class BalanceOut(BaseModel):
    asset: str
    free: Decimal
    locked: Decimal
    total: Decimal


class BalancesOut(BaseModel):
    mode: str
    account_status: Literal["CONNECTED", "NOT_CONFIGURED", "DISCONNECTED", "ERROR"]
    connected: bool
    source: Literal["demo", "binance", "none"]
    fetched_at: str | None
    stale: bool
    note: str | None = None
    balances: list[BalanceOut]


class RiskCheckOut(BaseModel):
    code: str
    passed: bool
    message: str


class RiskDecisionOut(BaseModel):
    approved: bool
    checked_at: str
    reasons: list[str]
    checks: list[RiskCheckOut]


class OrderPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(default="BTCUSDT", min_length=6, max_length=20)
    side: Side
    type: OrderType
    quantity: PositiveDecimal
    price: PositiveDecimal | None = None
    time_in_force: Literal["GTC"] = "GTC"


class OrderDraftOut(BaseModel):
    symbol: str
    side: Side
    type: OrderType
    time_in_force: str
    quantity: Decimal
    price: Decimal | None
    latest_price: Decimal
    estimated_notional: Decimal
    estimated_fee: Decimal
    fee_asset: str
    normalized: bool


class OrderPreviewOut(BaseModel):
    preview_token: str
    expires_at: str
    draft: OrderDraftOut
    risk: RiskDecisionOut
    warnings: list[str]
    mode: str
    market_source: str
    market_fetched_at: str
    account_fetched_at: str | None
    account_stale: bool


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation_token: str = Field(min_length=20, max_length=256)
    idempotency_key: IdempotencyKey


class FillOut(BaseModel):
    id: str
    exchange_trade_id: str | None
    price: Decimal
    quantity: Decimal
    commission: Decimal
    commission_asset: str | None
    filled_at: str


class OrderOut(BaseModel):
    id: str
    client_order_id: str
    exchange_order_id: str | None
    mode: str
    symbol: str
    side: Side
    type: OrderType
    time_in_force: str | None
    price: Decimal | None
    quantity: Decimal
    filled_qty: Decimal
    avg_fill_price: Decimal | None
    status: OrderStatus
    fee: Decimal
    fee_asset: str | None
    reserved_amount: Decimal
    reserved_asset: str | None
    error_code: str | None
    error_message: str | None
    created_at: str
    updated_at: str
    submitted_at: str | None
    risk: RiskDecisionOut | None
    fills: list[FillOut]


class OrderCreateOut(BaseModel):
    order: OrderOut
    replayed: bool = False


class OrdersOut(BaseModel):
    orders: list[OrderOut]
    count: int
    open_count: int
    status_filter: str | None = None


class PauseRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=200)


class CancelOpenOrdersRequest(BaseModel):
    confirm: bool = False
    reason: str = Field(default="admin cancel-open-orders", min_length=3, max_length=200)


class FlagStateOut(BaseModel):
    pause_new_orders: bool
    pause_reason: str | None
    pause_updated_at: str | None
    pause_updated_by: str | None


class CancelOpenOrdersOut(BaseModel):
    ok: bool
    canceled: int
    failed: list[dict[str, str]]
    message: str


class AuditEventOut(BaseModel):
    id: int
    ts: str
    actor: str | None
    action: str
    mode: str
    request_id: str | None
    entity_type: str | None
    entity_id: str | None
    detail: dict[str, Any]


class AuditEventsOut(BaseModel):
    events: list[AuditEventOut]
    count: int


class SystemStatusOut(BaseModel):
    mode: str
    version: str
    server_time: str
    server_ok: bool = True
    authenticated: bool
    user: UserOut
    flags: dict[str, bool]
    trading_enabled: bool
    live_trading_available: bool
    market: dict[str, Any]
    account: dict[str, Any]
    risk: FlagStateOut
    limits: dict[str, Any]


# ---------------------------------------------------------------------------
# Paper trading (纸上交易). Simulated money, real quotes.
# ---------------------------------------------------------------------------


class PaperOpenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(default="BTCUSDT", min_length=6, max_length=20)
    market: Literal["SPOT", "PERP"] = "PERP"
    side: Literal["LONG", "SHORT"] = "LONG"
    notional: PositiveDecimal = Field(description="名义价值（USDT），不是保证金")
    leverage: int = Field(default=1, ge=1, le=50)
    strategy: str = Field(default="NEMT", min_length=1, max_length=32)


class PaperCloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fraction: PositiveDecimal = Decimal("1")


class PaperPositionOut(BaseModel):
    id: str
    strategy: str
    symbol: str
    market: Literal["SPOT", "PERP"]
    side: Literal["LONG", "SHORT"]
    qty: Decimal
    entry_price: Decimal
    mark_price: Decimal
    leverage: int
    margin: Decimal
    notional: Decimal
    unrealized: Decimal
    realized: Decimal
    fees: Decimal
    funding: Decimal
    liquidation_price: Decimal | None = None
    margin_ratio: Decimal
    price_change_pct: Decimal
    opened_at: str
    updated_at: str


class PaperAccountOut(BaseModel):
    username: str
    initial_equity: Decimal
    equity: Decimal
    cash: Decimal
    spot_value: Decimal
    perp_value: Decimal
    unrealized: Decimal
    realized: Decimal
    fees: Decimal
    funding: Decimal
    net_pnl: Decimal
    return_pct: Decimal
    open_positions: int
    mode: str


class PaperPositionsOut(BaseModel):
    account: PaperAccountOut
    positions: list[PaperPositionOut]


class PaperFillOut(BaseModel):
    id: str
    position_id: str
    symbol: str
    market: str
    side: str
    action: str
    qty: Decimal
    price: Decimal
    fee: Decimal
    realized_pnl: Decimal
    created_at: str


class PaperFillsOut(BaseModel):
    fills: list[PaperFillOut]
    count: int


class PaperEquityPointOut(BaseModel):
    at: str
    equity: Decimal
    cash: Decimal
    unrealized: Decimal
    realized: Decimal


class PaperEquityOut(BaseModel):
    points: list[PaperEquityPointOut]
    count: int


class PaperCloseOut(BaseModel):
    position_id: str
    closed: bool
    qty: Decimal
    exit_price: Decimal
    gross_pnl: Decimal
    fee: Decimal
    margin_released: Decimal
    leverage: int
    account: PaperAccountOut


class PaperResetOut(BaseModel):
    account: PaperAccountOut


# ---------------------------------------------------------------------------
# NEMT signal board (相位/动量). Read-only view of the strategy engine.
# ---------------------------------------------------------------------------


class SignalCardOut(BaseModel):
    symbol: str
    interval: str
    mark_price: Decimal
    direction: Literal["LONG", "SHORT", "WAIT", "EXIT", "HOLD"]
    strength: int
    action_label: str
    reasons: list[str]
    entry: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    stop_pct: Decimal = Decimal("0")
    risk_usdt: Decimal | None = None
    suggested_notional: Decimal | None = None
    suggested_leverage: int = 1
    # NEMT state
    psi: Decimal
    phi: Decimal
    entropy: Decimal
    phase: Literal["stable", "critical", "critical_up", "critical_down", "decay"]
    phase_label: str
    wave_amplitude: Decimal = Decimal("0")
    wave_frequency: Decimal = Decimal("0")


class SignalsOut(BaseModel):
    interval: str
    equity: Decimal
    risk_per_trade_pct: Decimal
    thresholds: dict[str, Decimal]
    cards: list[SignalCardOut]
    count: int


# ---------------------------------------------------------------------------
# Strategy board (what the execution page renders)
# ---------------------------------------------------------------------------


class StrategyLegFillOut(BaseModel):
    at: int
    action: str
    qty: float
    price: float
    fee: float


class StrategyLegOut(BaseModel):
    symbol: str
    market: str
    side: str
    leverage: int
    unit: str
    mark: str
    margin: str
    stop: str = ""
    take: str = ""
    fills: list[StrategyLegFillOut]


class StrategyOut(BaseModel):
    id: str
    name: str
    code: str
    version: str
    timeframe: str
    state: str
    signal: str
    risk: str
    legs: list[StrategyLegOut]


class StrategyAccountOut(BaseModel):
    equity: str
    cash: str
    unrealized: str
    realized: str
    return_pct: str
    initial_equity: str


class AutoTradeEventOut(BaseModel):
    id: int
    ts: str
    symbol: str | None = None
    action: str
    reason: str
    position_id: str | None = None


class AutoTradeStatusOut(BaseModel):
    enabled: bool
    username: str
    interval_seconds: int
    timeframe: str
    max_positions: int
    cooldown_minutes: int
    last_run_at: str | None = None
    last_error: str | None = None


class StrategyBoardOut(BaseModel):
    strategy: StrategyOut
    account: StrategyAccountOut
    signals: list[SignalCardOut]
    events: list[AutoTradeEventOut]
    auto_trade: AutoTradeStatusOut


class AutoTradeToggleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool


class AutoTradeToggleOut(BaseModel):
    enabled: bool
    last_run_at: str | None = None


class AutoTradeRunOut(BaseModel):
    decisions: list[dict[str, Any]]
    count: int
