"""
Order Manager
订单管理器 - 订单生命周期管理
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from services.exchange_adapter import Order, OrderSide, OrderType, OrderStatus
from services.risk_gate import RiskGate, RiskCheck


@dataclass
class OrderRecord:
    """订单记录"""
    order: Order
    signal: str
    reason: str
    risk_checks: List[RiskCheck] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class OrderManager:
    """订单管理器"""

    def __init__(self, exchange, risk_gate: RiskGate):
        self.exchange = exchange
        self.risk_gate = risk_gate
        self.orders: Dict[str, OrderRecord] = {}
        self.order_history: List[OrderRecord] = []

    async def create_order_from_signal(
        self,
        symbol: str,
        signal: str,
        confidence: float,
        dci: float,
        current_balance: float = 10000.0,
        current_position: float = 0.0,
    ) -> Optional[Order]:
        """
        从信号创建订单

        Signal → Decision → Risk Check → Order
        """
        # 1. 信号解析
        side, order_type, quantity = self._parse_signal(signal, current_balance)

        # 2. 获取市场价格
        market_data = await self.exchange.get_market_data(symbol)
        price = market_data.price

        # 3. 风险检查
        passed, risk_checks = self.risk_gate.check_order(
            symbol=symbol,
            side=side.value,
            quantity=quantity,
            price=price,
            current_balance=current_balance,
            current_position=current_position,
        )

        # 4. 记录决策
        reason = self._generate_reason(signal, confidence, dci, passed, risk_checks)

        if not passed:
            print(f"❌ Order blocked by Risk Gate: {symbol}")
            # 记录被拒绝的订单
            self._record_rejected_order(
                symbol, side, order_type, quantity, price, signal, reason, risk_checks
            )
            return None

        # 5. 创建订单
        try:
            order = await self.exchange.place_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price,
            )

            # 6. 记录订单
            record = OrderRecord(
                order=order,
                signal=signal,
                reason=reason,
                risk_checks=risk_checks,
            )
            self.orders[order.id] = record
            self.order_history.append(record)

            print(f"✅ Order Created: {order.id}")
            return order

        except Exception as e:
            print(f"❌ Order creation failed: {e}")
            return None

    def _parse_signal(self, signal: str, balance: float) -> tuple:
        """解析信号为订单参数"""
        signal_map = {
            "BUY": (OrderSide.BUY, OrderType.MARKET, balance * 0.1),
            "STRONG_BUY": (OrderSide.BUY, OrderType.MARKET, balance * 0.2),
            "SELL": (OrderSide.SELL, OrderType.MARKET, balance * 0.1),
            "REDUCE": (OrderSide.SELL, OrderType.MARKET, balance * 0.05),
            "HOLD": (OrderSide.BUY, OrderType.MARKET, 0),
            "WAIT": (OrderSide.BUY, OrderType.MARKET, 0),
        }

        return signal_map.get(signal, (OrderSide.BUY, OrderType.MARKET, 0))

    def _generate_reason(
        self,
        signal: str,
        confidence: float,
        dci: float,
        passed: bool,
        risk_checks: List[RiskCheck],
    ) -> str:
        """生成订单原因"""
        status = "APPROVED" if passed else "REJECTED"

        risk_summary = ", ".join([
            f"{c.name}: {c.level.value}" for c in risk_checks
        ])

        return (
            f"Signal: {signal} | "
            f"Confidence: {confidence:.1f}% | "
            f"DCI: {dci:.1f} | "
            f"Status: {status} | "
            f"Risk: {risk_summary}"
        )

    def _record_rejected_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float,
        signal: str,
        reason: str,
        risk_checks: List[RiskCheck],
    ):
        """记录被拒绝的订单"""
        order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity,
            price=price,
            stop_price=None,
            status=OrderStatus.REJECTED,
            filled_quantity=0,
            avg_price=0,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        record = OrderRecord(
            order=order,
            signal=signal,
            reason=reason,
            risk_checks=risk_checks,
        )
        self.order_history.append(record)

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        if order_id not in self.orders:
            return False

        record = self.orders[order_id]
        success = await self.exchange.cancel_order(order_id, record.order.symbol)

        if success:
            record.order.status = OrderStatus.CANCELLED
            record.order.updated_at = datetime.now().isoformat()

        return success

    def get_order(self, order_id: str) -> Optional[OrderRecord]:
        """获取订单"""
        return self.orders.get(order_id)

    def get_open_orders(self) -> List[OrderRecord]:
        """获取未成交订单"""
        return [
            r for r in self.orders.values()
            if r.order.status in [OrderStatus.OPEN, OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
        ]

    def get_order_history(self, limit: int = 100) -> List[OrderRecord]:
        """获取订单历史"""
        return sorted(
            self.order_history,
            key=lambda r: r.created_at,
            reverse=True,
        )[:limit]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.order_history)
        filled = len([r for r in self.order_history if r.order.status == OrderStatus.FILLED])
        rejected = len([r for r in self.order_history if r.order.status == OrderStatus.REJECTED])
        cancelled = len([r for r in self.order_history if r.order.status == OrderStatus.CANCELLED])

        return {
            "total_orders": total,
            "filled": filled,
            "rejected": rejected,
            "cancelled": cancelled,
            "open": len(self.get_open_orders()),
        }
