"""Order preview, confirmation, idempotent submission, cancellation and audit."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from .accounts import AccountService, AccountSnapshot, Balance
from .binance_spot import BinanceError, BinanceOrderResult, BinanceSpotAdapter
from .config import AppMode, Settings
from .db import Database, decimal_str, iso, iso_after, parse_iso, utc_now
from .errors import ApiException
from .market import MarketService, MarketUnavailable, SymbolRules, Ticker
from .risk import OrderValidationError, RiskDecision, RiskService
from .schemas import (
    FillOut,
    OrderCreateOut,
    OrderDraftOut,
    OrderOut,
    OrderPreviewOut,
    OrderPreviewRequest,
    OrderStatus,
    OrderType,
    RiskDecisionOut,
    Side,
)
from .security import client_order_id_for, new_order_id, new_token, token_hash

OPEN_STATUSES = (
    OrderStatus.NEW.value,
    OrderStatus.PARTIALLY_FILLED.value,
    OrderStatus.PENDING_RECONCILIATION.value,
)
TERMINAL_STATUSES = {
    OrderStatus.FILLED.value,
    OrderStatus.CANCELED.value,
    OrderStatus.EXPIRED.value,
    OrderStatus.REJECTED.value,
}


def _decimal(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def _parse_risk(raw: str | None) -> RiskDecisionOut | None:
    if not raw:
        return None
    try:
        return RiskDecisionOut(**json.loads(raw))
    except (ValueError, TypeError):
        return None


class OrderService:
    def __init__(
        self,
        db: Database,
        settings: Settings,
        market: MarketService,
        risk: RiskService,
        accounts: AccountService,
        adapter: BinanceSpotAdapter | None,
    ):
        self.db = db
        self.settings = settings
        self.market = market
        self.risk = risk
        self.accounts = accounts
        self.adapter = adapter

    # ------------------------------------------------------------------
    # Queries and mappers
    # ------------------------------------------------------------------

    def _fills_for(self, order_id: str) -> list[FillOut]:
        rows = self.db.query_all(
            "SELECT id, exchange_trade_id, price, quantity, commission,"
            " commission_asset, filled_at FROM fills WHERE order_id = ? ORDER BY filled_at",
            (order_id,),
        )
        return [
            FillOut(
                id=str(row["id"]),
                exchange_trade_id=row["exchange_trade_id"],
                price=_decimal(row["price"]),
                quantity=_decimal(row["quantity"]),
                commission=_decimal(row["commission"]),
                commission_asset=row["commission_asset"],
                filled_at=str(row["filled_at"]),
            )
            for row in rows
        ]

    def _to_order_out(self, row: sqlite3.Row) -> OrderOut:
        return OrderOut(
            id=str(row["id"]),
            client_order_id=str(row["client_order_id"]),
            exchange_order_id=row["exchange_order_id"],
            mode=str(row["mode"]),
            symbol=str(row["symbol"]),
            side=Side(str(row["side"])),
            type=OrderType(str(row["type"])),
            time_in_force=row["time_in_force"],
            price=_decimal(row["price"]) if row["price"] is not None else None,
            quantity=_decimal(row["quantity"]),
            filled_qty=_decimal(row["filled_qty"]),
            avg_fill_price=(
                _decimal(row["avg_fill_price"]) if row["avg_fill_price"] is not None else None
            ),
            status=OrderStatus(str(row["status"])),
            fee=_decimal(row["fee"]),
            fee_asset=row["fee_asset"],
            reserved_amount=_decimal(row["reserved_amount"]),
            reserved_asset=row["reserved_asset"],
            error_code=row["error_code"],
            error_message=row["error_message"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            submitted_at=row["submitted_at"],
            risk=_parse_risk(row["risk_json"]),
            fills=self._fills_for(str(row["id"])),
        )

    def get_order(self, username: str, order_id: str) -> OrderOut:
        row = self.db.query_one(
            "SELECT * FROM orders WHERE id = ? AND username = ?", (order_id, username)
        )
        if row is None:
            raise ApiException(404, "order_not_found", "订单不存在")
        return self._to_order_out(row)

    def list_orders(
        self,
        username: str,
        *,
        status_filter: str | None = None,
        limit: int = 100,
    ) -> tuple[list[OrderOut], int]:
        limit = max(1, min(limit, 200))
        params: list[Any] = [username]
        if status_filter == "open":
            placeholders = ",".join("?" for _ in OPEN_STATUSES)
            where = f" AND status IN ({placeholders})"
            params.extend(OPEN_STATUSES)
        elif status_filter == "closed":
            placeholders = ",".join("?" for _ in TERMINAL_STATUSES)
            where = f" AND status IN ({placeholders})"
            params.extend(sorted(TERMINAL_STATUSES))
        elif status_filter:
            normalized = status_filter.upper()
            if normalized not in {item.value for item in OrderStatus}:
                raise ApiException(422, "invalid_status_filter", "无效的订单状态筛选")
            where = " AND status = ?"
            params.append(normalized)
        else:
            where = ""
        rows = self.db.query_all(
            f"SELECT * FROM orders WHERE username = ?{where}"
            " ORDER BY created_at DESC LIMIT ?",
            (*params, limit),
        )
        open_count_row = self.db.query_one(
            "SELECT COUNT(*) AS count FROM orders WHERE username = ? AND status IN (?, ?, ?)",
            (username, *OPEN_STATUSES),
        )
        return [self._to_order_out(row) for row in rows], int(open_count_row["count"] if open_count_row else 0)

    def _aggregates(
        self, conn: sqlite3.Connection, username: str
    ) -> tuple[int, int, Decimal]:
        mode = self.settings.mode.value
        open_row = conn.execute(
            "SELECT COUNT(*) AS count FROM orders"
            " WHERE username = ? AND mode = ? AND status IN (?, ?, ?)",
            (username, mode, *OPEN_STATUSES),
        ).fetchone()
        minute_ago = iso(utc_now() - timedelta(seconds=60))
        minute_row = conn.execute(
            "SELECT COUNT(*) AS count FROM orders"
            " WHERE username = ? AND mode = ? AND created_at >= ?",
            (username, mode, minute_ago),
        ).fetchone()
        midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        rows = conn.execute(
            "SELECT notional FROM orders WHERE username = ? AND mode = ?"
            " AND created_at >= ? AND status NOT IN (?, ?, ?)",
            (
                username,
                mode,
                iso(midnight),
                OrderStatus.REJECTED.value,
                OrderStatus.CANCELED.value,
                OrderStatus.EXPIRED.value,
            ),
        ).fetchall()
        daily_notional = sum((_decimal(row["notional"]) for row in rows), Decimal("0"))
        return (
            int(open_row["count"] if open_row else 0),
            int(minute_row["count"] if minute_row else 0),
            daily_notional,
        )

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    async def preview(
        self,
        *,
        username: str,
        request: OrderPreviewRequest,
        request_id: str,
    ) -> OrderPreviewOut:
        symbol = request.symbol.strip().upper()
        try:
            ticker = await self.market.ticker(symbol)
            rules = await self.market.symbol_rules(symbol)
        except MarketUnavailable as exc:
            raise ApiException(503, "market_unavailable", str(exc)) from exc

        account = await self.accounts.snapshot(username)
        open_count_row = self.db.query_one(
            "SELECT COUNT(*) AS count FROM orders WHERE username = ? AND status IN (?, ?, ?)",
            (username, *OPEN_STATUSES),
        )
        open_count = int(open_count_row["count"] if open_count_row else 0)
        minute_ago = iso(utc_now() - timedelta(seconds=60))
        minute_row = self.db.query_one(
            "SELECT COUNT(*) AS count FROM orders"
            " WHERE username = ? AND mode = ? AND created_at >= ?",
            (username, self.settings.mode.value, minute_ago),
        )
        minute_count = int(minute_row["count"] if minute_row else 0)
        daily_rows = self.db.query_all(
            "SELECT notional FROM orders WHERE username = ? AND mode = ?"
            " AND created_at >= ? AND status NOT IN (?, ?, ?)",
            (
                username,
                self.settings.mode.value,
                iso(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)),
                OrderStatus.REJECTED.value,
                OrderStatus.CANCELED.value,
                OrderStatus.EXPIRED.value,
            ),
        )
        daily_notional = sum((_decimal(row["notional"]) for row in daily_rows), Decimal("0"))

        decision = self.risk.assess(
            username=username,
            symbol=symbol,
            side=request.side,
            order_type=request.type,
            quantity=request.quantity,
            price=request.price,
            rules=rules,
            ticker=ticker,
            account=account,
            open_order_count=open_count,
            orders_last_minute=minute_count,
            daily_notional=daily_notional,
        )

        with self.db.tx() as conn:
            self.db.log_audit(
                conn,
                action="order.preview",
                mode=self.settings.mode.value,
                actor=username,
                request_id=request_id,
                entity_type="symbol",
                entity_id=symbol,
                detail={
                    "side": request.side.value,
                    "type": request.type.value,
                    "quantity": str(request.quantity),
                    "price": str(request.price) if request.price is not None else None,
                    "approved": decision.approved,
                    "reasons": decision.reasons,
                    "notional": str(decision.notional),
                },
            )

        if not decision.approved:
            raise ApiException(
                422,
                "risk_rejected",
                "订单未通过服务端风控",
                details={"risk": decision.as_dict()},
            )

        token = new_token()
        expires_at = iso_after(self.settings.confirmation_ttl_seconds)
        draft = {
            "username": username,
            "mode": self.settings.mode.value,
            "symbol": symbol,
            "side": request.side.value,
            "type": request.type.value,
            "time_in_force": request.time_in_force,
            "quantity": decimal_str(decision.normalized_quantity),
            "price": decimal_str(decision.normalized_price)
            if decision.normalized_price is not None
            else None,
            "latest_price": decimal_str(ticker.last_price),
            "notional": decimal_str(decision.notional),
            "estimated_fee": decimal_str(decision.estimated_fee),
            "fee_asset": decision.fee_asset,
            "account_fetched_at": account.fetched_at,
            "ticker_fetched_at": ticker.fetched_at,
            "ticker_source": ticker.source,
            "created_at": iso(),
        }
        draft_json = json.dumps(draft, ensure_ascii=False, sort_keys=True)
        with self.db.tx() as conn:
            conn.execute("DELETE FROM confirmations WHERE expires_at < ?", (iso(),))
            conn.execute(
                "INSERT INTO confirmations(token_hash, username, draft_json, draft_hash,"
                " created_at, expires_at, consumed_at) VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (
                    token_hash(token),
                    username,
                    draft_json,
                    token_hash(draft_json),
                    iso(),
                    expires_at,
                ),
            )

        warnings: list[str] = []
        if decision.normalized:
            warnings.append("价格或数量已按交易所精度向下规范化，请以确认页数值为准")
        if self.settings.mode is AppMode.DEMO:
            warnings.append("DEMO 环境：不会向任何交易所发送订单")
        if ticker.source == "demo":
            warnings.append("当前行情来自本地模拟数据，仅用于演示")

        return OrderPreviewOut(
            preview_token=token,
            expires_at=expires_at,
            draft=OrderDraftOut(
                symbol=symbol,
                side=request.side,
                type=request.type,
                time_in_force=request.time_in_force,
                quantity=decision.normalized_quantity,
                price=decision.normalized_price,
                latest_price=ticker.last_price,
                estimated_notional=decision.notional,
                estimated_fee=decision.estimated_fee,
                fee_asset=decision.fee_asset,
                normalized=decision.normalized,
            ),
            risk=RiskDecisionOut(**decision.as_dict()),
            warnings=warnings,
            mode=self.settings.mode.value,
            market_source=ticker.source,
            market_fetched_at=ticker.fetched_at,
            account_fetched_at=account.fetched_at,
            account_stale=account.stale,
        )

    # ------------------------------------------------------------------
    # Create / confirm
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        username: str,
        confirmation_token: str,
        idempotency_key: str,
        request_id: str,
    ) -> tuple[OrderOut, bool]:
        existing = self.db.query_one(
            "SELECT * FROM orders WHERE username = ? AND idempotency_key = ?",
            (username, idempotency_key),
        )
        if existing is not None:
            return self._to_order_out(existing), True

        confirmation = self.db.query_one(
            "SELECT * FROM confirmations WHERE token_hash = ?",
            (token_hash(confirmation_token),),
        )
        if confirmation is None or str(confirmation["username"]) != username:
            raise ApiException(422, "confirmation_invalid", "确认令牌无效，请重新预览订单")
        expires = parse_iso(str(confirmation["expires_at"]))
        if expires is None or expires <= utc_now():
            raise ApiException(422, "confirmation_expired", "确认已过期，请重新预览订单")
        if confirmation["consumed_at"] is not None:
            raise ApiException(409, "confirmation_consumed", "确认已使用；如已提交请刷新订单列表")

        draft = json.loads(str(confirmation["draft_json"]))
        if draft.get("mode") != self.settings.mode.value:
            raise ApiException(409, "mode_changed", "服务端运行模式已变化，请重新预览")

        symbol = str(draft["symbol"])
        side = Side(str(draft["side"]))
        order_type = OrderType(str(draft["type"]))
        quantity = Decimal(str(draft["quantity"]))
        price = Decimal(str(draft["price"])) if draft.get("price") is not None else None
        time_in_force = str(draft.get("time_in_force") or "GTC")

        try:
            ticker = await self.market.ticker(symbol)
            rules = await self.market.symbol_rules(symbol)
        except MarketUnavailable as exc:
            raise ApiException(503, "market_unavailable", str(exc)) from exc

        # TESTNET/LIVE balances come from the exchange; DEMO balances are read
        # inside the write transaction to avoid two orders spending the same
        # simulated funds.
        external_account: AccountSnapshot | None = None
        if self.settings.mode is not AppMode.DEMO:
            external_account = await self.accounts.snapshot(username)

        risk_rejection: tuple[RiskDecision, str] | None = None
        try:
            with self.db.tx(immediate=True) as conn:
                existing = conn.execute(
                    "SELECT * FROM orders WHERE username = ? AND idempotency_key = ?",
                    (username, idempotency_key),
                ).fetchone()
                if existing is not None:
                    return self._to_order_out(existing), True

                consumed = conn.execute(
                    "UPDATE confirmations SET consumed_at = ?"
                    " WHERE token_hash = ? AND consumed_at IS NULL",
                    (iso(), token_hash(confirmation_token)),
                )
                if consumed.rowcount != 1:
                    raise ApiException(
                        409, "confirmation_consumed", "确认已使用；请刷新订单列表"
                    )

                account = (
                    self._demo_account_snapshot(conn, username)
                    if self.settings.mode is AppMode.DEMO
                    else external_account
                )
                if account is None:
                    raise ApiException(503, "account_unavailable", "账户快照不可用")

                open_count, minute_count, daily_notional = self._aggregates(conn, username)
                decision = self.risk.assess(
                    username=username,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    rules=rules,
                    ticker=ticker,
                    account=account,
                    open_order_count=open_count,
                    orders_last_minute=minute_count,
                    daily_notional=daily_notional,
                )

                order_id = new_order_id()
                client_order_id = client_order_id_for(username, idempotency_key)
                now = iso()

                if not decision.approved:
                    self._insert_order(
                        conn,
                        order_id=order_id,
                        client_order_id=client_order_id,
                        idempotency_key=idempotency_key,
                        username=username,
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        time_in_force=time_in_force,
                        price=decision.normalized_price,
                        quantity=decision.normalized_quantity,
                        notional=decision.notional,
                        status=OrderStatus.REJECTED.value,
                        risk=decision,
                        request_id=request_id,
                        error_code="risk_rejected",
                        error_message="; ".join(decision.reasons) or "风控拒绝",
                    )
                    self.db.log_audit(
                        conn,
                        action="order.rejected",
                        mode=self.settings.mode.value,
                        actor=username,
                        request_id=request_id,
                        entity_type="order",
                        entity_id=order_id,
                        detail={"reasons": decision.reasons, "risk": decision.as_dict()},
                    )
                    risk_rejection = (decision, order_id)
                elif self.settings.mode is AppMode.DEMO:
                    self._execute_demo(
                        conn,
                        order_id=order_id,
                        client_order_id=client_order_id,
                        idempotency_key=idempotency_key,
                        username=username,
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        time_in_force=time_in_force,
                        quantity=decision.normalized_quantity,
                        price=decision.normalized_price,
                        notional=decision.notional,
                        decision=decision,
                        ticker=ticker,
                        request_id=request_id,
                    )
                else:
                    self._insert_order(
                        conn,
                        order_id=order_id,
                        client_order_id=client_order_id,
                        idempotency_key=idempotency_key,
                        username=username,
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        time_in_force=time_in_force,
                        price=decision.normalized_price,
                        quantity=decision.normalized_quantity,
                        notional=decision.notional,
                        status=OrderStatus.NEW.value,
                        risk=decision,
                        request_id=request_id,
                    )
                    self.db.log_audit(
                        conn,
                        action="order.persisted",
                        mode=self.settings.mode.value,
                        actor=username,
                        request_id=request_id,
                        entity_type="order",
                        entity_id=order_id,
                        detail={"client_order_id": client_order_id},
                    )
        except sqlite3.IntegrityError:
            existing = self.db.query_one(
                "SELECT * FROM orders WHERE username = ? AND idempotency_key = ?",
                (username, idempotency_key),
            )
            if existing is not None:
                return self._to_order_out(existing), True
            raise

        if risk_rejection is not None:
            decision, rejected_order_id = risk_rejection
            raise ApiException(
                422,
                "risk_rejected",
                "订单未通过服务端风控",
                details={
                    "order_id": rejected_order_id,
                    "risk": decision.as_dict(),
                },
            )

        if self.settings.mode is not AppMode.DEMO:
            await self._submit_to_exchange(
                order_id=order_id,
                client_order_id=client_order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                time_in_force=time_in_force,
                request_id=request_id,
                username=username,
            )

        row = self.db.query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
        if row is None:
            raise ApiException(500, "order_missing", "订单持久化后无法读取")
        order = self._to_order_out(row)
        if order.status is OrderStatus.REJECTED:
            raise ApiException(
                422,
                "order_rejected",
                order.error_message or "订单被交易所拒绝",
                details={
                    "order_id": order.id,
                    "order": order.model_dump(mode="json"),
                },
            )
        return order, False

    def _demo_account_snapshot(
        self, conn: sqlite3.Connection, username: str
    ) -> AccountSnapshot:
        rows = conn.execute(
            "SELECT asset, free, locked FROM demo_wallets WHERE username = ? ORDER BY asset",
            (username,),
        ).fetchall()
        return AccountSnapshot(
            status="CONNECTED",
            connected=True,
            source="demo",
            fetched_at=iso(),
            stale=False,
            note="DEMO 模拟账户",
            balances=tuple(
                Balance(
                    asset=str(row["asset"]),
                    free=_decimal(row["free"]),
                    locked=_decimal(row["locked"]),
                )
                for row in rows
            ),
        )

    def _insert_order(
        self,
        conn: sqlite3.Connection,
        *,
        order_id: str,
        client_order_id: str,
        idempotency_key: str,
        username: str,
        symbol: str,
        side: Side,
        order_type: OrderType,
        time_in_force: str,
        price: Decimal | None,
        quantity: Decimal,
        notional: Decimal,
        status: str,
        risk: RiskDecision,
        request_id: str,
        error_code: str | None = None,
        error_message: str | None = None,
        reserved_amount: Decimal = Decimal("0"),
        reserved_asset: str | None = None,
    ) -> None:
        now = iso()
        conn.execute(
            "INSERT INTO orders(id, client_order_id, idempotency_key, username, mode,"
            " symbol, side, type, time_in_force, price, quantity, notional, filled_qty,"
            " status, fee, reserved_amount, reserved_asset, risk_json, error_code,"
            " error_message, request_id, created_at, updated_at, submitted_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '0', ?, '0', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                order_id,
                client_order_id,
                idempotency_key,
                username,
                self.settings.mode.value,
                symbol,
                side.value,
                order_type.value,
                time_in_force,
                decimal_str(price) if price is not None else None,
                decimal_str(quantity),
                decimal_str(notional),
                status,
                decimal_str(reserved_amount),
                reserved_asset,
                json.dumps(risk.as_dict(), ensure_ascii=False, sort_keys=True),
                error_code,
                error_message,
                request_id,
                now,
                now,
                now if status not in {OrderStatus.REJECTED.value} else None,
            ),
        )

    def _wallet(
        self, conn: sqlite3.Connection, username: str, asset: str
    ) -> tuple[Decimal, Decimal]:
        row = conn.execute(
            "SELECT free, locked FROM demo_wallets WHERE username = ? AND asset = ?",
            (username, asset),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO demo_wallets(username, asset, free, locked, updated_at)"
                " VALUES (?, ?, '0', '0', ?)",
                (username, asset, iso()),
            )
            return Decimal("0"), Decimal("0")
        return _decimal(row["free"]), _decimal(row["locked"])

    def _set_wallet(
        self,
        conn: sqlite3.Connection,
        username: str,
        asset: str,
        free: Decimal,
        locked: Decimal,
    ) -> None:
        if free < 0 or locked < 0:
            raise ApiException(409, "balance_race", "余额不足，订单未提交")
        conn.execute(
            "UPDATE demo_wallets SET free = ?, locked = ?, updated_at = ?"
            " WHERE username = ? AND asset = ?",
            (decimal_str(free), decimal_str(locked), iso(), username, asset),
        )

    def _execute_demo(
        self,
        conn: sqlite3.Connection,
        *,
        order_id: str,
        client_order_id: str,
        idempotency_key: str,
        username: str,
        symbol: str,
        side: Side,
        order_type: OrderType,
        time_in_force: str,
        quantity: Decimal,
        price: Decimal | None,
        notional: Decimal,
        decision: RiskDecision,
        ticker: Ticker,
        request_id: str,
    ) -> None:
        base_asset = decision.base_asset
        quote_asset = decision.quote_asset
        now = iso()
        if order_type is OrderType.MARKET:
            execution_price = ticker.last_price
            executed_notional = (quantity * execution_price).quantize(Decimal("0.00000001"))
            fee = (executed_notional * self.settings.trading_fee_rate).quantize(
                Decimal("0.00000001")
            )
            free_quote, locked_quote = self._wallet(conn, username, quote_asset)
            free_base, locked_base = self._wallet(conn, username, base_asset)
            if side is Side.BUY:
                if free_quote < executed_notional + fee:
                    raise ApiException(409, "insufficient_balance", "USDT 余额不足")
                self._set_wallet(
                    conn,
                    username,
                    quote_asset,
                    free_quote - executed_notional - fee,
                    locked_quote,
                )
                self._set_wallet(
                    conn, username, base_asset, free_base + quantity, locked_base
                )
            else:
                if free_base < quantity:
                    raise ApiException(409, "insufficient_balance", "BTC 余额不足")
                self._set_wallet(
                    conn, username, base_asset, free_base - quantity, locked_base
                )
                self._set_wallet(
                    conn,
                    username,
                    quote_asset,
                    free_quote + executed_notional - fee,
                    locked_quote,
                )

            self._insert_order(
                conn,
                order_id=order_id,
                client_order_id=client_order_id,
                idempotency_key=idempotency_key,
                username=username,
                symbol=symbol,
                side=side,
                order_type=order_type,
                time_in_force=time_in_force,
                price=None,
                quantity=quantity,
                notional=executed_notional,
                status=OrderStatus.FILLED.value,
                risk=decision,
                request_id=request_id,
            )
            conn.execute(
                "UPDATE orders SET filled_qty = ?, avg_fill_price = ?, fee = ?,"
                " fee_asset = ?, exchange_order_id = ?, submitted_at = ?, updated_at = ?"
                " WHERE id = ?",
                (
                    decimal_str(quantity),
                    decimal_str(execution_price),
                    decimal_str(fee),
                    quote_asset,
                    f"demo-{client_order_id}",
                    now,
                    now,
                    order_id,
                ),
            )
            conn.execute(
                "INSERT INTO fills(id, order_id, exchange_trade_id, price, quantity,"
                " commission, commission_asset, filled_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"fill_{new_token()[:18]}",
                    order_id,
                    f"demo-trade-{client_order_id}",
                    decimal_str(execution_price),
                    decimal_str(quantity),
                    decimal_str(fee),
                    quote_asset,
                    now,
                ),
            )
            self.db.log_audit(
                conn,
                action="order.simulated_fill",
                mode=self.settings.mode.value,
                actor=username,
                request_id=request_id,
                entity_type="order",
                entity_id=order_id,
                detail={
                    "symbol": symbol,
                    "side": side.value,
                    "quantity": str(quantity),
                    "price": str(execution_price),
                    "fee": str(fee),
                },
            )
            return

        # LIMIT in DEMO: reserve funds and keep the order open until canceled.
        assert price is not None
        free_quote, locked_quote = self._wallet(conn, username, quote_asset)
        free_base, locked_base = self._wallet(conn, username, base_asset)
        if side is Side.BUY:
            reserve = (notional + decision.estimated_fee).quantize(Decimal("0.00000001"))
            if free_quote < reserve:
                raise ApiException(409, "insufficient_balance", "USDT 可用余额不足")
            self._set_wallet(
                conn, username, quote_asset, free_quote - reserve, locked_quote + reserve
            )
            reserved_asset = quote_asset
        else:
            if free_base < quantity:
                raise ApiException(409, "insufficient_balance", "BTC 可用余额不足")
            reserve = quantity
            self._set_wallet(
                conn, username, base_asset, free_base - reserve, locked_base + reserve
            )
            reserved_asset = base_asset
        self._insert_order(
            conn,
            order_id=order_id,
            client_order_id=client_order_id,
            idempotency_key=idempotency_key,
            username=username,
            symbol=symbol,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            price=price,
            quantity=quantity,
            notional=notional,
            status=OrderStatus.NEW.value,
            risk=decision,
            request_id=request_id,
            reserved_amount=reserve,
            reserved_asset=reserved_asset,
        )
        self.db.log_audit(
            conn,
            action="order.simulated_open",
            mode=self.settings.mode.value,
            actor=username,
            request_id=request_id,
            entity_type="order",
            entity_id=order_id,
            detail={
                "side": side.value,
                "price": str(price),
                "quantity": str(quantity),
                "reserved": f"{reserve} {reserved_asset}",
            },
        )

    # ------------------------------------------------------------------
    # Testnet submission and reconciliation
    # ------------------------------------------------------------------

    async def _submit_to_exchange(
        self,
        *,
        order_id: str,
        client_order_id: str,
        symbol: str,
        side: Side,
        order_type: OrderType,
        quantity: Decimal,
        price: Decimal | None,
        time_in_force: str,
        request_id: str,
        username: str,
    ) -> None:
        if self.adapter is None:
            self._mark_rejected(order_id, "adapter_missing", "交易所适配器未配置")
            return
        try:
            result = await self.adapter.create_order(
                symbol=symbol,
                side=side.value,
                order_type=order_type.value,
                quantity=quantity,
                price=price,
                client_order_id=client_order_id,
                time_in_force=time_in_force,
            )
            self._apply_exchange_result(order_id, result)
            with self.db.tx() as conn:
                self.db.log_audit(
                    conn,
                    action="order.exchange_ack",
                    mode=self.settings.mode.value,
                    actor=username,
                    request_id=request_id,
                    entity_type="order",
                    entity_id=order_id,
                    detail={
                        "exchange_order_id": result.exchange_order_id,
                        "status": result.status,
                    },
                )
        except BinanceError as exc:
            if exc.unknown_outcome:
                # Never blindly POST again. Query by our stable clientOrderId.
                try:
                    reconciled = await self.adapter.get_order(
                        symbol=symbol, client_order_id=client_order_id
                    )
                except BinanceError:
                    self._mark_pending(order_id, "outcome_unknown", str(exc))
                    return
                self._apply_exchange_result(order_id, reconciled)
                return
            self._mark_rejected(order_id, "exchange_rejected", str(exc))

    def _apply_exchange_result(
        self, order_id: str, result: BinanceOrderResult
    ) -> None:
        status = result.status
        if status == "EXPIRED_IN_MATCH":
            status = OrderStatus.EXPIRED.value
        if status not in {item.value for item in OrderStatus}:
            status = OrderStatus.PENDING_RECONCILIATION.value

        existing = self.db.query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
        prior_filled = _decimal(existing["filled_qty"]) if existing is not None else Decimal("0")
        prior_fee = _decimal(existing["fee"]) if existing is not None else Decimal("0")
        prior_fee_asset = existing["fee_asset"] if existing is not None else None
        executed_qty = max(result.executed_qty, prior_filled)

        avg_price = (
            _decimal(existing["avg_fill_price"])
            if existing is not None and executed_qty == prior_filled
            and existing["avg_fill_price"] is not None
            else None
        )
        if result.executed_qty > 0 and result.cummulative_quote_qty > 0:
            avg_price = (result.cummulative_quote_qty / result.executed_qty).quantize(
                Decimal("0.00000001")
            )

        fees: dict[str, Decimal] = {}
        for item in result.fills:
            asset = str(item.get("commissionAsset") or "")
            fees[asset] = fees.get(asset, Decimal("0")) + _decimal(item.get("commission", "0"))
        fee_asset = next(iter(fees), None) or prior_fee_asset
        fee = fees[fee_asset] if fee_asset in fees else prior_fee

        now = iso()
        with self.db.tx(immediate=True) as conn:
            conn.execute(
                "UPDATE orders SET exchange_order_id = ?, status = ?, filled_qty = ?,"
                " avg_fill_price = ?, fee = ?, fee_asset = ?, updated_at = ?,"
                " error_code = NULL, error_message = NULL WHERE id = ?",
                (
                    result.exchange_order_id,
                    status,
                    decimal_str(executed_qty),
                    decimal_str(avg_price) if avg_price is not None else None,
                    decimal_str(fee),
                    fee_asset,
                    now,
                    order_id,
                ),
            )
            for index, item in enumerate(result.fills):
                trade_id = str(item.get("tradeId") or f"{result.exchange_order_id}-{index}")
                conn.execute(
                    "INSERT OR IGNORE INTO fills(id, order_id, exchange_trade_id, price,"
                    " quantity, commission, commission_asset, filled_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"fill_{new_token()[:18]}",
                        order_id,
                        trade_id,
                        decimal_str(_decimal(item.get("price"))),
                        decimal_str(_decimal(item.get("qty"))),
                        decimal_str(_decimal(item.get("commission"))),
                        item.get("commissionAsset"),
                        now,
                    ),
                )

    def _mark_pending(self, order_id: str, code: str, message: str) -> None:
        with self.db.tx() as conn:
            conn.execute(
                "UPDATE orders SET status = ?, error_code = ?, error_message = ?,"
                " updated_at = ? WHERE id = ?",
                (OrderStatus.PENDING_RECONCILIATION.value, code, message, iso(), order_id),
            )

    def _mark_rejected(self, order_id: str, code: str, message: str) -> None:
        with self.db.tx() as conn:
            conn.execute(
                "UPDATE orders SET status = ?, error_code = ?, error_message = ?,"
                " updated_at = ? WHERE id = ?",
                (OrderStatus.REJECTED.value, code, message[:500], iso(), order_id),
            )
            self.db.log_audit(
                conn,
                action="order.exchange_rejected",
                mode=self.settings.mode.value,
                entity_type="order",
                entity_id=order_id,
                detail={"code": code, "message": message[:500]},
            )

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    async def cancel(
        self,
        *,
        username: str,
        order_id: str,
        request_id: str,
    ) -> OrderOut:
        row = self.db.query_one(
            "SELECT * FROM orders WHERE id = ? AND username = ?", (order_id, username)
        )
        if row is None:
            raise ApiException(404, "order_not_found", "订单不存在")
        if str(row["status"]) in TERMINAL_STATUSES:
            raise ApiException(409, "order_terminal", "该订单已结束，无法撤销")
        if str(row["status"]) not in OPEN_STATUSES:
            raise ApiException(409, "order_not_cancelable", "当前订单状态不可撤销")

        if self.settings.mode is AppMode.DEMO:
            with self.db.tx(immediate=True) as conn:
                current = conn.execute(
                    "SELECT * FROM orders WHERE id = ? AND username = ?", (order_id, username)
                ).fetchone()
                if current is None:
                    raise ApiException(404, "order_not_found", "订单不存在")
                if str(current["status"]) not in OPEN_STATUSES:
                    raise ApiException(409, "order_terminal", "订单已结束")
                reserved_amount = _decimal(current["reserved_amount"])
                reserved_asset = current["reserved_asset"]
                if reserved_amount > 0 and reserved_asset:
                    free, locked = self._wallet(conn, username, str(reserved_asset))
                    if locked < reserved_amount:
                        raise ApiException(
                            409, "reservation_mismatch", "冻结金额异常，已阻止自动释放"
                        )
                    self._set_wallet(
                        conn,
                        username,
                        str(reserved_asset),
                        free + reserved_amount,
                        locked - reserved_amount,
                    )
                conn.execute(
                    "UPDATE orders SET status = ?, reserved_amount = '0',"
                    " reserved_asset = NULL, updated_at = ? WHERE id = ?",
                    (OrderStatus.CANCELED.value, iso(), order_id),
                )
                self.db.log_audit(
                    conn,
                    action="order.canceled",
                    mode=self.settings.mode.value,
                    actor=username,
                    request_id=request_id,
                    entity_type="order",
                    entity_id=order_id,
                    detail={
                        "released": str(reserved_amount),
                        "asset": reserved_asset,
                    },
                )
        else:
            if self.adapter is None:
                raise ApiException(503, "adapter_missing", "交易所适配器未配置")
            try:
                result = await self.adapter.cancel_order(
                    symbol=str(row["symbol"]), client_order_id=str(row["client_order_id"])
                )
                self._apply_exchange_result(order_id, result)
                with self.db.tx() as conn:
                    self.db.log_audit(
                        conn,
                        action="order.canceled",
                        mode=self.settings.mode.value,
                        actor=username,
                        request_id=request_id,
                        entity_type="order",
                        entity_id=order_id,
                    )
            except BinanceError as exc:
                if exc.unknown_outcome:
                    try:
                        reconciled = await self.adapter.get_order(
                            symbol=str(row["symbol"]),
                            client_order_id=str(row["client_order_id"]),
                        )
                    except BinanceError:
                        self._mark_pending(order_id, "cancel_outcome_unknown", str(exc))
                        raise ApiException(
                            503,
                            "cancel_outcome_unknown",
                            "撤单结果未知，请刷新订单状态，切勿重复操作",
                        ) from exc
                    self._apply_exchange_result(order_id, reconciled)
                else:
                    raise ApiException(422, "cancel_rejected", str(exc)) from exc

        return self.get_order(username, order_id)
