"""
SignalCapsule - 信号胶囊

生成交易信号:
- DCI 指标计算
- 趋势信号
- 共振检测
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ["SignalCapsule"]


@dataclass
class Signal:
    """交易信号"""

    signal_type: str  # 'long', 'short', 'neutral'
    confidence: float  # 0.0 - 1.0
    symbol: str
    indicators: Dict[str, float]
    timestamp: float


class SignalCapsule(ModuleCapsule):
    """
    信号胶囊

    订阅事件:
    - market.bar: K线数据

    发布事件:
    - nemt.signal: 生成交易信号
    """

    def __init__(self):
        super().__init__("signal")

        # 指标参数
        self._dci_period: int = 14
        self._vortex_period: int = 14
        self._resonance_period: int = 20

        # K线数据缓存
        self._bars: List[Dict[str, Any]] = []
        self._max_bars: int = 100

        # 指标缓存
        self._indicators: Dict[str, float] = {}

        # 信号统计
        self._signal_count: int = 0
        self._last_signal_type: str = "neutral"

    def init(self) -> None:
        """初始化"""
        # 从配置加载参数
        self._dci_period = self.get_config("signal.dci.period", 14)
        self._vortex_period = self.get_config("signal.vortex.period", 14)
        self._resonance_period = self.get_config("signal.resonance.period", 20)

        # 订阅事件
        self.subscribe("market.bar", self._on_bar)

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回信号状态

        Returns:
            信号状态字典
        """
        return {
            "signal_count": self._signal_count,
            "last_signal_type": self._last_signal_type,
            "indicators": self._indicators.copy(),
            "bars_count": len(self._bars),
        }

    def _on_bar(self, event: Event) -> None:
        """处理 K线数据"""
        bar = event.data

        if not bar:
            return

        # 添加到缓存
        self._bars.append(bar)
        if len(self._bars) > self._max_bars:
            self._bars.pop(0)

        # 计算指标
        self._calculate_indicators()

        # 生成信号
        signal = self._generate_signal(bar)

        if signal:
            self._signal_count += 1
            self._last_signal_type = signal.signal_type

            # 发布信号事件
            self.publish(
                "nemt.signal",
                {
                    "signal": signal.signal_type,
                    "confidence": signal.confidence,
                    "symbol": signal.symbol,
                    "indicators": signal.indicators,
                    "timestamp": signal.timestamp,
                },
            )

    def _calculate_indicators(self) -> None:
        """计算指标"""
        if len(self._bars) < 2:
            return

        # DCI (Directional Change Indicator)
        self._indicators["dci"] = self._calc_dci()

        # Vortex
        self._indicators["vortex"] = self._calc_vortex()

        # 共振
        self._indicators["resonance"] = self._calc_resonance()

    def _calc_dci(self) -> float:
        """
        计算 DCI (Directional Change Indicator)

        DCI 范围: -100 到 +100
        +100: 强烈上涨
        -100: 强烈下跌
        0: 中性
        """
        if len(self._bars) < self._dci_period:
            return 0.0

        bars = self._bars[-self._dci_period :]

        # 计算方向变化
        up_moves = 0
        down_moves = 0

        for i in range(1, len(bars)):
            prev_close = bars[i - 1].get("close", 0)
            curr_close = bars[i].get("close", 0)

            if curr_close > prev_close:
                up_moves += 1
            elif curr_close < prev_close:
                down_moves += 1

        total = up_moves + down_moves
        if total == 0:
            return 0.0

        # DCI = (上涨比例 - 下跌比例) * 100
        dci = ((up_moves - down_moves) / total) * 100

        return dci

    def _calc_vortex(self) -> float:
        """
        计算 Vortex 指标

        Vortex 范围: 0 到 1
        > 0.5: 上涨趋势
        < 0.5: 下跌趋势
        """
        if len(self._bars) < self._vortex_period:
            return 0.5

        bars = self._bars[-self._vortex_period :]

        # 简化计算
        up_sum = 0
        down_sum = 0

        for i in range(1, len(bars)):
            prev_high = bars[i - 1].get("high", 0)
            curr_low = bars[i].get("low", 0)
            prev_low = bars[i - 1].get("low", 0)
            curr_high = bars[i].get("high", 0)

            up_move = abs(curr_high - prev_low)
            down_move = abs(curr_low - prev_high)

            up_sum += up_move
            down_sum += down_move

        total = up_sum + down_sum
        if total == 0:
            return 0.5

        return up_sum / total

    def _calc_resonance(self) -> float:
        """
        计算共振指标

        共振范围: 0 到 1
        多个指标方向一致时接近 1
        """
        dci = abs(self._indicators.get("dci", 0)) / 100
        vortex = self._indicators.get("vortex", 0.5)

        # 简化为两个指标的乘积
        resonance = (dci + vortex) / 2

        return resonance

    def _generate_signal(self, bar: Dict[str, Any]) -> Optional[Signal]:
        """
        生成交易信号

        Args:
            bar: 当前 K线

        Returns:
            Signal 或 None
        """
        dci = self._indicators.get("dci", 0)
        vortex = self._indicators.get("vortex", 0.5)

        # 置信度计算
        confidence = self._calculate_confidence(dci, vortex)

        # 信号类型
        if confidence > 0.6:
            if dci > 0 and vortex > 0.5:
                signal_type = "long"
            elif dci < 0 and vortex < 0.5:
                signal_type = "short"
            else:
                signal_type = "neutral"
        else:
            signal_type = "neutral"

        return Signal(
            signal_type=signal_type,
            confidence=confidence,
            symbol=bar.get("symbol", "BTC"),
            indicators=self._indicators.copy(),
            timestamp=bar.get("timestamp", self._get_time()),
        )

    def _calculate_confidence(self, dci: float, vortex: float) -> float:
        """
        计算信号置信度

        Args:
            dci: DCI 值
            vortex: Vortex 值

        Returns:
            置信度 0.0 - 1.0
        """
        # DCI 置信度 (0-1)
        dci_confidence = min(abs(dci) / 50, 1.0)

        # Vortex 置信度 (0-1)
        vortex_confidence = abs(vortex - 0.5) * 2

        # 共振置信度
        resonance = self._indicators.get("resonance", 0.5)
        resonance_confidence = resonance

        # 综合置信度
        confidence = dci_confidence * 0.4 + vortex_confidence * 0.3 + resonance_confidence * 0.3

        return min(confidence, 1.0)

    @staticmethod
    def _get_time() -> float:
        """获取当前时间"""
        import time

        return time.time()

    def shutdown(self) -> None:
        """关闭"""
        self.unsubscribe("market.bar", self._on_bar)
