"""
Brain Domain Models - 策略大脑领域模型

定义策略大脑上下文中所有业务实体：
- StrategyConfig: 策略配置聚合根
- StrategyType: 策略类型值对象
- FusedSignal: 融合信号实体

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StrategyType(Enum):
    """策略类型枚举"""

    TREND = "trend"  # 趋势策略
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    BREAKOUT = "breakout"  # 突破策略
    GRID = "grid"  # 网格策略
    MULTI = "multi"  # 多策略融合

    def __str__(self) -> str:
        return self.value

    @property
    def description(self) -> str:
        descriptions = {
            "trend": "追涨杀跌，顺势而为",
            "mean_reversion": "高抛低吸，回归均值",
            "breakout": "突破关键位，追入趋势",
            "grid": "区间定投，网格交易",
            "multi": "多策略综合判断",
        }
        return descriptions.get(self.value, "")


class FusionMethod(Enum):
    """融合方法枚举"""

    VOTE = "vote"  # 多数投票
    WEIGHTED_AVERAGE = "weighted_avg"  # 加权平均
    PRIORITY = "priority"  # 优先级选择
    CONFIDENCE = "confidence"  # 置信度选择


@dataclass
class PerformanceMetrics:
    """
    策略表现指标值对象

    记录策略的历史表现数据。
    """

    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    total_trades: int = 0
    profitable_trades: int = 0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "win_rate": self.win_rate,
            "avg_profit": self.avg_profit,
            "avg_loss": self.avg_loss,
            "total_trades": self.total_trades,
            "profitable_trades": self.profitable_trades,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class StrategyConfig:
    """
    策略配置聚合根

    定义单个策略的参数和权重。
    聚合根：外部只能通过此类访问策略配置。

    INVARIANTS:
    - 0 <= weight <= 1
    - len(strategies) <= 5
    """

    strategy_type: StrategyType
    enabled: bool = True
    weight: float = 1.0
    parameters: dict[str, Any] = field(default_factory=dict)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)

    # 元数据
    strategy_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    version: int = 1

    def __post_init__(self):
        if not (0 <= self.weight <= 1):
            raise ValueError("weight must be in [0, 1]")
        if not isinstance(self.strategy_type, StrategyType):
            self.strategy_type = StrategyType(self.strategy_type)
        if not self.name:
            self.name = self.strategy_type.value

    def update_weight(self, new_weight: float) -> None:
        """
        更新策略权重

        Args:
            new_weight: 新权重 [0, 1]
        """
        if not (0 <= new_weight <= 1):
            raise ValueError("weight must be in [0, 1]")
        self.weight = new_weight
        self.last_updated = datetime.now()
        self.version += 1

    def enable(self) -> None:
        """启用策略"""
        self.enabled = True
        self.last_updated = datetime.now()
        self.version += 1

    def disable(self) -> None:
        """禁用策略"""
        self.enabled = False
        self.last_updated = datetime.now()
        self.version += 1

    def update_performance(self, metrics: PerformanceMetrics) -> None:
        """更新表现指标"""
        self.performance = metrics
        self.last_updated = datetime.now()
        self.version += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_type": self.strategy_type.value,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "weight": self.weight,
            "parameters": self.parameters,
            "performance": self.performance.to_dict(),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyConfig:
        created = data.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        elif created is None:
            created = datetime.now()

        updated = data.get("last_updated")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        elif updated is None:
            updated = datetime.now()

        strategy_type = data.get("strategy_type", "trend")
        if isinstance(strategy_type, str):
            strategy_type = StrategyType(strategy_type)

        perf_data = data.get("performance", {})
        performance = PerformanceMetrics(
            win_rate=float(perf_data.get("win_rate", 0)),
            avg_profit=float(perf_data.get("avg_profit", 0)),
            avg_loss=float(perf_data.get("avg_loss", 0)),
            total_trades=int(perf_data.get("total_trades", 0)),
            profitable_trades=int(perf_data.get("profitable_trades", 0)),
            sharpe_ratio=float(perf_data.get("sharpe_ratio", 0)),
            max_drawdown=float(perf_data.get("max_drawdown", 0)),
        )

        return cls(
            strategy_id=data.get("strategy_id", str(uuid.uuid4())[:8]),
            strategy_type=strategy_type,
            name=data.get("name", ""),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            weight=float(data.get("weight", 1.0)),
            parameters=data.get("parameters", {}),
            performance=performance,
            created_at=created,
            last_updated=updated,
            version=int(data.get("version", 1)),
        )


@dataclass
class SignalVote:
    """
    信号投票值对象

    表示单个策略的投票信息。
    """

    signal_type: str  # "long", "short", "hold"
    confidence: float
    strategy_id: str
    strategy_type: str
    weight: float


@dataclass
class FusedSignal:
    """
    融合信号实体

    表示多策略融合后的最终信号。

    INVARIANTS:
    - 0 <= fused_confidence <= 1
    - len(original_signals) >= 1
    """

    fused_signal_type: str
    fused_confidence: float
    original_signals: list[dict[str, Any]]
    fusion_method: FusionMethod

    # 权重信息
    strategy_weights: dict[str, float] = field(default_factory=dict)
    votes: list[SignalVote] = field(default_factory=list)

    # 元数据
    symbol: str = ""
    reason: str = ""
    fused_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not (0 <= self.fused_confidence <= 1):
            raise ValueError("fused_confidence must be in [0, 1]")
        if not self.original_signals:
            raise ValueError("original_signals cannot be empty")
        if not isinstance(self.fusion_method, FusionMethod):
            self.fusion_method = FusionMethod(self.fusion_method)

    @property
    def signal_count(self) -> int:
        """参与融合的信号数"""
        return len(self.original_signals)

    @property
    def is_consensus(self) -> bool:
        """是否达成共识（多数一致）"""
        if not self.votes:
            return False
        signal_types = [v.signal_type for v in self.votes]
        most_common = max(set(signal_types), key=signal_types.count)
        return signal_types.count(most_common) > len(signal_types) / 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "fused_signal_type": self.fused_signal_type,
            "fused_confidence": self.fused_confidence,
            "original_signals": self.original_signals,
            "fusion_method": self.fusion_method.value,
            "strategy_weights": self.strategy_weights,
            "votes": [
                {
                    "signal_type": v.signal_type,
                    "confidence": v.confidence,
                    "strategy_id": v.strategy_id,
                    "strategy_type": v.strategy_type,
                    "weight": v.weight,
                }
                for v in self.votes
            ],
            "symbol": self.symbol,
            "reason": self.reason,
            "fused_at": self.fused_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FusedSignal:
        fused_at = data.get("fused_at")
        if isinstance(fused_at, str):
            fused_at = datetime.fromisoformat(fused_at)
        elif fused_at is None:
            fused_at = datetime.now()

        fusion_method = data.get("fusion_method", "vote")
        if isinstance(fusion_method, str):
            fusion_method = FusionMethod(fusion_method)

        votes_data = data.get("votes", [])
        votes = [
            SignalVote(
                signal_type=v.get("signal_type", "hold"),
                confidence=float(v.get("confidence", 0)),
                strategy_id=v.get("strategy_id", ""),
                strategy_type=v.get("strategy_type", ""),
                weight=float(v.get("weight", 1)),
            )
            for v in votes_data
        ]

        return cls(
            fused_signal_type=data.get("fused_signal_type", "hold"),
            fused_confidence=float(data.get("fused_confidence", 0)),
            original_signals=data.get("original_signals", []),
            fusion_method=fusion_method,
            strategy_weights=data.get("strategy_weights", {}),
            votes=votes,
            symbol=data.get("symbol", ""),
            reason=data.get("reason", ""),
            fused_at=fused_at,
            version=int(data.get("version", 1)),
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# Factory Methods
# =============================================================================


def create_strategy_config(
    strategy_type: StrategyType,
    weight: float = 1.0,
    enabled: bool = True,
    parameters: dict[str, Any] | None = None,
) -> StrategyConfig:
    """
    工厂方法：创建策略配置

    Args:
        strategy_type: 策略类型
        weight: 权重
        enabled: 是否启用
        parameters: 策略参数

    Returns:
        StrategyConfig 实例
    """
    return StrategyConfig(
        strategy_type=strategy_type,
        weight=weight,
        enabled=enabled,
        parameters=parameters or {},
    )


def create_fused_signal(
    symbol: str,
    signal_type: str,
    confidence: float,
    original_signals: list[dict[str, Any]],
    fusion_method: FusionMethod,
    votes: list[SignalVote],
    reason: str,
) -> FusedSignal:
    """
    工厂方法：创建融合信号

    Args:
        symbol: 交易对
        signal_type: 融合后的信号类型
        confidence: 融合置信度
        original_signals: 原始信号列表
        fusion_method: 融合方法
        votes: 投票列表
        reason: 融合原因

    Returns:
        FusedSignal 实例
    """
    return FusedSignal(
        fused_signal_type=signal_type,
        fused_confidence=confidence,
        original_signals=original_signals,
        fusion_method=fusion_method,
        strategy_weights={v.strategy_id: v.weight for v in votes},
        votes=votes,
        symbol=symbol,
        reason=reason,
    )


# =============================================================================
# Domain Services
# =============================================================================


def normalize_weights(configs: list[StrategyConfig]) -> list[StrategyConfig]:
    """
    归一化策略权重

    Args:
        configs: 策略配置列表

    Returns:
        归一化后的配置列表
    """
    if not configs:
        return []

    total = sum(c.weight for c in configs if c.enabled)
    if total == 0:
        return configs

    for config in configs:
        if config.enabled:
            config.weight = config.weight / total

    return configs


def fuse_by_vote(votes: list[SignalVote]) -> tuple:
    """
    多数投票融合

    Args:
        votes: 投票列表

    Returns:
        (信号类型, 置信度)
    """
    if not votes:
        return ("hold", 0.0)

    # 统计票数
    counts = {}
    for vote in votes:
        stype = vote.signal_type
        weight = vote.weight
        counts[stype] = counts.get(stype, 0) + weight

    # 选择票数最多的
    best_type = max(counts.items(), key=lambda x: x[1])

    # 置信度 = 胜出票数 / 总票数
    total_weight = sum(v.weight for v in votes)
    confidence = best_type[1] / total_weight if total_weight > 0 else 0

    return (best_type[0], confidence)


def fuse_by_weighted_average(
    votes: list[SignalVote],
) -> tuple:
    """
    加权平均融合

    Args:
        votes: 投票列表

    Returns:
        (信号类型, 置信度)
    """
    if not votes:
        return ("hold", 0.0)

    # 计算加权置信度
    weighted_votes = {"long": 0.0, "short": 0.0, "hold": 0.0}

    for vote in votes:
        stype = vote.signal_type
        if stype in weighted_votes:
            weighted_votes[stype] += vote.confidence * vote.weight

    # 选择加权值最高的
    best_type = max(weighted_votes.items(), key=lambda x: x[1])
    total = sum(weighted_votes.values())
    confidence = best_type[1] / total if total > 0 else 0

    return (best_type[0], confidence)


def adjust_weights_by_performance(
    configs: list[StrategyConfig],
    decay_factor: float = 0.95,
) -> list[StrategyConfig]:
    """
    根据历史表现调整权重

    Args:
        configs: 策略配置列表
        decay_factor: 衰减因子

    Returns:
        调整后的配置列表
    """
    for config in configs:
        if config.enabled and config.performance.total_trades > 0:
            # 基于胜率调整
            win_rate = config.performance.win_rate
            sharpe = config.performance.sharpe_ratio

            # 新权重 = 原权重 * (1 + (胜率 - 0.5)) * sharpe_factor
            adjustment = (win_rate - 0.5) * 2  # -1 到 1
            sharpe_factor = max(0.5, min(2.0, 1 + (sharpe - 1) * 0.2))
            new_weight = config.weight * (1 + adjustment * 0.1) * sharpe_factor

            config.update_weight(max(0.0, min(1.0, new_weight)))

    # 重新归一化
    return normalize_weights(configs)
