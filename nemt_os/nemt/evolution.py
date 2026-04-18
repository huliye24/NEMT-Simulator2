"""
NEMT 进化层 (Evolution Layer)
系统的自然选择机制，确保生态持续优化
"""

import numpy as np
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .strategy import Strategy, StrategyPool, StrategyStatus, StrategyType
from .market import MarketState


class EvolutionEventType(Enum):
    """进化事件类型"""
    STRATEGY_BORN = "BORN"      # 策略诞生
    STRATEGY_SCORE = "SCORE"    # 策略评分
    STRATEGY_EVICT = "EVICT"    # 策略淘汰
    STRATEGY_MUTATE = "MUTATE"  # 参数变异
    STRATEGY_DUPLICATE = "DUPLICATE"  # 策略复制


@dataclass
class EvolutionEvent:
    """进化事件"""
    event_type: EvolutionEventType
    strategy_name: str
    details: Dict
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.event_type.value}: {self.strategy_name}"


@dataclass
class EvolutionLog:
    """进化日志"""
    events: List[EvolutionEvent] = field(default_factory=list)

    def add_event(self, event: EvolutionEvent):
        self.events.append(event)

    def get_recent_events(self, n: int = 10) -> List[EvolutionEvent]:
        return self.events[-n:]

    def clear(self):
        self.events = []


class EvolutionLayer:
    """
    进化层

    核心功能：
    1. 策略评分系统
    2. 自动淘汰机制
    3. 新策略生成
    4. 参数优化
    """

    def __init__(
        self,
        strategy_pool: StrategyPool,
        eval_frequency: int = 20,
        keep_best: int = 3,
        min_score_threshold: float = 30.0,
        mutation_rate: float = 0.1
    ):
        self.strategy_pool = strategy_pool
        self.eval_frequency = eval_frequency
        self.keep_best = keep_best
        self.min_score_threshold = min_score_threshold
        self.mutation_rate = mutation_rate

        # 进化状态
        self.bar_count: int = 0
        self.last_eval_bar: int = 0
        self.generation: int = 0

        # 进化日志
        self.evolution_log = EvolutionLog()

        # 策略模板
        self.strategy_templates = self._init_templates()

    def _init_templates(self) -> Dict[StrategyType, dict]:
        """初始化策略模板"""
        return {
            StrategyType.TREND: {
                'class': 'TrendStrategy',
                'params': {
                    'fast_period': (5, 20),
                    'slow_period': (20, 50)
                }
            },
            StrategyType.MEAN_REVERSION: {
                'class': 'MeanReversionStrategy',
                'params': {
                    'period': (10, 50),
                    'std_dev': (1.5, 3.0)
                }
            },
            StrategyType.MOMENTUM: {
                'class': 'MomentumStrategy',
                'params': {
                    'roc_period': (5, 30),
                    'threshold': (1.0, 5.0)
                }
            }
        }

    def tick(self):
        """时钟tick，每bar调用"""
        self.bar_count += 1

    def should_evaluate(self) -> bool:
        """是否应该评估"""
        return (self.bar_count - self.last_eval_bar) >= self.eval_frequency

    def evaluate(self) -> List[EvolutionEvent]:
        """
        执行评估

        Returns:
            List[EvolutionEvent]: 发生的进化事件
        """
        self.last_eval_bar = self.bar_count
        events = []

        # 1. 评分所有策略
        events.extend(self._score_all_strategies())

        # 2. 检查淘汰
        events.extend(self._check_eviction())

        # 3. 检查是否需要生成新策略
        if self._should_generate_new_strategy():
            events.extend(self._generate_new_strategy())

        return events

    def _score_all_strategies(self) -> List[EvolutionEvent]:
        """对所有策略评分"""
        events = []

        for strategy in self.strategy_pool.strategies:
            # 更新策略指标
            strategy.update_metrics(lookback=20)

            # 计算评分
            score = strategy.calculate_performance_score()

            events.append(EvolutionEvent(
                event_type=EvolutionEventType.STRATEGY_SCORE,
                strategy_name=strategy.name,
                details={
                    'score': score,
                    'sharpe': strategy.metrics.sharpe_ratio,
                    'total_pnl': strategy.metrics.total_pnl,
                    'status': strategy.status.value
                }
            ))

        return events

    def _check_eviction(self) -> List[EvolutionEvent]:
        """检查策略淘汰"""
        events = []
        active = self.strategy_pool.get_active_strategies()

        # 只有在策略数量超过keep_best*2时才淘汰，给策略更多生存空间
        if len(active) <= self.keep_best * 2:
            return events

        # 按评分排序
        scored = [(s, s.calculate_performance_score()) for s in active]
        scored.sort(key=lambda x: x[1])

        # 淘汰最低分的策略，保留更多
        to_evict_count = len(scored) - self.keep_best * 2

        for i in range(min(to_evict_count, len(scored))):
            strategy, score = scored[i]
            # 只有分数特别低的才淘汰
            if score < 20:
                strategy.status = StrategyStatus.DEAD
                strategy.capital_weight = 0

                events.append(EvolutionEvent(
                    event_type=EvolutionEventType.STRATEGY_EVICT,
                    strategy_name=strategy.name,
                    details={
                        'score': score,
                        'reason': 'below_threshold'
                    }
                ))

        return events

    def _should_generate_new_strategy(self) -> bool:
        """是否应该生成新策略"""
        # 限制策略总数，不要生成太多
        if len(self.strategy_pool.strategies) >= 10:
            return False

        active = self.strategy_pool.get_active_strategies()

        # 如果没有活跃策略，应该生成
        if len(active) < 1:
            return True

        # 如果策略类型太单一，可以生成
        types_present = set(s.strategy_type for s in active)
        if len(types_present) < 2 and len(self.strategy_pool.strategies) < 6:
            return True

        return False

    def _generate_new_strategy(self) -> List[EvolutionEvent]:
        """生成新策略"""
        events = []
        self.generation += 1

        # 随机选择策略类型
        strategy_type = random.choice(list(StrategyType))
        template = self.strategy_templates.get(strategy_type)

        if not template:
            return events

        # 生成随机参数
        params = {}
        for param_name, (min_val, max_val) in template['params'].items():
            if isinstance(min_val, int):
                params[param_name] = random.randint(min_val, max_val)
            else:
                params[param_name] = random.uniform(min_val, max_val)

        # 创建新策略
        if strategy_type == StrategyType.TREND:
            from .strategy import TrendStrategy
            new_strategy = TrendStrategy(
                name=f"Trend_{self.generation}",
                fast_period=params.get('fast_period', 10),
                slow_period=params.get('slow_period', 30)
            )
        elif strategy_type == StrategyType.MEAN_REVERSION:
            from .strategy import MeanReversionStrategy
            new_strategy = MeanReversionStrategy(
                name=f"MeanRev_{self.generation}",
                period=params.get('period', 20),
                std_dev=params.get('std_dev', 2.0)
            )
        else:
            from .strategy import MomentumStrategy
            new_strategy = MomentumStrategy(
                name=f"Momentum_{self.generation}",
                roc_period=params.get('roc_period', 10),
                threshold=params.get('threshold', 2.0)
            )

        new_strategy.status = StrategyStatus.TESTING

        self.strategy_pool.add_strategy(new_strategy)

        events.append(EvolutionEvent(
            event_type=EvolutionEventType.STRATEGY_BORN,
            strategy_name=new_strategy.name,
            details={
                'type': strategy_type.value,
                'params': params,
                'generation': self.generation
            }
        ))

        return events

    def mutate_strategy(self, strategy: Strategy) -> Tuple[Strategy, List[EvolutionEvent]]:
        """
        变异策略

        Args:
            strategy: 要变异的策略

        Returns:
            (mutated_strategy, events)
        """
        events = []

        # 随机决定是否变异
        if random.random() > self.mutation_rate:
            return strategy, events

        # 复制策略
        if strategy.strategy_type == StrategyType.TREND:
            from .strategy import TrendStrategy
            mutated = TrendStrategy(
                name=f"{strategy.name}_mut",
                fast_period=int(strategy.params.get('fast_period', 10) * random.uniform(0.8, 1.2)),
                slow_period=int(strategy.params.get('slow_period', 30) * random.uniform(0.8, 1.2))
            )
        elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
            from .strategy import MeanReversionStrategy
            mutated = MeanReversionStrategy(
                name=f"{strategy.name}_mut",
                period=int(strategy.params.get('period', 20) * random.uniform(0.8, 1.2)),
                std_dev=strategy.params.get('std_dev', 2.0) * random.uniform(0.8, 1.2)
            )
        else:
            from .strategy import MomentumStrategy
            mutated = MomentumStrategy(
                name=f"{strategy.name}_mut",
                roc_period=int(strategy.params.get('roc_period', 10) * random.uniform(0.8, 1.2)),
                threshold=strategy.params.get('threshold', 2.0) * random.uniform(0.8, 1.2)
            )

        mutated.status = StrategyStatus.TESTING
        mutated.params = strategy.params.copy()

        events.append(EvolutionEvent(
            event_type=EvolutionEventType.STRATEGY_MUTATE,
            strategy_name=strategy.name,
            details={
                'original_params': strategy.params,
                'mutated_params': mutated.params
            }
        ))

        return mutated, events

    def duplicate_strategy(self, strategy: Strategy) -> Tuple[Strategy, List[EvolutionEvent]]:
        """
        复制策略

        Args:
            strategy: 要复制的策略

        Returns:
            (duplicate, events)
        """
        events = []

        if strategy.strategy_type == StrategyType.TREND:
            from .strategy import TrendStrategy
            dup = TrendStrategy(
                name=f"{strategy.name}_dup_{datetime.now().strftime('%H%M%S')}",
                fast_period=strategy.params.get('fast_period', 10),
                slow_period=strategy.params.get('slow_period', 30)
            )
        elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
            from .strategy import MeanReversionStrategy
            dup = MeanReversionStrategy(
                name=f"{strategy.name}_dup_{datetime.now().strftime('%H%M%S')}",
                period=strategy.params.get('period', 20),
                std_dev=strategy.params.get('std_dev', 2.0)
            )
        else:
            from .strategy import MomentumStrategy
            dup = MomentumStrategy(
                name=f"{strategy.name}_dup_{datetime.now().strftime('%H%M%S')}",
                roc_period=strategy.params.get('roc_period', 10),
                threshold=strategy.params.get('threshold', 2.0)
            )

        dup.status = StrategyStatus.TESTING

        events.append(EvolutionEvent(
            event_type=EvolutionEventType.STRATEGY_DUPLICATE,
            strategy_name=strategy.name,
            details={'new_name': dup.name}
        ))

        return dup, events

    def get_evolution_report(self) -> Dict:
        """获取进化报告"""
        alive = self.strategy_pool.get_active_strategies()
        testing = [s for s in self.strategy_pool.strategies if s.status == StrategyStatus.TESTING]
        dead = [s for s in self.strategy_pool.strategies if s.status == StrategyStatus.DEAD]

        scores = {s.name: s.calculate_performance_score() for s in alive}

        return {
            'generation': self.generation,
            'bar_count': self.bar_count,
            'alive_count': len(alive),
            'testing_count': len(testing),
            'dead_count': len(dead),
            'survival_rate': len(alive) / (len(alive) + len(dead)) * 100 if (len(alive) + len(dead)) > 0 else 100,
            'top_strategy': max(scores.items(), key=lambda x: x[1])[0] if scores else None,
            'recent_events': [str(e) for e in self.evolution_log.get_recent_events(5)]
        }

    def get_diversity_score(self) -> float:
        """获取策略多样性评分 (0-100)"""
        active = self.strategy_pool.get_active_strategies()

        if not active:
            return 0.0

        # 1. 类型多样性
        types = set(s.strategy_type for s in active)
        type_diversity = len(types) / 3 * 50  # 最多50分

        # 2. 权重均匀度
        weights = [s.capital_weight for s in active]
        weight_std = np.std(weights) if weights else 0
        weight_diversity = max(0, 50 - weight_std * 5)  # 标准差越小越好

        return type_diversity + weight_diversity

    def reset(self):
        """重置进化层"""
        self.bar_count = 0
        self.last_eval_bar = 0
        self.generation = 0
        self.evolution_log.clear()
