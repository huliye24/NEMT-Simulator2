#!/usr/bin/env python3
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
数据转换器 - 语义压缩与格式转换
================================
负责不同数据格式之间的转换，以及"语义压缩"（将原始数据转换为摘要）

核心功能:
1. 数据格式转换 (JSON ↔ CSV ↔ DataFrame ↔ MATLAB 矩阵)
2. 语义压缩 (将大量原始数据转换为有意义的摘要)
3. 时间序列对齐
4. 数据验证与清洗

使用方式:
    from transformers.data_transformer import DataTransformer
    transformer = DataTransformer()
    summary = transformer.compress_to_summary(raw_data)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import numpy as np

from ..config import config

logger = logging.getLogger(__name__)


# ============================================================================
# 数据类型枚举
# ============================================================================
class DataType(Enum):
    """数据类型"""
    PRICE = "price"           # 价格数据
    KLINE = "kline"          # K线数据
    TRADE = "trade"          # 交易记录
    SIGNAL = "signal"         # 交易信号
    NEMT_RESULT = "nemt_result"  # NEMT分析结果


# ============================================================================
# 语义压缩结果
# ============================================================================
@dataclass
class SemanticSummary:
    """
    语义压缩结果 - 将原始数据转换为有意义的摘要
    =============================================

    这是协议转换的关键组件：
    - 不要把原始数据全丢给 AI
    - 让转换器先处理成"摘要"（例如："回测夏普比率 2.1，最大回撤 5%"）
    - 再通过 MCP 传递给 Notion 记录
    """
    # 原始数据指纹
    data_hash: str = ""
    data_points: int = 0
    time_range: Tuple[str, str] = ("", "")

    # 核心统计
    mean: float = 0.0
    std: float = 0.0
    min: float = 0.0
    max: float = 0.0

    # 收益率统计
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0

    # 分布特征
    skewness: float = 0.0
    kurtosis: float = 0.0

    # NEMT 特有指标
    nemt_spectral_width: float = 0.0
    nemt_mean_frequency: float = 0.0
    nemt_resonance_peaks: int = 0

    # 自然语言描述
    narrative: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'data_hash': self.data_hash,
            'data_points': self.data_points,
            'time_range': {'start': self.time_range[0], 'end': self.time_range[1]},
            'statistics': {
                'mean': round(self.mean, 4),
                'std': round(self.std, 4),
                'min': round(self.min, 4),
                'max': round(self.max, 4),
            },
            'returns': {
                'total': round(self.total_return, 4),
                'annualized': round(self.annualized_return, 4),
                'volatility': round(self.volatility, 4),
            },
            'distribution': {
                'skewness': round(self.skewness, 4),
                'kurtosis': round(self.kurtosis, 4),
            },
            'nemt': {
                'spectral_width': round(self.nemt_spectral_width, 6),
                'mean_frequency': round(self.nemt_mean_frequency, 6),
                'resonance_peaks': self.nemt_resonance_peaks,
            },
            'narrative': self.narrative,
        }

    def to_notion_text(self) -> str:
        """转换为 Notion 可读文本"""
        return f"""
📊 数据摘要

数据点数: {self.data_points:,}
时间范围: {self.time_range[0]} ~ {self.time_range[1]}

📈 统计指标
- 均值: {self.mean:.4f}
- 标准差: {self.std:.4f}
- 范围: [{self.min:.4f}, {self.max:.4f}]

💰 收益分析
- 总收益率: {self.total_return:.2%}
- 年化收益率: {self.annualized_return:.2%}
- 波动率: {self.volatility:.2%}

📐 分布特征
- 偏度: {self.skewness:.4f} {'(右偏)' if self.skewness > 0 else '(左偏)'}
- 峰度: {self.kurtosis:.4f} {'(尖峰)' if self.kurtosis > 3 else '(平坦)'}

⚡ NEMT 分析
- 谱宽: {self.nemt_spectral_width:.6f}
- 平均频率: {self.nemt_mean_frequency:.6f}
- 共振峰: {self.nemt_resonance_peaks}

📝 自动解读
{self.narrative}
"""


# ============================================================================
# 数据转换器主类
# ============================================================================
class DataTransformer:
    """
    数据转换器 - 协议转换的核心转换层
    ===================================

    功能:
    1. 格式转换 (JSON ↔ CSV ↔ DataFrame ↔ MATLAB)
    2. 语义压缩 (大数据 → 有意义摘要)
    3. 数据验证
    4. 时间序列处理

    使用流程:
    1. 加载数据: transformer.load_klines(data)
    2. 验证: transformer.validate()
    3. 转换: transformer.to_matlab_format()
    4. 压缩: transformer.compress()
    """

    def __init__(self):
        self.raw_data: Optional[List[Dict]] = None
        self.close_prices: Optional[np.ndarray] = None
        self.summary: Optional[SemanticSummary] = None

    # =========================================================================
    # 数据加载
    # =========================================================================
    def load_from_json(self, filepath: str) -> bool:
        """从 JSON 文件加载数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)

            if isinstance(self.raw_data, dict):
                self.raw_data = [self.raw_data]
            elif isinstance(self.raw_data, list) and len(self.raw_data) > 0:
                pass

            self._extract_close_prices()
            logger.info(f"📂 从 JSON 加载了 {len(self.raw_data)} 条数据")
            return True

        except Exception as e:
            logger.error(f"加载 JSON 失败: {e}")
            return False

    def load_from_csv(self, filepath: str) -> bool:
        """从 CSV 文件加载数据"""
        try:
            import csv

            data = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append({
                        'timestamp': row.get('timestamp', row.get('time', '')),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'close': float(row.get('close', 0)),
                        'volume': float(row.get('volume', 0)),
                    })

            self.raw_data = data
            self._extract_close_prices()
            logger.info(f"📂 从 CSV 加载了 {len(self.raw_data)} 条数据")
            return True

        except Exception as e:
            logger.error(f"加载 CSV 失败: {e}")
            return False

    def load_klines(self, klines: List[Dict]) -> bool:
        """
        加载 K线数据

        Args:
            klines: K线数据列表，格式: [{'open':..., 'high':..., 'low':..., 'close':..., 'volume':...}, ...]
        """
        if not klines:
            logger.error("K线数据为空")
            return False

        self.raw_data = klines
        self._extract_close_prices()
        logger.info(f"📊 加载了 {len(klines)} 条 K线数据")
        return True

    def load_prices(self, prices: Union[List[float], np.ndarray]) -> bool:
        """加载纯价格数据"""
        if isinstance(prices, list):
            prices = np.array(prices)

        self.close_prices = prices
        self.raw_data = [{'close': float(p)} for p in prices]
        logger.info(f"📊 加载了 {len(prices)} 个价格数据")
        return True

    def _extract_close_prices(self):
        """从原始数据提取收盘价"""
        if not self.raw_data:
            return

        closes = []
        for item in self.raw_data:
            if 'close' in item:
                closes.append(float(item['close']))
            elif 'c' in item:
                closes.append(float(item['c']))

        self.close_prices = np.array(closes) if closes else None

    # =========================================================================
    # 数据验证
    # =========================================================================
    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证数据完整性

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        if not self.raw_data:
            errors.append("数据为空")
            return False, errors

        # 检查数据点数
        if len(self.raw_data) < 10:
            errors.append(f"数据点太少: {len(self.raw_data)} < 10")

        # 检查缺失值
        if self.close_prices is not None:
            nan_count = np.isnan(self.close_prices).sum()
            if nan_count > 0:
                errors.append(f"存在 {nan_count} 个 NaN 值")

            inf_count = np.isinf(self.close_prices).sum()
            if inf_count > 0:
                errors.append(f"存在 {inf_count} 个 Inf 值")

        # 检查价格异常
        if self.close_prices is not None and len(self.close_prices) > 0:
            price_changes = np.abs(np.diff(self.close_prices) / self.close_prices[:-1])
            max_change = np.max(price_changes)

            if max_change > 0.5:  # 单日涨跌超过 50%
                errors.append(f"存在异常价格波动: {max_change:.2%}")

        return len(errors) == 0, errors

    def clean(self) -> bool:
        """清洗数据 (移除 NaN/Inf)"""
        if self.close_prices is None:
            return False

        # 移除 NaN 和 Inf
        valid_mask = np.isfinite(self.close_prices)
        self.close_prices = self.close_prices[valid_mask]

        # 同步清洗原始数据
        if self.raw_data:
            self.raw_data = [r for r, v in zip(self.raw_data, valid_mask) if v]

        removed = len(valid_mask) - len(self.close_prices)
        if removed > 0:
            logger.info(f"🧹 清洗了 {removed} 个无效数据点")

        return True

    # =========================================================================
    # 格式转换
    # =========================================================================
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.raw_data, indent=2, ensure_ascii=False)

    def to_csv(self) -> str:
        """转换为 CSV 字符串"""
        if not self.raw_data:
            return ""

        lines = ["timestamp,open,high,low,close,volume"]
        for item in self.raw_data:
            ts = item.get('timestamp', '')
            o = item.get('open', item.get('o', 0))
            h = item.get('high', item.get('h', 0))
            l = item.get('low', item.get('l', 0))
            c = item.get('close', item.get('c', 0))
            v = item.get('volume', item.get('v', 0))
            lines.append(f"{ts},{o},{h},{l},{c},{v}")

        return "\n".join(lines)

    def to_numpy(self) -> np.ndarray:
        """转换为 numpy 数组"""
        return self.close_prices if self.close_prices is not None else np.array([])

    def to_matlab_matrix(self) -> str:
        """
        转换为 MATLAB 矩阵格式

        Returns:
            MATLAB 代码字符串，可直接在 MATLAB 中执行
        """
        if self.close_prices is None or len(self.close_prices) == 0:
            return ""

        # 转换为 MATLAB 可读的格式
        values_str = " ".join(f"{v:.6f}" for v in self.close_prices)

        return f"""
% 价格数据 (Python → MATLAB)
% 数据点数: {len(self.close_prices)}
priceData = [{values_str}];
priceData = priceData(:);

% 验证
fprintf('加载 %d 个价格数据\\n', length(priceData));
fprintf('价格范围: [%.4f, %.4f]\\n', min(priceData), max(priceData));
"""

    def to_dataframe(self) -> List[Dict]:
        """转换为 DataFrame 兼容格式"""
        if not self.raw_data:
            return []

        return [
            {
                'timestamp': item.get('timestamp', i),
                'close': float(item.get('close', 0)),
                'returns': float(item.get('close', 0)) / float(self.raw_data[i-1].get('close', 1)) - 1 if i > 0 else 0,
            }
            for i, item in enumerate(self.raw_data)
        ]

    # =========================================================================
    # 语义压缩
    # =========================================================================
    def compute_statistics(self) -> Dict[str, float]:
        """计算基础统计指标"""
        if self.close_prices is None or len(self.close_prices) == 0:
            return {}

        stats = {
            'count': len(self.close_prices),
            'mean': float(np.mean(self.close_prices)),
            'std': float(np.std(self.close_prices)),
            'min': float(np.min(self.close_prices)),
            'max': float(np.max(self.close_prices)),
        }

        # 收益率统计
        returns = np.diff(self.close_prices) / self.close_prices[:-1]
        stats['returns_mean'] = float(np.mean(returns))
        stats['returns_std'] = float(np.std(returns))
        stats['total_return'] = float(self.close_prices[-1] / self.close_prices[0] - 1)
        stats['volatility'] = float(np.std(returns) * np.sqrt(365 * 24 * 60))  # 年化波动率

        # 分布特征
        if len(returns) > 2:
            stats['skewness'] = float(self._compute_skewness(returns))
            stats['kurtosis'] = float(self._compute_kurtosis(returns))

        return stats

    def _compute_skewness(self, data: np.ndarray) -> float:
        """计算偏度"""
        if len(data) < 3:
            return 0.0
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return np.mean(((data - mean) / std) ** 3)

    def _compute_kurtosis(self, data: np.ndarray) -> float:
        """计算峰度"""
        if len(data) < 4:
            return 0.0
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return np.mean(((data - mean) / std) ** 4) - 3

    def compress_to_summary(self, nemt_result: Dict = None) -> SemanticSummary:
        """
        语义压缩 - 将原始数据转换为有意义的摘要
        =======================================

        这是 AI 友好的数据格式：
        - 大幅减少 token 消耗
        - 突出关键信息
        - 便于 AI 理解和决策
        """
        summary = SemanticSummary()

        # 基础统计
        stats = self.compute_statistics()
        if not stats:
            summary.narrative = "数据无效，无法生成摘要"
            return summary

        # 原始数据指纹
        import hashlib
        if self.close_prices is not None:
            summary.data_hash = hashlib.md5(
                self.close_prices[:100].tobytes()
            ).hexdigest()[:8]
        summary.data_points = stats.get('count', 0)

        # 核心统计
        summary.mean = stats.get('mean', 0)
        summary.std = stats.get('std', 0)
        summary.min = stats.get('min', 0)
        summary.max = stats.get('max', 0)

        # 收益统计
        summary.total_return = stats.get('total_return', 0)
        summary.annualized_return = stats.get('total_return', 0) * 365  # 简化估算
        summary.volatility = stats.get('volatility', 0)

        # 分布特征
        summary.skewness = stats.get('skewness', 0)
        summary.kurtosis = stats.get('kurtosis', 0)

        # NEMT 结果
        if nemt_result:
            summary.nemt_spectral_width = nemt_result.get('spectral_width', 0)
            summary.nemt_mean_frequency = nemt_result.get('mean_frequency', 0)
            summary.nemt_resonance_peaks = len(nemt_result.get('resonance_peaks', []))

        # 自动生成自然语言描述
        summary.narrative = self._generate_narrative(summary)

        self.summary = summary
        return summary

    def _generate_narrative(self, summary: SemanticSummary) -> str:
        """生成自然语言描述"""
        narratives = []

        # 整体描述
        if summary.total_return > 0:
            narratives.append(f"该数据段累计收益率为 {summary.total_return:.2%}，整体呈现{'强劲' if summary.total_return > 0.1 else ''}上涨趋势")
        else:
            narratives.append(f"该数据段累计收益率为 {summary.total_return:.2%}，整体呈现下跌趋势")

        # 波动性描述
        if summary.volatility > 0.5:
            narratives.append("波动性较高（年化超过 50%），属于高风险资产")
        elif summary.volatility > 0.2:
            narratives.append("波动性适中，适合中等风险偏好的投资者")
        else:
            narratives.append("波动性较低，市场相对平稳")

        # 分布特征
        if summary.skewness > 0.5:
            narratives.append("收益率分布右偏，存在正向黑天鹅风险")
        elif summary.skewness < -0.5:
            narratives.append("收益率分布左偏，存在负向黑天鹅风险")
        else:
            narratives.append("收益率分布相对对称")

        # NEMT 分析
        if summary.nemt_resonance_peaks > 0:
            narratives.append(f"NEMT 分析检测到 {summary.nemt_resonance_peaks} 个共振峰，表明市场存在周期性信号")
        if summary.nemt_spectral_width > 0:
            narratives.append(f"谱宽为 {summary.nemt_spectral_width:.4f}，{'市场相干性较弱' if summary.nemt_spectral_width > 0.1 else '市场相干性较强'}")

        return "；".join(narratives)

    # =========================================================================
    # 时间序列处理
    # =========================================================================
    def resample(self, interval: str) -> bool:
        """
        重采样 (改变时间粒度)

        Args:
            interval: 目标间隔 ('1m', '5m', '15m', '1h', '1d')
        """
        if not self.raw_data:
            return False

        # 简化的重采样逻辑
        multiplier = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '1d': 1440,
        }.get(interval, 1)

        if multiplier == 1 or len(self.raw_data) < multiplier:
            return False

        # 简化：取每组的最后一个值
        resampled = []
        for i in range(0, len(self.raw_data), multiplier):
            group = self.raw_data[i:i+multiplier]
            if group:
                resampled.append(group[-1])

        self.raw_data = resampled
        self._extract_close_prices()
        logger.info(f"📊 重采样为 {interval}：{len(resampled)} 条数据")
        return True

    def trim(self, start_idx: int = 0, end_idx: int = None) -> bool:
        """裁剪数据"""
        if not self.raw_data:
            return False

        end_idx = end_idx or len(self.raw_data)
        self.raw_data = self.raw_data[start_idx:end_idx]
        self._extract_close_prices()
        logger.info(f"✂️ 裁剪数据: {start_idx} ~ {end_idx}")
        return True


# ============================================================================
# 便捷函数
# ============================================================================
def transform_prices(prices: List[float], to_format: str = "numpy") -> Any:
    """快速转换价格数据"""
    transformer = DataTransformer()
    transformer.load_prices(prices)

    if to_format == "numpy":
        return transformer.to_numpy()
    elif to_format == "json":
        return transformer.to_json()
    elif to_format == "matlab":
        return transformer.to_matlab_matrix()
    else:
        return transformer.raw_data


def compress_result(result: Dict) -> str:
    """快速压缩分析结果为摘要"""
    transformer = DataTransformer()
    summary = transformer.compress_to_summary(result)
    return summary.to_notion_text()


# ============================================================================
# 单元测试
# ============================================================================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # 生成测试数据
    t = np.linspace(0, 10 * np.pi, 500)
    prices = 50000 + 1000 * np.sin(t) + 500 * np.random.randn(500)

    # 测试转换
    transformer = DataTransformer()
    transformer.load_prices(prices)

    # 验证
    valid, errors = transformer.validate()
    print(f"数据验证: {'✅ 通过' if valid else '❌ 失败'}")
    if errors:
        for e in errors:
            print(f"  - {e}")

    # 语义压缩
    summary = transformer.compress_to_summary()
    print(f"\n📝 语义摘要:")
    print(summary.to_notion_text())

    # 转换为 MATLAB
    matlab_code = transformer.to_matlab_matrix()
    print(f"\n📤 MATLAB 代码 (前200字符):")
    print(matlab_code[:200] + "...")
