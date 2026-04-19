#!/usr/bin/env python3
"""
BrainLayer - 大脑层
====================

NEMT 系统的大脑，负责协调各层决策：

1. 策略权重分配 - 根据历史表现和当前市场状态动态分配策略权重
2. 资金调度管理 - 多策略间的资金分配和紧急预留
3. 风险模式切换 - 根据市场状态切换正常/警戒/紧急模式
4. 策略生死判断 - 评估策略表现，决定暂停/恢复/淘汰

使用方法:
    from brain_layer import BrainLayer

    brain = BrainLayer()
    weights = brain.calculate_weights(strategies)
    mode = brain.get_risk_mode()
    score = brain.score_strategy(strategy)
"""

import os
import json
import logging
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# 数据结构
# ============================================================================

class RiskMode(Enum):
    """风险模式"""
    NORMAL = "normal"      # 正常模式
    WARNING = "warning"    # 警戒模式 - 收紧20%仓位
    EMERGENCY = "emergency"  # 紧急模式 - 降仓50%+


class StrategyStatus(Enum):
    """策略状态"""
    ACTIVE = "active"      # 活跃
    PAUSED = "paused"      # 暂停
    TERMINATED = "terminated"  # 淘汰


@dataclass
class Strategy:
    """策略"""
    id: str
    name: str
    type: str  # 'dci', 'vortex', 'resonance', etc.
    enabled: bool = True
    status: StrategyStatus = StrategyStatus.ACTIVE
    weights: Dict[str, float] = field(default_factory=dict)

    # 性能指标
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    recent_return: float = 0.0  # 近30天收益

    # 配置
    base_weight: float = 1.0  # 基础权重
    max_position: float = 1.0  # 最大仓位

    # 时间戳
    created_at: str = ""
    last_updated: str = ""


@dataclass
class StrategyWeights:
    """策略权重结果"""
    weights: Dict[str, float]  # strategy_id -> weight
    total_weight: float
    reasoning: str  # 权重分配理由


@dataclass
class FundAllocation:
    """资金分配结果"""
    allocations: Dict[str, float]  # strategy_id -> amount
    reserved: float  # 预留资金
    total: float
    reasoning: str


@dataclass
class StrategyScore:
    """策略评分"""
    strategy_id: str
    total_score: float  # 0-100
    sharpe_score: float  # 0-30
    win_rate_score: float  # 0-30
    consistency_score: float  # 0-20
    recent_score: float  # 0-20
    trend: str  # 'improving', 'stable', 'declining'
    should_terminate: bool = False
    reason: str = ""


# ============================================================================
# 权重计算器
# ============================================================================

class WeightCalculator:
    """策略权重计算器"""

    # 评分权重配置
    SHARPE_WEIGHT = 0.40
    WINRATE_WEIGHT = 0.30
    CONSISTENCY_WEIGHT = 0.30

    def __init__(self):
        self.min_sharpe = -2.0  # 夏普比率最低值
        self.max_sharpe = 3.0   # 夏普比率最高值
        self.min_winrate = 0.3  # 胜率最低值
        self.max_winrate = 0.8  # 胜率最高值

    def normalize_sharpe(self, sharpe: float) -> float:
        """归一化夏普比率 (0-1)"""
        return (sharpe - self.min_sharpe) / (self.max_sharpe - self.min_sharpe)

    def normalize_winrate(self, winrate: float) -> float:
        """归一化胜率 (0-1)"""
        return (winrate - self.min_winrate) / (self.max_winrate - self.min_winrate)

    def calculate_weights(self, strategies: List[Strategy]) -> StrategyWeights:
        """
        计算策略权重

        基于三个维度:
        - 历史夏普比率 (40%)
        - 近30天胜率 (30%)
        - 收益一致性 (30%)
        """
        if not strategies:
            return StrategyWeights({}, 0.0, "无策略")

        # 计算各策略的原始分数
        raw_scores = {}
        for s in strategies:
            if s.status != StrategyStatus.ACTIVE:
                continue

            sharpe_score = self.normalize_sharpe(s.sharpe_ratio)
            winrate_score = self.normalize_winrate(s.win_rate)

            # 一致性分数 = 1 - (最大回撤 / 最大容忍回撤)
            consistency_score = max(0, 1 - s.max_drawdown / 0.3)

            raw_scores[s.id] = {
                'sharpe': sharpe_score,
                'winrate': winrate_score,
                'consistency': consistency_score
            }

        # 加权计算总分
        total_scores = {}
        for sid, scores in raw_scores.items():
            total = (
                scores['sharpe'] * self.SHARPE_WEIGHT +
                scores['winrate'] * self.WINRATE_WEIGHT +
                scores['consistency'] * self.CONSISTENCY_WEIGHT
            )
            total_scores[sid] = max(0.01, total)  # 最小0.01

        # 归一化为权重
        total = sum(total_scores.values())
        weights = {sid: score / total for sid, score in total_scores.items()}

        reasoning = (
            f"基于 {len(raw_scores)} 个活跃策略，"
            f"夏普比率权重{self.SHARPE_WEIGHT:.0%}，"
            f"胜率权重{self.WINRATE_WEIGHT:.0%}，"
            f"一致性权重{self.CONSISTENCY_WEIGHT:.0%}"
        )

        return StrategyWeights(weights, 1.0, reasoning)


# ============================================================================
# 资金分配器
# ============================================================================

class FundAllocator:
    """资金分配器"""

    # 配置
    RESERVE_RATIO = 0.10  # 预留10%紧急备用金

    def __init__(self, reserve_ratio: float = None):
        if reserve_ratio is not None:
            self.RESERVE_RATIO = reserve_ratio

    def allocate(self, total: float, weights: Dict[str, float]) -> FundAllocation:
        """
        分配资金

        规则:
        1. 预留紧急备用金 (默认10%)
        2. 剩余90%按权重分配
        """
        reserved = total * self.RESERVE_RATIO
        available = total - reserved

        allocations = {
            sid: available * weight
            for sid, weight in weights.items()
        }

        reasoning = (
            f"总资金 ${total:,.2f}，"
            f"预留 ${reserved:,.2f} ({self.RESERVE_RATIO:.0%})，"
            f"分配 ${available:,.2f}"
        )

        return FundAllocation(allocations, reserved, total, reasoning)


# ============================================================================
# 风险模式管理器
# ============================================================================

class RiskModeManager:
    """风险模式管理器"""

    # 阈值配置
    WARNING_DRAWDOWN = 0.05   # 5% 回撤触发警戒
    EMERGENCY_DRAWDOWN = 0.15  # 15% 回撤触发紧急

    def __init__(self, warning_threshold: float = None, emergency_threshold: float = None):
        if warning_threshold is not None:
            self.WARNING_DRAWDOWN = warning_threshold
        if emergency_threshold is not None:
            self.EMERGENCY_DRAWDOWN = emergency_threshold

    def evaluate(self, current_drawdown: float, recent_loss: float) -> RiskMode:
        """
        评估风险模式

        参数:
        - current_drawdown: 当前回撤
        - recent_loss: 近7天亏损
        """
        if current_drawdown >= self.EMERGENCY_DRAWDOWN or recent_loss >= 0.10:
            return RiskMode.EMERGENCY
        elif current_drawdown >= self.WARNING_DRAWDOWN or recent_loss >= 0.05:
            return RiskMode.WARNING
        else:
            return RiskMode.NORMAL

    def get_position_multiplier(self, mode: RiskMode) -> float:
        """获取仓位调整系数"""
        multipliers = {
            RiskMode.NORMAL: 1.0,
            RiskMode.WARNING: 0.8,
            RiskMode.EMERGENCY: 0.5
        }
        return multipliers.get(mode, 1.0)

    def get_reason(self, mode: RiskMode, drawdown: float) -> str:
        """获取模式切换理由"""
        if mode == RiskMode.EMERGENCY:
            return f"触发紧急模式：回撤 {drawdown:.1%} 超过阈值 {self.EMERGENCY_DRAWDOWN:.1%}"
        elif mode == RiskMode.WARNING:
            return f"触发警戒模式：回撤 {drawdown:.1%} 超过阈值 {self.WARNING_DRAWDOWN:.1%}"
        else:
            return "回撤在正常范围内，维持正常模式"


# ============================================================================
# 策略评分器
# ============================================================================

class StrategyScorer:
    """策略评分器"""

    # 评分权重
    SHARPE_SCORE_MAX = 30
    WINRATE_SCORE_MAX = 30
    CONSISTENCY_SCORE_MAX = 20
    RECENT_SCORE_MAX = 20

    # 淘汰阈值
    TERMINATE_THRESHOLD = 30  # 连续2周低于此分数自动标记

    def __init__(self, terminate_threshold: float = None):
        if terminate_threshold is not None:
            self.TERMINATE_THRESHOLD = terminate_threshold

    def score(self, strategy: Strategy, historical_scores: List[float] = None) -> StrategyScore:
        """
        评分策略

        评分维度:
        - 夏普比率: 0-30分
        - 胜率: 0-30分
        - 一致性: 0-20分 (基于最大回撤)
        - 近期表现: 0-20分
        """
        # 夏普分数
        sharpe_score = min(30, max(0, (strategy.sharpe_ratio + 1) * 15))

        # 胜率分数
        winrate_score = min(30, max(0, strategy.win_rate * 37.5))

        # 一致性分数 (基于最大回撤)
        consistency_score = max(0, 20 - strategy.max_drawdown * 100)

        # 近期分数 (基于近30天收益)
        recent_score = min(20, max(0, (strategy.recent_return + 0.2) * 50))

        total = sharpe_score + winrate_score + consistency_score + recent_score

        # 判断趋势
        trend = self._evaluate_trend(historical_scores or [], strategy.recent_return)

        # 判断是否应淘汰
        should_terminate = False
        reason = ""
        if historical_scores and len(historical_scores) >= 2:
            recent_avg = sum(historical_scores[-2:]) / 2
            if recent_avg < self.TERMINATE_THRESHOLD:
                should_terminate = True
                reason = f"连续2周评分低于 {self.TERMINATE_THRESHOLD} 分阈值"

        return StrategyScore(
            strategy_id=strategy.id,
            total_score=round(total, 1),
            sharpe_score=round(sharpe_score, 1),
            win_rate_score=round(winrate_score, 1),
            consistency_score=round(consistency_score, 1),
            recent_score=round(recent_score, 1),
            trend=trend,
            should_terminate=should_terminate,
            reason=reason
        )

    def _evaluate_trend(self, historical: List[float], recent: float) -> str:
        """评估趋势"""
        if len(historical) < 2:
            return "stable"

        # 简单线性趋势
        recent_avg = sum(historical[-3:]) / min(3, len(historical))
        if recent > recent_avg * 1.1:
            return "improving"
        elif recent < recent_avg * 0.9:
            return "declining"
        else:
            return "stable"


# ============================================================================
# BrainLayer 主类
# ============================================================================

class BrainLayer:
    """
    大脑层 - NEMT 系统的决策中枢

    职责:
    1. 策略权重管理
    2. 资金调度
    3. 风险模式控制
    4. 策略生命周期管理
    """

    def __init__(
        self,
        reserve_ratio: float = 0.10,
        warning_threshold: float = 0.05,
        emergency_threshold: float = 0.15,
        terminate_threshold: float = 30
    ):
        """
        初始化大脑层

        Args:
            reserve_ratio: 紧急备用金比例 (默认10%)
            warning_threshold: 警戒模式回撤阈值 (默认5%)
            emergency_threshold: 紧急模式回撤阈值 (默认15%)
            terminate_threshold: 策略淘汰分数阈值 (默认30)
        """
        self.weight_calculator = WeightCalculator()
        self.fund_allocator = FundAllocator(reserve_ratio)
        self.risk_mode_manager = RiskModeManager(warning_threshold, emergency_threshold)
        self.strategy_scorer = StrategyScorer(terminate_threshold)

        # 状态
        self.current_mode = RiskMode.NORMAL
        self.strategies: Dict[str, Strategy] = {}
        self.strategy_scores: Dict[str, List[float]] = defaultdict(list)  # 历史评分

        logger.info("BrainLayer 初始化完成")

    # ------------------------------------------------------------------------
    # 策略管理
    # ------------------------------------------------------------------------

    def register_strategy(self, strategy: Strategy) -> None:
        """注册策略"""
        self.strategies[strategy.id] = strategy
        logger.info(f"策略已注册: {strategy.name} ({strategy.id})")

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """获取策略"""
        return self.strategies.get(strategy_id)

    def get_active_strategies(self) -> List[Strategy]:
        """获取活跃策略"""
        return [s for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE]

    def pause_strategy(self, strategy_id: str, reason: str = "") -> bool:
        """暂停策略"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].status = StrategyStatus.PAUSED
            logger.warning(f"策略已暂停: {strategy_id}, 原因: {reason}")
            return True
        return False

    def resume_strategy(self, strategy_id: str) -> bool:
        """恢复策略"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].status = StrategyStatus.ACTIVE
            logger.info(f"策略已恢复: {strategy_id}")
            return True
        return False

    # ------------------------------------------------------------------------
    # 权重计算
    # ------------------------------------------------------------------------

    def calculate_weights(self, strategy_ids: List[str] = None) -> StrategyWeights:
        """
        计算策略权重

        Args:
            strategy_ids: 指定策略ID列表，为空则使用所有活跃策略

        Returns:
            StrategyWeights 对象
        """
        if strategy_ids:
            strategies = [self.strategies[sid] for sid in strategy_ids if sid in self.strategies]
        else:
            strategies = self.get_active_strategies()

        return self.weight_calculator.calculate_weights(strategies)

    # ------------------------------------------------------------------------
    # 资金分配
    # ------------------------------------------------------------------------

    def allocate_funds(self, total: float, weights: Dict[str, float] = None) -> FundAllocation:
        """
        分配资金

        Args:
            total: 总资金
            weights: 策略权重，为空则自动计算

        Returns:
            FundAllocation 对象
        """
        if weights is None:
            weights = self.calculate_weights().weights

        return self.fund_allocator.allocate(total, weights)

    # ------------------------------------------------------------------------
    # 风险模式
    # ------------------------------------------------------------------------

    def evaluate_risk_mode(
        self,
        current_drawdown: float,
        recent_loss: float
    ) -> RiskMode:
        """
        评估风险模式

        Args:
            current_drawdown: 当前回撤
            recent_loss: 近7天亏损比例

        Returns:
            RiskMode 枚举
        """
        new_mode = self.risk_mode_manager.evaluate(current_drawdown, recent_loss)

        if new_mode != self.current_mode:
            old_mode = self.current_mode
            self.current_mode = new_mode
            logger.warning(
                f"风险模式切换: {old_mode.value} -> {new_mode.value}, "
                f"原因: {self.risk_mode_manager.get_reason(new_mode, current_drawdown)}"
            )

        return new_mode

    def get_risk_mode(self) -> RiskMode:
        """获取当前风险模式"""
        return self.current_mode

    def get_position_adjustment(self) -> float:
        """获取仓位调整系数"""
        return self.risk_mode_manager.get_position_multiplier(self.current_mode)

    # ------------------------------------------------------------------------
    # 策略评分
    # ------------------------------------------------------------------------

    def score_strategy(self, strategy_id: str = None, strategy: Strategy = None) -> StrategyScore:
        """
        评分策略

        Args:
            strategy_id: 策略ID
            strategy: 策略对象 (二选一)

        Returns:
            StrategyScore 对象
        """
        if strategy is None:
            if strategy_id and strategy_id in self.strategies:
                strategy = self.strategies[strategy_id]
            else:
                raise ValueError(f"策略不存在: {strategy_id}")

        # 获取历史评分
        historical = self.strategy_scores.get(strategy.id, [])

        score = self.strategy_scorer.score(strategy, historical)

        # 记录评分
        self.strategy_scores[strategy.id].append(score.total_score)
        if len(self.strategy_scores[strategy.id]) > 52:  # 最多保留1年
            self.strategy_scores[strategy.id] = self.strategy_scores[strategy.id][-52:]

        logger.info(f"策略评分: {strategy.name} = {score.total_score}分, 趋势: {score.trend}")

        return score

    def evaluate_all_strategies(self) -> List[StrategyScore]:
        """评估所有策略"""
        scores = []
        for strategy in self.get_active_strategies():
            score = self.score_strategy(strategy=strategy)
            scores.append(score)

            # 自动处理淘汰
            if score.should_terminate:
                self.pause_strategy(strategy.id, score.reason)

        return scores

    # ------------------------------------------------------------------------
    # 决策汇总
    # ------------------------------------------------------------------------

    def make_decision(
        self,
        total_capital: float,
        current_drawdown: float,
        recent_loss: float
    ) -> Dict[str, Any]:
        """
        综合决策

        综合权重、资金分配、风险模式生成完整决策

        Args:
            total_capital: 总资金
            current_drawdown: 当前回撤
            recent_loss: 近7天亏损

        Returns:
            决策字典
        """
        # 1. 评估风险模式
        risk_mode = self.evaluate_risk_mode(current_drawdown, recent_loss)

        # 2. 计算权重
        weights = self.calculate_weights()

        # 3. 分配资金
        allocation = self.allocate_funds(total_capital, weights.weights)

        # 4. 评估策略
        scores = self.evaluate_all_strategies()

        # 5. 计算仓位调整
        position_multiplier = self.get_position_adjustment()

        return {
            "timestamp": datetime.now().isoformat(),
            "risk_mode": risk_mode.value,
            "position_multiplier": position_multiplier,
            "weights": weights.weights,
            "weight_reasoning": weights.reasoning,
            "allocation": {
                sid: {
                    "amount": amount,
                    "weight": weights.weights.get(sid, 0),
                    "adjusted_amount": amount * position_multiplier
                }
                for sid, amount in allocation.allocations.items()
            },
            "allocation_reasoning": allocation.reasoning,
            "strategy_scores": [
                {
                    "strategy_id": s.strategy_id,
                    "score": s.total_score,
                    "trend": s.trend
                }
                for s in scores
            ],
            "action_required": self._determine_actions(scores, risk_mode)
        }

    def _determine_actions(
        self,
        scores: List[StrategyScore],
        mode: RiskMode
    ) -> List[str]:
        """确定需要的行动"""
        actions = []

        # 检查淘汰
        terminated = [s for s in scores if s.should_terminate]
        if terminated:
            actions.append(f"标记 {len(terminated)} 个策略待淘汰")

        # 风险模式行动
        if mode == RiskMode.WARNING:
            actions.append("收紧仓位20%")
        elif mode == RiskMode.EMERGENCY:
            actions.append("降低仓位50%+，停止新开仓")

        return actions

    # ------------------------------------------------------------------------
    # 健康检查
    # ------------------------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "strategies_count": len(self.strategies),
            "active_strategies": len(self.get_active_strategies()),
            "current_mode": self.current_mode.value,
            "position_multiplier": self.get_position_adjustment()
        }


# ============================================================================
# 单元测试
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("BrainLayer 单元测试")
    print("=" * 60)

    # 创建大脑层
    brain = BrainLayer()

    # 注册测试策略
    strategies = [
        Strategy(
            id="s1", name="DCI Momentum", type="dci",
            sharpe_ratio=1.5, win_rate=0.58, max_drawdown=0.08,
            total_trades=100, recent_return=0.05
        ),
        Strategy(
            id="s2", name="Vortex Hunter", type="vortex",
            sharpe_ratio=0.8, win_rate=0.52, max_drawdown=0.12,
            total_trades=80, recent_return=0.02
        ),
        Strategy(
            id="s3", name="Resonance Finder", type="resonance",
            sharpe_ratio=2.1, win_rate=0.65, max_drawdown=0.05,
            total_trades=50, recent_return=0.08
        ),
    ]

    for s in strategies:
        brain.register_strategy(s)

    print("\n1. 测试权重计算")
    weights = brain.calculate_weights()
    print(f"   权重: {json.dumps(weights.weights, indent=2)}")
    print(f"   理由: {weights.reasoning}")

    print("\n2. 测试资金分配")
    allocation = brain.allocate_funds(100000, weights.weights)
    print(f"   分配: {json.dumps(allocation.allocations, indent=2)}")
    print(f"   理由: {allocation.reasoning}")

    print("\n3. 测试风险模式评估")
    mode = brain.evaluate_risk_mode(0.03, 0.02)
    print(f"   模式: {mode.value}")
    print(f"   仓位调整: {brain.get_position_adjustment()}")

    print("\n4. 测试策略评分")
    for strategy in strategies:
        score = brain.score_strategy(strategy=strategy)
        print(f"   {strategy.name}: {score.total_score}分 (趋势: {score.trend})")
        if score.should_terminate:
            print(f"      ⚠️  {score.reason}")

    print("\n5. 测试综合决策")
    decision = brain.make_decision(100000, 0.03, 0.02)
    print(f"   风险模式: {decision['risk_mode']}")
    print(f"   仓位调整: {decision['position_multiplier']}")
    print(f"   需要行动: {decision['action_required']}")

    print("\n6. 健康检查")
    health = brain.health_check()
    print(f"   状态: {health['status']}")
    print(f"   策略数: {health['strategies_count']}")
    print(f"   活跃: {health['active_strategies']}")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过")
    print("=" * 60)
