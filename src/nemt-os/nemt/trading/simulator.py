"""
StrategySimulator - 策略模拟器

提供策略模拟执行、信号生成能力。
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "Signal",
    "SignalType",
    "Order",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "Position",
    "StrategySimulator",
]


class SignalType(Enum):
    """信号类型"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


@dataclass
class Signal:
    """交易信号"""

    timestamp: float
    symbol: str
    signal_type: SignalType
    strength: float = 1.0  # 0-1
    price: float = 0
    reason: str = ""
    metadata: dict = field(default_factory=dict)


class OrderType(Enum):
    """订单类型"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """订单方向"""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""

    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """订单"""

    order_id: str
    timestamp: float
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float = 0
    filled_quantity: float = 0
    filled_price: float = 0
    status: OrderStatus = OrderStatus.PENDING
    metadata: dict = field(default_factory=dict)


@dataclass
class Position:
    """持仓"""

    symbol: str
    quantity: float = 0
    avg_price: float = 0
    unrealized_pnl: float = 0
    realized_pnl: float = 0


class StrategySimulator:
    """
    策略模拟器

    示例:
    ```python
    simulator = StrategySimulator(initial_capital=100000)

    # 设置市场数据
    simulator.set_market_data("AAPL", [150, 151, 152, 151.5])

    # 定义策略
    def simple_strategy(data, position):
        if data[-1] > data[-2]:
            return SignalType.BUY
        return SignalType.SELL

    # 运行模拟
    result = simulator.run("AAPL", simple_strategy)

    # 查看结果
    print(f"最终收益: {result['final_pnl']}")
    print(f"交易次数: {result['total_trades']}")
    ```
    """

    def __init__(self, initial_capital: float = 100000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self._positions: dict[str, Position] = {}
        self._orders: list[Order] = []
        self._trades: list[dict] = []
        self._equity_curve: list[float] = []
        self._capital = initial_capital
        self._logger = logging.getLogger("StrategySimulator")

    def reset(self) -> None:
        """重置模拟器"""
        self._positions.clear()
        self._orders.clear()
        self._trades.clear()
        self._equity_curve.clear()
        self._capital = self.initial_capital

    def set_market_data(self, symbol: str, prices: list[float]) -> None:
        """设置市场数据"""
        self._market_data = getattr(self, "_market_data", {})
        self._market_data[symbol] = prices

    def run(
        self,
        symbol: str,
        strategy: Callable,
        params: dict = None,
    ) -> dict[str, Any]:
        """运行模拟"""
        self.reset()
        params = params or {}

        prices = self._market_data.get(symbol, [])
        if not prices:
            self._logger.warning(f"无市场数据: {symbol}")
            return self._generate_result()

        for i, price in enumerate(prices):
            # 获取当前位置
            position = self._positions.get(symbol)
            pos_quantity = position.quantity if position else 0

            # 调用策略
            data = prices[: i + 1]
            signal = strategy(data, pos_quantity, params)

            # 处理信号
            if signal == SignalType.BUY and self._capital > 0:
                quantity = (self._capital * 0.1) / price  # 10% 资金
                self._execute_order(symbol, OrderSide.BUY, quantity, price)

            elif signal == SignalType.SELL and pos_quantity > 0:
                self._execute_order(symbol, OrderSide.SELL, pos_quantity, price)

            # 更新权益曲线
            self._update_equity(symbol, price)

        # 平仓
        self._close_all_positions(symbol, prices[-1] if prices else 0)

        return self._generate_result()

    def _execute_order(self, symbol: str, side: OrderSide, quantity: float, price: float) -> None:
        """执行订单"""
        commission_cost = quantity * price * self.commission

        if side == OrderSide.BUY:
            total_cost = quantity * price + commission_cost
            if total_cost > self._capital:
                quantity = self._capital / (price * (1 + self.commission))

            self._capital -= quantity * price + quantity * price * self.commission

            if symbol not in self._positions:
                self._positions[symbol] = Position(symbol=symbol)

            pos = self._positions[symbol]
            total_cost = pos.quantity * pos.avg_price + quantity * price
            pos.quantity += quantity
            pos.avg_price = total_cost / pos.quantity if pos.quantity > 0 else 0

        else:  # SELL
            if symbol not in self._positions:
                return

            pos = self._positions[symbol]
            if quantity > pos.quantity:
                quantity = pos.quantity

            self._capital += quantity * price - quantity * price * self.commission
            pnl = (price - pos.avg_price) * quantity
            pos.realized_pnl += pnl
            pos.quantity -= quantity

            if pos.quantity <= 0:
                del self._positions[symbol]

        # 记录交易
        self._trades.append(
            {
                "timestamp": time.time(),
                "symbol": symbol,
                "side": side.value,
                "quantity": quantity,
                "price": price,
                "commission": quantity * price * self.commission,
            }
        )

    def _update_equity(self, symbol: str, price: float) -> None:
        """更新权益"""
        position_value = 0
        for pos in self._positions.values():
            if pos.symbol == symbol:
                position_value += pos.quantity * price
            position_value += pos.realized_pnl

        total_equity = self._capital + position_value
        self._equity_curve.append(total_equity)

    def _close_all_positions(self, symbol: str, price: float) -> None:
        """平仓"""
        if symbol in self._positions:
            pos = self._positions[symbol]
            if pos.quantity > 0:
                self._execute_order(symbol, OrderSide.SELL, pos.quantity, price)

    def _generate_result(self) -> dict[str, Any]:
        """生成结果"""
        initial = self.initial_capital
        final = self._equity_curve[-1] if self._equity_curve else initial

        returns = []
        for i in range(1, len(self._equity_curve)):
            ret = (self._equity_curve[i] - self._equity_curve[i - 1]) / self._equity_curve[i - 1]
            returns.append(ret)

        # 计算夏普比率
        if returns and len(returns) > 1:
            import statistics

            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns) if len(returns) > 1 else 0
            sharpe = (avg_return / std_return * (252**0.5)) if std_return > 0 else 0
        else:
            sharpe = 0

        # 最大回撤
        peak = self._equity_curve[0] if self._equity_curve else initial
        max_drawdown = 0
        for equity in self._equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

        return {
            "initial_capital": initial,
            "final_capital": final,
            "total_pnl": final - initial,
            "total_return": (final - initial) / initial if initial > 0 else 0,
            "total_trades": len(self._trades),
            "winning_trades": len([t for t in self._trades if t["side"] == "sell"]),
            "losing_trades": len([t for t in self._trades if t["side"] == "buy"]),
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "equity_curve": self._equity_curve,
            "trades": self._trades,
        }

    def get_position(self, symbol: str) -> Position | None:
        """获取持仓"""
        return self._positions.get(symbol)

    def get_all_positions(self) -> list[Position]:
        """获取所有持仓"""
        return list(self._positions.values())
