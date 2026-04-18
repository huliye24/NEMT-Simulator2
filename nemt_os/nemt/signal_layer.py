"""
NEMT 信号层 (Signal Layer)
把市场数据转化为可交易信号，提供决策原材料
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """信号类型"""
    TREND = "TREND"                   # 趋势信号
    MEAN_REVERSION = "MEAN_REVERSION" # 均值回归信号
    MOMENTUM = "MOMENTUM"            # 动量信号
    VOLATILITY = "VOLATILITY"         # 波动率信号


@dataclass
class Signal:
    """交易信号"""
    name: str
    signal_type: SignalType
    direction: int  # 1: 多头, -1: 空头, 0: 中性
    strength: float  # 0-100
    confidence: float  # 0-1
    price: float
    timestamp: pd.Timestamp

    def is_strong(self, threshold: float = 70.0) -> bool:
        """判断是否为强信号"""
        return self.strength >= threshold

    def is_bullish(self) -> bool:
        """是否为多头信号"""
        return self.direction > 0

    def is_bearish(self) -> bool:
        """是否为空头信号"""
        return self.direction < 0


class SignalLayer:
    """
    信号生成层

    核心功能：
    1. 计算各类技术指标
    2. 生成标准化交易信号
    3. 信号质量评估
    4. 信号过滤和聚合
    """

    def __init__(self):
        self.signals: List[Signal] = []
        self.indicators_cache: Dict[str, float] = {}

    def reset(self):
        """重置信号"""
        self.signals = []
        self.indicators_cache = {}

    def calculate_indicators(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        volumes: np.ndarray
    ) -> Dict[str, float]:
        """
        计算所有技术指标

        Returns:
            dict: 指标名称 -> 值
        """
        if len(closes) < 2:
            return {}

        indicators = {}

        # 移动平均线
        indicators['sma_5'] = self._sma(closes, 5)
        indicators['sma_10'] = self._sma(closes, 10)
        indicators['sma_20'] = self._sma(closes, 20)
        indicators['sma_50'] = self._sma(closes, 50)

        # 指数移动平均
        indicators['ema_12'] = self._ema(closes, 12)
        indicators['ema_26'] = self._ema(closes, 26)

        # RSI
        indicators['rsi'] = self._rsi(closes, 14)

        # MACD
        macd, signal, hist = self._macd(closes)
        indicators['macd'] = macd
        indicators['macd_signal'] = signal
        indicators['macd_hist'] = hist

        # ATR
        indicators['atr'] = self._atr(highs, lows, closes, 14)

        # 布林带
        indicators['bb_upper'], indicators['bb_middle'], indicators['bb_lower'] = self._bollinger_bands(closes)

        # 随机指标
        indicators['stoch_k'], indicators['stoch_d'] = self._stochastic(highs, lows, closes)

        # ADX
        indicators['adx'] = self._adx(highs, lows, closes, 14)

        # 价格动量
        indicators['roc'] = self._roc(closes, 10)
        indicators['momentum'] = self._momentum(closes, 10)

        # 成交量动量
        indicators['volume_ma'] = self._sma(volumes, 20)
        indicators['volume_ratio'] = volumes[-1] / indicators['volume_ma'] if indicators['volume_ma'] > 0 else 1.0

        self.indicators_cache = indicators
        return indicators

    # ==================== 移动平均线 ====================

    def _sma(self, data: np.ndarray, period: int) -> float:
        """简单移动平均"""
        if len(data) < period:
            return data[-1] if len(data) > 0 else 0.0
        return float(np.mean(data[-period:]))

    def _ema(self, data: np.ndarray, period: int) -> float:
        """指数移动平均"""
        if len(data) < period:
            return data[-1] if len(data) > 0 else 0.0

        multiplier = 2 / (period + 1)
        ema = np.mean(data[:period])

        for price in data[period:]:
            ema = (price - ema) * multiplier + ema

        return float(ema)

    # ==================== RSI ====================

    def _rsi(self, data: np.ndarray, period: int = 14) -> float:
        """相对强弱指数"""
        if len(data) < period + 1:
            return 50.0

        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    # ==================== MACD ====================

    def _macd(self, data: np.ndarray, fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[float, float, float]:
        """MACD指标"""
        if len(data) < slow:
            return 0.0, 0.0, 0.0

        ema_fast = self._ema(data, fast)
        ema_slow = self._ema(data, slow)
        macd_line = ema_fast - ema_slow

        # Signal line (简化计算)
        macd_history = []
        for i in range(slow, len(data)):
            ef = self._ema(data[:i+1], fast)
            es = self._ema(data[:i+1], slow)
            macd_history.append(ef - es)

        if len(macd_history) >= signal_period:
            signal_line = np.mean(macd_history[-signal_period:])
        else:
            signal_line = macd_line

        histogram = macd_line - signal_line

        return float(macd_line), float(signal_line), float(histogram)

    # ==================== ATR ====================

    def _atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """平均真实波幅"""
        if len(closes) < 2:
            return 0.0

        high = highs[-period:]
        low = lows[-period:]
        close = closes[-period:]

        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))[1:]
        tr3 = np.abs(low - np.roll(close, 1))[1:]

        tr = np.maximum(tr1[1:], np.maximum(tr2, tr3))
        atr = np.mean(tr) if len(tr) > 0 else 0.0

        return float(atr)

    # ==================== 布林带 ====================

    def _bollinger_bands(self, data: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
        """布林带"""
        if len(data) < period:
            return data[-1], data[-1], data[-1]

        middle = np.mean(data[-period:])
        std = np.std(data[-period:])

        upper = middle + std_dev * std
        lower = middle - std_dev * std

        return float(upper), float(middle), float(lower)

    # ==================== 随机指标 ====================

    def _stochastic(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Tuple[float, float]:
        """随机指标 K和D"""
        if len(closes) < period:
            return 50.0, 50.0

        highest_high = np.max(highs[-period:])
        lowest_low = np.min(lows[-period:])
        current_close = closes[-1]

        if highest_high == lowest_low:
            k = 50.0
        else:
            k = (current_close - lowest_low) / (highest_high - lowest_low) * 100

        # %D 是 %K 的3日简单移动平均 (简化)
        d = k  # 简化处理

        return float(k), float(d)

    # ==================== ADX ====================

    def _adx(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """平均趋向指数"""
        if len(closes) < period + 1:
            return 25.0

        # 简化ADX计算
        high_diff = np.diff(highs)
        low_diff = -np.diff(lows)

        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

        atr_val = self._atr(highs, lows, closes, period)

        if atr_val == 0:
            return 25.0

        plus_di = np.mean(plus_dm[-period:]) / atr_val * 100
        minus_di = np.mean(minus_dm[-period:]) / atr_val * 100

        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0

        # 简化ADX
        adx = min(100, dx * 1.5)

        return float(adx)

    # ==================== 动量指标 ====================

    def _roc(self, data: np.ndarray, period: int = 10) -> float:
        """价格变化率"""
        if len(data) < period + 1:
            return 0.0
        return float((data[-1] - data[-period - 1]) / data[-period - 1] * 100)

    def _momentum(self, data: np.ndarray, period: int = 10) -> float:
        """动量指标"""
        if len(data) < period + 1:
            return 0.0
        return float(data[-1] - data[-period - 1])

    # ==================== 信号生成 ====================

    def generate_trend_signal(self, indicators: Dict[str, float], price: float) -> Signal:
        """生成趋势信号"""
        direction = 0
        strength = 0

        # 均线交叉信号
        sma_5 = indicators.get('sma_5', 0)
        sma_20 = indicators.get('sma_20', 0)
        sma_50 = indicators.get('sma_50', 0)

        if sma_5 > sma_20 and sma_20 > sma_50:
            direction = 1
            strength = 70
        elif sma_5 < sma_20 and sma_20 < sma_50:
            direction = -1
            strength = 70

        # MACD确认
        macd_hist = indicators.get('macd_hist', 0)
        if abs(macd_hist) > 0:
            strength = min(100, strength + abs(macd_hist) / price * 10000)

        confidence = min(1.0, strength / 100)

        return Signal(
            name="Trend Signal",
            signal_type=SignalType.TREND,
            direction=direction,
            strength=strength,
            confidence=confidence,
            price=price,
            timestamp=pd.Timestamp.now()
        )

    def generate_mean_reversion_signal(self, indicators: Dict[str, float], price: float) -> Signal:
        """生成均值回归信号"""
        direction = 0
        strength = 0

        # RSI超买超卖
        rsi = indicators.get('rsi', 50)
        bb_upper = indicators.get('bb_upper', price)
        bb_lower = indicators.get('bb_lower', price)
        bb_middle = indicators.get('bb_middle', price)

        # 价格触及布林带下轨，超卖，可能反弹
        if price < bb_lower:
            direction = 1
            strength = min(100, (bb_lower - price) / bb_lower * 1000 + 60)
        # 价格触及布林带上轨，超买，可能回调
        elif price > bb_upper:
            direction = -1
            strength = min(100, (price - bb_upper) / bb_upper * 1000 + 60)
        # RSI超卖
        elif rsi < 30:
            direction = 1
            strength = min(100, (30 - rsi) * 2 + 50)
        # RSI超买
        elif rsi > 70:
            direction = -1
            strength = min(100, (rsi - 70) * 2 + 50)

        confidence = min(1.0, strength / 100)

        return Signal(
            name="Mean Reversion Signal",
            signal_type=SignalType.MEAN_REVERSION,
            direction=direction,
            strength=strength,
            confidence=confidence,
            price=price,
            timestamp=pd.Timestamp.now()
        )

    def generate_momentum_signal(self, indicators: Dict[str, float], price: float) -> Signal:
        """生成动量信号"""
        direction = 0
        strength = 0

        roc = indicators.get('roc', 0)
        rsi = indicators.get('rsi', 50)
        stoch_k = indicators.get('stoch_k', 50)

        # ROC + RSI组合
        if roc > 0 and rsi > 50 and stoch_k > 50:
            direction = 1
            strength = min(100, abs(roc) * 10 + 50)
        elif roc < 0 and rsi < 50 and stoch_k < 50:
            direction = -1
            strength = min(100, abs(roc) * 10 + 50)

        # 随机指标确认
        if direction != 0 and 20 < stoch_k < 80:
            strength = min(100, strength + 10)

        confidence = min(1.0, strength / 100)

        return Signal(
            name="Momentum Signal",
            signal_type=SignalType.MOMENTUM,
            direction=direction,
            strength=strength,
            confidence=confidence,
            price=price,
            timestamp=pd.Timestamp.now()
        )

    def generate_all_signals(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        volumes: np.ndarray,
        price: float,
        timestamp: pd.Timestamp = None
    ) -> List[Signal]:
        """生成所有类型的信号"""
        if timestamp is None:
            timestamp = pd.Timestamp.now()

        indicators = self.calculate_indicators(closes, highs, lows, volumes)

        signals = [
            self.generate_trend_signal(indicators, price),
            self.generate_mean_reversion_signal(indicators, price),
            self.generate_momentum_signal(indicators, price)
        ]

        # 更新时间戳
        for signal in signals:
            signal.timestamp = timestamp

        self.signals = signals
        return signals

    def get_combined_signal(self) -> Optional[Signal]:
        """获取合并后的信号"""
        if not self.signals:
            return None

        # 权重配置
        weights = {
            SignalType.TREND: 0.4,
            SignalType.MEAN_REVERSION: 0.3,
            SignalType.MOMENTUM: 0.3
        }

        total_weight = 0
        weighted_direction = 0
        weighted_strength = 0

        for signal in self.signals:
            w = weights.get(signal.signal_type, 0.25)
            total_weight += w
            weighted_direction += signal.direction * w * signal.strength
            weighted_strength += signal.strength * w

        if total_weight > 0:
            final_direction = 1 if weighted_direction > 500 else (-1 if weighted_direction < -500 else 0)
            final_strength = min(100, weighted_strength / total_weight)
        else:
            final_direction = 0
            final_strength = 0

        return Signal(
            name="Combined Signal",
            signal_type=SignalType.TREND,
            direction=final_direction,
            strength=final_strength,
            confidence=final_strength / 100,
            price=self.signals[0].price if self.signals else 0,
            timestamp=timestamp
        )
