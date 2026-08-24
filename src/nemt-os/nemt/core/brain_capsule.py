"""
BrainCapsule - 策略大脑胶囊

管理策略选择和调度:
- 多策略支持
- 波动率自适应
- 策略权重分配
- 信号融合
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ["BrainCapsule", "StrategyType", "StrategySignal"]


class StrategyType(Enum):
    """策略类型"""

    TREND = "trend"  # 趋势跟踪
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    BREAKOUT = "breakout"  # 突破策略
    SCALPING = "scalping"  # 剥头皮
    GRID = "grid"  # 网格交易


@dataclass
class StrategySignal:
    """策略信号"""

    strategy: StrategyType
    signal: str  # 'long', 'short', 'neutral'
    confidence: float
    weight: float  # 策略权重
    timestamp: float


class BrainCapsule(ModuleCapsule):
    """
    策略大脑胶囊

    订阅事件:
    - nemt.signal: 原始信号

    发布事件:
    - nemt.strategy_signal: 融合后的策略信号
    - nemt.strategy_select: 策略选择结果
    """

    def __init__(self):
        super().__init__("brain")

        # 策略配置
        self._strategies: List[StrategyType] = []
        self._strategy_weights: Dict[StrategyType, float] = {}
        self._strategy_enabled: Dict[StrategyType, bool] = {}

        # 波动率参数
        self._high_vol_threshold: float = 0.3
        self._low_vol_threshold: float = 0.1
        self._current_volatility: float = 0.1

        # 信号缓存
        self._raw_signals: Dict[StrategyType, StrategySignal] = {}
        self._signal_history: List[Dict[str, Any]] = []
        self._max_history: int = 100

        # 统计
        self._signal_count: int = 0
        self._strategy_usage: Dict[StrategyType, int] = {}

    def init(self) -> None:
        """初始化"""
        # 从配置加载策略
        strategy_names = self.get_config("brain.strategies", ["trend", "mean_reversion"])
        self._strategies = [StrategyType(s) for s in strategy_names if s in [e.value for e in StrategyType]]

        # 默认启用所有策略
        for strategy in self._strategies:
            self._strategy_enabled[strategy] = True
            self._strategy_weights[strategy] = 1.0 / len(self._strategies) if self._strategies else 1.0
            self._strategy_usage[strategy] = 0

        # 波动率阈值
        self._high_vol_threshold = self.get_config("brain.high_vol_threshold", 0.3)
        self._low_vol_threshold = self.get_config("brain.low_vol_threshold", 0.1)

        # 订阅事件
        self.subscribe("nemt.signal", self._on_signal)

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回大脑状态

        Returns:
            大脑状态字典
        """
        return {
            "strategies": [s.value for s in self._strategies],
            "enabled_strategies": [s.value for s in self._strategies if self._strategy_enabled.get(s, False)],
            "weights": {s.value: w for s, w in self._strategy_weights.items()},
            "usage": {s.value: u for s, u in self._strategy_usage.items()},
            "current_volatility": self._current_volatility,
            "signal_count": self._signal_count,
            "signal_history_len": len(self._signal_history),
        }

    def _on_signal(self, event: Event) -> None:
        """处理原始信号"""
        data = event.data
        if not data:
            return

        # 获取信号信息
        raw_signal = data.get("signal", "neutral")
        confidence = data.get("confidence", 0.5)
        symbol = data.get("symbol", "BTC")
        indicators = data.get("indicators", {})

        # 根据市场状态选择策略
        selected_strategy = self._select_strategy(indicators)

        # 计算融合信号
        fused_signal = self._fuse_signals(raw_signal, confidence, selected_strategy)

        # 发布策略信号
        self.publish(
            "nemt.strategy_signal",
            {
                "strategy": selected_strategy.value,
                "signal": fused_signal["signal"],
                "confidence": fused_signal["confidence"],
                "weight": self._strategy_weights.get(selected_strategy, 1.0),
                "symbol": symbol,
                "raw_signal": raw_signal,
                "timestamp": self._get_time(),
            },
        )

        self._signal_count += 1
        self._strategy_usage[selected_strategy] = self._strategy_usage.get(selected_strategy, 0) + 1

    def _select_strategy(self, indicators: Dict[str, float]) -> StrategyType:
        """
        选择策略

        基于波动率和指标选择最佳策略
        """
        if not self._strategies:
            return StrategyType.TREND

        # 计算波动率 (简化：使用 DCI 变化率作为波动率代理)
        dci = abs(indicators.get("dci", 0)) / 100
        vortex = indicators.get("vortex", 0.5)
        resonance = indicators.get("resonance", 0.5)

        # 综合波动率
        self._current_volatility = (dci + abs(vortex - 0.5) * 2 + resonance) / 3

        # 根据波动率选择策略
        if self._current_volatility > self._high_vol_threshold:
            # 高波动：趋势策略
            if StrategyType.TREND in self._strategies and self._strategy_enabled.get(StrategyType.TREND, False):
                return StrategyType.TREND
        elif self._current_volatility < self._low_vol_threshold:
            # 低波动：均值回归或网格
            if StrategyType.MEAN_REVERSION in self._strategies and self._strategy_enabled.get(
                StrategyType.MEAN_REVERSION, False
            ):
                return StrategyType.MEAN_REVERSION
            if StrategyType.GRID in self._strategies and self._strategy_enabled.get(StrategyType.GRID, False):
                return StrategyType.GRID
        else:
            # 中等波动：默认趋势
            if StrategyType.TREND in self._strategies and self._strategy_enabled.get(StrategyType.TREND, False):
                return StrategyType.TREND

        # 默认返回第一个启用的策略
        for strategy in self._strategies:
            if self._strategy_enabled.get(strategy, False):
                return strategy

        return StrategyType.TREND

    def _fuse_signals(self, raw_signal: str, confidence: float, strategy: StrategyType) -> Dict[str, float]:
        """
        融合信号

        将原始信号与策略权重融合
        """
        weight = self._strategy_weights.get(strategy, 1.0)

        # 加权置信度
        fused_confidence = confidence * (0.5 + 0.5 * weight)

        # 调整信号强度
        if raw_signal == "long":
            adjusted_signal = "long" if fused_confidence > 0.5 else "neutral"
        elif raw_signal == "short":
            adjusted_signal = "short" if fused_confidence > 0.5 else "neutral"
        else:
            adjusted_signal = "neutral"

        return {"signal": adjusted_signal, "confidence": fused_confidence}

    def set_strategy_weight(self, strategy: StrategyType, weight: float) -> None:
        """
        设置策略权重

        Args:
            strategy: 策略类型
            weight: 权重 (0-1)
        """
        self._strategy_weights[strategy] = max(0.0, min(1.0, weight))
        self._normalize_weights()

    def enable_strategy(self, strategy: StrategyType) -> None:
        """启用策略"""
        self._strategy_enabled[strategy] = True

    def disable_strategy(self, strategy: StrategyType) -> None:
        """禁用策略"""
        self._strategy_enabled[strategy] = False

    def _normalize_weights(self) -> None:
        """归一化权重"""
        total = sum(self._strategy_weights.values())
        if total > 0:
            for strategy in self._strategy_weights:
                self._strategy_weights[strategy] /= total

    def get_strategy_performance(self) -> Dict[str, float]:
        """获取策略表现"""
        total_signals = sum(self._strategy_usage.values()) if self._strategy_usage else 1
        return {strategy.value: count / total_signals for strategy, count in self._strategy_usage.items()}

    def shutdown(self) -> None:
        """关闭"""
        self.unsubscribe("nemt.signal", self._on_signal)

    @staticmethod
    def _get_time() -> float:
        """获取当前时间"""
        import time

        return time.time()
