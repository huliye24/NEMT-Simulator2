"""
Execution Domain Models - 执行领域模型

定义执行上下文中所有业务实体：
- Order: 订单聚合根
- FillRecord: 成交记录实体
- AccountBalance: 账户余额实体

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class OrderStatus(Enum):
    """订单状态枚举"""

    PENDING = "pending"  # 等待提交
    SUBMITTED = "submitted"  # 已提交
    PARTIAL_FILLED = "partial_filled"  # 部分成交
    FILLED = "filled"  # 完全成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"  # 已拒绝

    def __str__(self) -> str:
        return self.value

    def can_transition_to(self, new_status: OrderStatus) -> bool:
        """检查状态是否可以转换"""
        valid_transitions = {
            OrderStatus.PENDING: [
                OrderStatus.SUBMITTED,
                OrderStatus.CANCELLED,
                OrderStatus.REJECTED,
            ],
            OrderStatus.SUBMITTED: [
                OrderStatus.PARTIAL_FILLED,
                OrderStatus.FILLED,
                OrderStatus.CANCELLED,
                OrderStatus.REJECTED,
            ],
            OrderStatus.PARTIAL_FILLED: [
                OrderStatus.FILLED,
                OrderStatus.CANCELLED,
            ],
        }
        return new_status in valid_transitions.get(self, [])


class OrderSide(Enum):
    """订单方向枚举"""

    BUY = "buy"
    SELL = "sell"

    def __str__(self) -> str:
        return self.value

    @property
    def is_long(self) -> bool:
        return self == OrderSide.BUY

    @property
    def is_short(self) -> bool:
        return self == OrderSide.SELL


class OrderType(Enum):
    """订单类型枚举"""

    LIMIT = "limit"
    MARKET = "market"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

    def __str__(self) -> str:
        return self.value


@dataclass
class FillRecord:
    """
    成交记录实体

    表示订单的部分成交详情。

    INVARIANTS:
    - quantity > 0
    - price > 0
    - commission >= 0
    """

    fill_id: str
    order_id: str
    quantity: float
    price: float
    commission: float

    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    fill_type: str = "normal"  # normal, liquidation, adjustment
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.commission < 0:
            raise ValueError("commission must be non-negative")
        if not self.fill_id:
            self.fill_id = str(uuid.uuid4())[:8]

    @property
    def notional_value(self) -> float:
        """成交名义价值"""
        return self.quantity * self.price

    @property
    def net_value(self) -> float:
        """净价值（扣除手续费）"""
        return self.notional_value - self.commission

    def to_dict(self) -> dict[str, Any]:
        return {
            "fill_id": self.fill_id,
            "order_id": self.order_id,
            "quantity": self.quantity,
            "price": self.price,
            "commission": self.commission,
            "notional_value": self.notional_value,
            "net_value": self.net_value,
            "timestamp": self.timestamp.isoformat(),
            "fill_type": self.fill_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FillRecord:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now()

        return cls(
            fill_id=data.get("fill_id", str(uuid.uuid4())[:8]),
            order_id=data.get("order_id", ""),
            quantity=float(data.get("quantity", 0)),
            price=float(data.get("price", 0)),
            commission=float(data.get("commission", 0)),
            timestamp=ts,
            fill_type=data.get("fill_type", "normal"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Order:
    """
    订单聚合根

    表示一笔完整的交易订单。
    聚合根：外部只能通过此类访问订单相关数据。

    INVARIANTS:
    - filled_quantity <= quantity
    - 状态机严格流转

    VERSION: 支持乐观锁
    """

    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: float
    quantity: float

    # 状态
    filled_quantity: float = 0.0
    status: OrderStatus = OrderStatus.PENDING

    # 成交记录
    fills: list[FillRecord] = field(default_factory=list)

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    submitted_at: datetime | None = None
    filled_at: datetime | None = None

    # 拒绝/取消原因
    reject_reason: str = ""
    cancel_reason: str = ""

    # 元数据
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.filled_quantity < 0:
            raise ValueError("filled_quantity must be non-negative")
        if self.filled_quantity > self.quantity:
            raise ValueError("filled_quantity cannot exceed quantity")
        if not isinstance(self.side, OrderSide):
            self.side = OrderSide(self.side)
        if not isinstance(self.order_type, OrderType):
            self.order_type = OrderType(self.order_type)
        if not self.order_id:
            self.order_id = str(uuid.uuid4())[:8].upper()

    def submit(self) -> None:
        """提交订单"""
        if not self.status.can_transition_to(OrderStatus.SUBMITTED):
            raise ValueError(f"Cannot submit from status {self.status}")
        self.status = OrderStatus.SUBMITTED
        self.submitted_at = datetime.now()
        self.updated_at = datetime.now()
        self.version += 1

    def add_fill(self, quantity: float, price: float, commission: float = 0) -> FillRecord:
        """
        添加成交记录

        Args:
            quantity: 成交数量
            price: 成交价格
            commission: 手续费

        Returns:
            FillRecord 实例
        """
        new_filled = self.filled_quantity + quantity
        if new_filled > self.quantity:
            raise ValueError(
                f"fill would exceed order quantity: " f"{self.filled_quantity} + {quantity} > {self.quantity}"
            )

        fill = FillRecord(
            fill_id=str(uuid.uuid4())[:8],
            order_id=self.order_id,
            quantity=quantity,
            price=price,
            commission=commission,
        )
        self.fills.append(fill)
        self.filled_quantity = new_filled
        self.updated_at = datetime.now()
        self.version += 1

        # 更新状态
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.now()
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL_FILLED

        return fill

    def cancel(self, reason: str = "") -> None:
        """取消订单"""
        if not self.status.can_transition_to(OrderStatus.CANCELLED):
            raise ValueError(f"Cannot cancel from status {self.status}")
        self.status = OrderStatus.CANCELLED
        self.cancel_reason = reason
        self.updated_at = datetime.now()
        self.version += 1

    def reject(self, reason: str = "") -> None:
        """拒绝订单"""
        if not self.status.can_transition_to(OrderStatus.REJECTED):
            raise ValueError(f"Cannot reject from status {self.status}")
        self.status = OrderStatus.REJECTED
        self.reject_reason = reason
        self.updated_at = datetime.now()
        self.version += 1

    @property
    def remaining_quantity(self) -> float:
        """剩余未成交数量"""
        return self.quantity - self.filled_quantity

    @property
    def fill_rate(self) -> float:
        """成交比例"""
        return self.filled_quantity / self.quantity if self.quantity > 0 else 0

    @property
    def is_filled(self) -> bool:
        """是否完全成交"""
        return self.status == OrderStatus.FILLED

    @property
    def is_active(self) -> bool:
        """是否活跃（可成交）"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED]

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "price": self.price,
            "quantity": self.quantity,
            "filled_quantity": self.filled_quantity,
            "remaining_quantity": self.remaining_quantity,
            "fill_rate": self.fill_rate,
            "status": self.status.value,
            "fills": [f.to_dict() for f in self.fills],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "reject_reason": self.reject_reason,
            "cancel_reason": self.cancel_reason,
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Order:
        created = data.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        elif created is None:
            created = datetime.now()

        submitted = data.get("submitted_at")
        if isinstance(submitted, str):
            submitted = datetime.fromisoformat(submitted)

        filled = data.get("filled_at")
        if isinstance(filled, str):
            filled = datetime.fromisoformat(filled)

        side = data.get("side", "buy")
        if isinstance(side, str):
            side = OrderSide(side)

        order_type = data.get("order_type", "limit")
        if isinstance(order_type, str):
            order_type = OrderType(order_type)

        status = data.get("status", "pending")
        if isinstance(status, str):
            status = OrderStatus(status)

        fills_data = data.get("fills", [])
        fills = [FillRecord.from_dict(f) for f in fills_data]

        return cls(
            order_id=data.get("order_id", str(uuid.uuid4())[:8].upper()),
            symbol=data.get("symbol", ""),
            side=side,
            order_type=order_type,
            price=float(data.get("price", 0)),
            quantity=float(data.get("quantity", 0)),
            filled_quantity=float(data.get("filled_quantity", 0)),
            status=status,
            fills=fills,
            created_at=created,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else created,
            submitted_at=submitted,
            filled_at=filled,
            reject_reason=data.get("reject_reason", ""),
            cancel_reason=data.get("cancel_reason", ""),
            version=int(data.get("version", 1)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AccountBalance:
    """
    账户余额实体

    记录账户的资金状态。

    INVARIANTS:
    - total_balance >= 0
    - available >= 0
    - locked >= 0
    - total_balance = available + locked
    """

    total_balance: float
    available: float
    locked: float = 0.0  # 挂单冻结
    unrealized_pnl: float = 0.0  # 浮动盈亏

    # 时间戳
    updated_at: datetime = field(default_factory=datetime.now)

    # 元数据
    currency: str = "USDT"
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.total_balance < 0:
            raise ValueError("total_balance must be non-negative")
        if self.available < 0:
            raise ValueError("available must be non-negative")
        if self.locked < 0:
            raise ValueError("locked must be non-negative")

    @property
    def equity(self) -> float:
        """账户权益 = 总余额 + 浮动盈亏"""
        return self.total_balance + self.unrealized_pnl

    @property
    def leverage(self) -> float:
        """杠杆率（权益/总余额）"""
        return self.equity / self.total_balance if self.total_balance > 0 else 0

    def freeze(self, amount: float) -> None:
        """冻结资金"""
        if amount > self.available:
            raise ValueError("Insufficient available balance")
        self.available -= amount
        self.locked += amount
        self.updated_at = datetime.now()
        self.version += 1

    def unfreeze(self, amount: float) -> None:
        """解冻资金"""
        if amount > self.locked:
            raise ValueError("Insufficient locked balance")
        self.locked -= amount
        self.available += amount
        self.updated_at = datetime.now()
        self.version += 1

    def deposit(self, amount: float) -> None:
        """充值"""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.total_balance += amount
        self.available += amount
        self.updated_at = datetime.now()
        self.version += 1

    def withdraw(self, amount: float) -> None:
        """提现"""
        if amount <= 0:
            raise ValueError("Withdraw amount must be positive")
        if amount > self.available:
            raise ValueError("Insufficient available balance")
        self.total_balance -= amount
        self.available -= amount
        self.updated_at = datetime.now()
        self.version += 1

    def update_unrealized_pnl(self, pnl: float) -> None:
        """更新浮动盈亏"""
        self.unrealized_pnl = pnl
        self.updated_at = datetime.now()
        self.version += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_balance": self.total_balance,
            "available": self.available,
            "locked": self.locked,
            "unrealized_pnl": self.unrealized_pnl,
            "equity": self.equity,
            "currency": self.currency,
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AccountBalance:
        updated = data.get("updated_at")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        elif updated is None:
            updated = datetime.now()

        return cls(
            total_balance=float(data.get("total_balance", 0)),
            available=float(data.get("available", 0)),
            locked=float(data.get("locked", 0)),
            unrealized_pnl=float(data.get("unrealized_pnl", 0)),
            updated_at=updated,
            currency=data.get("currency", "USDT"),
            version=int(data.get("version", 1)),
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# Factory Methods
# =============================================================================


def create_order(
    symbol: str,
    side: OrderSide,
    quantity: float,
    price: float,
    order_type: OrderType = OrderType.LIMIT,
) -> Order:
    """
    工厂方法：创建订单

    Args:
        symbol: 交易对
        side: 买卖方向
        quantity: 委托数量
        price: 委托价格
        order_type: 订单类型

    Returns:
        Order 实例
    """
    return Order(
        order_id="",  # 自动生成
        symbol=symbol,
        side=side,
        order_type=order_type,
        price=price,
        quantity=quantity,
    )


def create_account_balance(
    initial_balance: float,
    currency: str = "USDT",
) -> AccountBalance:
    """
    工厂方法：创建账户余额

    Args:
        initial_balance: 初始余额
        currency: 币种

    Returns:
        AccountBalance 实例
    """
    return AccountBalance(
        total_balance=initial_balance,
        available=initial_balance,
        locked=0.0,
        currency=currency,
    )


# =============================================================================
# Domain Services
# =============================================================================


def calculate_commission(
    quantity: float,
    price: float,
    rate: float = 0.001,
) -> float:
    """
    计算手续费

    Args:
        quantity: 数量
        price: 价格
        rate: 手续费率 (默认 0.1%)

    Returns:
        手续费金额
    """
    return quantity * price * rate


def estimate_order_cost(
    side: OrderSide,
    quantity: float,
    price: float,
    commission_rate: float = 0.001,
) -> float:
    """
    估算订单成本

    Args:
        side: 买卖方向
        quantity: 数量
        price: 价格
        commission_rate: 手续费率

    Returns:
        订单成本（买入为正，卖出为负）
    """
    commission = calculate_commission(quantity, price, commission_rate)
    notional = quantity * price

    if side == OrderSide.BUY:
        return notional + commission
    else:
        return -(notional - commission)
