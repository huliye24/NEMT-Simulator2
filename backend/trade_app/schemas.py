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
