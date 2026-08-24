"""
Signal Domain Models - 信号生成领域模型

定义信号生成上下文中所有业务实体：
- TradingSignal: 交易信号聚合根
- IndicatorResult: 技术指标结果实体
- SignalFilter: 信号过滤器实体

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SignalType(Enum):
    """信号类型枚举"""

    LONG = "long"  # 多头信号
    SHORT = "short"  # 空头信号
    CLOSE_LONG = "close_long"  # 平多信号
    CLOSE_SHORT = "close_short"  # 平空信号
    HOLD = "hold"  # 观望信号

    def __str__(self) -> str:
        return self.value


class SignalSource(Enum):
    """信号来源"""

    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    TREND = "trend"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    FUSION = "fusion"


@dataclass
class IndicatorResult:
    """
    技术指标计算结果实体

    表示单一技术指标的计算值。

    INVARIANTS:
    - value 是实数
    """

    name: str  # RSI, MACD, BOLLINGER, etc.
    value: float
    values: list[float] = field(default_factory=list)  # 历史序列
    params: dict[str, Any] = field(default_factory=dict)  # 计算参数
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "values": self.values,
            "params": self.params,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndicatorResult:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now()
        return cls(
            name=data.get("name", ""),
            value=float(data.get("value", 0)),
            values=data.get("values", []),
            params=data.get("params", {}),
            timestamp=ts,
            metadata=data.get("metadata", {}),
        )


@dataclass
class FilterCondition:
    """
    过滤器条件值对象

    表示信号过滤的单个条件。
    """

    field: str  # 字段名
    operator: str  # 操作符: >, <, >=, <=, ==, !=, in, not_in
    value: Any  # 比较值

    def evaluate(self, signal: dict[str, Any]) -> bool:
        """评估条件是否满足"""
        signal_value = signal.get(self.field)

        if self.operator == ">":
            return signal_value > self.value
        elif self.operator == "<":
            return signal_value < self.value
        elif self.operator == ">=":
            return signal_value >= self.value
        elif self.operator == "<=":
            return signal_value <= self.value
        elif self.operator == "==":
            return signal_value == self.value
        elif self.operator == "!=":
            return signal_value != self.value
        elif self.operator == "in":
            return signal_value in self.value
        elif self.operator == "not_in":
            return signal_value not in self.value
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
        }


@dataclass
class SignalFilter:
    """
    信号过滤器实体

    定义信号的过滤规则。

    INVARIANTS:
    - enabled 时才会生效
    - conditions 至少有一个
    """

    filter_id: str
    name: str
    filter_type: str  # cooldown, threshold, blacklist
    conditions: list[FilterCondition] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0  # 执行优先级，数字越小优先级越高
    cooldown_seconds: int = 0  # 冷却期秒数
    last_triggered: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.filter_id:
            self.filter_id = str(uuid.uuid4())[:8]

    def evaluate(self, signal: dict[str, Any]) -> bool:
        """
        评估信号是否通过过滤器

        Args:
            signal: 信号数据

        Returns:
            True 表示通过，False 表示被过滤
        """
        if not self.enabled:
            return True

        # 检查冷却期
        if self.cooldown_seconds > 0 and self.last_triggered:
            elapsed = (datetime.now() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False

        # 评估所有条件
        for condition in self.conditions:
            if not condition.evaluate(signal):
                return False

        # 更新最后触发时间
        self.last_triggered = datetime.now()
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "filter_id": self.filter_id,
            "name": self.name,
            "filter_type": self.filter_type,
            "conditions": [c.to_dict() for c in self.conditions],
            "enabled": self.enabled,
            "priority": self.priority,
            "cooldown_seconds": self.cooldown_seconds,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "metadata": self.metadata,
        }


@dataclass
class TradingSignal:
    """
    交易信号聚合根

    表示系统生成的交易信号，包含入场、止损、止盈信息。
    聚合根：外部只能通过此类访问信号相关数据。

    INVARIANTS:
    - 0 <= confidence <= 1
    - signal_type 是 SignalType 枚举
    - LONG: entry > stop_loss, take_profit > entry
    - SHORT: entry < stop_loss, take_profit < entry

    VERSION: 支持信号版本追踪
    """

    signal_id: str
    signal_type: SignalType
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float

    # 元数据
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    source: SignalSource = SignalSource.RSI
    indicators: dict[str, IndicatorResult] = field(default_factory=dict)
    version: int = 1
    is_active: bool = True
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # 生成 ID
        if not self.signal_id:
            self.signal_id = str(uuid.uuid4())[:12]

        # 置信度范围
        if not (0 <= self.confidence <= 1):
            raise ValueError("confidence must be in [0, 1]")

        # 类型验证
        if not isinstance(self.signal_type, SignalType):
            if isinstance(self.signal_type, str):
                self.signal_type = SignalType(self.signal_type)
            else:
                raise ValueError("signal_type must be SignalType enum")

        # 止损止盈验证
        self._validate_prices()

    def _validate_prices(self) -> None:
        """验证价格关系的正确性"""
        if self.signal_type == SignalType.LONG:
            if self.entry_price <= self.stop_loss:
                raise ValueError("LONG: entry_price must be > stop_loss")
            if self.take_profit <= self.entry_price:
                raise ValueError("LONG: take_profit must be > entry_price")
        elif self.signal_type == SignalType.SHORT:
            if self.entry_price >= self.stop_loss:
                raise ValueError("SHORT: entry_price must be < stop_loss")
            if self.take_profit >= self.entry_price:
                raise ValueError("SHORT: take_profit must be < entry_price")

    @property
    def risk_amount(self) -> float:
        """风险金额"""
        return abs(self.entry_price - self.stop_loss)

    @property
    def reward_amount(self) -> float:
        """回报金额"""
        return abs(self.take_profit - self.entry_price)

    @property
    def risk_reward_ratio(self) -> float:
        """风险回报比"""
        risk = self.risk_amount
        if risk == 0:
            return 0.0
        return self.reward_amount / risk

    @property
    def is_expired(self) -> bool:
        """信号是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """信号是否有效"""
        return self.is_active and not self.is_expired

    def invalidate(self, reason: str = "") -> None:
        """使信号失效"""
        self.is_active = False
        self.metadata["invalidate_reason"] = reason
        self.metadata["invalidate_at"] = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "symbol": self.symbol,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "confidence": self.confidence,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source.value,
            "indicators": {k: v.to_dict() for k, v in self.indicators.items()},
            "version": self.version,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TradingSignal:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now()

        expires = data.get("expires_at")
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires)

        signal_type = data.get("signal_type")
        if isinstance(signal_type, str):
            signal_type = SignalType(signal_type)

        source = data.get("source", "rsi")
        if isinstance(source, str):
            source = SignalSource(source)

        return cls(
            signal_id=data.get("signal_id", ""),
            signal_type=signal_type,
            symbol=data.get("symbol", ""),
            entry_price=float(data.get("entry_price", 0)),
            stop_loss=float(data.get("stop_loss", 0)),
            take_profit=float(data.get("take_profit", 0)),
            confidence=float(data.get("confidence", 0)),
            reason=data.get("reason", ""),
            timestamp=ts,
            source=source,
            version=int(data.get("version", 1)),
            is_active=data.get("is_active", True),
            expires_at=expires,
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# Factory Methods
# =============================================================================


def create_signal(
    symbol: str,
    signal_type: SignalType,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    confidence: float,
    reason: str,
    source: SignalSource = SignalSource.RSI,
    expires_seconds: int = 3600,
) -> TradingSignal:
    """
    工厂方法：创建交易信号

    Args:
        symbol: 交易对
        signal_type: 信号类型
        entry_price: 入场价格
        stop_loss: 止损价格
        take_profit: 止盈价格
        confidence: 置信度 [0, 1]
        reason: 生成原因
        source: 信号来源
        expires_seconds: 过期秒数

    Returns:
        TradingSignal 实例
    """
    return TradingSignal(
        signal_id="",  # 自动生成
        signal_type=signal_type,
        symbol=symbol,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=confidence,
        reason=reason,
        source=source,
        expires_at=datetime.now() + datetime.timedelta(seconds=expires_seconds),
    )


def create_cooldown_filter(
    name: str,
    cooldown_seconds: int,
    priority: int = 0,
) -> SignalFilter:
    """
    工厂方法：创建冷却过滤器

    Args:
        name: 过滤器名称
        cooldown_seconds: 冷却秒数
        priority: 优先级

    Returns:
        SignalFilter 实例
    """
    return SignalFilter(
        filter_id="",  # 自动生成
        name=name,
        filter_type="cooldown",
        conditions=[],
        cooldown_seconds=cooldown_seconds,
        priority=priority,
    )


def create_confidence_filter(
    min_confidence: float,
    priority: int = 0,
) -> SignalFilter:
    """
    工厂方法：创建置信度过滤器

    Args:
        min_confidence: 最小置信度
        priority: 优先级

    Returns:
        SignalFilter 实例
    """
    return SignalFilter(
        filter_id="",
        name=f"min_confidence_{min_confidence}",
        filter_type="threshold",
        conditions=[
            FilterCondition(
                field="confidence",
                operator=">=",
                value=min_confidence,
            )
        ],
        priority=priority,
    )


# =============================================================================
# Domain Services
# =============================================================================


def validate_signal(signal: TradingSignal) -> list[str]:
    """
    验证信号的有效性

    Args:
        signal: 待验证的信号

    Returns:
        错误列表，空列表表示有效
    """
    errors = []

    if signal.confidence < 0 or signal.confidence > 1:
        errors.append("confidence must be in [0, 1]")

    if signal.entry_price <= 0:
        errors.append("entry_price must be positive")

    if signal.risk_reward_ratio < 1.5:
        errors.append(f"risk_reward_ratio {signal.risk_reward_ratio:.2f} < 1.5")

    if signal.is_expired:
        errors.append("signal is expired")

    return errors


def merge_signals(signals: list[TradingSignal]) -> TradingSignal | None:
    """
    合并多个信号

    Args:
        signals: 信号列表

    Returns:
        合并后的信号，或 None
    """
    if not signals:
        return None

    # 按置信度排序
    sorted_signals = sorted(signals, key=lambda s: s.confidence, reverse=True)

    # 取最高置信度的信号
    best = sorted_signals[0]

    # 融合置信度
    avg_confidence = sum(s.confidence for s in signals) / len(signals)

    # 创建合并信号
    return TradingSignal(
        signal_id="",  # 新 ID
        signal_type=best.signal_type,
        symbol=best.symbol,
        entry_price=best.entry_price,
        stop_loss=best.stop_loss,
        take_profit=best.take_profit,
        confidence=avg_confidence,
        reason=f"Merged from {len(signals)} signals",
        source=SignalSource.FUSION,
        metadata={
            "merged_signals": [s.signal_id for s in signals],
            "original_confidences": [s.confidence for s in signals],
        },
    )
