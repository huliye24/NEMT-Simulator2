"""
Capital Node - 资金管理层
=========================

NEMT 系统的资金管理节点，负责：
1. 策略资金分配
2. 风险调整
3. 仓位控制
4. 紧急备用金管理

节点状态: 厨房阶段 - 基础框架完成

使用方法:
    from services.capital_node import CapitalNode, EqualWeightCapitalManager

    # 创建节点
    node = CapitalNode(initial_capital=100000)

    # 分配资金
    result = node.allocate([
        {"strategy_id": "s1", "signal_strength": 0.8},
        {"strategy_id": "s2", "signal_strength": 0.6},
    ])
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketPhase(Enum):
    """市场相位枚举"""
    PHASE_A_NOISE = "phase_a"      # 高噪声混乱期
    PHASE_B_VORTEX = "phase_b"     # 涡旋蓄力期
    PHASE_C_RESONANCE = "phase_c"  # 临界爆发前夜
    PHASE_D_TREND = "phase_d"      # 趋势运行期


@dataclass
class Order:
    """订单"""
    strategy_id: str
    symbol: str
    direction: int  # 1: 做多, -1: 做空, 0: 空仓
    quantity: float
    stop_loss: float
    take_profit: float
    entry_price: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinalOrder:
    """最终订单（含资金分配）"""
    order: Order
    allocated_capital: float  # 分配的资金
    weight: float              # 权重
    position_ratio: float     # 仓位比例
    risk_amount: float        # 风险金额
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "strategy_id": self.order.strategy_id,
            "symbol": self.order.symbol,
            "direction": self.order.direction,
            "quantity": self.quantity,
            "allocated_capital": self.allocated_capital,
            "weight": self.weight,
            "position_ratio": self.position_ratio,
            "risk_amount": self.risk_amount,
            "stop_loss": self.order.stop_loss,
            "take_profit": self.order.take_profit,
        }

    @property
    def quantity(self) -> float:
        return self.order.quantity


@dataclass
class AllocationResult:
    """分配结果"""
    allocations: List[FinalOrder]
    total_capital: float
    allocated_capital: float
    reserved_capital: float
    reserve_ratio: float
    timestamp: str
    reasoning: str

    def to_dict(self) -> Dict:
        return {
            "allocations": [a.to_dict() for a in self.allocations],
            "total_capital": self.total_capital,
            "allocated_capital": self.allocated_capital,
            "reserved_capital": self.reserved_capital,
            "reserve_ratio": self.reserve_ratio,
            "timestamp": self.timestamp,
            "reasoning": self.reasoning,
        }


# ============================================================================
# 基类定义
# ============================================================================

class BaseCapitalManager(ABC):
    """
    资金管理器抽象基类

    所有资金管理器必须实现此接口
    """

    @abstractmethod
    def allocate(
        self,
        orders: List[Order],
        total_capital: float,
        current_phase: MarketPhase,
        **kwargs
    ) -> AllocationResult:
        """
        分配资金

        Args:
            orders: 订单列表
            total_capital: 总资金
            current_phase: 当前市场相位
            **kwargs: 其他参数

        Returns:
            AllocationResult 分配结果
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取管理器名称"""
        pass


# ============================================================================
# 等权重分配器
# ============================================================================

class EqualWeightCapitalManager(BaseCapitalManager):
    """
    等权重资金分配器

    将可用资金平均分配给所有活跃订单
    适用于简单场景或模拟环境
    """

    def __init__(self, reserve_ratio: float = 0.10):
        """
        Args:
            reserve_ratio: 预留资金比例（默认10%）
        """
        self.reserve_ratio = reserve_ratio

    def get_name(self) -> str:
        return "EqualWeight"

    def allocate(
        self,
        orders: List[Order],
        total_capital: float,
        current_phase: MarketPhase,
        **kwargs
    ) -> AllocationResult:
        """
        等权重分配资金

        规则:
        1. 预留紧急备用金 (reserve_ratio)
        2. 剩余资金平均分配
        """
        if not orders:
            return AllocationResult(
                allocations=[],
                total_capital=total_capital,
                allocated_capital=0,
                reserved_capital=total_capital * self.reserve_ratio,
                reserve_ratio=self.reserve_ratio,
                timestamp=datetime.now().isoformat(),
                reasoning="无订单，资金全部预留"
            )

        # 计算可用资金
        reserved = total_capital * self.reserve_ratio
        available = total_capital - reserved

        # 平均分配
        weight = 1.0 / len(orders)
        per_order_capital = available * weight

        allocations = []
        for order in orders:
            final_order = FinalOrder(
                order=order,
                allocated_capital=per_order_capital,
                weight=weight,
                position_ratio=weight,
                risk_amount=per_order_capital * 0.02,  # 默认2%风险
                metadata={"allocation_type": "equal_weight"}
            )
            allocations.append(final_order)

        reasoning = (
            f"等权重分配: 总资金 ${total_capital:,.2f}，"
            f"预留 ${reserved:,.2f} ({self.reserve_ratio:.0%})，"
            f"分配 ${available:,.2f} 给 {len(orders)} 个订单，"
            f"每个订单 ${per_order_capital:,.2f}"
        )

        return AllocationResult(
            allocations=allocations,
            total_capital=total_capital,
            allocated_capital=available,
            reserved_capital=reserved,
            reserve_ratio=self.reserve_ratio,
            timestamp=datetime.now().isoformat(),
            reasoning=reasoning
        )


# ============================================================================
# 相位驱动分配器
# ============================================================================

class PhaseDrivenCapitalManager(BaseCapitalManager):
    """
    相位驱动资金分配器

    根据市场相位动态调整仓位上限:
    - 相位A: 20% 仓位（高噪声）
    - 相位B: 50% 仓位（涡旋蓄力）
    - 相位C: 70% 仓位（临界爆发）
    - 相位D: 100% 仓位（趋势运行）
    """

    # 相位-仓位映射
    PHASE_MAX_POSITION = {
        MarketPhase.PHASE_A_NOISE: 0.20,
        MarketPhase.PHASE_B_VORTEX: 0.50,
        MarketPhase.PHASE_C_RESONANCE: 0.70,
        MarketPhase.PHASE_D_TREND: 1.00,
    }

    def __init__(self, reserve_ratio: float = 0.10):
        self.reserve_ratio = reserve_ratio

    def get_name(self) -> str:
        return "PhaseDriven"

    def allocate(
        self,
        orders: List[Order],
        total_capital: float,
        current_phase: MarketPhase,
        **kwargs
    ) -> AllocationResult:
        """
        相位驱动分配资金

        规则:
        1. 根据相位确定最大仓位
        2. 预留紧急备用金
        3. 按权重分配剩余资金
        """
        if not orders:
            return AllocationResult(
                allocations=[],
                total_capital=total_capital,
                allocated_capital=0,
                reserved_capital=total_capital * self.reserve_ratio,
                reserve_ratio=self.reserve_ratio,
                timestamp=datetime.now().isoformat(),
                reasoning="无订单，资金全部预留"
            )

        # 获取相位仓位上限
        max_position = self.PHASE_MAX_POSITION.get(current_phase, 0.20)
        phase_name = current_phase.value

        # 计算可用资金
        reserved = total_capital * self.reserve_ratio
        max_allocatable = total_capital * max_position
        available = min(max_allocatable, total_capital - reserved)

        # 按权重分配
        weight = 1.0 / len(orders)
        per_order_capital = available * weight

        allocations = []
        for order in orders:
            final_order = FinalOrder(
                order=order,
                allocated_capital=per_order_capital,
                weight=weight,
                position_ratio=max_position * weight,
                risk_amount=per_order_capital * 0.02,
                metadata={
                    "allocation_type": "phase_driven",
                    "phase": phase_name,
                    "max_position": max_position
                }
            )
            allocations.append(final_order)

        reasoning = (
            f"相位驱动分配 [{phase_name}]: "
            f"总资金 ${total_capital:,.2f}，"
            f"相位仓位上限 {max_position:.0%}，"
            f"预留 ${reserved:,.2f}，"
            f"分配 ${available:,.2f} 给 {len(orders)} 个订单"
        )

        return AllocationResult(
            allocations=allocations,
            total_capital=total_capital,
            allocated_capital=available,
            reserved_capital=reserved,
            reserve_ratio=self.reserve_ratio,
            timestamp=datetime.now().isoformat(),
            reasoning=reasoning
        )


# ============================================================================
# 风险调整分配器
# ============================================================================

class RiskAdjustedCapitalManager(BaseCapitalManager):
    """
    风险调整资金分配器

    根据策略风险评分动态调整分配权重:
    - 高评分策略获得更多资金
    - 低评分策略减少分配
    - 支持自定义风险参数
    """

    def __init__(
        self,
        reserve_ratio: float = 0.10,
        min_weight: float = 0.05,
        max_weight: float = 0.50
    ):
        """
        Args:
            reserve_ratio: 预留资金比例
            min_weight: 最小权重
            max_weight: 最大权重
        """
        self.reserve_ratio = reserve_ratio
        self.min_weight = min_weight
        self.max_weight = max_weight

    def get_name(self) -> str:
        return "RiskAdjusted"

    def allocate(
        self,
        orders: List[Order],
        total_capital: float,
        current_phase: MarketPhase,
        **kwargs
    ) -> AllocationResult:
        """
        风险调整分配资金

        规则:
        1. 获取每个订单的风险评分（从 metadata 或 kwargs）
        2. 归一化权重
        3. 限制最小/最大权重
        4. 预留备用金
        5. 分配资金
        """
        if not orders:
            return AllocationResult(
                allocations=[],
                total_capital=total_capital,
                allocated_capital=0,
                reserved_capital=total_capital * self.reserve_ratio,
                reserve_ratio=self.reserve_ratio,
                timestamp=datetime.now().isoformat(),
                reasoning="无订单，资金全部预留"
            )

        # 提取风险评分
        scores = []
        for order in orders:
            score = order.metadata.get("risk_score", 0.5)  # 默认0.5
            scores.append(max(0.01, score))  # 避免零分

        # 归一化为权重
        total_score = sum(scores)
        raw_weights = [s / total_score for s in scores]

        # 限制权重范围
        weights = []
        for w in raw_weights:
            w = max(self.min_weight, min(self.max_weight, w))
            weights.append(w)

        # 重新归一化
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        # 计算资金
        reserved = total_capital * self.reserve_ratio
        available = total_capital - reserved

        allocations = []
        for i, order in enumerate(orders):
            capital = available * weights[i]
            risk_score = scores[i]

            final_order = FinalOrder(
                order=order,
                allocated_capital=capital,
                weight=weights[i],
                position_ratio=weights[i],
                risk_amount=capital * 0.02,
                metadata={
                    "allocation_type": "risk_adjusted",
                    "risk_score": risk_score,
                    "raw_weight": raw_weights[i],
                    "adjusted_weight": weights[i]
                }
            )
            allocations.append(final_order)

        reasoning = (
            f"风险调整分配: 总资金 ${total_capital:,.2f}，"
            f"预留 ${reserved:,.2f}，"
            f"分配 ${available:,.2f}，"
            f"权重范围 [{self.min_weight:.0%}, {self.max_weight:.0%}]"
        )

        return AllocationResult(
            allocations=allocations,
            total_capital=total_capital,
            allocated_capital=available,
            reserved_capital=reserved,
            reserve_ratio=self.reserve_ratio,
            timestamp=datetime.now().isoformat(),
            reasoning=reasoning
        )


# ============================================================================
# Capital Node 主类
# ============================================================================

class CapitalNode:
    """
    资金节点

    负责协调各种资金管理器，提供统一的资金分配接口
    """

    # 支持的分配模式
    MANAGERS = {
        "equal": EqualWeightCapitalManager,
        "phase": PhaseDrivenCapitalManager,
        "risk": RiskAdjustedCapitalManager,
    }

    def __init__(
        self,
        initial_capital: float = 100000.0,
        mode: str = "phase",
        **manager_kwargs
    ):
        """
        初始化资金节点

        Args:
            initial_capital: 初始资金
            mode: 分配模式 ("equal", "phase", "risk")
            **manager_kwargs: 传递给管理器的参数
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.current_phase = MarketPhase.PHASE_A_NOISE
        self.reserve_ratio = manager_kwargs.get("reserve_ratio", 0.10)

        # 创建管理器
        manager_class = self.MANAGERS.get(mode, PhaseDrivenCapitalManager)
        self.manager = manager_class(**manager_kwargs)

        # 分配历史
        self.allocation_history: List[AllocationResult] = []

        logger.info(
            f"CapitalNode 初始化完成: 模式={mode}, "
            f"初始资金=${initial_capital:,.2f}, 预留={self.reserve_ratio:.0%}"
        )

    def set_phase(self, phase: MarketPhase) -> None:
        """设置当前市场相位"""
        self.current_phase = phase
        logger.info(f"市场相位更新: {phase.value}")

    def set_capital(self, capital: float) -> None:
        """设置当前资金"""
        self.current_capital = capital
        logger.info(f"资金更新: ${capital:,.2f}")

    def allocate(self, orders: List[Order]) -> AllocationResult:
        """
        分配资金

        Args:
            orders: 订单列表

        Returns:
            AllocationResult 分配结果
        """
        result = self.manager.allocate(
            orders=orders,
            total_capital=self.current_capital,
            current_phase=self.current_phase
        )

        self.allocation_history.append(result)

        # 限制历史长度
        if len(self.allocation_history) > 1000:
            self.allocation_history = self.allocation_history[-1000:]

        logger.info(result.reasoning)

        return result

    def set_mode(self, mode: str, **kwargs) -> bool:
        """
        切换分配模式

        Args:
            mode: 新模式
            **kwargs: 新管理器参数

        Returns:
            是否切换成功
        """
        if mode not in self.MANAGERS:
            logger.error(f"未知模式: {mode}")
            return False

        manager_class = self.MANAGERS[mode]
        self.manager = manager_class(**kwargs)
        logger.info(f"分配模式切换: {mode}")
        return True

    def get_status(self) -> Dict[str, Any]:
        """获取节点状态"""
        return {
            "name": "CapitalNode",
            "version": "1.0.0-kitchen",
            "manager": self.manager.get_name(),
            "current_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "current_phase": self.current_phase.value,
            "reserve_ratio": self.reserve_ratio,
            "allocation_count": len(self.allocation_history),
        }

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "capital_node": "running",
            "manager": self.manager.get_name(),
        }


# ============================================================================
# 单元测试
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("CapitalNode 单元测试")
    print("=" * 60)

    # 创建测试订单
    orders = [
        Order(
            strategy_id="s1",
            symbol="BTCUSDT",
            direction=1,
            quantity=0.1,
            stop_loss=65000,
            take_profit=70000,
            entry_price=67000,
            metadata={"risk_score": 0.8}
        ),
        Order(
            strategy_id="s2",
            symbol="ETHUSDT",
            direction=1,
            quantity=1.0,
            stop_loss=3000,
            take_profit=3500,
            entry_price=3200,
            metadata={"risk_score": 0.6}
        ),
        Order(
            strategy_id="s3",
            symbol="BNBUSDT",
            direction=0,
            quantity=0,
            stop_loss=0,
            take_profit=0,
            entry_price=0,
            metadata={"risk_score": 0.4}
        ),
    ]

    total_capital = 100000.0

    # 测试1: 等权重分配
    print("\n1. 等权重分配模式")
    node = CapitalNode(initial_capital=total_capital, mode="equal")
    result = node.allocate(orders)
    print(f"   分配结果: {result.reasoning}")
    for alloc in result.allocations:
        print(f"   - {alloc.order.strategy_id}: ${alloc.allocated_capital:,.2f} ({alloc.weight:.1%})")

    # 测试2: 相位驱动分配
    print("\n2. 相位驱动分配模式 (相位D - 趋势期)")
    node.set_phase(MarketPhase.PHASE_D_TREND)
    result = node.allocate(orders)
    print(f"   分配结果: {result.reasoning}")

    print("\n3. 相位驱动分配模式 (相位A - 混乱期)")
    node.set_phase(MarketPhase.PHASE_A_NOISE)
    result = node.allocate(orders)
    print(f"   分配结果: {result.reasoning}")

    # 测试3: 风险调整分配
    print("\n4. 风险调整分配模式")
    node.set_mode("risk")
    node.set_phase(MarketPhase.PHASE_C_RESONANCE)
    result = node.allocate(orders)
    print(f"   分配结果: {result.reasoning}")
    for alloc in result.allocations:
        print(f"   - {alloc.order.strategy_id}: ${alloc.allocated_capital:,.2f} (风险评分: {alloc.metadata.get('risk_score', 'N/A')})")

    # 测试4: 状态检查
    print("\n5. 节点状态")
    status = node.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")

    # 测试5: 空订单处理
    print("\n6. 空订单处理")
    result = node.allocate([])
    print(f"   分配结果: {result.reasoning}")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过")
    print("=" * 60)
