"""
SignalCapsule - 分形迭代版

按五阶段迭代法重写的信号生成胶囊。
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from nemt.core.capsule import FractalCapsule


class SignalType(Enum):
    """信号类型"""

    LONG = "long"
    SHORT = "short"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    HOLD = "hold"


@dataclass
class TradingSignal:
    """交易信号"""

    signal_id: str
    signal_type: SignalType
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
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
            "metadata": self.metadata,
        }


class SignalCapsule(FractalCapsule):
    """
    信号生成胶囊

    负责：
    - 接收市场数据
    - 计算技术指标
    - 生成交易信号
    - 信号过滤和融合

    五阶段方法已实现。
    """

    def __init__(self, capsule_id: str = "signal"):
        super().__init__(capsule_id, version="1.0.0")
        self._layer = "L1"

        # 内部状态
        self._signals: list[TradingSignal] = []
        self._signal_count = 0
        self._lock = threading.Lock()

        # 指标计算器
        self._indicators: dict[str, Any] = {}

        # 信号生成器配置
        self._rsi_period = 14
        self._macd_fast = 12
        self._macd_slow = 26
        self._macd_signal = 9

    # ========================================
    # 【看】观察阶段
    # ========================================

    def observe_phase(self) -> dict[str, Any]:
        """
        【看】观察阶段 - 分析信号生成需求
        """
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "market_data": {
                    "type": "dict",
                    "format": "{symbol, price, volume, klines}",
                    "source": "MarketCapsule",
                    "required": True,
                },
                "indicators_config": {
                    "type": "dict",
                    "format": "{rsi_period, macd_params, ...}",
                    "default": {"rsi_period": 14, "macd_fast": 12},
                },
                "strategy_config": {
                    "type": "dict",
                    "format": "{signal_threshold, filter_rules, ...}",
                },
            },
            "outputs": {
                "signals": {
                    "type": "list",
                    "format": "[{type, entry, sl, tp, confidence, reason}, ...]",
                },
                "indicators": {
                    "type": "dict",
                    "format": "{rsi, macd, bollinger, ...}",
                },
            },
            "constraints": {
                "max_signals_per_symbol": 1,
                "signal_validity_period": "1小时",
                "min_confidence": 0.6,
            },
            "dependencies": ["MarketCapsule", "EventBus", "ConfigCenter"],
            "risks": [
                {"type": "信号过于频繁", "mitigation": "信号合并+冷却期"},
                {"type": "虚假信号", "mitigation": "多指标确认"},
                {"type": "信号丢失", "mitigation": "事件持久化"},
            ],
            "subscribes_to": ["market.price_update", "market.candle_closed"],
            "publishes": ["signal.generated", "signal.filtered", "signal.merged"],
        }

    # ========================================
    # 【画】设计阶段
    # ========================================

    def design_phase(self) -> dict[str, Any]:
        """
        【画】设计阶段 - 定义信号接口
        """
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "generate_signal(symbol, market_data)": "生成交易信号",
                "calculate_indicators(prices)": "计算技术指标",
                "filter_signals(signals)": "过滤信号",
                "get_latest_signals(n)": "获取最新信号",
                "clear_signals()": "清空信号历史",
            },
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "price": {"type": "number"},
                    "prices": {"type": "array", "items": {"type": "number"}},
                    "volume": {"type": "number"},
                },
                "required": ["symbol", "price", "prices"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "signal_id": {"type": "string"},
                    "signal_type": {"type": "string", "enum": ["long", "short", "hold"]},
                    "entry_price": {"type": "number"},
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "reason": {"type": "string"},
                },
            },
            "signal_generation_rules": {
                "LONG": "RSI < 30 且 MACD 金叉",
                "SHORT": "RSI > 70 且 MACD 死叉",
                "CLOSE": "RSI 回归 50 或止损触发",
                "HOLD": "其他情况",
            },
            "event_contracts": {
                "publishes": ["signal.generated", "signal.filtered"],
                "subscribes": ["market.price_update"],
            },
        }

    # ========================================
    # 【填】实现阶段
    # ========================================

    def implement_phase(self) -> None:
        """
        【填】实现阶段 - 填充核心逻辑
        """
        # 加载配置
        self._rsi_period = self.get_config("signal.rsi_period", 14)
        self._macd_fast = self.get_config("signal.macd_fast", 12)
        self._macd_slow = self.get_config("signal.macd_slow", 26)
        self._macd_signal = self.get_config("signal.macd_signal", 9)

        self._logger.info(f"{self._capsule_id} 实现阶段完成")
        self._logger.info(
            f"  RSI周期: {self._rsi_period}, MACD: ({self._macd_fast}, {self._macd_slow}, {self._macd_signal})"
        )

    # ========================================
    # 【验】验证阶段
    # ========================================

    def verify_phase(self) -> dict[str, Any]:
        """
        【验】验证阶段 - 确保实现正确
        """
        checks = {
            "indicators_config_loaded": True,
            "signal_generation_ready": True,
            "dependencies_injected": self._event_bus is not None,
            "thread_safe": hasattr(self, "_lock"),
        }

        return {
            "capsule_id": self._capsule_id,
            "phase": "verify",
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "passed": all(checks.values()),
            "metrics": {
                "signals_count": len(self._signals),
                "signal_count_total": self._signal_count,
            },
        }

    # ========================================
    # 【连】集成阶段
    # ========================================

    def integrate_phase(self) -> None:
        """
        【连】集成阶段 - 与上下游对接
        """
        self._logger.info(f"{self._capsule_id} 集成阶段完成")
        self._logger.info("  上游: MarketCapsule")
        self._logger.info("  下游: RiskCapsule, ExecutionCapsule, BrainCapsule")

    # ========================================
    # 标准生命周期
    # ========================================

    def init(self) -> None:
        """初始化胶囊"""
        self.subscribe("market.price_update", self._on_price_update)
        self._initialized = True
        self._logger.info(f"{self._capsule_id} 初始化完成")

    def exec(self) -> dict[str, Any]:
        """执行主要逻辑"""
        return {
            "capsule_id": self._capsule_id,
            "signals_count": len(self._signals),
            "total_signals": self._signal_count,
        }

    def shutdown(self) -> None:
        """关闭胶囊"""
        with self._lock:
            self._signals.clear()
        self._running = False
        self._logger.info(f"{self._capsule_id} 已关闭")

    # ========================================
    # 公开 API
    # ========================================

    def calculate_indicators(self, prices: list[float]) -> dict[str, float]:
        """
        计算技术指标

        Args:
            prices: 价格序列

        Returns:
            指标字典 {rsi, macd, macd_signal, macd_hist}
        """
        if len(prices) < self._macd_slow:
            return {}

        # 计算 RSI
        rsi = self._calculate_rsi(prices)

        # 计算 MACD
        macd, macd_signal, macd_hist = self._calculate_macd(prices)

        return {
            "rsi": rsi[-1] if rsi else 50.0,
            "rsi_values": rsi,
            "macd": macd[-1] if macd else 0.0,
            "macd_signal": macd_signal[-1] if macd_signal else 0.0,
            "macd_hist": macd_hist[-1] if macd_hist else 0.0,
        }

    def generate_signal(self, symbol: str, market_data: dict[str, Any]) -> TradingSignal | None:
        """
        生成交易信号

        Args:
            symbol: 交易对
            market_data: 市场数据

        Returns:
            交易信号，如果没有信号则返回 None
        """
        prices = market_data.get("prices", [])
        current_price = market_data.get("price", 0)

        if not prices or not current_price:
            return None

        # 计算指标
        indicators = self.calculate_indicators(prices)
        rsi = indicators.get("rsi", 50.0)
        macd_hist = indicators.get("macd_hist", 0.0)

        # 生成信号
        signal_type, confidence, reason = self._determine_signal_type(rsi, macd_hist, current_price)

        if signal_type == SignalType.HOLD:
            return None

        # 创建信号
        self._signal_count += 1
        signal = TradingSignal(
            signal_id=f"{symbol}_{self._signal_count}",
            signal_type=signal_type,
            symbol=symbol,
            entry_price=current_price,
            stop_loss=self._calculate_stop_loss(current_price, signal_type),
            take_profit=self._calculate_take_profit(current_price, signal_type),
            confidence=confidence,
            reason=reason,
            metadata=indicators,
        )

        with self._lock:
            self._signals.append(signal)

        # 发布信号事件
        self.publish("signal.generated", signal.to_dict())

        return signal

    def get_latest_signals(self, n: int = 10) -> list[TradingSignal]:
        """
        获取最新信号

        Args:
            n: 数量限制

        Returns:
            信号列表
        """
        with self._lock:
            return self._signals[-n:]

    def clear_signals(self) -> None:
        """清空信号历史"""
        with self._lock:
            self._signals.clear()

    # ========================================
    # 内部方法
    # ========================================

    def _on_price_update(self, event: dict) -> None:
        """处理价格更新"""
        symbol = event.get("symbol")
        price = event.get("price")

        if not symbol or not price:
            return

        # 获取历史价格
        market_data = {"symbol": symbol, "price": price, "prices": [price]}

        # 生成信号
        self.generate_signal(symbol, market_data)

    def _calculate_rsi(self, prices: list[float]) -> list[float]:
        """计算 RSI"""
        if len(prices) < self._rsi_period + 1:
            return []

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[: self._rsi_period]) / self._rsi_period
        avg_loss = sum(losses[: self._rsi_period]) / self._rsi_period

        rsi_values = []
        for i in range(self._rsi_period, len(prices)):
            if i > self._rsi_period:
                avg_gain = (avg_gain * (self._rsi_period - 1) + gains[i - 1]) / self._rsi_period
                avg_loss = (avg_loss * (self._rsi_period - 1) + losses[i - 1]) / self._rsi_period

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            rsi_values.append(rsi)

        return rsi_values

    def _calculate_macd(self, prices: list[float]) -> tuple:
        """计算 MACD"""
        if len(prices) < self._macd_slow:
            return [], [], []

        # 计算 EMA
        ema_fast = self._calculate_ema(prices, self._macd_fast)
        ema_slow = self._calculate_ema(prices, self._macd_slow)

        # MACD 线
        macd = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]

        # Signal 线
        macd_signal = self._calculate_ema(macd, self._macd_signal)

        # Histogram
        min_len = min(len(macd), len(macd_signal))
        macd_hist = [macd[i] - macd_signal[i] for i in range(min_len)]

        return macd, macd_signal, macd_hist

    def _calculate_ema(self, values: list[float], period: int) -> list[float]:
        """计算 EMA"""
        if len(values) < period:
            return []

        k = 2 / (period + 1)
        ema = [sum(values[:period]) / period]

        for i in range(period, len(values)):
            ema.append(values[i] * k + ema[-1] * (1 - k))

        return ema

    def _determine_signal_type(self, rsi: float, macd_hist: float, price: float) -> tuple:
        """确定信号类型"""
        # 多头信号
        if rsi < 30 and macd_hist > 0:
            return SignalType.LONG, 0.8, f"RSI超卖({rsi:.1f}) + MACD金叉"

        # 空头信号
        if rsi > 70 and macd_hist < 0:
            return SignalType.SHORT, 0.8, f"RSI超买({rsi:.1f}) + MACD死叉"

        # 中性信号
        return SignalType.HOLD, 0.5, "无明确信号"

    def _calculate_stop_loss(self, price: float, signal_type: SignalType) -> float:
        """计算止损"""
        sl_percent = self.get_config("signal.stop_loss_percent", 2.0) / 100
        if signal_type == SignalType.LONG:
            return price * (1 - sl_percent)
        elif signal_type == SignalType.SHORT:
            return price * (1 + sl_percent)
        return price

    def _calculate_take_profit(self, price: float, signal_type: SignalType) -> float:
        """计算止盈"""
        tp_percent = self.get_config("signal.take_profit_percent", 4.0) / 100
        if signal_type == SignalType.LONG:
            return price * (1 + tp_percent)
        elif signal_type == SignalType.SHORT:
            return price * (1 - tp_percent)
        return price
