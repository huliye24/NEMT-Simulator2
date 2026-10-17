"""Independent, fail-closed pre-trade risk checks.

This module never trusts values sent by the browser for mode, limits or
balances. Every check returns an auditable result with a stable code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from typing import Any

from .accounts import AccountSnapshot
from .config import AppMode, Settings
from .db import Database, iso
from .errors import ApiException
from .market import SymbolRules, Ticker
from .schemas import OrderType, Side


class OrderValidationError(ApiException):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(422, code, message, details=details)


def quantize_down(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        raise OrderValidationError("invalid_exchange_rules", "Exchange step size is invalid")
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def normalize_order(
    *,
    rules: SymbolRules,
    symbol: str,
    side: Side,
    order_type: OrderType,
    quantity: Decimal,
    price: Decimal | None,
    latest_price: Decimal,
) -> tuple[Decimal, Decimal | None, bool]:
    """Clamp user input to venue tick/step sizes, then validate it."""

    if quantity <= 0:
        raise OrderValidationError("invalid_quantity", "数量必须大于 0")
    if order_type is OrderType.LIMIT:
        if price is None or price <= 0:
            raise OrderValidationError("price_required", "限价单必须填写价格")
        normalized_price = quantize_down(price, rules.tick_size)
        if normalized_price <= 0:
            raise OrderValidationError("price_too_small", "价格低于交易对允许的最小变动单位")
    elif order_type is OrderType.MARKET:
        if price is not None:
            raise OrderValidationError("price_not_allowed", "市价单不接受价格字段")
        normalized_price = None
    else:
        raise OrderValidationError("unsupported_order_type", "仅支持市价单与限价单")

    normalized_qty = quantize_down(quantity, rules.step_size)
    if normalized_qty < rules.min_qty or normalized_qty <= 0:
        raise OrderValidationError(
            "quantity_too_small",
            f"数量低于交易所最小下单量 {rules.min_qty} {rules.base_asset}",
        )
    if normalized_qty > rules.max_qty:
        raise OrderValidationError(
            "quantity_too_large",
            f"数量超过交易所最大下单量 {rules.max_qty} {rules.base_asset}",
        )

    reference_price = normalized_price if normalized_price is not None else latest_price
    notional = (normalized_qty * reference_price).quantize(Decimal("0.00000001"))
    if notional < rules.min_notional:
        raise OrderValidationError(
            "below_min_notional",
            f"订单名义金额 {notional:.2f} USDT 低于最小要求 {rules.min_notional} USDT",
            details={"notional": str(notional), "min_notional": str(rules.min_notional)},
        )

    changed = normalized_qty != quantity or (
        normalized_price is not None and normalized_price != price
    )
    return normalized_qty, normalized_price, changed


@dataclass(frozen=True)
class RiskCheck:
    code: str
    passed: bool
    message: str

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "passed": self.passed, "message": self.message}


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    checked_at: str
    reasons: list[str]
    checks: list[RiskCheck]
    notional: Decimal
    estimated_fee: Decimal
    fee_asset: str
    normalized_quantity: Decimal
    normalized_price: Decimal | None
    normalized: bool
    reference_price: Decimal
    base_asset: str
    quote_asset: str
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "checked_at": self.checked_at,
            "reasons": self.reasons,
            "checks": [check.as_dict() for check in self.checks],
        }


class RiskService:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings

    def flag_state(self) -> dict[str, object]:
        rows = {
            str(row["key"]): str(row["value"])
            for row in self.db.query_all(
                "SELECT key, value FROM system_flags WHERE key IN"
                " ('pause_new_orders', 'pause_reason', 'pause_updated_at', 'pause_updated_by')"
            )
        }
        return {
            "pause_new_orders": rows.get("pause_new_orders", "0") == "1",
            "pause_reason": rows.get("pause_reason") or None,
            "pause_updated_at": rows.get("pause_updated_at") or None,
            "pause_updated_by": rows.get("pause_updated_by") or None,
        }

    def assess(
        self,
        *,
        username: str,
        symbol: str,
        side: Side,
        order_type: OrderType,
        quantity: Decimal,
        price: Decimal | None,
        rules: SymbolRules,
        ticker: Ticker,
        account: AccountSnapshot,
        open_order_count: int,
        orders_last_minute: int,
        daily_notional: Decimal,
    ) -> RiskDecision:
        checks: list[RiskCheck] = []

        def add(code: str, passed: bool, message: str) -> None:
            checks.append(RiskCheck(code=code, passed=passed, message=message))

        if self.settings.mode is AppMode.DEMO:
            add("mode", True, "DEMO 模式：订单仅进入本地模拟账本，不发送到交易所")
        elif self.settings.mode is AppMode.TESTNET:
            if self.settings.allow_testnet_trading and self.settings.testnet_credentials_configured:
                add("mode", True, "TESTNET 模式：订单只发送到 Binance Spot Testnet")
            else:
                add(
                    "mode",
                    False,
                    "TESTNET 交易未启用或服务端凭据未配置，新订单被拒绝",
                )
        else:
            add(
                "mode",
                False,
                "V0.1 不提供 LIVE 下单路径；实盘需要 issue #15 独立审批门禁",
            )

        flags = self.flag_state()
        if flags["pause_new_orders"]:
            add(
                "kill_switch",
                False,
                f"全局暂停新订单已启用：{flags['pause_reason'] or '未填写原因'}",
            )
        else:
            add("kill_switch", True, "全局暂停开关未启用")

        symbol_allowed = symbol.upper() in self.settings.allowed_symbols
        add(
            "symbol_allowlist",
            symbol_allowed,
            f"{symbol} {'在' if symbol_allowed else '不在'}服务端允许交易列表",
        )

        if ticker.stale:
            add("market_freshness", False, "行情已过期，禁止下单")
        elif self.settings.mode is not AppMode.DEMO and ticker.source != "binance":
            add("market_freshness", False, "TESTNET/LIVE 必须使用真实交易所行情")
        else:
            add(
                "market_freshness",
                True,
                f"行情源 {ticker.source}，更新时间 {ticker.fetched_at}",
            )

        if not account.connected:
            add("account", False, account.note or "账户未连接")
        elif account.stale:
            add("account", False, "账户快照已过期，禁止下单")
        else:
            add("account", True, "账户快照可用")

        try:
            normalized_qty, normalized_price, normalized = normalize_order(
                rules=rules,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                latest_price=ticker.last_price,
            )
            add("precision", True, "数量与价格已按交易所过滤器规范化")
        except OrderValidationError as exc:
            add("precision", False, exc.message)
            return self._finish(
                checks=checks,
                ticker=ticker,
                rules=rules,
                notional=Decimal("0"),
                fee=Decimal("0"),
                quantity=quantity,
                price=price,
                reference_price=ticker.last_price,
                normalized=False,
            )

        reference_price = normalized_price if normalized_price is not None else ticker.last_price
        notional = (normalized_qty * reference_price).quantize(Decimal("0.00000001"))
        fee = (notional * self.settings.trading_fee_rate).quantize(Decimal("0.00000001"))
        fee_asset = rules.quote_asset

        add(
            "min_notional",
            notional >= self.settings.min_order_notional,
            f"本环境最小单笔名义额 {self.settings.min_order_notional} {rules.quote_asset}",
        )
        add(
            "max_notional",
            notional <= self.settings.max_order_notional,
            f"本环境最大单笔名义额 {self.settings.max_order_notional} {rules.quote_asset}",
        )
        add(
            "daily_budget",
            daily_notional + notional <= self.settings.max_daily_notional,
            f"当日已用 {daily_notional} / {self.settings.max_daily_notional} {rules.quote_asset}",
        )
        add(
            "open_orders",
            open_order_count < self.settings.max_open_orders,
            f"未完成订单 {open_order_count} / 上限 {self.settings.max_open_orders}",
        )
        add(
            "order_rate",
            orders_last_minute < self.settings.max_orders_per_minute,
            f"最近一分钟订单 {orders_last_minute} / 上限 {self.settings.max_orders_per_minute}",
        )

        free_balances = {item.asset: item.free for item in account.balances}
        free_quote = free_balances.get(rules.quote_asset, Decimal("0"))
        free_base = free_balances.get(rules.base_asset, Decimal("0"))
        if side is Side.BUY:
            required_quote = notional + fee
            balance_ok = free_quote >= required_quote
            add(
                "balance",
                balance_ok,
                f"可用 {rules.quote_asset} {free_quote}，需要 {required_quote}（含估算手续费）",
            )
            current_position = (
                Decimal("0")
                if ticker.last_price <= 0
                else (free_base * ticker.last_price)
            )
            add(
                "position_limit",
                current_position + notional <= self.settings.max_position_notional,
                f"持仓估值 {current_position:.2f}，加上本单后需不超过"
                f" {self.settings.max_position_notional} {rules.quote_asset}",
            )
        else:
            add(
                "balance",
                free_base >= normalized_qty,
                f"可用 {rules.base_asset} {free_base}，需要 {normalized_qty}",
            )
            add("position_limit", True, "卖出不增加持仓风险")

        decision = self._finish(
            checks=checks,
            ticker=ticker,
            rules=rules,
            notional=notional,
            fee=fee,
            quantity=normalized_qty,
            price=normalized_price,
            reference_price=reference_price,
            normalized=normalized,
        )
        return RiskDecision(
            **{
                **decision.__dict__,
                "details": {
                    "open_order_count": open_order_count,
                    "orders_last_minute": orders_last_minute,
                    "daily_notional": str(daily_notional),
                },
            }
        )

    def _finish(
        self,
        *,
        checks: list[RiskCheck],
        ticker: Ticker,
        rules: SymbolRules,
        notional: Decimal,
        fee: Decimal,
        quantity: Decimal,
        price: Decimal | None,
        reference_price: Decimal,
        normalized: bool,
    ) -> RiskDecision:
        failed = [check for check in checks if not check.passed]
        return RiskDecision(
            approved=not failed,
            checked_at=iso(),
            reasons=[f"[{check.code}] {check.message}" for check in failed],
            checks=checks,
            notional=notional,
            estimated_fee=fee,
            fee_asset=rules.quote_asset,
            normalized_quantity=quantity,
            normalized_price=price,
            normalized=normalized,
            reference_price=reference_price,
            base_asset=rules.base_asset,
            quote_asset=rules.quote_asset,
        )
