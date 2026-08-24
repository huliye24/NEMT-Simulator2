"""
Services Package - NEMT Quant Sync Server
=======================================

包含所有业务服务模块:
- capital_node: 资金管理层
- market_node: 市场数据层 (规划中)
- model_node: 模型层 (规划中)
- strategy_node: 策略层 (规划中)
"""

from .capital_node import (
    CapitalNode,
    BaseCapitalManager,
    EqualWeightCapitalManager,
    PhaseDrivenCapitalManager,
    RiskAdjustedCapitalManager,
    MarketPhase,
    Order,
    FinalOrder,
    AllocationResult,
)

__all__ = [
    "CapitalNode",
    "BaseCapitalManager",
    "EqualWeightCapitalManager",
    "PhaseDrivenCapitalManager",
    "RiskAdjustedCapitalManager",
    "MarketPhase",
    "Order",
    "FinalOrder",
    "AllocationResult",
]
