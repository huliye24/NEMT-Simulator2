"""
NEMT Platform - Signal Service
信号服务

职责：
- 订阅市场 K线数据
- 计算 DCI、Vortex、共振指标
- 生成交易信号
"""

import asyncio
from dataclasses import dataclass

from ..base import BaseService
from ..common.types import EventTypes


@dataclass
class Signal:
    """交易信号"""

    signal_type: str  # 'long', 'short', 'neutral'
    confidence: float  # 0.0 - 1.0
    symbol: str
    indicators: dict[str, float]
    timestamp: float


class SignalService(BaseService):
    """
    Signal Service

    订阅事件：
    - market.bar: K线数据

    发布事件：
    - signal.generated: 新信号
    - signal.confidence_update: 置信度变化
    """

    def __init__(self):
        super().__init__("signal", port=8002)

        # 指标参数
        self._dci_period: int = 14
        self._vortex_period: int = 14
        self._resonance_period: int = 20

        # K线数据缓存
        self._bars: dict[str, list[dict]] = {}
        self._max_bars: int = 100

        # 指标缓存
        self._indicators: dict[str, dict[str, float]] = {}

        # 信号统计
        self._signal_count: int = 0
        self._last_signal_type: str = "neutral"

    async def on_init(self):
        """初始化"""
        self.logger.info("Signal Service 初始化中...")

        # 设置默认参数
        self._dci_period = 14
        self._vortex_period = 14
        self._resonance_period = 20

        self.logger.info("Signal Service 初始化完成")

    async def on_start(self):
        """启动"""
        self.logger.info("Signal Service 启动中...")

        # 订阅市场数据
        self.subscribe(EventTypes.MARKET_BAR, self._on_market_bar)

        self.logger.info("Signal Service 启动完成")

    async def on_market_bar(self, data: dict):
        """处理 K线数据"""
        symbol = data.get("symbol")
        if not symbol:
            return

        # 添加到缓存
        if symbol not in self._bars:
            self._bars[symbol] = []

        self._bars[symbol].append(data)

        if len(self._bars[symbol]) > self._max_bars:
            self._bars[symbol].pop(0)

        # 计算指标
        await self._calculate_indicators(symbol)

        # 生成信号
        await self._generate_signal(symbol, data)

    async def _on_market_bar(self, data: dict):
        """处理市场 K线事件"""
        await self.on_market_bar(data)

    async def _calculate_indicators(self, symbol: str):
        """计算指标"""
        bars = self._bars.get(symbol, [])

        if len(bars) < 2:
            return

        # DCI
        self._indicators[symbol] = {
            "dci": self._calc_dci(bars),
            "vortex": self._calc_vortex(bars),
            "resonance": self._calc_resonance(bars),
        }

    def _calc_dci(self, bars: list[dict]) -> float:
        """计算 DCI"""
        period = min(self._dci_period, len(bars))
        bars = bars[-period:]

        up_moves = 0
        down_moves = 0

        for i in range(1, len(bars)):
            prev_close = bars[i - 1].get("price", 0)
            curr_close = bars[i].get("price", 0)

            if curr_close > prev_close:
                up_moves += 1
            elif curr_close < prev_close:
                down_moves += 1

        total = up_moves + down_moves
        if total == 0:
            return 0.0

        return ((up_moves - down_moves) / total) * 100

    def _calc_vortex(self, bars: list[dict]) -> float:
        """计算 Vortex"""
        period = min(self._vortex_period, len(bars))
        bars = bars[-period:]

        up_sum = 0.0
        down_sum = 0.0

        for i in range(1, len(bars)):
            prev_high = bars[i - 1].get("price", 0) * 1.002
            curr_low = bars[i].get("price", 0) * 0.998
            prev_low = bars[i - 1].get("price", 0) * 0.998
            curr_high = bars[i].get("price", 0) * 1.002

            up_move = abs(curr_high - prev_low)
            down_move = abs(curr_low - prev_high)

            up_sum += up_move
            down_sum += down_move

        total = up_sum + down_sum
        if total == 0:
            return 0.5

        return up_sum / total

    def _calc_resonance(self, bars: list[dict]) -> float:
        """计算共振"""
        indicators = self._indicators.get(bars[0].get("symbol", ""), {})

        dci = abs(indicators.get("dci", 0)) / 100
        vortex = indicators.get("vortex", 0.5)

        return (dci + vortex) / 2

    async def _generate_signal(self, symbol: str, bar: dict):
        """生成信号"""
        indicators = self._indicators.get(symbol, {})

        dci = indicators.get("dci", 0)
        vortex = indicators.get("vortex", 0.5)

        # 置信度
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

        # 只有信号变化才发布
        if signal_type != self._last_signal_type or confidence > 0.8:
            self._signal_count += 1
            self._last_signal_type = signal_type

            signal = Signal(
                signal_type=signal_type,
                confidence=confidence,
                symbol=symbol,
                indicators=indicators,
                timestamp=bar.get("timestamp", 0),
            )

            await self.publish(
                EventTypes.SIGNAL_GENERATED,
                {
                    "signal": signal.signal_type,
                    "confidence": signal.confidence,
                    "symbol": signal.symbol,
                    "indicators": signal.indicators,
                    "timestamp": signal.timestamp,
                },
            )

    def _calculate_confidence(self, dci: float, vortex: float) -> float:
        """计算置信度"""
        # DCI 置信度
        dci_confidence = min(abs(dci) / 50, 1.0)

        # Vortex 置信度
        vortex_confidence = abs(vortex - 0.5) * 2

        # 共振置信度
        resonance = self._calc_resonance(list(self._bars.values())[0] if self._bars else [])
        resonance_confidence = resonance

        # 综合
        confidence = dci_confidence * 0.4 + vortex_confidence * 0.3 + resonance_confidence * 0.3

        return min(confidence, 1.0)

    async def get_status(self) -> dict:
        """获取状态"""
        return {
            "signal_count": self._signal_count,
            "last_signal_type": self._last_signal_type,
            "indicators": self._indicators.copy(),
            "bars_count": sum(len(b) for b in self._bars.values()),
        }


async def main():
    """入口"""
    service = SignalService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
