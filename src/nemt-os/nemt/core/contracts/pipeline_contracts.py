"""
L0 系统级接口契约

定义 Pipeline 与各胶囊间的标准接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MarketPhase(Enum):
    """市场相位枚举"""

    UNKNOWN = "unknown"
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    CONSOLIDATION = "consolidation"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"


@dataclass
class PipelineInput:
    """
    Pipeline 输入数据

    定义进入处理管道的数据格式。
    """

    timestamp: datetime
    symbol: str
    price: float
    volume: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineInput":
        """从字典创建"""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            timestamp=timestamp,
            symbol=data.get("symbol", ""),
            price=float(data.get("price", 0)),
            volume=float(data.get("volume", 0)),
            open=float(data.get("open", 0)),
            high=float(data.get("high", 0)),
            low=float(data.get("low", 0)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PipelineOutput:
    """
    Pipeline 输出数据

    定义处理管道输出的数据格式。
    """

    timestamp: datetime
    symbol: str
    phase: MarketPhase
    confidence: float
    signals: list[dict[str, Any]] = field(default_factory=list)
    indicators: dict[str, float] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "phase": self.phase.value,
            "confidence": self.confidence,
            "signals": self.signals,
            "indicators": self.indicators,
            "state": self.state,
            "errors": self.errors,
        }

    @property
    def has_signals(self) -> bool:
        """是否有信号"""
        return len(self.signals) > 0

    @property
    def is_valid(self) -> bool:
        """输出是否有效"""
        return self.confidence > 0 and len(self.errors) == 0


@dataclass
class SignalData:
    """
    信号数据

    定义交易信号的结构。
    """

    signal_type: str  # 'long', 'short', 'close', 'hold'
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "signal_type": self.signal_type,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "confidence": self.confidence,
            "reason": self.reason,
            "metadata": self.metadata,
        }


class IPipelineContract(ABC):
    """
    L0 系统级接口契约

    定义数据处理管道的标准接口。
    自相似性：每个处理阶段（看画填验连）都有明确的输入输出。
    """

    @abstractmethod
    def observe(self, context: dict) -> PipelineInput:
        """
        【看】接收并理解输入数据

        Args:
            context: 原始上下文数据

        Returns:
            标准化的 PipelineInput
        """
        pass

    @abstractmethod
    def design(self, input_data: PipelineInput) -> dict[str, Any]:
        """
        【画】设计处理流程

        Args:
            input_data: 标准化后的输入数据

        Returns:
            处理流程设计
        """
        pass

    @abstractmethod
    def implement(self, design: dict) -> None:
        """
        【填】实现核心处理逻辑

        Args:
            design: 处理流程设计
        """
        pass

    @abstractmethod
    def verify(self) -> bool:
        """
        【验】验证处理结果

        Returns:
            验证是否通过
        """
        pass

    @abstractmethod
    def integrate(self, output: PipelineOutput) -> None:
        """
        【连】输出结果给下游

        Args:
            output: 处理后的输出数据
        """
        pass

    # ========================================
    # 管道执行接口
    # ========================================

    def process(self, raw_data: dict[str, Any]) -> PipelineOutput:
        """
        执行完整的处理流程

        Args:
            raw_data: 原始数据

        Returns:
            处理结果
        """
        # 看
        input_data = self.observe(raw_data)

        # 画
        design = self.design(input_data)

        # 填
        self.implement(design)

        # 验
        if not self.verify():
            return PipelineOutput(
                timestamp=datetime.now(),
                symbol=input_data.symbol,
                phase=MarketPhase.UNKNOWN,
                confidence=0.0,
                errors=["Verification failed"],
            )

        # 生成输出
        output = PipelineOutput(
            timestamp=datetime.now(),
            symbol=input_data.symbol,
            phase=MarketPhase.UNKNOWN,
            confidence=1.0,
        )

        # 连
        self.integrate(output)

        return output
