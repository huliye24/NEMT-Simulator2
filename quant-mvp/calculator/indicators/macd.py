# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
MACD (Moving Average Convergence Divergence) 指数平滑异同移动平均线
"""
from typing import List, Optional, Tuple
from .ma import EMA


class MACD:
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast_period = fast
        self.slow_period = slow
        self.signal_period = signal
        
        self.fast_ema = EMA(fast)
        self.slow_ema = EMA(slow)
        self.signal_ema = EMA(signal)
        
        self.macd_line: List[float] = []
        self.signal_line: List[float] = []
        self.histogram: List[float] = []

    def update(self, price: float) -> Optional[Tuple[float, float, float]]:
        """
        更新价格，返回 (MACD线, 信号线, 柱状图)
        """
        fast = self.fast_ema.update(price)
        slow = self.slow_ema.update(price)
        
        if fast is None or slow is None:
            return None
        
        macd = fast - slow
        self.macd_line.append(macd)
        
        sig = self.signal_ema.update(macd)
        if sig is None:
            self.signal_line.append(macd)
        else:
            self.signal_line.append(sig)
        
        if len(self.macd_line) > self.signal_period:
            macd_val = self.macd_line[-1]
            sig_val = self.signal_line[-1]
            hist = macd_val - sig_val
            self.histogram.append(hist)
            
            return (round(macd_val, 4), round(sig_val, 4), round(hist, 4))
        
        return (round(macd, 4), round(macd, 4), 0)

    def get_signal(self) -> str:
        """获取 MACD 信号"""
        if len(self.histogram) < 2:
            return "neutral"
        
        # 金叉：MACD 从下方穿过信号线
        if self.histogram[-1] > 0 and self.histogram[-2] <= 0:
            return "golden_cross"  # 买入信号
        
        # 死叉：MACD 从上方穿过信号线
        if self.histogram[-1] < 0 and self.histogram[-2] >= 0:
            return "death_cross"   # 卖出信号
        
        # 背离检测
        if len(self.macd_line) > 20:
            if self.histogram[-1] > 0 and self.macd_line[-1] < self.macd_line[-5]:
                return "bearish_divergence"  # 顶背离
            if self.histogram[-1] < 0 and self.macd_line[-1] > self.macd_line[-5]:
                return "bullish_divergence"  # 底背离
        
        return "neutral"
