"""
NEMT 大脑层 (Brain Layer)
系统控制中心，管理整个生态系统
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .market import MarketState
from .strategy import Strategy, StrategyPool, StrategyStatus, StrategyType
from .risk import RiskMode


class AllocationMode(Enum):
    """资金分配模式"""
    EQUAL = "EQUAL"           # 等权重
    SHARPE_WEIGHTED = "SHARPE" # 夏普加权
    RECENT_PERFORMANCE = "RECENT"  # 近期表现加权


@dataclass
class BrainDecision:
    """大脑决策"""
    action: str                    # 动作: REBALANCE, SWITCH_MODE, ACTIVATE, DORMANT, EVICT
    target: str                    # 目标策略或系统
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketStateWeights:
    """市场状态对应的策略权重配置"""
    trend_weight: float = 0.4      # 趋势策略权重
    mean_rev_weight: float = 0.3   # 均值回归权重
    momentum_weight: float = 0.3    # 动量策略权重
    overall_position: float = 1.0  # 整体仓位水平

    @classmethod
    def for_state(cls, state: MarketState) -> "MarketStateWeights":
        """根据市场状态获取权重配置"""
        configs = {
            MarketState.TRENDING_UP: cls(0.6, 0.2, 0.2, 1.0),
            MarketState.TRENDING_DOWN: cls(0.6, 0.1, 0.3, 0.8),
            MarketState.RANGING: cls(0.2, 0.5, 0.3, 0.7),
            MarketState.HIGH_VOLATILITY: cls(0.3, 0.4, 0.3, 0.5),
            MarketState.LOW_LIQUIDITY: cls(0.4, 0.3, 0.3, 0.3),
        }
        return configs.get(state, cls())


class BrainLayer:
    """
    系统大脑层

    核心功能：
    1. 策略权重分配
    2. 资金调度
    3. 风险模式切换
    4. 策略生命周期管理
    5. 市场状态感知
    """

    def __init__(
        self,
        strategy_pool: StrategyPool,
        allocation_mode: AllocationMode = AllocationMode.EQUAL,
        lookback_days: int = 20
    ):
        self.strategy_pool = strategy_pool
        self.allocation_mode = allocation_mode
        self.lookback_days = lookback_days

        # 当前状态
        self.current_market_state: MarketState = MarketState.RANGING
        self.current_risk_mode: RiskMode = RiskMode.NORMAL

        # 决策历史
        self.decisions: List[BrainDecision] = []

        # 权重配置
        self.state_weights: Dict[MarketState, MarketStateWeights] = {}

    def sense_market(self, market_data, indicators: Dict[str, float]) -> MarketState:
        """
        感知市场状态

        Args:
            market_data: 市场数据
            indicators: 市场指标

        Returns:
            MarketState: 当前市场状态
        """
        # 简单实现：基于ADX和波动率判断
        adx = indicators.get('adx', 25)
        atr_pct = indicators.get('atr', 0) / indicators.get('price', 1) if indicators.get('price', 0) > 0 else 0

        # 高波动
        if atr_pct > 0.02:
            self.current_market_state = MarketState.HIGH_VOLATILITY
        # 强趋势
        elif adx > 30:
            # 还需要判断方向
            sma_5 = indicators.get('sma_5', 0)
            sma_20 = indicators.get('sma_20', 0)
            if sma_5 > sma_20:
                self.current_market_state = MarketState.TRENDING_UP
            elif sma_5 < sma_20:
                self.current_market_state = MarketState.TRENDING_DOWN
            else:
                self.current_market_state = MarketState.RANGING
        else:
            self.current_market_state = MarketState.RANGING

        return self.current_market_state

    def allocate_weights(self) -> Dict[str, float]:
        """
        分配策略权重

        Returns:
            dict: 策略名 -> 权重
        """
        weights = {}

        if self.allocation_mode == AllocationMode.EQUAL:
            weights = self._allocate_equal()
        elif self.allocation_mode == AllocationMode.SHARPE_WEIGHTED:
            weights = self._allocate_sharpe_weighted()
        elif self.allocation_mode == AllocationMode.RECENT_PERFORMANCE:
            weights = self._allocate_recent_performance()

        # 应用市场状态调整
        weights = self._apply_market_state_adjustment(weights)

        # 更新策略权重
        for strategy in self.strategy_pool.strategies:
            strategy.capital_weight = weights.get(strategy.name, 0)

        return weights

    def _allocate_equal(self) -> Dict[str, float]:
        """等权重分配"""
        active = self.strategy_pool.get_active_strategies()
        if not active:
            return {}

        equal_weight = 100 / len(active)
        return {s.name: equal_weight for s in active}

    def _allocate_sharpe_weighted(self) -> Dict[str, float]:
        """基于夏普比率加权"""
        active = self.strategy_pool.get_active_strategies()
        if not active:
            return {}

        # 获取各策略夏普比率
        sharpes = {s.name: max(0, s.metrics.sharpe_ratio) for s in active}
        total_sharpe = sum(sharpes.values())

        if total_sharpe == 0:
            return self._allocate_equal()

        weights = {}
        for s in active:
            if total_sharpe > 0:
                weights[s.name] = (sharpes[s.name] / total_sharpe) * 100
            else:
                weights[s.name] = 100 / len(active)

        return weights

    def _allocate_recent_performance(self) -> Dict[str, float]:
        """基于近期表现加权"""
        active = self.strategy_pool.get_active_strategies()
        if not active:
            return {}

        # 获取近期收益
        recent_returns = {}
        for s in active:
            if len(s.performance) >= 5:
                recent_returns[s.name] = np.mean(s.performance[-5:])
            else:
                recent_returns[s.name] = 0

        total_return = sum(max(0, r) for r in recent_returns.values())

        if total_return == 0:
            return self._allocate_equal()

        weights = {}
        for s in active:
            ret = max(0, recent_returns.get(s.name, 0))
            weights[s.name] = (ret / total_return) * 100 if total_return > 0 else 0

        return weights

    def _apply_market_state_adjustment(self, weights: Dict[str, float]) -> Dict[str, float]:
        """应用市场状态权重调整"""
        state_config = MarketStateWeights.for_state(self.current_market_state)

        # 获取各类型策略的当前权重
        type_weights = {}
        for strategy in self.strategy_pool.strategies:
            type_weights[strategy.strategy_type] = weights.get(strategy.name, 0)

        # 重新分配权重
        adjusted = {}
        total_weight = sum(weights.values())

        for strategy in self.strategy_pool.strategies:
            if strategy.status != StrategyStatus.ALIVE:
                continue

            target_weight = 0
            if strategy.strategy_type == StrategyType.TREND:
                target_weight = state_config.trend_weight * total_weight / 100
            elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
                target_weight = state_config.mean_rev_weight * total_weight / 100
            elif strategy.strategy_type == StrategyType.MOMENTUM:
                target_weight = state_config.momentum_weight * total_weight / 100

            # 过渡调整
            current = weights.get(strategy.name, 0)
            adjusted[strategy.name] = current * 0.7 + target_weight * 100 * 0.3

        return adjusted

    def get_combined_signal(self) -> float:
        """
        获取合并后的信号

        Returns:
            float: 合并信号 -1 到 1
        """
        active = self.strategy_pool.get_active_strategies()
        if not active:
            return 0.0

        total_weight = sum(s.capital_weight for s in active)
        if total_weight == 0:
            return 0.0

        # 计算加权信号
        weighted_signal = 0.0
        for strategy in active:
            weight_ratio = strategy.capital_weight / total_weight

            # 获取策略信号 (需要策略自己计算)
            # 这里假设策略信号已经计算好了
            weighted_signal += strategy.capital_weight * weight_ratio

        return weighted_signal / 100  # 归一化

    def decide_action(self) -> List[BrainDecision]:
        """
        决定行动

        Returns:
            List[BrainDecision]: 需要执行的决策列表
        """
        decisions = []

        # 1. 检查是否需要重新分配权重
        decisions.append(BrainDecision(
            action="REBALANCE",
            target="STRATEGY_POOL",
            details={'mode': self.allocation_mode.value}
        ))

        # 2. 根据市场状态调整
        if self.current_market_state != MarketState.RANGING:
            decisions.append(BrainDecision(
                action="ADJUST_POSITION",
                target="SYSTEM",
                details={'market_state': self.current_market_state.value}
            ))

        # 3. 检查策略生命周期
        strategy_decisions = self._check_strategy_lifecycle()
        decisions.extend(strategy_decisions)

        self.decisions.extend(decisions)
        return decisions

    def _check_strategy_lifecycle(self) -> List[BrainDecision]:
        """检查策略生命周期"""
        decisions = []

        for strategy in self.strategy_pool.strategies:
            score = strategy.calculate_performance_score()

            # Only evict very low scoring strategies (score < 20)
            # Give strategies more room to prove themselves
            if score < 20 and strategy.status != StrategyStatus.DEAD:
                decisions.append(BrainDecision(
                    action="EVICT",
                    target=strategy.name,
                    details={'score': score, 'reason': 'performance_too_low'}
                ))

            # Only set dormant for extremely poor performance (score < 30)
            # Let strategies with moderate scores continue operating
            elif score < 30 and strategy.status == StrategyStatus.ALIVE:
                decisions.append(BrainDecision(
                    action="DORMANT",
                    target=strategy.name,
                    details={'score': score}
                ))

            # Activate dormant strategies that have improved (score > 50)
            elif score > 50 and strategy.status == StrategyStatus.DORMANT:
                decisions.append(BrainDecision(
                    action="ACTIVATE",
                    target=strategy.name,
                    details={'score': score}
                ))

            # Activate testing strategies that are performing okay (score > 40)
            elif score > 40 and strategy.status == StrategyStatus.TESTING:
                decisions.append(BrainDecision(
                    action="ACTIVATE",
                    target=strategy.name,
                    details={'score': score}
                ))

        return decisions

    def execute_decision(self, decision: BrainDecision):
        """执行决策"""
        if decision.action == "EVICT":
            strategy = self.strategy_pool.get_strategy(decision.target)
            if strategy:
                strategy.status = StrategyStatus.DEAD
                strategy.capital_weight = 0
                print(f"[EVICT] Strategy evicted: {decision.target} (score: {decision.details.get('score', 0):.1f})")

        elif decision.action == "DORMANT":
            strategy = self.strategy_pool.get_strategy(decision.target)
            if strategy:
                strategy.status = StrategyStatus.DORMANT
                print(f"[DORMANT] Strategy dormant: {decision.target} (score: {decision.details.get('score', 0):.1f})")

        elif decision.action == "ACTIVATE":
            strategy = self.strategy_pool.get_strategy(decision.target)
            if strategy:
                strategy.status = StrategyStatus.ALIVE
                print(f"[ACTIVE] Strategy activated: {decision.target} (score: {decision.details.get('score', 0):.1f})")

        elif decision.action == "REBALANCE":
            self.allocate_weights()

    def get_state_report(self) -> Dict:
        """获取状态报告"""
        return {
            'market_state': self.current_market_state.value,
            'risk_mode': self.current_risk_mode.value,
            'allocation_mode': self.allocation_mode.value,
            'active_strategies': len(self.strategy_pool.get_active_strategies()),
            'total_strategies': len(self.strategy_pool),
            'decisions_count': len(self.decisions),
            'strategy_weights': {
                s.name: {
                    'weight': s.capital_weight,
                    'score': s.calculate_performance_score(),
                    'status': s.status.value
                }
                for s in self.strategy_pool.strategies
            }
        }

    def reset(self):
        """重置大脑层"""
        self.current_market_state = MarketState.RANGING
        self.decisions = []
        for strategy in self.strategy_pool.strategies:
            strategy.capital_weight = 100 / len(self.strategy_pool) if len(self.strategy_pool) > 0 else 0


class BrainController:
    """大脑控制器 - 整合大脑层和其他层"""

    def __init__(self, brain_layer: BrainLayer, risk_layer):
        self.brain = brain_layer
        self.risk = risk_layer

    def make_decision(
        self,
        signals: List[float],
        market_indicators: Dict[str, float]
    ) -> Tuple[float, List[BrainDecision]]:
        """
        做出决策

        Args:
            signals: 各策略信号列表
            market_indicators: 市场指标

        Returns:
            (combined_signal, decisions)
        """
        # 1. 感知市场
        self.brain.sense_market(None, market_indicators)

        # 2. 分配权重
        self.brain.allocate_weights()

        # 3. 决定行动
        decisions = self.brain.decide_action()

        # 4. 执行决策
        for decision in decisions:
            self.brain.execute_decision(decision)

        # 5. 获取合并信号
        combined_signal = self._combine_signals(signals)

        # 6. 应用风控调整
        if self.brain.current_market_state == MarketState.HIGH_VOLATILITY:
            combined_signal *= self.risk.get_position_multiplier()
        elif self.brain.current_market_state == MarketState.LOW_LIQUIDITY:
            combined_signal *= 0.5

        return combined_signal, decisions

    def _combine_signals(self, signals: List[float]) -> float:
        """合并信号"""
        if not signals:
            return 0.0

        active = self.brain.strategy_pool.get_active_strategies()
        if not active:
            return 0.0

        total_weight = sum(s.capital_weight for s in active)
        if total_weight == 0:
            return 0.0

        # 加权平均
        combined = 0.0
        for i, signal in enumerate(signals):
            if i < len(active):
                weight = active[i].capital_weight / total_weight
                combined += signal * weight

        return combined
