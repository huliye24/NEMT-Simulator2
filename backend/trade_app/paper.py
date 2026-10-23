"""Paper trading engine (纸上交易 / forward test).

Real quotes, simulated money. Four invariants:

1. Nothing here can reach an exchange. It reads public prices and writes only
   to the ``paper_*`` tables; no API key, no signature, no order routing.
2. Money is ``Decimal`` and stored as TEXT. SQL never performs arithmetic on a
   money column (SQLite would coerce TEXT to REAL and lose precision), so every
   update reads the stored text, computes in Decimal and writes it back.
3. The equity identity always holds:

       equity = cash + sum(spot qty * mark) + sum(perp margin + perp pnl)

4. ``realized_pnl`` is gross trading PnL and ``fees`` is the cost of trading,
   reported separately like an exchange statement. ``equity`` reflects both.

Model
-----
* SPOT — long only, paid in full from cash, held as a base-asset position.
* PERP — isolated margin, LONG or SHORT, leverage 1..N, liquidation price and
  8h funding modelled.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import ROUND_DOWN, Decimal, InvalidOperation
from typing import Any

from .config import Settings
from .db import Database, iso, parse_iso
from .errors import ApiException
from .market import MarketService

SPOT = "SPOT"
PERP = "PERP"
LONG = "LONG"
SHORT = "SHORT"

ACTION_OPEN = "OPEN"
ACTION_REDUCE = "REDUCE"
ACTION_CLOSE = "CLOSE"
ACTION_LIQUIDATE = "LIQUIDATE"

ONE = Decimal("1")
ZERO = Decimal("0")
QTY_PLACES = Decimal("0.00000001")
PRICE_PLACES = Decimal("0.00000001")
USDT_PLACES = Decimal("0.00000001")

_ACCOUNT_COLUMNS = "cash, fees_paid, realized_pnl, funding_paid"
_POSITION_COLUMNS = "fees, realized_pnl, funding"


def dec(value: Any, default: str = "0") -> Decimal:
    """Decimal from stored TEXT/None, never raising on bad input."""

    try:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def money(value: Decimal) -> str:
    return format(value.quantize(USDT_PLACES, rounding=ROUND_DOWN), "f")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def funding_boundaries(
    since: datetime, now: datetime, interval_hours: int = 8, limit: int = 24
) -> list[datetime]:
    """Funding settles at fixed UTC hours (00/08/16 when the interval is 8).

    Returns the settlement times strictly after ``since`` and at or before
    ``now``, so a position that slept through two windows accrues twice.
    """

    interval = max(1, int(interval_hours))
    anchor_hour = (since.hour // interval) * interval
    cursor = since.replace(hour=anchor_hour, minute=0, second=0, microsecond=0)
    cursor += timedelta(hours=interval)
    boundaries: list[datetime] = []
    while cursor <= now and len(boundaries) < limit:
        boundaries.append(cursor)
        cursor += timedelta(hours=interval)
    return boundaries


class PaperService:
    """Per-user simulated account with live mark-to-market."""

    def __init__(self, db: Database, settings: Settings, market: MarketService):
        self.db = db
        self.settings = settings
        self.market = market

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    def ensure_account(self, username: str) -> None:
        initial = money(dec(self.settings.paper_initial_equity))
        now = iso()
        with self.db.tx(immediate=True) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO paper_accounts"
                " (username, initial_equity, cash, realized_pnl, fees_paid,"
                "  funding_paid, created_at, updated_at)"
                " VALUES (?, ?, ?, '0', '0', '0', ?, ?)",
                (username, initial, initial, now, now),
            )

    def _account_row(self, username: str) -> Any:
        self.ensure_account(username)
        row = self.db.query_one(
            "SELECT * FROM paper_accounts WHERE username = ?", (username,)
        )
        if row is None:  # pragma: no cover - ensure_account just created it
            raise ApiException(500, "paper_account_missing", "模拟账户创建失败")
        return row

    async def account(self, username: str) -> dict[str, Any]:
        positions = await self.positions(username)
        row = self._account_row(username)
        cash = dec(row["cash"])
        spot_value = sum(
            (
                dec(item["mark_price"]) * dec(item["qty"])
                for item in positions
                if item["market"] == SPOT
            ),
            ZERO,
        )
        perp_value = sum(
            (
                dec(item["margin"]) + dec(item["unrealized"])
                for item in positions
                if item["market"] == PERP
            ),
            ZERO,
        )
        unrealized = sum((dec(item["unrealized"]) for item in positions), ZERO)
        equity = cash + spot_value + perp_value
        initial = dec(row["initial_equity"])
        realized = dec(row["realized_pnl"])
        return {
            "username": username,
            "initial_equity": initial,
            "equity": equity,
            "cash": cash,
            "spot_value": spot_value,
            "perp_value": perp_value,
            "unrealized": unrealized,
            "realized": realized,
            "fees": dec(row["fees_paid"]),
            "funding": dec(row["funding_paid"]),
            "net_pnl": equity - initial,
            "return_pct": ((equity - initial) / initial * 100) if initial > 0 else ZERO,
            "open_positions": len(positions),
            "mode": "PAPER",
        }

    async def reset(self, username: str) -> dict[str, Any]:
        """Reset the paper account back to the starting equity."""

        initial = money(dec(self.settings.paper_initial_equity))
        now = iso()
        with self.db.tx(immediate=True) as conn:
            conn.execute(
                "UPDATE paper_positions SET status = 'CLOSED', qty = '0',"
                " margin = '0', closed_at = ?, updated_at = ?"
                " WHERE username = ? AND status = 'OPEN'",
                (now, now, username),
            )
            conn.execute("DELETE FROM paper_fills WHERE username = ?", (username,))
            conn.execute("DELETE FROM paper_equity WHERE username = ?", (username,))
            conn.execute(
                "INSERT INTO paper_accounts"
                " (username, initial_equity, cash, realized_pnl, fees_paid,"
                "  funding_paid, created_at, updated_at)"
                " VALUES (?, ?, ?, '0', '0', '0', ?, ?)"
                " ON CONFLICT(username) DO UPDATE SET"
                " initial_equity = excluded.initial_equity,"
                " cash = excluded.cash, realized_pnl = '0', fees_paid = '0',"
                " funding_paid = '0', updated_at = excluded.updated_at",
                (username, initial, initial, now, now),
            )
        return await self.account(username)

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------

    async def mark_price(self, symbol: str) -> Decimal:
        try:
            ticker = await self.market.ticker(symbol)
        except Exception as exc:  # noqa: BLE001 - surfaced as 503 below
            raise ApiException(
                503, "market_unavailable", f"{symbol} 行情不可用，无法估值"
            ) from exc
        if ticker.last_price <= 0:
            raise ApiException(503, "market_unavailable", f"{symbol} 行情价格异常")
        return ticker.last_price

    def _fill_price(self, mark: Decimal, *, buying: bool) -> Decimal:
        """Fixed slippage: fills are always slightly worse than the mark."""

        slip = dec(self.settings.paper_slippage_bps) / Decimal("10000")
        price = mark * (ONE + slip) if buying else mark * (ONE - slip)
        return price.quantize(PRICE_PLACES, rounding=ROUND_DOWN)

    def _fee_rate(self, market: str) -> Decimal:
        if market == PERP:
            return dec(self.settings.paper_taker_fee_perp)
        return dec(self.settings.paper_taker_fee_spot)

    @staticmethod
    def _liquidation_price(
        *, entry: Decimal, side: str, leverage: int, mmr: Decimal
    ) -> Decimal:
        """Isolated-margin liquidation price, maintenance margin included."""

        lev = Decimal(max(1, int(leverage)))
        if side == LONG:
            price = entry * (ONE - ONE / lev + mmr)
        else:
            price = entry * (ONE + ONE / lev - mmr)
        return max(ZERO, price).quantize(PRICE_PLACES, rounding=ROUND_DOWN)

    # ------------------------------------------------------------------
    # Settlement: funding + forced liquidation, before every read or write
    # ------------------------------------------------------------------

    async def _settle(self, username: str) -> dict[str, Decimal]:
        rows = self.db.query_all(
            "SELECT * FROM paper_positions WHERE username = ? AND status = 'OPEN'"
            " AND market = ?",
            (username, PERP),
        )
        marks: dict[str, Decimal] = {}
        if not rows:
            return marks
        for symbol in {str(row["symbol"]) for row in rows}:
            marks[symbol] = await self.mark_price(symbol)

        now_dt = datetime.now(timezone.utc)
        interval = int(self.settings.paper_funding_interval_hours)
        mmr = dec(self.settings.paper_maintenance_margin_rate)

        for row in rows:
            symbol = str(row["symbol"])
            mark = marks[symbol]
            position_id = str(row["id"])
            qty = dec(row["qty"])
            entry = dec(row["entry_price"])
            margin = dec(row["margin"])
            leverage = int(row["leverage"] or 1)
            side = str(row["side"])

            last_funding = parse_iso(str(row["last_funding_at"] or "")) or parse_iso(
                str(row["opened_at"])
            )
            funding_delta = ZERO
            if last_funding is not None:
                rate = await self.market.funding_rate(symbol)
                for _boundary in funding_boundaries(last_funding, now_dt, interval):
                    payment = qty * mark * rate
                    if side == SHORT:
                        payment = -payment
                    funding_delta += payment

            liquidation_price = self._liquidation_price(
                entry=entry, side=side, leverage=leverage, mmr=mmr
            )
            breached = (side == LONG and mark <= liquidation_price) or (
                side == SHORT and mark >= liquidation_price
            )

            if breached:
                gross = (
                    (liquidation_price - entry) * qty
                    if side == LONG
                    else (entry - liquidation_price) * qty
                )
                gross = gross.quantize(USDT_PLACES, rounding=ROUND_DOWN)
                fee = liquidation_price * qty * self._fee_rate(PERP)
                cash_delta = margin + gross - fee - funding_delta
                self._write_fill_and_close(
                    position_id=position_id,
                    username=username,
                    symbol=symbol,
                    market=PERP,
                    side=side,
                    action=ACTION_LIQUIDATE,
                    qty=qty,
                    price=liquidation_price,
                    fee=fee,
                    realized=gross,
                    closed=True,
                    cash_delta=cash_delta,
                    funding_delta=funding_delta,
                )
                continue

            if funding_delta != 0:
                self._apply_funding(
                    username=username,
                    position_id=position_id,
                    funding_delta=funding_delta,
                    cash_delta=-funding_delta,
                )
        return marks

    def _apply_funding(
        self,
        *,
        username: str,
        position_id: str,
        funding_delta: Decimal,
        cash_delta: Decimal,
    ) -> None:
        now = iso()
        with self.db.tx(immediate=True) as conn:
            account = conn.execute(
                f"SELECT {_ACCOUNT_COLUMNS} FROM paper_accounts WHERE username = ?",
                (username,),
            ).fetchone()
            position = conn.execute(
                f"SELECT {_POSITION_COLUMNS} FROM paper_positions WHERE id = ?",
                (position_id,),
            ).fetchone()
            if account is None or position is None:
                return
            conn.execute(
                "UPDATE paper_accounts SET cash = ?, funding_paid = ?, updated_at = ?"
                " WHERE username = ?",
                (
                    money(dec(account["cash"]) + cash_delta),
                    money(dec(account["funding_paid"]) + funding_delta),
                    now,
                    username,
                ),
            )
            conn.execute(
                "UPDATE paper_positions SET funding = ?, updated_at = ? WHERE id = ?",
                (money(dec(position["funding"]) + funding_delta), now, position_id),
            )

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------

    async def positions(self, username: str) -> list[dict[str, Any]]:
        self.ensure_account(username)
        marks = await self._settle(username)
        rows = self.db.query_all(
            "SELECT * FROM paper_positions WHERE username = ? AND status = 'OPEN'"
            " ORDER BY opened_at",
            (username,),
        )
        if not rows:
            return []
        for row in rows:
            symbol = str(row["symbol"])
            if symbol not in marks:
                marks[symbol] = await self.mark_price(symbol)

        views: list[dict[str, Any]] = []
        mmr = dec(self.settings.paper_maintenance_margin_rate)
        for row in rows:
            symbol = str(row["symbol"])
            market = str(row["market"])
            side = str(row["side"])
            qty = dec(row["qty"])
            entry = dec(row["entry_price"])
            mark = marks[symbol]
            leverage = int(row["leverage"] or 1)
            margin = dec(row["margin"])
            notional = mark * qty
            if market == PERP:
                unrealized = (mark - entry) * qty if side == LONG else (entry - mark) * qty
                liquidation: Decimal | None = self._liquidation_price(
                    entry=entry, side=side, leverage=leverage, mmr=mmr
                )
                equity_part = margin + unrealized
            else:
                unrealized = (mark - entry) * qty
                liquidation = None
                equity_part = notional
            views.append(
                {
                    "id": str(row["id"]),
                    "strategy": str(row["strategy"]),
                    "symbol": symbol,
                    "market": market,
                    "side": side,
                    "qty": qty,
                    "entry_price": entry,
                    "mark_price": mark,
                    "leverage": leverage,
                    "margin": margin,
                    "notional": notional,
                    "unrealized": unrealized,
                    "realized": dec(row["realized_pnl"]),
                    "fees": dec(row["fees"]),
                    "funding": dec(row["funding"]),
                    "liquidation_price": liquidation,
                    "margin_ratio": (equity_part / notional * 100)
                    if notional > 0
                    else ZERO,
                    "price_change_pct": ((mark - entry) / entry * 100)
                    if entry > 0
                    else ZERO,
                    "opened_at": str(row["opened_at"]),
                    "updated_at": str(row["updated_at"]),
                }
            )
        return views

    def position_meta(self, username: str) -> dict[str, dict[str, Any]]:
        """Protective levels recorded on open, keyed by position id."""

        rows = self.db.query_all(
            "SELECT id, stop_price, take_price, opened_reason FROM paper_positions"
            " WHERE username = ? AND status = 'OPEN'",
            (username,),
        )
        return {
            str(row["id"]): {
                "stop_price": dec(row["stop_price"]) if row["stop_price"] else None,
                "take_price": dec(row["take_price"]) if row["take_price"] else None,
                "opened_reason": row["opened_reason"],
            }
            for row in rows
        }

    def fills_for_positions(
        self, username: str, position_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        """All fills grouped by position id, oldest first (for the UI)."""

        if not position_ids:
            return {}
        placeholders = ",".join("?" for _ in position_ids)
        rows = self.db.query_all(
            "SELECT * FROM paper_fills WHERE username = ?"
            f" AND position_id IN ({placeholders}) ORDER BY created_at, rowid",
            (username, *position_ids),
        )
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(str(row["position_id"]), []).append(
                {
                    "id": str(row["id"]),
                    "action": str(row["action"]),
                    "side": str(row["side"]),
                    "qty": dec(row["qty"]),
                    "price": dec(row["price"]),
                    "fee": dec(row["fee"]),
                    "realized_pnl": dec(row["realized_pnl"]),
                    "created_at": str(row["created_at"]),
                }
            )
        return grouped

    # ------------------------------------------------------------------
    # Open
    # ------------------------------------------------------------------
    async def open_position(
        self,
        username: str,
        *,
        symbol: str,
        market: str,
        side: str,
        notional: Decimal,
        leverage: int = 1,
        strategy: str = "NEMT",
        stop_price: Decimal | None = None,
        take_price: Decimal | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        symbol = symbol.strip().upper()
        market = market.strip().upper()
        side = side.strip().upper()

        if symbol not in self.settings.paper_symbols:
            raise ApiException(
                422,
                "paper_symbol_not_allowed",
                f"{symbol} 不在模拟盘支持的币种内：{', '.join(self.settings.paper_symbols)}",
            )
        if market not in (SPOT, PERP):
            raise ApiException(422, "paper_market_invalid", "market 只能是 SPOT 或 PERP")
        if side not in (LONG, SHORT):
            raise ApiException(422, "paper_side_invalid", "side 只能是 LONG 或 SHORT")
        if market == SPOT and side != LONG:
            raise ApiException(422, "paper_spot_long_only", "模拟现货只支持做多")
        max_lev = int(self.settings.paper_max_leverage)
        if market == PERP:
            if leverage < 1 or leverage > max_lev:
                raise ApiException(
                    422, "paper_leverage_invalid", f"杠杆必须在 1–{max_lev} 之间"
                )
        else:
            leverage = 1

        min_notional = dec(self.settings.paper_min_notional)
        if notional < min_notional:
            raise ApiException(
                422,
                "paper_notional_too_small",
                f"单笔名义价值不能小于 {min_notional} USDT（当前 {notional}）",
            )

        self.ensure_account(username)
        await self._settle(username)
        mark = await self.mark_price(symbol)
        buying = side == LONG
        fill_price = self._fill_price(mark, buying=buying)
        qty = (notional / fill_price).quantize(QTY_PLACES, rounding=ROUND_DOWN)
        if qty <= 0:
            raise ApiException(422, "paper_qty_too_small", "数量精度不足以成交")
        actual_notional = qty * fill_price
        # Rounding quantity down can land a hair under the requested notional
        # and trip the minimum-size guard, so top up by one step when it does.
        if actual_notional < notional:
            qty = qty + QTY_PLACES
            actual_notional = qty * fill_price
        fee = (actual_notional * self._fee_rate(market)).quantize(
            USDT_PLACES, rounding=ROUND_DOWN
        )
        margin = (
            (actual_notional / Decimal(leverage)).quantize(
                USDT_PLACES, rounding=ROUND_DOWN
            )
            if market == PERP
            else ZERO
        )
        required = margin + fee if market == PERP else actual_notional + fee

        position_id = _new_id("paper")
        now = iso()
        with self.db.tx(immediate=True) as conn:
            account = conn.execute(
                f"SELECT {_ACCOUNT_COLUMNS} FROM paper_accounts WHERE username = ?",
                (username,),
            ).fetchone()
            cash = dec(account["cash"]) if account is not None else ZERO
            if required > cash:
                raise ApiException(
                    422,
                    "paper_insufficient_funds",
                    f"可用资金不足：需要 {money(required)} USDT，可用 {money(cash)} USDT",
                )
            conn.execute(
                "INSERT INTO paper_positions (id, username, strategy, symbol, market,"
                " side, qty, entry_price, leverage, margin, realized_pnl, fees,"
                " funding, last_funding_at, status, opened_at, updated_at,"
                " stop_price, take_price, opened_reason)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '0', ?, '0', ?, 'OPEN', ?, ?,"
                " ?, ?, ?)",
                (
                    position_id,
                    username,
                    strategy[:32],
                    symbol,
                    market,
                    side,
                    format(qty, "f"),
                    format(fill_price, "f"),
                    leverage,
                    money(margin),
                    money(fee),
                    now,
                    now,
                    now,
                    format(stop_price, "f") if stop_price is not None else None,
                    format(take_price, "f") if take_price is not None else None,
                    (reason or "")[:200] or None,
                ),
            )
            conn.execute(
                "INSERT INTO paper_fills (id, position_id, username, symbol, market,"
                " side, action, qty, price, fee, realized_pnl, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '0', ?)",
                (
                    _new_id("fill"),
                    position_id,
                    username,
                    symbol,
                    market,
                    "BUY" if buying else "SELL",
                    ACTION_OPEN,
                    format(qty, "f"),
                    format(fill_price, "f"),
                    money(fee),
                    now,
                ),
            )
            conn.execute(
                "UPDATE paper_accounts SET cash = ?, fees_paid = ?, updated_at = ?"
                " WHERE username = ?",
                (
                    money(cash - required),
                    money(dec(account["fees_paid"]) + fee if account is not None else fee),
                    now,
                    username,
                ),
            )
        await self._snapshot(username)
        views = await self.positions(username)
        return next((view for view in views if view["id"] == position_id), {})

    # ------------------------------------------------------------------
    # Close / reduce
    # ------------------------------------------------------------------

    async def close_position(
        self, username: str, position_id: str, *, fraction: Decimal = ONE
    ) -> dict[str, Any]:
        if fraction <= 0 or fraction > 1:
            raise ApiException(
                422, "paper_fraction_invalid", "平仓比例必须大于 0 且不超过 1"
            )

        self.ensure_account(username)
        await self._settle(username)
        row = self.db.query_one(
            "SELECT * FROM paper_positions WHERE id = ? AND username = ?"
            " AND status = 'OPEN'",
            (position_id, username),
        )
        if row is None:
            raise ApiException(404, "paper_position_not_found", "模拟持仓不存在或已平仓")

        symbol = str(row["symbol"])
        market = str(row["market"])
        side = str(row["side"])
        qty_total = dec(row["qty"])
        qty_close = (qty_total * fraction).quantize(QTY_PLACES, rounding=ROUND_DOWN)
        if qty_close <= 0:
            raise ApiException(422, "paper_qty_too_small", "平仓数量精度不足")
        closing_all = qty_close >= qty_total

        mark = await self.mark_price(symbol)
        # Closing a long is a sell; closing a short is a buy.
        exit_price = self._fill_price(mark, buying=(side == SHORT))
        entry = dec(row["entry_price"])
        margin = dec(row["margin"])
        leverage = int(row["leverage"] or 1)
        notional = qty_close * exit_price
        fee = (notional * self._fee_rate(market)).quantize(
            USDT_PLACES, rounding=ROUND_DOWN
        )
        gross = (exit_price - entry) * qty_close
        if side == SHORT:
            gross = -gross
        gross = gross.quantize(USDT_PLACES, rounding=ROUND_DOWN)

        if market == PERP:
            released_margin = (
                margin if closing_all else (margin * qty_close / qty_total)
            ).quantize(USDT_PLACES, rounding=ROUND_DOWN)
            cash_delta = released_margin + gross - fee
        else:
            released_margin = ZERO
            cash_delta = notional - fee

        self._write_fill_and_close(
            position_id=position_id,
            username=username,
            symbol=symbol,
            market=market,
            side=side,
            action=ACTION_CLOSE if closing_all else ACTION_REDUCE,
            qty=qty_close,
            price=exit_price,
            fee=fee,
            realized=gross,
            closed=closing_all,
            cash_delta=cash_delta,
            remaining_qty=ZERO if closing_all else qty_total - qty_close,
            remaining_margin=ZERO if closing_all else margin - released_margin,
        )
        await self._snapshot(username)
        return {
            "position_id": position_id,
            "closed": closing_all,
            "qty": qty_close,
            "exit_price": exit_price,
            "gross_pnl": gross,
            "fee": fee,
            "margin_released": released_margin,
            "leverage": leverage,
        }

    def _write_fill_and_close(
        self,
        *,
        position_id: str,
        username: str,
        symbol: str,
        market: str,
        side: str,
        action: str,
        qty: Decimal,
        price: Decimal,
        fee: Decimal,
        realized: Decimal,
        closed: bool,
        cash_delta: Decimal,
        funding_delta: Decimal = ZERO,
        remaining_qty: Decimal | None = None,
        remaining_margin: Decimal | None = None,
    ) -> None:
        """One atomic write: fill row, position row, account row.

        Every money column is read as TEXT, converted to Decimal, summed in
        Python and written back, so no float ever touches the ledger.
        """

        now = iso()
        with self.db.tx(immediate=True) as conn:
            account = conn.execute(
                f"SELECT {_ACCOUNT_COLUMNS} FROM paper_accounts WHERE username = ?",
                (username,),
            ).fetchone()
            position = conn.execute(
                f"SELECT {_POSITION_COLUMNS} FROM paper_positions WHERE id = ?",
                (position_id,),
            ).fetchone()
            if account is None or position is None:
                raise ApiException(500, "paper_state_missing", "模拟盘状态缺失，写入中止")

            conn.execute(
                "INSERT INTO paper_fills (id, position_id, username, symbol, market,"
                " side, action, qty, price, fee, realized_pnl, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _new_id("fill"),
                    position_id,
                    username,
                    symbol,
                    market,
                    "SELL" if side == LONG else "BUY",
                    action,
                    format(qty, "f"),
                    format(price, "f"),
                    money(fee),
                    money(realized),
                    now,
                ),
            )

            position_fees = dec(position["fees"]) + fee
            position_realized = dec(position["realized_pnl"]) + realized
            if closed:
                conn.execute(
                    "UPDATE paper_positions SET status = 'CLOSED', qty = '0',"
                    " margin = '0', realized_pnl = ?, fees = ?, closed_at = ?,"
                    " updated_at = ? WHERE id = ?",
                    (
                        money(position_realized),
                        money(position_fees),
                        now,
                        now,
                        position_id,
                    ),
                )
            else:
                conn.execute(
                    "UPDATE paper_positions SET qty = ?, margin = ?,"
                    " realized_pnl = ?, fees = ?, updated_at = ? WHERE id = ?",
                    (
                        format(remaining_qty or ZERO, "f"),
                        money(remaining_margin or ZERO),
                        money(position_realized),
                        money(position_fees),
                        now,
                        position_id,
                    ),
                )

            conn.execute(
                "UPDATE paper_accounts SET cash = ?, fees_paid = ?,"
                " realized_pnl = ?, funding_paid = ?, updated_at = ?"
                " WHERE username = ?",
                (
                    money(dec(account["cash"]) + cash_delta),
                    money(dec(account["fees_paid"]) + fee),
                    money(dec(account["realized_pnl"]) + realized),
                    money(dec(account["funding_paid"]) + funding_delta),
                    now,
                    username,
                ),
            )

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    async def _snapshot(self, username: str) -> None:
        try:
            state = await self.account(username)
        except ApiException:
            return
        with self.db.tx() as conn:
            conn.execute(
                "INSERT INTO paper_equity (username, at, equity, cash, unrealized,"
                " realized) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    username,
                    iso(),
                    money(state["equity"]),
                    money(state["cash"]),
                    money(state["unrealized"]),
                    money(state["realized"]),
                ),
            )

    def fills(self, username: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.db.query_all(
            "SELECT * FROM paper_fills WHERE username = ?"
            " ORDER BY created_at DESC, rowid DESC LIMIT ?",
            (username, max(1, min(int(limit), 500))),
        )
        return [
            {
                "id": str(row["id"]),
                "position_id": str(row["position_id"]),
                "symbol": str(row["symbol"]),
                "market": str(row["market"]),
                "side": str(row["side"]),
                "action": str(row["action"]),
                "qty": dec(row["qty"]),
                "price": dec(row["price"]),
                "fee": dec(row["fee"]),
                "realized_pnl": dec(row["realized_pnl"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def equity_curve(self, username: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.db.query_all(
            "SELECT * FROM paper_equity WHERE username = ? ORDER BY id DESC LIMIT ?",
            (username, max(2, min(int(limit), 1000))),
        )
        return [
            {
                "at": str(row["at"]),
                "equity": dec(row["equity"]),
                "cash": dec(row["cash"]),
                "unrealized": dec(row["unrealized"]),
                "realized": dec(row["realized"]),
            }
            for row in reversed(rows)
        ]
