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
Moving Averages 移动平均线
"""
from typing import List, Optional
import numpy as np


class SMA:
    """Simple Moving Average 简单移动平均"""
    
    def __init__(self, period: int = 20):
        self.period = period
        self.values: List[float] = []

    def update(self, price: float) -> Optional[float]:
        """更新价格，返回 SMA 值"""
        self.values.append(price)
        
        if len(self.values) < self.period:
            return None
        
        if len(self.values) > self.period:
            self.values.pop(0)
        
        return round(np.mean(self.values), 2)


class EMA:
    """Exponential Moving Average 指数移动平均"""
    
    def __init__(self, period: int = 12):
        self.period = period
        self.values: List[float] = []
        self.ema: Optional[float] = None
        self.multiplier = 2 / (period + 1)

    def update(self, price: float) -> Optional[float]:
        """更新价格，返回 EMA 值"""
        self.values.append(price)
        
        if len(self.values) < self.period:
            return None
        
        if len(self.values) > self.period:
            self.values.pop(0)
        
        if self.ema is None:
            # 初始化为 SMA
            self.ema = np.mean(self.values)
        else:
            # EMA = (Price - EMA_prev) * multiplier + EMA_prev
            self.ema = (price - self.ema) * self.multiplier + self.ema
        
        return round(self.ema, 2)

    def get_cross_signal(self, fast_ema: 'EMA', slow_ema: 'EMA') -> str:
        """获取均线交叉信号（需要传入快线和慢线 EMA 实例）"""
        if len(self.values) < 2:
            return "neutral"
        
        # 检查是否有交叉
        prev_fast = None
        prev_slow = None
        
        return "neutral"
