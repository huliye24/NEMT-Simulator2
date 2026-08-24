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
Bollinger Bands 布林带指标
"""
from typing import List, Optional, Tuple
import numpy as np


class BollingerBands:
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
        self.prices: List[float] = []
        
    def update(self, price: float) -> Optional[Tuple[float, float, float]]:
        """
        更新价格，返回 (上轨, 中轨, 下轨)
        """
        self.prices.append(price)
        
        if len(self.prices) < self.period:
            return None
        
        if len(self.prices) > self.period:
            self.prices.pop(0)
        
        middle = np.mean(self.prices)
        std = np.std(self.prices)
        
        upper = middle + (std * self.std_dev)
        lower = middle - (std * self.std_dev)
        
        return (round(upper, 2), round(middle, 2), round(lower, 2))
    
    def get_position(self, price: float) -> str:
        """获取价格相对于布林带的位置"""
        if len(self.prices) < self.period:
            return "neutral"
        
        bands = self.update(price)
        if bands is None:
            return "neutral"
        
        upper, middle, lower = bands
        
        if price > upper:
            return "above_upper"    # 突破上轨，强势
        elif price < lower:
            return "below_lower"    # 突破下轨，超卖
        elif price > middle:
            return "upper_half"     # 在中轨上方
        else:
            return "lower_half"     # 在中轨下方
