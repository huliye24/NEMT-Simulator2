"""
NEMT 执行层 (Execution Layer)
连接策略决策与真实交易，负责订单执行和交易监控
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderSide(Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """订单类型"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "PENDING"       # 待成交
    FILLED = "FILLED"        # 已成交
    PARTIAL = "PARTIAL"      # 部分成交
    CANCELLED = "CANCELLED"  # 已取消
    REJECTED = "REJECTED"    # 已拒绝


@dataclass
class Order:
    """订单"""
    order_id: str
    side: OrderSide
    order_type: OrderType
    symbol: str
    quantity: float           # 数量
    price: float              # 价格
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    slippage: float = 0.0     # 滑点

    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED

    def get_unfilled_quantity(self) -> float:
        return self.quantity - self.filled_quantity


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: float = 0.0
    avg_entry_price: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    def update_price(self, price: float):
        """更新当前价格"""
        self.current_price = price
        if self.quantity > 0 and self.avg_entry_price > 0:
            self.unrealized_pnl = (price - self.avg_entry_price) * self.quantity

    def update_position(self, side: OrderSide, quantity: float, price: float):
        """更新持仓"""
        if side == OrderSide.BUY:
            new_quantity = self.quantity + quantity
            new_avg_price = (self.quantity * self.avg_entry_price + quantity * price) / new_quantity if new_quantity > 0 else 0
            self.quantity = new_quantity
            self.avg_entry_price = new_avg_price
        elif side == OrderSide.SELL:
            # 平多
            close_qty = min(self.quantity, quantity)
            self.realized_pnl += (price - self.avg_entry_price) * close_qty
            self.quantity -= close_qty
            if self.quantity == 0:
                self.avg_entry_price = 0.0

        self.update_price(price)


@dataclass
class Trade:
    """交易记录"""
    trade_id: str
    order_id: str
    side: OrderSide
    symbol: str
    quantity: float
    entry_price: float
    exit_price: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    slippage: float = 0.0
    fee: float = 0.0
    entry_time: datetime = None
    exit_time: Optional[datetime] = None
    holding_hours: float = 0.0
    strategy_name: str = ""

    def close_trade(self, exit_price: float, exit_time: datetime):
        """平仓"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.pnl = (self.exit_price - self.entry_price) * self.quantity if self.side == OrderSide.BUY else (self.entry_price - self.exit_price) * self.quantity
        self.pnl_percent = self.pnl / (self.entry_price * self.quantity) * 100
        self.holding_hours = (exit_time - self.entry_time).total_seconds() / 3600 if self.entry_time else 0


class ExecutionLayer:
    """
    执行层

    核心功能：
    1. 订单生成和管理
    2. 模拟订单执行 (滑点、手续费)
    3. 持仓管理
    4. 交易记录
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        slippage_bps: float = 1.0,
        commission_bps: float = 5.0
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.slippage_bps = slippage_bps
        self.commission_bps = commission_bps

        # 持仓和订单
        self.positions: Dict[str, Position] = {}
        self.pending_orders: List[Order] = []
        self.closed_trades: List[Trade] = []
        self.open_trades: Dict[str, Trade] = {}

        # 统计
        self.total_trades = 0
        self.total_pnl = 0.0
        self.winning_trades = 0
        self.losing_trades = 0

        # ID生成器
        self._order_counter = 0
        self._trade_counter = 0

    def _generate_order_id(self) -> str:
        self._order_counter += 1
        return f"ORD_{self._order_counter:06d}"

    def _generate_trade_id(self) -> str:
        self._trade_counter += 1
        return f"TRD_{self._trade_counter:06d}"

    def create_order(
        self,
        side: OrderSide,
        symbol: str,
        quantity: float,
        price: float,
        order_type: OrderType = OrderType.MARKET
    ) -> Order:
        """创建订单"""
        order = Order(
            order_id=self._generate_order_id(),
            side=side,
            order_type=order_type,
            symbol=symbol,
            quantity=quantity,
            price=price
        )
        self.pending_orders.append(order)
        return order

    def execute_order(
        self,
        order: Order,
        execution_price: float,
        timestamp: datetime = None
    ) -> Tuple[bool, str]:
        """
        执行订单

        Args:
            order: 订单
            execution_price: 执行价格
            timestamp: 执行时间

        Returns:
            (success, message)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # 计算滑点
        slippage = self._calculate_slippage(execution_price, order.side)

        # 考虑滑点的执行价格
        if order.side == OrderSide.BUY:
            executed_price = execution_price * (1 + slippage)
        else:
            executed_price = execution_price * (1 - slippage)

        # 计算手续费
        commission = executed_price * order.quantity * self.commission_bps / 10000

        # 更新订单
        order.filled_price = executed_price
        order.filled_quantity = order.quantity
        order.status = OrderStatus.FILLED
        order.filled_at = timestamp
        order.slippage = slippage

        # 扣除手续费
        self.current_capital -= commission

        # 更新持仓
        if order.symbol not in self.positions:
            self.positions[order.symbol] = Position(symbol=order.symbol)

        position = self.positions[order.symbol]
        position.update_position(order.side, order.quantity, executed_price)

        # 记录开仓交易
        if order.side == OrderSide.BUY:
            trade = Trade(
                trade_id=self._generate_trade_id(),
                order_id=order.order_id,
                side=order.side,
                symbol=order.symbol,
                quantity=order.quantity,
                entry_price=executed_price,
                entry_time=timestamp,
                slippage=slippage,
                fee=commission
            )
            self.open_trades[order.symbol] = trade

        # 从待执行队列移除
        if order in self.pending_orders:
            self.pending_orders.remove(order)

        return True, f"订单已成交: {order.order_id} @ {executed_price:.2f}"

    def _calculate_slippage(self, price: float, side: OrderSide) -> float:
        """计算滑点"""
        # 简化滑点计算：基于价格的基点
        slippage_rate = self.slippage_bps / 10000
        # 随机波动
        import random
        return slippage_rate * (1 + random.uniform(-0.5, 0.5))

    def close_position(
        self,
        symbol: str,
        quantity: float = None,
        exit_price: float = None,
        timestamp: datetime = None
    ) -> Tuple[bool, str]:
        """
        平仓

        Args:
            symbol: 品种
            quantity: 平仓数量，None表示全部
            exit_price: 平仓价格
            timestamp: 平仓时间

        Returns:
            (success, message)
        """
        if timestamp is None:
            timestamp = datetime.now()

        if symbol not in self.positions:
            return False, f"没有持仓: {symbol}"

        position = self.positions[symbol]
        if position.quantity <= 0:
            return False, f"没有多头持仓: {symbol}"

        # 数量
        close_qty = quantity if quantity else position.quantity

        # 执行平仓订单
        order = self.create_order(
            side=OrderSide.SELL,
            symbol=symbol,
            quantity=close_qty,
            price=exit_price if exit_price else position.current_price,
            order_type=OrderType.MARKET
        )

        success, msg = self.execute_order(order, exit_price if exit_price else position.current_price, timestamp)

        if success and symbol in self.open_trades:
            trade = self.open_trades[symbol]
            trade.close_trade(order.filled_price, timestamp)

            # 更新统计
            self.total_trades += 1
            self.total_pnl += trade.pnl

            if trade.pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1

            # 移动到已平仓交易
            self.closed_trades.append(trade)
            del self.open_trades[symbol]

        return success, msg

    def update_prices(self, prices: Dict[str, float]):
        """批量更新持仓价格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

    def get_equity(self) -> float:
        """获取账户权益"""
        position_value = sum(p.quantity * p.current_price for p in self.positions.values())
        return self.current_capital + position_value

    def get_available_capital(self) -> float:
        """获取可用资金"""
        position_value = sum(p.quantity * p.avg_entry_price for p in self.positions.values())
        return self.current_capital - position_value

    def get_position_value(self) -> float:
        """获取持仓价值"""
        return sum(p.quantity * p.current_price for p in self.positions.values())

    def get_unrealized_pnl(self) -> float:
        """获取未实现盈亏"""
        return sum(p.unrealized_pnl for p in self.positions.values())

    def get_realized_pnl(self) -> float:
        """获取已实现盈亏"""
        return self.total_pnl

    def get_total_pnl(self) -> float:
        """获取总盈亏"""
        return self.get_realized_pnl() + self.get_unrealized_pnl()

    def get_return_percent(self) -> float:
        """获取收益率"""
        return (self.get_equity() - self.initial_capital) / self.initial_capital * 100

    def get_win_rate(self) -> float:
        """获取胜率"""
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades * 100

    def get_profit_factor(self) -> float:
        """获取盈亏比"""
        gross_profit = sum(t.pnl for t in self.closed_trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.closed_trades if t.pnl < 0))

        if gross_loss == 0:
            return gross_profit if gross_profit > 0 else 1.0

        return gross_profit / gross_loss

    def get_positions_summary(self) -> List[Dict]:
        """获取持仓汇总"""
        return [
            {
                'symbol': p.symbol,
                'quantity': p.quantity,
                'avg_entry': p.avg_entry_price,
                'current': p.current_price,
                'unrealized_pnl': p.unrealized_pnl
            }
            for p in self.positions.values() if p.quantity > 0
        ]

    def get_trades_summary(self) -> Dict:
        """获取交易统计"""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.get_win_rate(),
            'profit_factor': self.get_profit_factor(),
            'total_pnl': self.total_pnl,
            'return_pct': self.get_return_percent()
        }

    def reset(self):
        """重置执行层"""
        self.current_capital = self.initial_capital
        self.positions = {}
        self.pending_orders = []
        self.closed_trades = []
        self.open_trades = {}
        self.total_trades = 0
        self.total_pnl = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
