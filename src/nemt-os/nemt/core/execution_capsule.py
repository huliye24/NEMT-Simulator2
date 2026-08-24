"""
ExecutionCapsule - 执行胶囊

执行交易订单:
- 订单管理
- 持仓管理
- 佣金计算
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import time as time_module
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ["ExecutionCapsule"]


@dataclass
class Order:
    """订单"""

    order_id: str
    symbol: str
    direction: str  # 'long' or 'short'
    quantity: float
    price: float
    status: str = "pending"  # pending, filled, rejected, cancelled
    timestamp: float = field(default_factory=time_module.time)
    filled_price: float = 0.0
    commission: float = 0.0


@dataclass
class Position:
    """持仓"""

    symbol: str
    direction: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


class ExecutionCapsule(ModuleCapsule):
    """
    执行胶囊

    订阅事件:
    - nemt.signal: 交易信号
    - market.tick: 市场数据

    发布事件:
    - nemt.order_filled: 订单成交
    - nemt.position: 持仓变化
    """

    def __init__(self):
        super().__init__("execution")

        # 订单管理
        self._orders: Dict[str, Order] = {}
        self._order_counter: int = 0

        # 持仓管理
        self._positions: Dict[str, Position] = {}

        # 执行参数
        self._min_order_size: float = 0.001
        self._commission_rate: float = 0.001
        self._base_size: float = 0.1
        self._slippage: float = 0.0005

        # 统计
        self._filled_orders: int = 0
        self._rejected_orders: int = 0
        self._total_commission: float = 0.0

    def init(self) -> None:
        """初始化"""
        # 从配置加载参数
        self._min_order_size = self.get_config("execution.min_order_size", 0.001)
        self._commission_rate = self.get_config("execution.commission_rate", 0.001)
        self._base_size = self.get_config("execution.base_size", 0.1)
        self._slippage = self.get_config("execution.slippage", 0.0005)
        self._confidence_threshold = self.get_config("signal.confidence_threshold", 0.6)

        # 订阅事件
        self.subscribe("nemt.signal", self._on_signal)
        self.subscribe("market.tick", self._on_tick)

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回执行状态

        Returns:
            执行状态字典
        """
        return {
            "orders": {
                "pending": len([o for o in self._orders.values() if o.status == "pending"]),
                "filled": self._filled_orders,
                "rejected": self._rejected_orders,
            },
            "positions": {symbol: self._position_to_dict(pos) for symbol, pos in self._positions.items()},
            "statistics": {
                "total_orders": len(self._orders),
                "filled_orders": self._filled_orders,
                "total_commission": self._total_commission,
            },
        }

    def _on_signal(self, event: Event) -> None:
        """处理交易信号"""
        data = event.data

        if not data:
            return

        signal = data.get("signal", "neutral")
        confidence = data.get("confidence", 0)
        symbol = data.get("symbol", "BTC")

        # 置信度阈值 (使用配置的阈值)
        if confidence < self._confidence_threshold:
            return

        # 执行订单
        if signal == "long":
            self._create_order(symbol, "long", confidence)
        elif signal == "short":
            self._create_order(symbol, "short", confidence)

    def _on_tick(self, event: Event) -> None:
        """处理市场数据"""
        data = event.data

        if not data:
            return

        symbol = data.get("symbol")
        price = data.get("price") or data.get("close")

        if symbol and price:
            self._update_position_prices(symbol, price)

    def _create_order(self, symbol: str, direction: str, confidence: float) -> Optional[Order]:
        """
        创建订单

        Args:
            symbol: 交易品种
            direction: 方向
            confidence: 置信度

        Returns:
            Order 或 None
        """
        self._order_counter += 1
        order_id = f"ORD_{self._order_counter:06d}"

        # 计算订单数量
        quantity = self._calculate_order_size(confidence)

        if quantity < self._min_order_size:
            self._rejected_orders += 1
            return None

        # 获取当前价格 (简化处理)
        price = self._get_current_price(symbol)

        order = Order(
            order_id=order_id, symbol=symbol, direction=direction, quantity=quantity, price=price, status="pending"
        )

        self._orders[order_id] = order

        # 执行订单 (简化处理，直接成交)
        return self._execute_order(order)

    def _execute_order(self, order: Order) -> Order:
        """
        执行订单

        Args:
            order: 订单

        Returns:
            执行后的订单
        """
        # 模拟滑点
        slippage_factor = 1 + (self._slippage if order.direction == "long" else -self._slippage)
        order.filled_price = order.price * slippage_factor

        # 计算佣金
        order.commission = order.quantity * order.filled_price * self._commission_rate
        self._total_commission += order.commission

        # 更新订单状态
        order.status = "filled"
        self._filled_orders += 1

        # 更新持仓
        self._update_position(order)

        # 发布成交事件
        self.publish("nemt.order_filled", {"order": order, "pnl": 0})  # 开仓时 PnL 为 0

        return order

    def _calculate_order_size(self, confidence: float) -> float:
        """
        计算订单数量

        Args:
            confidence: 置信度

        Returns:
            订单数量
        """
        # 基础数量 * 置信度
        size = self._base_size * confidence

        # 确保不超过配置的最大值
        max_size = self.get_config("execution.max_order_size", 1.0)
        return min(size, max_size)

    def _update_position(self, order: Order) -> None:
        """
        更新持仓

        Args:
            order: 成交订单
        """
        symbol = order.symbol
        direction = order.direction
        quantity = order.quantity
        price = order.filled_price

        if symbol not in self._positions:
            # 新建持仓
            self._positions[symbol] = Position(
                symbol=symbol, direction=direction, quantity=quantity, entry_price=price, current_price=price
            )
        else:
            pos = self._positions[symbol]

            if pos.direction == direction:
                # 同向加仓
                total_value = pos.quantity * pos.entry_price + quantity * price
                pos.quantity += quantity
                pos.entry_price = total_value / pos.quantity
            else:
                # 反向减仓/平仓
                if quantity >= pos.quantity:
                    # 全部平仓
                    pnl_per_unit = (pos.entry_price - price) if direction == "short" else (price - pos.entry_price)
                    pos.realized_pnl += pos.quantity * pnl_per_unit
                    pos.quantity = quantity - pos.quantity
                    pos.direction = direction
                    pos.entry_price = price if pos.quantity > 0 else 0
                else:
                    # 部分平仓
                    pnl_per_unit = (pos.entry_price - price) if direction == "short" else (price - pos.entry_price)
                    pos.realized_pnl += quantity * pnl_per_unit
                    pos.quantity -= quantity

        # 发布持仓变化
        self.publish(
            "nemt.position",
            {
                "symbol": symbol,
                "direction": self._positions[symbol].direction,
                "quantity": self._positions[symbol].quantity,
                "entry_price": self._positions[symbol].entry_price,
                "current_price": self._positions[symbol].current_price,
            },
        )

    def _update_position_prices(self, symbol: str, price: float) -> None:
        """
        更新持仓价格

        Args:
            symbol: 交易品种
            price: 当前价格
        """
        if symbol not in self._positions:
            return

        pos = self._positions[symbol]
        pos.current_price = price

        # 计算未实现盈亏
        if pos.direction == "long":
            pos.unrealized_pnl = (pos.current_price - pos.entry_price) * pos.quantity
        else:
            pos.unrealized_pnl = (pos.entry_price - pos.current_price) * pos.quantity

    def _get_current_price(self, symbol: str) -> float:
        """
        获取当前价格

        Args:
            symbol: 交易品种

        Returns:
            当前价格
        """
        # 简化处理：如果有持仓，返回持仓价格；否则返回默认价格
        if symbol in self._positions:
            return self._positions[symbol].current_price
        return 50000.0  # 默认价格

    def _position_to_dict(self, pos: Position) -> Dict[str, Any]:
        """持仓转字典"""
        return {
            "symbol": pos.symbol,
            "direction": pos.direction,
            "quantity": pos.quantity,
            "entry_price": pos.entry_price,
            "current_price": pos.current_price,
            "unrealized_pnl": pos.unrealized_pnl,
            "realized_pnl": pos.realized_pnl,
        }

    def shutdown(self) -> None:
        """关闭"""
        self.unsubscribe("nemt.signal", self._on_signal)
        self.unsubscribe("market.tick", self._on_tick)
