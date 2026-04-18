"""
NEMT 策略层 (Strategy Layer)
策略生命体系统，管理策略从诞生到淘汰的完整生命周期
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class StrategyStatus(Enum):
    """策略状态"""
    ALIVE = "ALIVE"         # 正常运行
    TESTING = "TESTING"     # 测试中
    DORMANT = "DORMANT"     # 休眠
    DEAD = "DEAD"           # 淘汰


class StrategyType(Enum):
    """策略类型"""
    TREND = "TREND"              # 趋势策略
    MEAN_REVERSION = "MEAN_REV" # 均值回归策略
    MOMENTUM = "MOMENTUM"       # 动量策略
    HYBRID = "HYBRID"           # 混合策略


@dataclass
class StrategyMetrics:
    """策略性能指标"""
    sharpe_ratio: float = 0.0          # 夏普比率
    max_drawdown: float = 0.0          # 最大回撤
    win_rate: float = 0.0             # 胜率
    profit_factor: float = 0.0         # 盈亏比
    total_trades: int = 0             # 总交易次数
    avg_holding_hours: float = 0.0     # 平均持仓时间
    total_pnl: float = 0.0           # 总盈亏

    # 运行时指标
    recent_sharpe: float = 0.0        # 近期夏普
    recent_return: float = 0.0        # 近期收益

    def calculate_sharpe(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if len(returns) < 2:
            return 0.0

        returns_arr = np.array(returns)
        excess_returns = returns_arr - risk_free_rate / 252  # 日化无风险利率

        if np.std(excess_returns) == 0:
            return 0.0

        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)


@dataclass
class Strategy:
    """
    策略基类

    核心概念：
    - 策略 = 生物体，有生命周期
    - 能感知环境变化 (市场状态)
    - 有竞争关系 (资源有限)
    - 有遗传特性 (参数可继承变异)
    """
    name: str
    strategy_type: StrategyType
    version: str = "1.0"
    description: str = ""

    # 状态
    status: StrategyStatus = StrategyStatus.TESTING
    capital_weight: float = 0.0  # 资金权重 0-100%

    # 指标
    metrics: StrategyMetrics = field(default_factory=StrategyMetrics)
    performance: List[float] = field(default_factory=list)  # 每日收益

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    last_trade_at: Optional[datetime] = None
    last_update_at: datetime = field(default_factory=datetime.now)

    # 参数
    params: Dict = field(default_factory=dict)

    def generate_signal(self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> float:
        """
        生成仓位信号

        Args:
            closes: 收盘价序列
            highs: 最高价序列
            lows: 最低价序列
            volumes: 成交量序列

        Returns:
            float: 仓位信号 -1 到 1
        """
        raise NotImplementedError("子类必须实现 generate_signal 方法")

    def update_performance(self, pnl: float):
        """更新策略表现"""
        self.performance.append(pnl)
        self.metrics.total_pnl += pnl
        self.metrics.total_trades += 1
        self.last_trade_at = datetime.now()
        self.last_update_at = datetime.now()

    def get_position_size(self, total_capital: float, risk_per_trade: float = 0.02) -> float:
        """
        计算仓位大小

        Args:
            total_capital: 总资金
            risk_per_trade: 每笔交易风险比例

        Returns:
            float: 仓位大小 (金额)
        """
        return total_capital * self.capital_weight / 100 * risk_per_trade

    def update_metrics(self, lookback: int = 20):
        """更新策略指标"""
        if len(self.performance) < 2:
            return

        returns = self.performance[-lookback:]

        # 计算夏普比率
        if len(returns) >= 2:
            self.metrics.recent_sharpe = self.metrics.calculate_sharpe(returns)
            self.metrics.sharpe_ratio = self.metrics.calculate_sharpe(self.performance)

        # 计算近期收益
        if len(returns) >= 2:
            self.metrics.recent_return = (returns[-1] / returns[0] - 1) * 100 if returns[0] != 0 else 0

    def calculate_performance_score(self) -> float:
        """
        计算表现评分 (0-100)

        评分维度：
        - 盈利能力 (30%)
        - 一致性 (20%)
        - 风险调整收益 (30%)
        - 适应性 (20%)
        """
        # New strategies get a baseline score to prevent immediate eviction
        if len(self.performance) == 0:
            return 60.0  # Default 60 for strategies with no trading history

        scores = {
            'profitability': 50.0,
            'consistency': 50.0,
            'risk_adjusted': 50.0,
            'adaptability': 50.0
        }

        # 盈利能力 (基于总PnL)
        if self.metrics.total_pnl > 0:
            scores['profitability'] = min(100, 50 + self.metrics.total_pnl / 100)
        elif self.metrics.total_pnl < 0:
            # Penalize losses but not too harshly
            scores['profitability'] = max(20, 50 + self.metrics.total_pnl / 100)
        else:
            scores['profitability'] = 50.0  # Break even gives 50

        # 一致性 (基于胜率)
        if self.metrics.total_trades > 0:
            scores['consistency'] = self.metrics.win_rate * 100

        # 风险调整收益 (基于夏普比率)
        if len(self.performance) >= 5:
            scores['risk_adjusted'] = min(100, max(20, self.metrics.sharpe_ratio * 10 + 50))

        # 适应性 (基于近期表现)
        if len(self.performance) >= 10:
            recent = self.performance[-10:]
            older = self.performance[-20:-10] if len(self.performance) >= 20 else recent
            if np.mean(older) != 0:
                adapt_ratio = np.mean(recent) / np.mean(older)
                scores['adaptability'] = min(100, max(20, adapt_ratio * 50))
            else:
                scores['adaptability'] = 50
        elif len(self.performance) >= 5:
            scores['adaptability'] = 50
        else:
            scores['adaptability'] = 50  # New strategies get baseline adaptability

        # Weighted average
        weights = {'profitability': 0.3, 'consistency': 0.2, 'risk_adjusted': 0.3, 'adaptability': 0.2}
        total_score = sum(s * weights[k] for k, s in scores.items())

        return min(100, max(0, total_score))

    def should_evict(self, min_score: float = 30.0) -> bool:
        """判断是否应该淘汰"""
        score = self.calculate_performance_score()
        return (score < min_score or
                self.metrics.max_drawdown > 20 or
                self.metrics.sharpe_ratio < 0.5)


class TrendStrategy(Strategy):
    """趋势跟踪策略"""

    def __init__(self, name: str = "Trend Strategy", fast_period: int = 10, slow_period: int = 30):
        super().__init__(
            name=name,
            strategy_type=StrategyType.TREND,
            description="基于均线交叉的趋势跟踪策略"
        )
        self.params = {'fast_period': fast_period, 'slow_period': slow_period}

    def generate_signal(self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> float:
        """均线交叉信号"""
        if len(closes) < self.params['slow_period']:
            return 0.0

        fast_p = self.params['fast_period']
        slow_p = self.params['slow_period']

        fast_ma = np.mean(closes[-fast_p:])
        slow_ma = np.mean(closes[-slow_p:])

        # 多头信号
        if closes[-1] > fast_ma and fast_ma > slow_ma:
            return 1.0
        # 空头信号
        elif closes[-1] < fast_ma and fast_ma < slow_ma:
            return -1.0

        return 0.0


class MeanReversionStrategy(Strategy):
    """均值回归策略"""

    def __init__(self, name: str = "Mean Reversion Strategy", period: int = 20, std_dev: float = 2.0):
        super().__init__(
            name=name,
            strategy_type=StrategyType.MEAN_REVERSION,
            description="基于布林带的均值回归策略"
        )
        self.params = {'period': period, 'std_dev': std_dev}

    def generate_signal(self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> float:
        """布林带回归信号"""
        if len(closes) < self.params['period']:
            return 0.0

        period = self.params['period']
        std_dev = self.params['std_dev']

        middle = np.mean(closes[-period:])
        std = np.std(closes[-period:])
        current = closes[-1]

        upper = middle + std_dev * std
        lower = middle - std_dev * std

        # 价格偏离度
        deviation = (current - middle) / std if std > 0 else 0

        # 触及下轨，做多
        if current < lower:
            return 1.0
        # 触及上轨，做空
        elif current > upper:
            return -1.0
        # 回归中轨
        elif abs(deviation) < 0.5:
            return 0.0

        # 部分仓位
        return -deviation / std_dev


class MomentumStrategy(Strategy):
    """动量策略"""

    def __init__(self, name: str = "Momentum Strategy", roc_period: int = 10, threshold: float = 2.0):
        super().__init__(
            name=name,
            strategy_type=StrategyType.MOMENTUM,
            description="基于动量指标的策略"
        )
        self.params = {'roc_period': roc_period, 'threshold': threshold}

    def generate_signal(self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> float:
        """动量信号"""
        if len(closes) < self.params['roc_period'] + 1:
            return 0.0

        roc_p = self.params['roc_period']
        threshold = self.params['threshold']

        # 价格变化率
        roc = (closes[-1] - closes[-roc_p - 1]) / closes[-roc_p - 1] * 100

        # 动量强度
        if roc > threshold:
            return min(1.0, roc / 10)
        elif roc < -threshold:
            return max(-1.0, roc / 10)

        return 0.0


class StrategyPool:
    """策略池管理器"""

    def __init__(self):
        self.strategies: List[Strategy] = []
        self._strategy_map: Dict[str, Strategy] = {}

    def add_strategy(self, strategy: Strategy):
        """添加策略"""
        self.strategies.append(strategy)
        self._strategy_map[strategy.name] = strategy

    def remove_strategy(self, name: str) -> bool:
        """移除策略"""
        if name in self._strategy_map:
            strategy = self._strategy_map.pop(name)
            self.strategies.remove(strategy)
            return True
        return False

    def get_strategy(self, name: str) -> Optional[Strategy]:
        """获取策略"""
        return self._strategy_map.get(name)

    def get_active_strategies(self) -> List[Strategy]:
        """获取活跃策略"""
        return [s for s in self.strategies if s.status == StrategyStatus.ALIVE]

    def get_by_type(self, strategy_type: StrategyType) -> List[Strategy]:
        """按类型获取策略"""
        return [s for s in self.strategies if s.strategy_type == strategy_type]

    def rebalance_weights(self, total_weight: float = 100.0):
        """重新分配策略权重"""
        active = self.get_active_strategies()
        if not active:
            return

        equal_weight = total_weight / len(active)
        for strategy in active:
            strategy.capital_weight = equal_weight

    def get_combined_signal(self) -> float:
        """获取合并信号"""
        active = self.get_active_strategies()
        if not active:
            return 0.0

        total_weight = sum(s.capital_weight for s in active)
        if total_weight == 0:
            return 0.0

        combined = 0.0
        for strategy in active:
            weight_ratio = strategy.capital_weight / total_weight
            combined += strategy.capital_weight * weight_ratio

        return combined / 100  # 归一化到 -1 到 1

    def __len__(self) -> int:
        return len(self.strategies)


def create_default_pool() -> StrategyPool:
    """创建默认策略池"""
    pool = StrategyPool()

    # 添加默认策略
    trend = TrendStrategy("Trend MA", fast_period=10, slow_period=30)
    trend.capital_weight = 33.33  # 等权重
    trend.status = StrategyStatus.ALIVE

    meanrev = MeanReversionStrategy("MeanRev BB", period=20, std_dev=2.0)
    meanrev.capital_weight = 33.33
    meanrev.status = StrategyStatus.ALIVE

    momentum = MomentumStrategy("Momentum ROC", roc_period=10, threshold=2.0)
    momentum.capital_weight = 33.34
    momentum.status = StrategyStatus.ALIVE

    pool.add_strategy(trend)
    pool.add_strategy(meanrev)
    pool.add_strategy(momentum)

    return pool
