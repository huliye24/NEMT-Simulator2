"""NEMT App Cloud API (v1).

Run from the backend directory:

    uvicorn trade_app.main:create_app --factory --host 127.0.0.1 --port 8000

The app never sends exchange credentials to the browser. All trading
mutations require a session, RBAC, CSRF and a server-issued confirmation.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .accounts import AccountService
from .admin import AdminService
from .auth import AuthService, SessionContext
from .auto_trader import AutoTrader
from .binance_spot import BinanceSpotAdapter
from .config import AppMode, Settings, load_settings
from .db import Database, iso
from .errors import ApiException
from .market import MarketService, MarketUnavailable
from .orders import OrderService
from .paper import PaperService
from .risk import RiskService
from .schemas import (
    AuditEventOut,
    AuditEventsOut,
    AutoTradeEventOut,
    AutoTradeRunOut,
    AutoTradeStatusOut,
    AutoTradeToggleOut,
    AutoTradeToggleRequest,
    BalanceOut,
    BalancesOut,
    CancelOpenOrdersOut,
    CancelOpenOrdersRequest,
    DemoLoginRequest,
    ErrorResponse,
    FlagStateOut,
    KlineOut,
    KlinesOut,
    LoginRequest,
    LogoutOut,
    OrderCreateOut,
    OrderCreateRequest,
    OrderOut,
    OrderPreviewOut,
    OrderPreviewRequest,
    OrdersOut,
    PaperAccountOut,
    PaperCloseOut,
    PaperCloseRequest,
    PaperEquityOut,
    PaperEquityPointOut,
    PaperFillOut,
    PaperFillsOut,
    PaperOpenRequest,
    PaperPositionOut,
    PaperPositionsOut,
    PaperResetOut,
    PauseRequest,
    SessionOut,
    SignalCardOut,
    SignalsOut,
    StrategyBoardOut,
    SystemStatusOut,
    TickerOut,
    UserOut,
)
from .signals import NemtSignalService

logger = logging.getLogger("nemt.trade_api")

REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{8,64}$")
SAFE_VALIDATION_FIELDS = ("loc", "msg", "type")


@dataclass
class AppServices:
    settings: Settings
    db: Database
    auth: AuthService
    market: MarketService
    accounts: AccountService
    risk: RiskService
    orders: OrderService
    admin: AdminService
    adapter: BinanceSpotAdapter | None
    paper: PaperService | None = None
    signals: NemtSignalService | None = None
    auto_trader: AutoTrader | None = None


def _services(request: Request) -> AppServices:
    return request.app.state.services


def _set_session_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )


def _session_out(session: SessionContext, settings: Settings) -> SessionOut:
    return SessionOut(
        user=UserOut(username=session.user.username, roles=list(session.user.roles)),
        csrf_token=session.csrf_token,
        expires_at=session.expires_at,
        mode=settings.mode.value,
    )


async def get_session(request: Request) -> SessionContext:
    services = _services(request)
    token = request.cookies.get(services.settings.cookie_name)
    session = services.auth.authenticate(token)
    if session is None:
        raise ApiException(401, "auth_required", "请先登录 NEMT DEMO/服务端账户")
    return session


def require_role(required: str) -> Callable[..., Any]:
    async def dependency(session: SessionContext = Depends(get_session)) -> SessionContext:
        if not session.user.has_role(required):
            raise ApiException(403, "forbidden", f"需要 {required} 权限")
        return session

    return dependency


async def require_csrf(
    request: Request,
    session: SessionContext = Depends(get_session),
) -> SessionContext:
    provided = request.headers.get("x-csrf-token")
    services = _services(request)
    if not services.auth.verify_csrf(session.csrf_token, provided):
        raise ApiException(403, "csrf_invalid", "CSRF 校验失败，请刷新页面后重试")
    return session


def _ticker_out(ticker: Any) -> TickerOut:
    return TickerOut(
        symbol=ticker.symbol,
        last_price=ticker.last_price,
        price_change=ticker.price_change,
        price_change_percent=ticker.price_change_percent,
        high_price=ticker.high_price,
        low_price=ticker.low_price,
        volume=ticker.volume,
        quote_volume=ticker.quote_volume,
        event_time=ticker.event_time,
        fetched_at=ticker.fetched_at,
        source=ticker.source,
        stale=ticker.stale,
    )


def _balances_out(snapshot: Any, mode: str) -> BalancesOut:
    return BalancesOut(
        mode=mode,
        account_status=snapshot.status,
        connected=snapshot.connected,
        source=snapshot.source,
        fetched_at=snapshot.fetched_at,
        stale=snapshot.stale,
        note=snapshot.note,
        balances=[
            BalanceOut(
                asset=item.asset,
                free=item.free,
                locked=item.locked,
                total=item.total,
            )
            for item in snapshot.balances
        ],
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or load_settings()
    db = Database(config.database_path)
    db.initialize(config)

    adapter: BinanceSpotAdapter | None = None
    if config.binance_api_key and config.binance_api_secret and config.mode is not AppMode.DEMO:
        adapter = BinanceSpotAdapter(config)

    market = MarketService(config)
    accounts = AccountService(db, config, adapter)
    risk = RiskService(db, config)
    orders = OrderService(db, config, market, risk, accounts, adapter)
    admin = AdminService(db, config, risk, orders)
    auth = AuthService(db, config)
    paper = PaperService(db, config, market)
    signals = NemtSignalService(config, market)
    auto_trader = AutoTrader(db, config, paper, signals)
    services = AppServices(
        settings=config,
        db=db,
        auth=auth,
        market=market,
        accounts=accounts,
        risk=risk,
        orders=orders,
        admin=admin,
        adapter=adapter,
        paper=paper,
        signals=signals,
        auto_trader=auto_trader,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("NEMT App API starting in %s mode", config.mode.value)
        auto_trader.start()
        try:
            yield
        finally:
            await auto_trader.stop()
            await market.close()
            if adapter is not None:
                await adapter.close()
            logger.info("NEMT App API stopped")

    app = FastAPI(
        title="NEMT App API",
        version=config.app_version,
        description=(
            "NEMT App V0.1 cloud API. DEMO is local simulation only; TESTNET "
            "requires server-side credentials and an explicit allow flag. "
            "V0.1 exposes no LIVE order-writing path."
        ),
        lifespan=lifespan,
        docs_url=f"{config.api_prefix}/docs",
        redoc_url=None,
        openapi_url=f"{config.api_prefix}/openapi.json",
    )
    app.state.services = services
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next: Any) -> Response:
        header_request_id = request.headers.get("x-request-id", "")
        request_id = (
            header_request_id
            if REQUEST_ID_RE.match(header_request_id)
            else uuid.uuid4().hex
        )
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled error method=%s path=%s request_id=%s",
                request.method,
                request.url.path,
                request_id,
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": "服务端内部错误",
                        "request_id": request_id,
                        "details": None,
                    }
                },
            )
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith(config.api_prefix):
            response.headers["Cache-Control"] = "no-store"
        logger.info(
            "%s %s -> %s (%.1fms) request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response

    @app.exception_handler(ApiException)
    async def api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": getattr(request.state, "request_id", None),
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        safe_errors = [
            {key: item[key] for key in SAFE_VALIDATION_FIELDS if key in item}
            for item in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "请求参数不合法",
                    "request_id": getattr(request.state, "request_id", None),
                    "details": {"errors": safe_errors},
                }
            },
        )

    prefix = config.api_prefix

    @app.get(f"{prefix}/health", tags=["system"])
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "mode": config.mode.value,
            "version": config.app_version,
            "server_time": iso(),
        }

    @app.get(f"{prefix}/health/ready", tags=["system"])
    async def readiness() -> dict[str, Any]:
        try:
            db.query_one("SELECT 1 AS ok")
        except Exception as exc:
            raise ApiException(503, "database_unavailable", "数据库不可用") from exc
        return {
            "status": "ready",
            "database": "ok",
            "market_source": config.market_source,
            "trading_enabled": config.trading_enabled,
        }

    @app.post(
        f"{prefix}/auth/login",
        response_model=SessionOut,
        responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
        tags=["auth"],
    )
    async def login(payload: LoginRequest, request: Request, response: Response) -> SessionOut:
        try:
            session = services.auth.login(
                payload.username,
                payload.password,
                client_ip=request.client.host if request.client else "unknown",
                request_id=request.state.request_id,
            )
        except PermissionError as exc:
            raise ApiException(429, "login_rate_limited", str(exc)) from exc
        except ValueError as exc:
            raise ApiException(401, "invalid_credentials", str(exc)) from exc
        _set_session_cookie(response, config, session.token)
        return _session_out(session, config)

    @app.post(
        f"{prefix}/auth/demo",
        response_model=SessionOut,
        responses={404: {"model": ErrorResponse}},
        tags=["auth"],
    )
    async def demo_login(
        payload: DemoLoginRequest, request: Request, response: Response
    ) -> SessionOut:
        if not config.is_demo:
            raise ApiException(404, "not_available", "演示登录仅在 DEMO 环境可用")
        try:
            session = services.auth.demo_login(
                payload.account, request_id=request.state.request_id
            )
        except (PermissionError, ValueError) as exc:
            raise ApiException(403, "demo_login_unavailable", str(exc)) from exc
        _set_session_cookie(response, config, session.token)
        return _session_out(session, config)

    @app.get(
        f"{prefix}/auth/me",
        response_model=SessionOut,
        responses={401: {"model": ErrorResponse}},
        tags=["auth"],
    )
    async def me(
        session: SessionContext = Depends(get_session),
    ) -> SessionOut:
        return _session_out(session, config)

    @app.post(f"{prefix}/auth/logout", response_model=LogoutOut, tags=["auth"])
    async def logout(
        request: Request,
        response: Response,
        session: SessionContext = Depends(require_csrf),
    ) -> LogoutOut:
        services.auth.logout(session, request_id=request.state.request_id)
        _clear_session_cookie(response, config)
        return LogoutOut()

    @app.get(
        f"{prefix}/system/status",
        response_model=SystemStatusOut,
        responses={401: {"model": ErrorResponse}},
        tags=["system"],
    )
    async def system_status(
        session: SessionContext = Depends(require_role("viewer")),
    ) -> SystemStatusOut:
        market_health = await market.feed_health()
        account = await accounts.snapshot(session.user.username)
        flag_state = risk.flag_state()
        paused = bool(flag_state["pause_new_orders"])
        trading_enabled = config.trading_enabled and not paused
        return SystemStatusOut(
            mode=config.mode.value,
            version=config.app_version,
            server_time=iso(),
            authenticated=True,
            user=UserOut(
                username=session.user.username, roles=list(session.user.roles)
            ),
            flags={
                "server_ok": True,
                "authenticated": True,
                "market_fresh": market_health.get("status") == "ok",
                "account_connected": account.connected,
                "trading_enabled": trading_enabled,
                "paused": paused,
            },
            trading_enabled=trading_enabled,
            live_trading_available=config.live_trading_available,
            market=market_health,
            account={
                "status": account.status,
                "connected": account.connected,
                "source": account.source,
                "fetched_at": account.fetched_at,
                "stale": account.stale,
                "note": account.note,
            },
            risk=FlagStateOut(**flag_state),
            limits=config.public_status()["limits"],
        )

    @app.get(
        f"{prefix}/market/ticker",
        response_model=TickerOut,
        tags=["market"],
    )
    async def ticker(
        symbol: str = Query(default=config.allowed_symbols[0], max_length=20),
        _: SessionContext = Depends(require_role("viewer")),
    ) -> TickerOut:
        try:
            return _ticker_out(await market.ticker(symbol))
        except MarketUnavailable as exc:
            raise ApiException(503, "market_unavailable", str(exc)) from exc

    @app.get(
        f"{prefix}/market/klines",
        response_model=KlinesOut,
        tags=["market"],
    )
    async def klines(
        symbol: str = Query(default=config.allowed_symbols[0], max_length=20),
        interval: str = Query(default="5m", max_length=5),
        limit: int = Query(default=80, ge=10, le=200),
        _: SessionContext = Depends(require_role("viewer")),
    ) -> KlinesOut:
        try:
            series = await market.klines(symbol, interval, limit)
        except MarketUnavailable as exc:
            raise ApiException(503, "market_unavailable", str(exc)) from exc
        return KlinesOut(
            symbol=series.symbol,
            interval=series.interval,
            source=series.source,
            stale=series.stale,
            fetched_at=series.fetched_at,
            items=[
                KlineOut(
                    open_time=item.open_time,
                    open_time_iso=item.open_time_iso,
                    open=item.open,
                    high=item.high,
                    low=item.low,
                    close=item.close,
                    volume=item.volume,
                    close_time=item.close_time,
                    is_closed=item.is_closed,
                )
                for item in series.items
            ],
        )

    @app.get(
        f"{prefix}/account/balances",
        response_model=BalancesOut,
        tags=["account"],
    )
    async def balances(
        session: SessionContext = Depends(require_role("viewer")),
    ) -> BalancesOut:
        snapshot = await accounts.snapshot(session.user.username)
        return _balances_out(snapshot, config.mode.value)

    @app.post(
        f"{prefix}/orders/preview",
        response_model=OrderPreviewOut,
        responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
        tags=["orders"],
    )
    async def preview_order(
        payload: OrderPreviewRequest,
        request: Request,
        session: SessionContext = Depends(require_csrf),
    ) -> OrderPreviewOut:
        if not session.user.has_role("trader"):
            raise ApiException(403, "forbidden", "需要 trader 权限")
        return await orders.preview(
            username=session.user.username,
            request=payload,
            request_id=request.state.request_id,
        )

    @app.post(
        f"{prefix}/orders",
        response_model=OrderCreateOut,
        status_code=201,
        responses={422: {"model": ErrorResponse}},
        tags=["orders"],
    )
    async def create_order(
        payload: OrderCreateRequest,
        request: Request,
        response: Response,
        session: SessionContext = Depends(require_csrf),
    ) -> OrderCreateOut:
        if not session.user.has_role("trader"):
            raise ApiException(403, "forbidden", "需要 trader 权限")
        order, replayed = await orders.create(
            username=session.user.username,
            confirmation_token=payload.confirmation_token,
            idempotency_key=payload.idempotency_key,
            request_id=request.state.request_id,
        )
        if replayed:
            response.status_code = 200
        return OrderCreateOut(order=order, replayed=replayed)

    @app.get(f"{prefix}/orders", response_model=OrdersOut, tags=["orders"])
    async def list_orders(
        status_filter: str | None = Query(default=None, alias="status", max_length=20),
        limit: int = Query(default=100, ge=1, le=200),
        session: SessionContext = Depends(require_role("viewer")),
    ) -> OrdersOut:
        items, open_count = orders.list_orders(
            session.user.username, status_filter=status_filter, limit=limit
        )
        return OrdersOut(
            orders=items,
            count=len(items),
            open_count=open_count,
            status_filter=status_filter,
        )

    @app.post(
        f"{prefix}/orders/{{order_id}}/cancel",
        response_model=OrderOut,
        responses={409: {"model": ErrorResponse}},
        tags=["orders"],
    )
    async def cancel_order(
        order_id: str,
        request: Request,
        session: SessionContext = Depends(require_csrf),
    ) -> OrderOut:
        if not session.user.has_role("trader"):
            raise ApiException(403, "forbidden", "需要 trader 权限")
        return await orders.cancel(
            username=session.user.username,
            order_id=order_id,
            request_id=request.state.request_id,
        )

    @app.post(
        f"{prefix}/admin/pause-new-orders",
        response_model=FlagStateOut,
        tags=["admin"],
    )
    async def pause_new_orders(
        payload: PauseRequest,
        request: Request,
        session: SessionContext = Depends(require_role("admin")),
        _: SessionContext = Depends(require_csrf),
    ) -> FlagStateOut:
        state = admin.pause(
            actor=session.user.username,
            reason=payload.reason,
            request_id=request.state.request_id,
        )
        return FlagStateOut(**state)

    @app.post(
        f"{prefix}/admin/resume-new-orders",
        response_model=FlagStateOut,
        tags=["admin"],
    )
    async def resume_new_orders(
        payload: PauseRequest,
        request: Request,
        session: SessionContext = Depends(require_role("admin")),
        _: SessionContext = Depends(require_csrf),
    ) -> FlagStateOut:
        state = admin.resume(
            actor=session.user.username,
            reason=payload.reason,
            request_id=request.state.request_id,
        )
        return FlagStateOut(**state)

    @app.post(
        f"{prefix}/admin/cancel-open-orders",
        response_model=CancelOpenOrdersOut,
        tags=["admin"],
    )
    async def cancel_open_orders(
        payload: CancelOpenOrdersRequest,
        request: Request,
        session: SessionContext = Depends(require_role("admin")),
        _: SessionContext = Depends(require_csrf),
    ) -> CancelOpenOrdersOut:
        result = await admin.cancel_open_orders(
            actor=session.user.username,
            confirm=payload.confirm,
            reason=payload.reason,
            request_id=request.state.request_id,
        )
        return CancelOpenOrdersOut(**result)

    @app.get(
        f"{prefix}/audit/events",
        response_model=AuditEventsOut,
        tags=["admin"],
    )
    async def audit_events(
        limit: int = Query(default=100, ge=1, le=500),
        _: SessionContext = Depends(require_role("admin")),
    ) -> AuditEventsOut:
        events = admin.audit_events(limit)
        return AuditEventsOut(
            events=[AuditEventOut(**event) for event in events], count=len(events)
        )

    # ------------------------------------------------------------------
    # Paper trading (纸上交易). Simulated money, real quotes; no exchange
    # credentials are involved and no order can leave this process.
    # ------------------------------------------------------------------

    @app.get(
        f"{prefix}/paper/account",
        response_model=PaperAccountOut,
        tags=["paper"],
    )
    async def paper_account(
        session: SessionContext = Depends(require_role("viewer")),
    ) -> PaperAccountOut:
        return PaperAccountOut(**await paper.account(session.user.username))

    @app.get(
        f"{prefix}/paper/positions",
        response_model=PaperPositionsOut,
        tags=["paper"],
    )
    async def paper_positions(
        session: SessionContext = Depends(require_role("viewer")),
    ) -> PaperPositionsOut:
        username = session.user.username
        positions = await paper.positions(username)
        account = await paper.account(username)
        return PaperPositionsOut(
            account=PaperAccountOut(**account),
            positions=[PaperPositionOut(**item) for item in positions],
        )

    @app.post(
        f"{prefix}/paper/positions",
        response_model=PaperPositionsOut,
        responses={422: {"model": ErrorResponse}},
        tags=["paper"],
    )
    async def paper_open(
        payload: PaperOpenRequest,
        request: Request,
        session: SessionContext = Depends(require_csrf),
    ) -> PaperPositionsOut:
        if not session.user.has_role("trader"):
            raise ApiException(403, "forbidden", "需要 trader 权限")
        username = session.user.username
        await paper.open_position(
            username,
            symbol=payload.symbol,
            market=payload.market,
            side=payload.side,
            notional=payload.notional,
            leverage=payload.leverage,
            strategy=payload.strategy,
        )
        positions = await paper.positions(username)
        account = await paper.account(username)
        logger.info(
            "paper open user=%s %s %s %s notional=%s lev=%s request_id=%s",
            username,
            payload.market,
            payload.side,
            payload.symbol,
            payload.notional,
            payload.leverage,
            request.state.request_id,
        )
        return PaperPositionsOut(
            account=PaperAccountOut(**account),
            positions=[PaperPositionOut(**item) for item in positions],
        )

    @app.post(
        f"{prefix}/paper/positions/{{position_id}}/close",
        response_model=PaperCloseOut,
        responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
        tags=["paper"],
    )
    async def paper_close(
        position_id: str,
        payload: PaperCloseRequest,
        session: SessionContext = Depends(require_csrf),
    ) -> PaperCloseOut:
        if not session.user.has_role("trader"):
            raise ApiException(403, "forbidden", "需要 trader 权限")
        username = session.user.username
        result = await paper.close_position(
            username, position_id, fraction=payload.fraction
        )
        account = await paper.account(username)
        return PaperCloseOut(**result, account=PaperAccountOut(**account))

    @app.get(
        f"{prefix}/paper/fills",
        response_model=PaperFillsOut,
        tags=["paper"],
    )
    async def paper_fills(
        limit: int = Query(default=100, ge=1, le=500),
        session: SessionContext = Depends(require_role("viewer")),
    ) -> PaperFillsOut:
        items = paper.fills(session.user.username, limit)
        return PaperFillsOut(
            fills=[PaperFillOut(**item) for item in items], count=len(items)
        )

    @app.get(
        f"{prefix}/paper/equity",
        response_model=PaperEquityOut,
        tags=["paper"],
    )
    async def paper_equity(
        limit: int = Query(default=200, ge=2, le=1000),
        session: SessionContext = Depends(require_role("viewer")),
    ) -> PaperEquityOut:
        points = paper.equity_curve(session.user.username, limit)
        return PaperEquityOut(
            points=[PaperEquityPointOut(**item) for item in points],
            count=len(points),
        )

    @app.post(
        f"{prefix}/paper/reset",
        response_model=PaperResetOut,
        tags=["paper"],
    )
    async def paper_reset(
        session: SessionContext = Depends(require_csrf),
    ) -> PaperResetOut:
        if not session.user.has_role("trader"):
            raise ApiException(403, "forbidden", "需要 trader 权限")
        return PaperResetOut(account=PaperAccountOut(**await paper.reset(session.user.username)))

    # ------------------------------------------------------------------
    # NEMT signal board (相位/动量). Read-only: it never places an order;
    # the UI turns a card into a *paper* position if the operator chooses.
    # ------------------------------------------------------------------

    @app.get(
        f"{prefix}/signals/nemt",
        response_model=SignalsOut,
        tags=["signals"],
    )
    async def nemt_signals(
        interval: str = Query(default="15m", max_length=5),
        symbols: str | None = Query(default=None, max_length=120),
        session: SessionContext = Depends(require_role("viewer")),
    ) -> SignalsOut:
        wanted = (
            tuple(item.strip().upper() for item in symbols.split(",") if item.strip())
            if symbols
            else config.paper_symbols
        )
        state = await paper.account(session.user.username) if paper else None
        equity = state["equity"] if state else config.paper_initial_equity
        cards = await signals.board(wanted, interval, equity=equity)
        if not cards:
            raise ApiException(503, "market_unavailable", "暂时取不到任何 NEMT 信号")
        return SignalsOut(
            interval=interval,
            equity=equity,
            risk_per_trade_pct=config.nemt_risk_per_trade_pct,
            thresholds={
                "critical_entropy": config.nemt_critical_entropy,
                "critical_psi": config.nemt_critical_psi,
                "stable_psi": config.nemt_stable_psi,
                "low_entropy": config.nemt_low_entropy,
            },
            cards=[SignalCardOut(**card.as_dict()) for card in cards],
            count=len(cards),
        )

    # ------------------------------------------------------------------
    # Strategy board: the auto trader's view of the book. The execution page
    # renders this instead of a static fixture, so every number is real.
    # ------------------------------------------------------------------

    @app.get(
        f"{prefix}/strategy/board",
        response_model=StrategyBoardOut,
        tags=["strategy"],
    )
    async def strategy_board(
        session: SessionContext = Depends(require_role("viewer")),
    ) -> StrategyBoardOut:
        # DEMO shares one paper book (the auto trader's account) so the operator
        # sees the strategy's positions rather than an empty personal wallet.
        username = (
            config.auto_trade_username
            if config.is_demo
            else session.user.username
        )
        payload = await auto_trader.board(username)
        return StrategyBoardOut(**payload)

    @app.post(
        f"{prefix}/strategy/auto-trade",
        response_model=AutoTradeToggleOut,
        tags=["strategy"],
    )
    async def toggle_auto_trade(
        payload: AutoTradeToggleRequest,
        request: Request,
        session: SessionContext = Depends(require_csrf),
    ) -> AutoTradeToggleOut:
        if not session.user.has_role("trader"):
            raise ApiException(403, "forbidden", "需要 trader 权限")
        enabled = auto_trader.set_enabled(
            payload.enabled, actor=session.user.username
        )
        logger.info(
            "auto trade toggled to %s by %s request_id=%s",
            enabled,
            session.user.username,
            request.state.request_id,
        )
        return AutoTradeToggleOut(enabled=enabled, last_run_at=auto_trader._last_run_at)

    @app.post(
        f"{prefix}/strategy/run-once",
        response_model=AutoTradeRunOut,
        tags=["strategy"],
    )
    async def run_auto_trade_once(
        session: SessionContext = Depends(require_csrf),
    ) -> AutoTradeRunOut:
        if not session.user.has_role("trader"):
            raise ApiException(403, "forbidden", "需要 trader 权限")
        decisions = await auto_trader.run_once()
        return AutoTradeRunOut(decisions=decisions, count=len(decisions))

    return app
