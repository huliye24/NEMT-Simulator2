"""
BrainCapsule - 分形迭代版

按五阶段迭代法重写的策略大脑胶囊。
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from nemt.core.capsule import FractalCapsule


class StrategyType(Enum):
    """策略类型"""

    TREND = "trend"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    GRID = "grid"
    MULTI = "multi"


@dataclass
class StrategyConfig:
    """策略配置"""

    strategy_type: StrategyType
    enabled: bool = True
    weight: float = 1.0
    parameters: dict[str, Any] = field(default_factory=dict)


class BrainCapsule(FractalCapsule):
    """
    策略大脑胶囊

    负责：
    - 多策略管理
    - 策略选择
    - 信号融合
    - 权重调整

    五阶段方法已实现。
    """

    def __init__(self, capsule_id: str = "brain"):
        super().__init__(capsule_id, version="1.0.0")
        self._layer = "L1"

        # 策略管理
        self._strategies: dict[StrategyType, StrategyConfig] = {}
        self._signal_weights: dict[str, float] = {}
        self._lock = threading.Lock()

        # 历史表现
        self._performance_history: dict[str, list[float]] = {}

        # 默认策略
        self._default_strategy = StrategyType.TREND

    # ========================================
    # 【看】观察阶段
    # ========================================

    def observe_phase(self) -> dict[str, Any]:
        """【看】观察阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "market_data": {
                    "type": "dict",
                    "source": "MarketCapsule",
                },
                "signals": {
                    "type": "list",
                    "source": "SignalCapsule",
                },
                "performance": {
                    "type": "dict",
                    "format": "{strategy: {win_rate, sharpe, ...}}",
                },
            },
            "outputs": {
                "selected_signals": {
                    "type": "list",
                    "description": "融合后的信号",
                },
                "strategy_weights": {
                    "type": "dict",
                    "description": "策略权重",
                },
            },
            "constraints": {
                "max_strategies": 5,
                "min_confidence": 0.5,
                "rebalance_interval": "1小时",
            },
            "dependencies": ["SignalCapsule", "MarketCapsule", "MonitorCapsule"],
            "risks": [
                {"type": "策略冲突", "mitigation": "信号融合+优先级"},
                {"type": "策略失效", "mitigation": "动态权重调整"},
            ],
            "subscribes_to": ["signal.generated", "position.closed"],
            "publishes": ["brain.decision", "brain.weight_update"],
        }

    # ========================================
    # 【画】设计阶段
    # ========================================

    def design_phase(self) -> dict[str, Any]:
        """【画】设计阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "add_strategy(type, config)": "添加策略",
                "remove_strategy(type)": "移除策略",
                "update_weight(strategy, weight)": "更新权重",
                "fuse_signals(signals)": "融合信号",
                "get_active_strategies()": "获取活跃策略",
            },
            "input_schema": {
                "signals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "signal_type": {"type": "string"},
                            "confidence": {"type": "number"},
                            "strategy": {"type": "string"},
                        },
                    },
                }
            },
            "output_schema": {
                "fused_signal": {
                    "type": "object",
                    "properties": {
                        "signal_type": {"type": "string"},
                        "confidence": {"type": "number"},
                        "reason": {"type": "string"},
                    },
                }
            },
            "fusion_rules": {
                "vote": "多数投票",
                "weighted_average": "加权平均",
                "priority": "优先级选择",
            },
        }

    # ========================================
    # 【填】实现阶段
    # ========================================

    def implement_phase(self) -> None:
        """【填】实现阶段"""
        # 默认策略
        self.add_strategy(
            StrategyType.TREND,
            StrategyConfig(
                strategy_type=StrategyType.TREND,
                enabled=True,
                weight=0.4,
                parameters={"lookback": 20},
            ),
        )
        self.add_strategy(
            StrategyType.MEAN_REVERSION,
            StrategyConfig(
                strategy_type=StrategyType.MEAN_REVERSION,
                enabled=True,
                weight=0.3,
                parameters={"period": 14},
            ),
        )
        self.add_strategy(
            StrategyType.BREAKOUT,
            StrategyConfig(
                strategy_type=StrategyType.BREAKOUT,
                enabled=True,
                weight=0.3,
                parameters={"threshold": 0.02},
            ),
        )
        self._logger.info(f"{self._capsule_id} 实现阶段完成")

    # ========================================
    # 【验】验证阶段
    # ========================================

    def verify_phase(self) -> dict[str, Any]:
        """【验】验证阶段"""
        enabled_count = sum(1 for s in self._strategies.values() if s.enabled)
        return {
            "capsule_id": self._capsule_id,
            "phase": "verify",
            "passed": enabled_count > 0,
            "checks": {
                "strategies_configured": len(self._strategies) > 0,
                "strategies_enabled": enabled_count > 0,
                "weights_sum": abs(sum(s.weight for s in self._strategies.values()) - 1.0) < 0.01,
            },
        }

    # ========================================
    # 【连】集成阶段
    # ========================================

    def integrate_phase(self) -> None:
        """【连】集成阶段"""
        self._logger.info(f"{self._capsule_id} 集成阶段完成")
        self._logger.info("  上游: SignalCapsule, MarketCapsule")
        self._logger.info("  下游: RiskCapsule")

    # ========================================
    # 标准生命周期
    # ========================================

    def init(self) -> None:
        """初始化"""
        self.subscribe("signal.generated", self._on_signal)
        self._initialized = True

    def exec(self) -> dict[str, Any]:
        """执行"""
        with self._lock:
            return {
                "active_strategies": [
                    {"type": s.strategy_type.value, "weight": s.weight, "enabled": s.enabled}
                    for s in self._strategies.values()
                    if s.enabled
                ],
            }

    def shutdown(self) -> None:
        """关闭"""
        self._strategies.clear()
        self._performance_history.clear()

    # ========================================
    # 公开 API
    # ========================================

    def add_strategy(self, strategy_type: StrategyType, config: StrategyConfig) -> None:
        """添加策略"""
        with self._lock:
            self._strategies[strategy_type] = config

    def remove_strategy(self, strategy_type: StrategyType) -> bool:
        """移除策略"""
        with self._lock:
            if strategy_type in self._strategies:
                del self._strategies[strategy_type]
                return True
            return False

    def update_weight(self, strategy_type: StrategyType, weight: float) -> bool:
        """更新策略权重"""
        with self._lock:
            if strategy_type not in self._strategies:
                return False
            self._strategies[strategy_type].weight = weight
            self.publish("brain.weight_update", {"strategy": strategy_type.value, "weight": weight})
            return True

    def fuse_signals(self, signals: list[dict]) -> dict | None:
        """融合信号"""
        if not signals:
            return None

        # 加权投票
        weighted_votes = {"long": 0.0, "short": 0.0, "hold": 0.0}

        for signal in signals:
            signal_type = signal.get("signal_type", "hold")
            confidence = signal.get("confidence", 0.5)
            strategy = signal.get("strategy", "default")

            weight = self._signal_weights.get(strategy, 1.0)

            if signal_type in weighted_votes:
                weighted_votes[signal_type] += confidence * weight

        # 选择最高权重
        best_signal = max(weighted_votes.items(), key=lambda x: x[1])

        if best_signal[1] > 0:
            return {
                "signal_type": best_signal[0],
                "confidence": min(best_signal[1] / len(signals), 1.0),
                "reason": f"融合{len(signals)}个信号",
                "votes": weighted_votes,
            }

        return {"signal_type": "hold", "confidence": 0.5, "reason": "无明确信号"}

    def get_active_strategies(self) -> list[StrategyConfig]:
        """获取活跃策略"""
        with self._lock:
            return [s for s in self._strategies.values() if s.enabled]

    # ========================================
    # 内部方法
    # ========================================

    def _on_signal(self, signal: dict) -> None:
        """处理信号"""
        symbol = signal.get("symbol")

        # 记录性能
        if symbol:
            if symbol not in self._performance_history:
                self._performance_history[symbol] = []
            self._performance_history[symbol].append(signal.get("confidence", 0))

            # 动态调整权重
            self._adjust_weights(symbol)

        # 发布决策
        self.publish("brain.decision", signal)

    def _adjust_weights(self, symbol: str) -> None:
        """动态调整权重"""
        if symbol not in self._performance_history:
            return

        history = self._performance_history[symbol]
        if len(history) < 10:
            return

        # 最近10次表现
        recent = history[-10:]
        avg_performance = sum(recent) / len(recent)

        # 简单调整
        for strategy in self._strategies.values():
            if strategy.strategy_type == StrategyType.TREND:
                strategy.weight = 0.4 + (avg_performance - 0.5) * 0.2
            elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
                strategy.weight = 0.3 + (0.5 - avg_performance) * 0.1
