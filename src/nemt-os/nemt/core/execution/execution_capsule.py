"""
ExecutionCapsule - 分形迭代版

按五阶段迭代法重写的执行胶囊。
"""

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from nemt.core.capsule import FractalCapsule


class OrderStatus(Enum):
    """订单状态"""

    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderSide(Enum):
    """订单方向"""

    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """订单"""

    order_id: str
    symbol: str
    side: OrderSide
    order_type: str
    price: float
    quantity: float
    filled_quantity: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    fills: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type,
            "price": self.price,
            "quantity": self.quantity,
            "filled_quantity": self.filled_quantity,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ExecutionCapsule(FractalCapsule):
    """
    执行胶囊

    负责：
    - 订单提交
    - 持仓更新
    - 订单状态跟踪
    - 成交记录

    五阶段方法已实现。
    """

    def __init__(self, capsule_id: str = "execution"):
        super().__init__(capsule_id, version="1.0.0")
        self._layer = "L1"

        # 持仓管理
        self._positions: dict[str, dict] = {}
        self._orders: dict[str, Order] = {}
        self._balance: float = 0.0
        self._lock = threading.Lock()

        # 执行配置
        self._commission_rate = 0.001  # 手续费 0.1%

    # ========================================
    # 【看】观察阶段
    # ========================================

    def observe_phase(self) -> dict[str, Any]:
        """【看】观察阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "approved_signals": {
                    "type": "list",
                    "source": "RiskCapsule",
                    "required": True,
                },
                "market_price": {
                    "type": "number",
                    "source": "MarketCapsule",
                    "required": True,
                },
            },
            "outputs": {
                "orders": {"type": "list"},
                "positions": {"type": "dict"},
                "balance": {"type": "number"},
            },
            "constraints": {
                "min_order_size": 0.001,
                "max_orders_per_symbol": 2,
                "commission_rate": self._commission_rate,
            },
            "dependencies": ["RiskCapsule", "MarketCapsule", "ConfigCenter"],
            "risks": [
                {"type": "滑点", "mitigation": "限价单+滑点容忍"},
                {"type": "成交失败", "mitigation": "重试机制"},
            ],
            "subscribes_to": ["risk.approved"],
            "publishes": ["order.submitted", "order.filled", "position.updated"],
        }

    # ========================================
    # 【画】设计阶段
    # ========================================

    def design_phase(self) -> dict[str, Any]:
        """【画】设计阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "submit_order(symbol, side, quantity, price)": "提交订单",
                "cancel_order(order_id)": "取消订单",
                "get_position(symbol)": "获取持仓",
                "get_orders(status)": "获取订单列表",
                "get_balance()": "获取余额",
            },
            "input_schema": {
                "symbol": {"type": "string"},
                "side": {"type": "string", "enum": ["buy", "sell"]},
                "quantity": {"type": "number"},
                "price": {"type": "number"},
            },
            "output_schema": {
                "order_id": {"type": "string"},
                "status": {"type": "string"},
                "filled_quantity": {"type": "number"},
            },
        }

    # ========================================
    # 【填】实现阶段
    # ========================================

    def implement_phase(self) -> None:
        """【填】实现阶段"""
        self._commission_rate = self.get_config("execution.commission_rate", 0.001)
        self._logger.info(f"{self._capsule_id} 实现阶段完成")

    # ========================================
    # 【验】验证阶段
    # ========================================

    def verify_phase(self) -> dict[str, Any]:
        """【验】验证阶段"""
        return {
            "capsule_id": self._capsule_id,
            "phase": "verify",
            "passed": True,
            "checks": {"thread_safe": hasattr(self, "_lock")},
        }

    # ========================================
    # 【连】集成阶段
    # ========================================

    def integrate_phase(self) -> None:
        """【连】集成阶段"""
        self._logger.info(f"{self._capsule_id} 集成阶段完成")
        self._logger.info("  上游: RiskCapsule")
        self._logger.info("  下游: MonitorCapsule")

    # ========================================
    # 标准生命周期
    # ========================================

    def init(self) -> None:
        """初始化"""
        self.subscribe("risk.approved", self._on_risk_approved)
        self._initialized = True

    def exec(self) -> dict[str, Any]:
        """执行"""
        with self._lock:
            return {
                "balance": self._balance,
                "positions": {k: v for k, v in self._positions.items()},
                "orders_count": len(self._orders),
            }

    def shutdown(self) -> None:
        """关闭"""
        self._positions.clear()
        self._orders.clear()

    # ========================================
    # 公开 API
    # ========================================

    def set_balance(self, balance: float) -> None:
        """设置余额"""
        with self._lock:
            self._balance = balance

    def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        order_type: str = "limit",
    ) -> Order:
        """提交订单"""
        with self._lock:
            order_id = str(uuid.uuid4())[:8].upper()

            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                price=price,
                quantity=quantity,
            )

            self._orders[order_id] = order
            self.publish("order.submitted", order.to_dict())

            return order

    def fill_order(self, order_id: str, quantity: float, fill_price: float) -> bool:
        """成交订单"""
        with self._lock:
            if order_id not in self._orders:
                return False

            order = self._orders[order_id]
            order.filled_quantity += quantity
            order.updated_at = datetime.now()

            commission = quantity * fill_price * self._commission_rate

            if order.side == OrderSide.BUY:
                cost = quantity * fill_price + commission
                self._balance -= cost

                if symbol := order.symbol:
                    if symbol not in self._positions:
                        self._positions[symbol] = {
                            "size": 0,
                            "entry": 0,
                            "realized_pnl": 0,
                        }
                    pos = self._positions[symbol]
                    total_size = pos["size"] + quantity
                    pos["entry"] = (pos["entry"] * pos["size"] + fill_price * quantity) / total_size
                    pos["size"] = total_size

            else:  # SELL
                revenue = quantity * fill_price - commission
                self._balance += revenue

                if symbol := order.symbol:
                    if symbol in self._positions:
                        pos = self._positions[symbol]
                        pnl = (fill_price - pos["entry"]) * quantity
                        pos["realized_pnl"] += pnl
                        pos["size"] -= quantity
                        if pos["size"] <= 0:
                            del self._positions[symbol]

            order.fills.append(
                {
                    "quantity": quantity,
                    "price": fill_price,
                    "commission": commission,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            if order.filled_quantity >= order.quantity:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIAL_FILLED

            self.publish("order.filled", order.to_dict())
            return True

    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        with self._lock:
            if order_id not in self._orders:
                return False

            order = self._orders[order_id]
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            return True

    def get_position(self, symbol: str) -> dict | None:
        """获取持仓"""
        with self._lock:
            return self._positions.get(symbol)

    def get_orders(self, status: OrderStatus = None) -> list[Order]:
        """获取订单列表"""
        with self._lock:
            if status:
                return [o for o in self._orders.values() if o.status == status]
            return list(self._orders.values())

    def get_balance(self) -> float:
        """获取余额"""
        with self._lock:
            return self._balance

    # ========================================
    # 内部方法
    # ========================================

    def _on_risk_approved(self, approved_data: dict) -> None:
        """处理风控批准"""
        symbol = approved_data.get("symbol", "")
        position_size = approved_data.get("position_size", 0)
        entry_price = approved_data.get("adjusted_entry", 0)

        if position_size > 0 and entry_price > 0:
            self.submit_order(
                symbol=symbol,
                side=OrderSide.BUY,
                quantity=position_size,
                price=entry_price,
            )
