"""
NEMT Platform - Execution Service
执行服务

职责：
- 订阅风控通过的信号
- 订单执行
- 持仓跟踪
- 成交回报处理
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from ..base import BaseService
from ..common.types import EventTypes


@dataclass
class Order:
    """订单"""

    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market' or 'limit'
    quantity: float
    price: float
    status: str = "pending"  # pending, sent, filled, cancelled
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    """持仓"""

    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    opened_at: datetime = field(default_factory=datetime.now)


class ExecutionService(BaseService):
    """
    Execution Service

    订阅事件：
    - risk.approved: 风控通过
    - risk.rejected: 风控拒绝

    发布事件：
    - execution.order_sent: 订单发送
    - execution.filled: 订单成交
    - execution.position_update: 持仓更新
    """

    def __init__(self):
        super().__init__("execution", port=8004)

        # 账户
        self._balance = 100000.0
        self._available_balance = 100000.0

        # 持仓
        self._positions: dict[str, Position] = {}

        # 订单历史
        self._orders: dict[str, Order] = {}

    async def on_init(self):
        """初始化"""
        self.logger.info("Execution Service 初始化中...")

        self._balance = 100000.0
        self._available_balance = 100000.0
        self._positions = {}
        self._orders = {}

        self.logger.info("Execution Service 初始化完成")

    async def on_start(self):
        """启动"""
        self.logger.info("Execution Service 启动中...")

        # 订阅风控事件
        self.subscribe(EventTypes.RISK_APPROVED, self._on_risk_approved)
        self.subscribe(EventTypes.RISK_REJECTED, self._on_risk_rejected)

        self.logger.info("Execution Service 启动完成")

    async def _on_risk_approved(self, data: dict):
        """处理风控通过"""
        self.logger.info(f"收到风控通过信号: {data.get('symbol')}")
        await self._execute_order(data)

    async def _on_risk_rejected(self, data: dict):
        """处理风控拒绝"""
        self.logger.info(f"收到风控拒绝信号: {data.get('symbol')}, 原因: {data.get('reasons')}")

    async def _execute_order(self, risk_data: dict):
        """执行订单"""
        symbol = risk_data.get("symbol")
        position_size = risk_data.get("position_size", 0)
        entry_price = risk_data.get("adjusted_entry", 0)

        if position_size <= 0 or entry_price <= 0:
            return

        # 创建订单
        order_id = str(uuid.uuid4())
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side="buy",
            order_type="market",
            quantity=position_size,
            price=entry_price,
            status="sent",
        )

        self._orders[order_id] = order
        self.logger.info(f"发送订单: {order_id} {symbol} {position_size} @ {entry_price}")

        # 发布订单发送事件
        await self.publish(
            EventTypes.EXECUTION_ORDER_SENT,
            {
                "order_id": order_id,
                "symbol": symbol,
                "side": "buy",
                "quantity": position_size,
                "price": entry_price,
            },
        )

        # 模拟成交（实际应该连接交易所 API）
        asyncio.create_task(self._simulate_fill(order))

    async def _simulate_fill(self, order: Order):
        """模拟成交"""
        await asyncio.sleep(0.5)  # 模拟网络延迟

        # 更新订单状态
        order.status = "filled"

        # 创建持仓
        position = Position(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            entry_price=order.price,
            current_price=order.price,
            unrealized_pnl=0.0,
        )

        self._positions[order.symbol] = position

        # 扣除保证金
        cost = order.quantity * order.price
        self._available_balance -= cost

        self.logger.info(f"订单成交: {order.order_id} {order.symbol} {order.quantity} @ {order.price}")

        # 发布成交事件
        await self.publish(
            EventTypes.EXECUTION_FILLED,
            {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "price": order.price,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # 发布持仓更新
        await self._publish_position_update()

    async def _publish_position_update(self):
        """发布持仓更新"""
        positions_data = [
            {
                "symbol": p.symbol,
                "side": p.side,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "unrealized_pnl": p.unrealized_pnl,
            }
            for p in self._positions.values()
        ]

        await self.publish(
            EventTypes.EXECUTION_POSITION_UPDATE,
            {
                "positions": positions_data,
                "balance": self._balance,
                "available_balance": self._available_balance,
            },
        )

    async def close_position(self, symbol: str):
        """平仓"""
        if symbol not in self._positions:
            return

        position = self._positions[symbol]

        # 创建平仓订单
        order_id = str(uuid.uuid4())
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side="sell",
            order_type="market",
            quantity=position.quantity,
            price=position.current_price,
            status="sent",
        )

        self._orders[order_id] = order

        # 模拟成交
        await asyncio.sleep(0.5)
        order.status = "filled"

        # 计算收益
        if position.side == "buy":
            pnl = (position.current_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - position.current_price) * position.quantity

        # 更新余额
        proceeds = position.quantity * position.current_price
        self._available_balance += proceeds

        # 删除持仓
        del self._positions[symbol]

        self.logger.info(f"平仓: {symbol} PnL: {pnl:.2f}")

        # 发布成交事件
        await self.publish(
            EventTypes.EXECUTION_FILLED,
            {
                "order_id": order_id,
                "symbol": symbol,
                "side": "sell",
                "quantity": position.quantity,
                "price": position.current_price,
                "pnl": pnl,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def get_status(self) -> dict:
        """获取状态"""
        total_pnl = sum(p.unrealized_pnl for p in self._positions.values())

        return {
            "balance": self._balance,
            "available_balance": self._available_balance,
            "positions_count": len(self._positions),
            "orders_count": len(self._orders),
            "total_unrealized_pnl": total_pnl,
        }


async def main():
    """入口"""
    service = ExecutionService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
