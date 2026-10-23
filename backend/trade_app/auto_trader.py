"""The closed loop: NEMT signal in, paper position out, no human click.

One pass (``run_once``) does three things in order:

1. **Protect open positions** — hit stop or take-profit? close it.
2. **React to the strategy** — a fresh ``critical_up`` / ``critical_down`` opens a
   position; a flipped direction or a ``decay`` phase closes one.
3. **Journal everything** — every decision is written to ``auto_trade_events`` so
   the execution page can show why the book looks the way it does.

Safety rails: a cooldown per symbol, a cap on concurrent positions, the paper
engine's own cash check, and a kill switch (``set_enabled(False)``) that the UI
drives. Nothing here can reach a real exchange — it only calls :class:`PaperService`.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from .config import Settings
from .db import Database, iso, parse_iso
from .errors import ApiException
from .paper import LONG, PERP, SHORT, PaperService, dec, money
from .signals import PHASE_LABELS, NemtSignalService, SignalCard

logger = logging.getLogger("nemt.auto_trade")


class AutoTrader:
    def __init__(
        self,
        db: Database,
        settings: Settings,
        paper: PaperService,
        signals: NemtSignalService,
    ):
        self.db = db
        self.settings = settings
        self.paper = paper
        self.signals = signals
        self._task: asyncio.Task[None] | None = None
        self._last_run_at: str | None = None
        self._last_error: str | None = None

    # ------------------------------------------------------------------
    # Kill switch
    # ------------------------------------------------------------------

    @property
    def username(self) -> str:
        return self.settings.auto_trade_username

    def enabled(self) -> bool:
        row = self.db.query_one(
            "SELECT value FROM auto_trade_flags WHERE key = 'enabled'"
        )
        if row is not None:
            return str(row["value"]) == "1"
        return bool(self.settings.auto_trade_enabled)

    def set_enabled(self, enabled: bool, *, actor: str | None = None) -> bool:
        now = iso()
        with self.db.tx(immediate=True) as conn:
            conn.execute(
                "INSERT INTO auto_trade_flags(key, value, updated_at, updated_by)"
                " VALUES ('enabled', ?, ?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
                " updated_at = excluded.updated_at, updated_by = excluded.updated_by",
                ("1" if enabled else "0", now, actor or "operator"),
            )
            self.db.log_audit(
                conn,
                action="auto_trade.toggle",
                mode=self.settings.mode.value,
                actor=actor,
                detail={"enabled": enabled},
            )
        logger.info("auto trade %s by %s", "enabled" if enabled else "paused", actor)
        return self.enabled()

    # ------------------------------------------------------------------
    # Journal
    # ------------------------------------------------------------------

    def _log(self, action: str, reason: str, *, symbol: str | None = None,
             position_id: str | None = None, detail: dict[str, Any] | None = None) -> None:
        import json

        with self.db.tx() as conn:
            conn.execute(
                "INSERT INTO auto_trade_events(ts, symbol, action, reason, position_id,"
                " detail_json) VALUES (?, ?, ?, ?, ?, ?)",
                (iso(), symbol, action, reason, position_id, json.dumps(detail or {}, ensure_ascii=False)),
            )

    def events(self, limit: int = 60) -> list[dict[str, Any]]:
        rows = self.db.query_all(
            "SELECT * FROM auto_trade_events ORDER BY id DESC LIMIT ?",
            (max(1, min(int(limit), 300)),),
        )
        return [
            {
                "id": int(row["id"]),
                "ts": str(row["ts"]),
                "symbol": row["symbol"],
                "action": str(row["action"]),
                "reason": str(row["reason"]),
                "position_id": row["position_id"],
            }
            for row in rows
        ]

    def _state(self, symbol: str) -> Any:
        return self.db.query_one(
            "SELECT * FROM auto_trade_state WHERE symbol = ?", (symbol,)
        )

    def _remember(self, symbol: str, *, phase: str | None, signal: str | None,
                  action: str | None = None) -> None:
        now = iso()
        with self.db.tx(immediate=True) as conn:
            conn.execute(
                "INSERT INTO auto_trade_state(symbol, last_phase, last_signal,"
                " last_action, last_action_at) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(symbol) DO UPDATE SET"
                " last_phase = excluded.last_phase,"
                " last_signal = excluded.last_signal,"
                " last_action = COALESCE(excluded.last_action, auto_trade_state.last_action),"
                " last_action_at = COALESCE(excluded.last_action_at, auto_trade_state.last_action_at)",
                (
                    symbol,
                    phase,
                    signal,
                    action,
                    now if action else None,
                ),
            )

    def _cooling_down(self, symbol: str) -> bool:
        row = self._state(symbol)
        if row is None or not row["last_action_at"]:
            return False
        last = parse_iso(str(row["last_action_at"]))
        if last is None:
            return False
        cooldown = timedelta(minutes=int(self.settings.auto_trade_cooldown_minutes))
        return datetime.now(timezone.utc) - last < cooldown

    # ------------------------------------------------------------------
    # One pass
    # ------------------------------------------------------------------

    async def run_once(self) -> list[dict[str, Any]]:
        username = self.username
        self.paper.ensure_account(username)
        decisions: list[dict[str, Any]] = []

        try:
            account = await self.paper.account(username)
            positions = await self.paper.positions(username)
        except ApiException as exc:
            self._last_error = str(exc)
            return decisions

        max_positions = int(self.settings.auto_trade_max_positions)
        # One slot per symbol: a small account must not let the first signal eat
        # every dollar and starve the other symbols.
        equity = account["equity"] if account else self.settings.paper_initial_equity
        slot = (Decimal(equity) * Decimal("0.95") / Decimal(max(1, max_positions))).quantize(
            Decimal("0.01")
        )

        meta = self.paper.position_meta(username)
        by_symbol = {position["symbol"]: position for position in positions}

        # 1) protective exits -------------------------------------------------
        for position in positions:
            level = meta.get(position["id"], {})
            mark = position["mark_price"]
            side = position["side"]
            stop = level.get("stop_price")
            take = level.get("take_price")
            hit_stop = stop is not None and (
                (side == LONG and mark <= stop) or (side == SHORT and mark >= stop)
            )
            hit_take = take is not None and (
                (side == LONG and mark >= take) or (side == SHORT and mark <= take)
            )
            if not (hit_stop or hit_take):
                continue
            label = "止损" if hit_stop else "止盈"
            try:
                result = await self.paper.close_position(
                    username, position["id"], fraction=Decimal("1")
                )
            except ApiException as exc:
                self._log("ERROR", f"{label}平仓失败：{exc.message}", symbol=position["symbol"],
                          position_id=position["id"])
                continue
            self._remember(position["symbol"], phase=None, signal=None, action=f"CLOSE_{label}")
            self._log(
                "CLOSE",
                f"{label}触发：标记价 {money(mark)} 穿越 {money(stop if hit_stop else take)}，"
                f"平仓毛利 {money(result['gross_pnl'])} USDT",
                symbol=position["symbol"],
                position_id=position["id"],
                detail={"gross_pnl": str(result["gross_pnl"]), "fee": str(result["fee"])},
            )
            decisions.append({"symbol": position["symbol"], "action": f"CLOSE_{label}"})
            by_symbol.pop(position["symbol"], None)

        # Pausing the strategy stops *new* risk, never the protective exits:
        # otherwise a paused desk would silently hold unprotected positions.
        if not self.enabled():
            self._last_run_at = iso()
            self._last_error = None
            return decisions

        # 2) strategy driven entries / exits ----------------------------------
        for symbol in self.settings.paper_symbols:
            try:
                card = await self.signals.card(symbol, self.settings.auto_trade_interval)
            except ApiException as exc:
                self._log("SKIP", f"信号不可用：{exc.message}", symbol=symbol)
                continue

            self._remember(symbol, phase=card.state.phase, signal=card.direction)
            position = by_symbol.get(symbol)

            if position is not None:
                flip = (position["side"] == LONG and card.direction == "SHORT") or (
                    position["side"] == SHORT and card.direction == "LONG"
                )
                if card.state.phase == "decay" or flip:
                    reason = (
                        f"相位转 decay，趋势衰竭，平掉{card.symbol}"
                        if card.state.phase == "decay"
                        else f"信号反向（{card.direction}），平掉{position['side']}"
                    )
                    try:
                        result = await self.paper.close_position(
                            username, position["id"], fraction=Decimal("1")
                        )
                    except ApiException as exc:
                        self._log("ERROR", f"平仓失败：{exc.message}", symbol=symbol,
                                  position_id=position["id"])
                        continue
                    self._remember(symbol, phase=card.state.phase, signal=card.direction,
                                   action="CLOSE")
                    self._log(
                        "CLOSE",
                        f"{reason}；毛利 {money(result['gross_pnl'])} USDT",
                        symbol=symbol,
                        position_id=position["id"],
                        detail={"gross_pnl": str(result["gross_pnl"])},
                    )
                    decisions.append({"symbol": symbol, "action": "CLOSE"})
                    by_symbol.pop(symbol, None)
                continue

            if card.direction not in ("LONG", "SHORT"):
                continue
            if len(by_symbol) >= max_positions:
                self._log("SKIP", f"已有 {len(by_symbol)} 个持仓达到上限 {max_positions}", symbol=symbol)
                continue
            if self._cooling_down(symbol):
                self._log(
                    "SKIP",
                    f"冷却期中（{self.settings.auto_trade_cooldown_minutes} 分钟内不重复开仓）",
                    symbol=symbol,
                )
                continue

            side = LONG if card.direction == "LONG" else SHORT
            notional = card.suggested_notional or slot
            notional = min(Decimal(notional), slot)
            if notional < self.settings.paper_min_notional:
                notional = Decimal(self.settings.paper_min_notional)
            leverage = max(1, card.suggested_leverage)
            try:
                opened = await self.paper.open_position(
                    username,
                    symbol=symbol,
                    market=PERP,
                    side=side,
                    notional=notional,
                    leverage=leverage,
                    strategy="NEMT",
                    stop_price=card.stop_loss,
                    take_price=card.take_profit,
                    reason=f"NEMT {card.state.phase} ψ={card.state.psi:+.3f}%",
                )
            except ApiException as exc:
                self._log("SKIP", f"开仓被拒：{exc.message}", symbol=symbol)
                continue

            self._remember(symbol, phase=card.state.phase, signal=card.direction, action="OPEN")
            self._log(
                "OPEN",
                f"{card.state.phase} 触发：{card.direction} {money(notional)} USDT "
                f"{leverage}x，止损 {money(card.stop_loss)} / 止盈 {money(card.take_profit)}",
                symbol=symbol,
                position_id=opened.get("id"),
                detail={
                    "psi": str(round(card.state.psi, 6)),
                    "entropy": str(round(card.state.entropy, 6)),
                    "leverage": leverage,
                },
            )
            decisions.append({"symbol": symbol, "action": f"OPEN_{card.direction}"})
            by_symbol[symbol] = opened

        self._last_run_at = iso()
        self._last_error = None
        return decisions

    # ------------------------------------------------------------------
    # Loop
    # ------------------------------------------------------------------

    async def loop(self) -> None:
        interval = max(10, int(self.settings.auto_trade_interval_seconds))
        logger.info(
            "auto trader started: interval=%ss timeframe=%s user=%s symbols=%s",
            interval,
            self.settings.auto_trade_interval,
            self.username,
            ",".join(self.settings.paper_symbols),
        )
        while True:
            try:
                decisions = await self.run_once()
                if decisions:
                    logger.info("auto trade decisions: %s", decisions)
            except asyncio.CancelledError:  # pragma: no cover - shutdown path
                raise
            except Exception as exc:  # noqa: BLE001 - the loop must survive
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("auto trade pass failed")
            await asyncio.sleep(interval)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
            self._task = None

    # ------------------------------------------------------------------
    # Board for the execution page
    # ------------------------------------------------------------------

    async def board(self, username: str | None = None) -> dict[str, Any]:
        """Everything the execution page needs, in the shape it already renders."""

        user = username or self.username
        self.paper.ensure_account(user)
        try:
            account = await self.paper.account(user)
            positions = await self.paper.positions(user)
        except ApiException:
            account = None
            positions = []

        meta = self.paper.position_meta(user)
        fills = self.paper.fills_for_positions(user, [p["id"] for p in positions])
        equity = Decimal(account["equity"]) if account else Decimal("0")

        legs: list[dict[str, Any]] = []
        for position in positions:
            symbol = position["symbol"]
            unit = symbol.replace("USDT", "")
            hits = fills.get(position["id"], [])
            if not hits:
                # The engine always writes an OPEN fill; guard anyway so the UI
                # never computes a position out of thin air.
                continue
            # 保证金率 = 该仓位锁定的保证金 / 账户权益，和传统交易软件同义
            margin_rate = (
                Decimal(position["margin"]) / equity * 100 if equity > 0 else Decimal("0")
            )
            legs.append(
                {
                    "symbol": f"{unit}/USDT",
                    "market": "PERPETUAL" if position["market"] == PERP else "SPOT",
                    "side": position["side"],
                    "leverage": position["leverage"],
                    "unit": unit,
                    "mark": str(Decimal(position["mark_price"]).quantize(Decimal("0.01"))),
                    "margin": f"{margin_rate:.1f}%",
                    "stop": str(meta.get(position["id"], {}).get("stop_price") or ""),
                    "take": str(meta.get(position["id"], {}).get("take_price") or ""),
                    "fills": [
                        {
                            "at": int(parse_iso(item["created_at"]).timestamp() * 1000)
                            if parse_iso(item["created_at"])
                            else 0,
                            "action": "CLOSE" if item["action"] == "LIQUIDATE" else item["action"],
                            "qty": float(item["qty"]),
                            "price": float(item["price"]),
                            "fee": float(item["fee"]),
                        }
                        for item in hits
                    ],
                }
            )

        # signal summary, one short line per symbol
        cards: list[SignalCard] = []
        try:
            cards = await self.signals.board(
                self.settings.paper_symbols,
                self.settings.auto_trade_interval,
                equity=account["equity"] if account else None,
            )
        except ApiException:
            cards = []
        signal_text = " · ".join(
            f"{card.symbol.replace('USDT', '')} {PHASE_LABELS[card.state.phase]}"
            for card in cards
        ) or "等待信号"

        state_row = self._state(self.settings.paper_symbols[0]) if self.settings.paper_symbols else None
        strategy = {
            "id": "nemt",
            "name": "NEMT Momentum",
            "code": "EMG-01",
            "version": "v1.0",
            "timeframe": self.settings.auto_trade_interval,
            "state": "运行中" if self.enabled() else "已暂停",
            "signal": signal_text,
            "risk": f"{Decimal(self.settings.nemt_risk_per_trade_pct):.0f}%",
            "legs": legs,
        }

        return {
            "strategy": strategy,
            "account": {
                "equity": str(account["equity"]) if account else "0",
                "cash": str(account["cash"]) if account else "0",
                "unrealized": str(account["unrealized"]) if account else "0",
                "realized": str(account["realized"]) if account else "0",
                "return_pct": str(account["return_pct"]) if account else "0",
                "initial_equity": str(account["initial_equity"]) if account else "0",
            },
            "signals": [card.as_dict() for card in cards],
            "events": self.events(40),
            "auto_trade": {
                "enabled": self.enabled(),
                "username": user,
                "interval_seconds": int(self.settings.auto_trade_interval_seconds),
                "timeframe": self.settings.auto_trade_interval,
                "max_positions": int(self.settings.auto_trade_max_positions),
                "cooldown_minutes": int(self.settings.auto_trade_cooldown_minutes),
                "last_run_at": self._last_run_at,
                "last_error": self._last_error,
                "state_row_present": state_row is not None,
            },
        }
