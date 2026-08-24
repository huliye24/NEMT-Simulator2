"""
SignalNode - 信号节点

基于 CapsuleNode 的信号生成节点
"""

import threading
import uuid
from datetime import datetime
from typing import Any

from nemt.core.capsule_node import (
    ConstraintSchema,
    FractalCapsuleNode,
    PortSchema,
)


class SignalNode(FractalCapsuleNode):
    """
    SignalNode - 信号生成胶囊节点

    职责：
    - 接收市场数据 (OHLCV)
    - 生成交易信号 (LONG/SHORT/NEUTRAL)
    - 计算置信度
    - 发布信号事件

    AI 可直接读取：
    - state: 当前状态
    - signals: 当前有效信号
    - export_json(): 导出完整状态
    """

    # ═══════════════════════════════════════════════════════════════════════════════
    # 节点身份
    # ═══════════════════════════════════════════════════════════════════════════════
    NODE_ID = "signal_node"
    NODE_NAME = "Signal Generation Node"
    NODE_VERSION = "1.0.0"

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输入端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    INPUT_PORTS = [
        PortSchema(
            name="ohlcv",
            data_type="object",
            required=True,
            description="Market OHLCV data",
            properties={
                "symbol": {"type": "string"},
                "open": {"type": "number"},
                "high": {"type": "number"},
                "low": {"type": "number"},
                "close": {"type": "number"},
                "volume": {"type": "number"},
                "timestamp": {"type": "integer"},
            },
            required_fields=["symbol", "close"],
        ),
        PortSchema(
            name="market_phase",
            data_type="string",
            required=True,
            description="Detected market phase",
            enum_values=["UNKNOWN", "TREND_UP", "TREND_DOWN", "RANGE", "VOLATILE"],
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输出端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    OUTPUT_PORTS = [
        PortSchema(
            name="signal",
            data_type="object",
            required=True,
            description="Trading signal",
            properties={
                "signal_id": {"type": "string"},
                "symbol": {"type": "string"},
                "direction": {"type": "string", "enum": ["LONG", "SHORT", "NEUTRAL"]},
                "signal_type": {"type": "string", "enum": ["ENTRY", "EXIT", "STOP_LOSS", "TAKE_PROFIT"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "entry_price": {"type": "number"},
                "stop_loss": {"type": "number"},
                "take_profit": {"type": "number"},
                "timestamp": {"type": "integer"},
            },
            required_fields=["signal_id", "symbol", "direction", "confidence"],
        ),
        PortSchema(
            name="signals_summary",
            data_type="object",
            required=False,
            description="Summary of all active signals",
            properties={
                "total_signals": {"type": "integer"},
                "long_signals": {"type": "integer"},
                "short_signals": {"type": "integer"},
                "avg_confidence": {"type": "number"},
            },
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 约束 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    CONSTRAINTS = [
        ConstraintSchema(
            name="min_confidence",
            constraint_type="validation",
            value=0.6,
            description="Minimum confidence threshold",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="max_signals_per_symbol",
            constraint_type="runtime",
            value=5,
            description="Maximum concurrent signals per symbol",
            min_value=1,
            max_value=20,
        ),
        ConstraintSchema(
            name="signal_ttl_seconds",
            constraint_type="runtime",
            value=300,
            description="Signal time-to-live",
            min_value=60,
            max_value=3600,
        ),
        ConstraintSchema(
            name="risk_per_trade",
            constraint_type="immutable",
            value=0.02,
            description="Risk per trade (2%)",
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 初始化
    # ═══════════════════════════════════════════════════════════════════════════════

    def __init__(self, node_id: str = "signal_node"):
        super().__init__(node_id)

        # 内部状态
        self._signals: dict[str, list[dict]] = {}  # symbol -> signals
        self._signal_history: list[dict] = []
        self._lock = threading.Lock()

        # 策略参数
        self._rsi_period = 14
        self._rsi_overbought = 70
        self._rsi_oversold = 30
        self._ma_short = 10
        self._ma_long = 20

    # ═══════════════════════════════════════════════════════════════════════════════
    # 处理实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _process_impl(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        生成交易信号

        Args:
            inputs = {
                "ohlcv": {...},
                "market_phase": "RANGE"
            }

        Returns:
            {
                "signal": {...},
                "signals_summary": {...}
            }
        """
        ohlcv = inputs.get("ohlcv")
        market_phase = inputs.get("market_phase", "UNKNOWN")

        if not ohlcv:
            raise ValueError("Missing required input: ohlcv")

        symbol = ohlcv["symbol"]
        close_price = ohlcv["close"]

        # 计算信号
        direction, confidence = self._calculate_signal(ohlcv, market_phase)

        # 生成信号
        signal = {
            "signal_id": f"sig_{uuid.uuid4().hex[:8]}",
            "symbol": symbol,
            "direction": direction,
            "signal_type": "ENTRY",
            "confidence": confidence,
            "entry_price": close_price,
            "stop_loss": self._calculate_stop_loss(close_price, direction),
            "take_profit": self._calculate_take_profit(close_price, direction),
            "timestamp": int(datetime.now().timestamp()),
            "market_phase": market_phase,
        }

        # 只保留高于阈值的信号
        min_confidence = self.get_config("min_confidence", 0.6)
        if confidence < min_confidence:
            signal["direction"] = "NEUTRAL"
            signal["signal_type"] = "EXIT"

        # 存储信号
        with self._lock:
            if symbol not in self._signals:
                self._signals[symbol] = []
            self._signals[symbol].append(signal)
            self._signal_history.append(signal)

            # 限制每 symbol 的信号数量
            max_signals = self.get_config("max_signals_per_symbol", 5)
            if len(self._signals[symbol]) > max_signals:
                self._signals[symbol] = self._signals[symbol][-max_signals:]

        # 生成摘要
        summary = self._generate_summary()

        return {
            "signal": signal,
            "signals_summary": summary,
        }

    def _calculate_signal(self, ohlcv: dict, market_phase: str) -> tuple:
        """
        计算交易信号

        使用简单策略：
        - RSI > 70 -> SHORT
        - RSI < 30 -> LONG
        - MA10 > MA20 -> LONG
        - MA10 < MA20 -> SHORT

        Returns:
            (direction, confidence)
        """
        close = ohlcv["close"]
        high = ohlcv.get("high", close)
        low = ohlcv.get("low", close)

        # 模拟 RSI 计算
        rsi = self._calculate_rsi(ohlcv)

        # 模拟 MA 计算
        ma10 = close * 0.99  # 简化
        ma20 = close * 0.98  # 简化

        # 趋势信号
        if ma10 > ma20:
            ma_direction = 1  # LONG
        elif ma10 < ma20:
            ma_direction = -1  # SHORT
        else:
            ma_direction = 0

        # RSI 信号
        if rsi > self._rsi_overbought:
            rsi_direction = -1  # SHORT
        elif rsi < self._rsi_oversold:
            rsi_direction = 1  # LONG
        else:
            rsi_direction = 0

        # 结合市场相位
        if market_phase == "TREND_UP":
            if ma_direction == 1:
                direction = "LONG"
                confidence = 0.7 + (rsi_direction == 1 and 0.15 or 0)
            elif ma_direction == -1:
                direction = "SHORT"
                confidence = 0.4  # 逆势
            else:
                direction = "NEUTRAL"
                confidence = 0.5
        elif market_phase == "TREND_DOWN":
            if ma_direction == -1:
                direction = "SHORT"
                confidence = 0.7 + (rsi_direction == -1 and 0.15 or 0)
            elif ma_direction == 1:
                direction = "LONG"
                confidence = 0.4  # 逆势
            else:
                direction = "NEUTRAL"
                confidence = 0.5
        elif market_phase == "RANGE":
            # 区间震荡，RSI 更重要
            if rsi_direction != 0:
                direction = "LONG" if rsi_direction == 1 else "SHORT"
                confidence = 0.6
            else:
                direction = "NEUTRAL"
                confidence = 0.5
        else:  # VOLATILE
            direction = "NEUTRAL"
            confidence = 0.4

        # 调整置信度
        confidence = max(0.1, min(0.95, confidence))

        return direction, confidence

    def _calculate_rsi(self, ohlcv: dict) -> float:
        """模拟 RSI 计算"""
        close = ohlcv["close"]
        # 简化：用价格变化模拟 RSI
        # 实际应该用历史数据计算
        change = (close - ohlcv.get("open", close)) / ohlcv.get("open", close)

        # 映射到 0-100
        rsi = 50 + change * 500
        return max(0, min(100, rsi))

    def _calculate_stop_loss(self, price: float, direction: str) -> float:
        """计算止损"""
        risk = self.get_config("risk_per_trade", 0.02)
        if direction == "LONG":
            return price * (1 - risk)
        elif direction == "SHORT":
            return price * (1 + risk)
        return price

    def _calculate_take_profit(self, price: float, direction: str) -> float:
        """计算止盈"""
        reward = self.get_config("risk_per_trade", 0.02) * 2
        if direction == "LONG":
            return price * (1 + reward)
        elif direction == "SHORT":
            return price * (1 - reward)
        return price

    def _generate_summary(self) -> dict:
        """生成信号摘要"""
        with self._lock:
            total = sum(len(sigs) for sigs in self._signals.values())
            longs = sum(1 for sigs in self._signals.values() for s in sigs if s["direction"] == "LONG")
            shorts = sum(1 for sigs in self._signals.values() for s in sigs if s["direction"] == "SHORT")
            confidences = [s["confidence"] for sigs in self._signals.values() for s in sigs]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0

            return {
                "total_signals": total,
                "long_signals": longs,
                "short_signals": shorts,
                "avg_confidence": round(avg_conf, 4),
            }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 五阶段实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _observe_phase_impl(self) -> dict[str, Any]:
        """观察阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "ohlcv": {"type": "object", "source": "market_node"},
                "market_phase": {"type": "string", "source": "market_node"},
            },
            "outputs": {
                "signal": {"type": "object", "destination": "risk_node"},
                "signals_summary": {"type": "object", "destination": "brain_node"},
            },
            "constraints": {
                "min_confidence": {"value": 0.6},
                "max_signals_per_symbol": {"value": 5},
                "risk_per_trade": {"value": 0.02},
            },
            "dependencies": ["market_node"],
            "risks": [
                {"type": "假信号", "mitigation": "高置信度阈值"},
                {"type": "信号延迟", "mitigation": "实时计算"},
            ],
        }

    def _design_phase_impl(self) -> dict[str, Any]:
        """设计阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "run(inputs)": "Generate trading signal",
                "get_signal(symbol)": "Get latest signal for symbol",
                "get_all_signals()": "Get all active signals",
            },
            "internal_structure": {
                "_signals": "Dict[str, List[Dict]] - 信号缓存",
                "_signal_history": "List[Dict] - 信号历史",
            },
            "event_contracts": {
                "publishes": ["signal.generated", "signal.updated"],
                "subscribes": ["market.ohlcv", "market.phase"],
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 公开 API
    # ═══════════════════════════════════════════════════════════════════════════════

    def get_signal(self, symbol: str) -> dict | None:
        """获取最新信号"""
        with self._lock:
            signals = self._signals.get(symbol, [])
            return signals[-1] if signals else None

    def get_all_signals(self) -> list[dict]:
        """获取所有信号"""
        with self._lock:
            result = []
            for sigs in self._signals.values():
                result.extend(sigs)
            return result

    def clear_signals(self, symbol: str | None = None) -> None:
        """清除信号"""
        with self._lock:
            if symbol:
                self._signals.pop(symbol, None)
            else:
                self._signals.clear()
                self._signal_history.clear()
