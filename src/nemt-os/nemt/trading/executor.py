"""
OrderExecutor - 订单执行器

提供订单路由、成交匹配、滑点控制能力。
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "OrderExecutor",
    "ExecutionPlan",
    "Fill",
]


@dataclass
class ExecutionPlan:
    """执行计划"""

    order_id: str
    symbol: str
    target_quantity: float
    filled_quantity: float = 0
    avg_price: float = 0
    slippage: float = 0
    status: str = "pending"
    fills: list["Fill"] = field(default_factory=list)


@dataclass
class Fill:
    """成交"""

    fill_id: str
    order_id: str
    timestamp: float
    quantity: float
    price: float
    commission: float = 0


class OrderExecutor:
    """
    订单执行器

    示例:
    ```python
    executor = OrderExecutor()

    # 提交订单
    order_id = executor.submit_order(
        symbol="AAPL",
        side="buy",
        quantity=100,
        order_type="market",
    )

    # 获取执行状态
    plan = executor.get_plan(order_id)
    print(f"成交: {plan.filled_quantity} @ {plan.avg_price}")
    ```
    """

    def __init__(self, slippage_model: float = 0.001):
        self.slippage_model = slippage_model
        self._orders: dict[str, ExecutionPlan] = {}
        self._fills: dict[str, list[Fill]] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger("OrderExecutor")

    def submit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        limit_price: float = None,
        target_price: float = None,
    ) -> str:
        """提交订单"""
        order_id = str(uuid.uuid4())

        plan = ExecutionPlan(
            order_id=order_id,
            symbol=symbol,
            target_quantity=quantity,
        )

        with self._lock:
            self._orders[order_id] = plan
            self._fills[order_id] = []

        # 模拟执行
        self._execute_order(plan, side, order_type, limit_price, target_price)

        return order_id

    def _execute_order(
        self,
        plan: ExecutionPlan,
        side: str,
        order_type: str,
        limit_price: float,
        target_price: float,
    ) -> None:
        """执行订单（模拟）"""
        if order_type == "market":
            # 市价单：假设以目标价格执行
            exec_price = target_price * (1 + self.slippage_model if side == "buy" else 1 - self.slippage_model)
        else:
            exec_price = limit_price or target_price

        # 模拟分批成交
        quantity = plan.target_quantity
        fill_quantity = quantity * 0.7  # 70% 立即成交
        remaining = quantity - fill_quantity

        # 第一次成交
        fill = Fill(
            fill_id=str(uuid.uuid4()),
            order_id=plan.order_id,
            timestamp=time.time(),
            quantity=fill_quantity,
            price=exec_price,
            commission=fill_quantity * exec_price * 0.0001,
        )

        with self._lock:
            plan.filled_quantity += fill_quantity
            plan.avg_price = (
                (plan.avg_price * (plan.filled_quantity - fill_quantity) + fill.price * fill.quantity)
                / plan.filled_quantity
                if plan.filled_quantity > 0
                else 0
            )
            plan.fills.append(fill)
            self._fills[plan.order_id].append(fill)

        # 剩余部分延迟成交
        if remaining > 0:
            time.sleep(0.1)
            fill2 = Fill(
                fill_id=str(uuid.uuid4()),
                order_id=plan.order_id,
                timestamp=time.time(),
                quantity=remaining,
                price=exec_price * 1.001,  # 轻微滑点
                commission=remaining * exec_price * 0.0001,
            )

            with self._lock:
                plan.filled_quantity += remaining
                plan.avg_price = (
                    plan.avg_price * (plan.filled_quantity - remaining) + fill2.price * remaining
                ) / plan.filled_quantity
                plan.fills.append(fill2)
                self._fills[plan.order_id].append(fill2)

        plan.status = "filled" if plan.filled_quantity >= plan.target_quantity else "partial"

    def get_plan(self, order_id: str) -> ExecutionPlan | None:
        """获取执行计划"""
        return self._orders.get(order_id)

    def get_fills(self, order_id: str) -> list[Fill]:
        """获取成交列表"""
        return self._fills.get(order_id, [])

    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        with self._lock:
            plan = self._orders.get(order_id)
            if plan and plan.status in ("pending", "partial"):
                plan.status = "cancelled"
                return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """获取统计"""
        with self._lock:
            total_orders = len(self._orders)
            filled_orders = len([p for p in self._orders.values() if p.status == "filled"])

            total_quantity = sum(p.filled_quantity for p in self._orders.values())
            total_commission = sum(f.commission for fills in self._fills.values() for f in fills)

            return {
                "total_orders": total_orders,
                "filled_orders": filled_orders,
                "total_quantity": total_quantity,
                "total_commission": total_commission,
            }
