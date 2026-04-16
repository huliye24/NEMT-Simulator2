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
RSI (Relative Strength Index) 相对强弱指标
"""
from typing import List, Optional
import numpy as np


class RSI:
    def __init__(self, period: int = 14):
        self.period = period
        self.values: List[float] = []
        self._gains: List[float] = []
        self._losses: List[float] = []

    def update(self, price: float) -> Optional[float]:
        """更新价格，返回 RSI 值"""
        self.values.append(price)

        if len(self.values) < 2:
            return None

        # 计算价格变动
        delta = self.values[-1] - self.values[-2]
        gain = max(delta, 0)
        loss = max(-delta, 0)

        self._gains.append(gain)
        self._losses.append(loss)

        if len(self._gains) < self.period:
            return None

        # 只需要保留最近 period 个数据
        if len(self._gains) > self.period:
            self._gains.pop(0)
            self._losses.pop(0)

        # 计算平均增益和损失
        avg_gain = np.mean(self._gains)
        avg_loss = np.mean(self._losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def get_signal(self) -> str:
        """获取交易信号"""
        if len(self.values) < self.period:
            return "neutral"

        rsi = self.values[-1]  # 使用最新 RSI 值
        if rsi < 30:
            return "oversold"   # 超卖，可能买入
        elif rsi > 70:
            return "overbought" # 超买，可能卖出
        return "neutral"
