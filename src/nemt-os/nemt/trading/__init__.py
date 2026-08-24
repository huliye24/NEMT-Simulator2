"""
Trading Module - 交易模块

提供策略模拟、订单执行、风险计算等交易能力。
"""

from nemt.trading.executor import (
    ExecutionPlan,
    Fill,
    OrderExecutor,
)
from nemt.trading.risk import (
    RiskCalculator,
    RiskMetrics,
)
from nemt.trading.simulator import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    Signal,
    SignalType,
    StrategySimulator,
)

__all__ = [
    # 模拟器
    "SignalType",
    "Signal",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "Order",
    "Position",
    "StrategySimulator",
    # 执行器
    "ExecutionPlan",
    "Fill",
    "OrderExecutor",
    # 风险
    "RiskMetrics",
    "RiskCalculator",
]
