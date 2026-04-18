"""
NEMT 数据层 (Data Layer)
统一数据入口，为上层提供标准化数据服务
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class OHLCV:
    """K线数据结构"""
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }


@dataclass
class DataQualityReport:
    """数据质量报告"""
    total_records: int
    missing_count: int
    anomaly_count: int
    fill_rate: float
    quality_score: float  # 0-100

    def is_acceptable(self, threshold: float = 80.0) -> bool:
        return self.quality_score >= threshold


class DataLayer:
    """
    数据服务层

    核心功能：
    1. 提供标准化OHLCV数据接口
    2. 数据质量控制
    3. 历史数据查询
    4. 实时数据更新
    """

    def __init__(self, data: pd.DataFrame = None):
        """
        Args:
            data: 初始数据
        """
        self._data: Optional[pd.DataFrame] = data
        self._current_idx: int = 0
        self._quality_report: Optional[DataQualityReport] = None

        if data is not None:
            self._validate_quality()

    @property
    def data(self) -> Optional[pd.DataFrame]:
        return self._data

    @data.setter
    def data(self, value: pd.DataFrame):
        self._data = value
        self._validate_quality()

    def _validate_quality(self):
        """验证数据质量"""
        if self._data is None:
            return

        total = len(self._data)
        missing = self._data.isnull().sum().sum()
        fill_rate = 1 - (missing / (total * len(self._data.columns)))

        # 检测异常值 (使用IQR方法)
        anomaly_count = 0
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in self._data.columns:
                Q1 = self._data[col].quantile(0.25)
                Q3 = self._data[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((self._data[col] < Q1 - 3 * IQR) |
                          (self._data[col] > Q3 + 3 * IQR)).sum()
                anomaly_count += outliers

        # 计算质量分数
        quality_score = min(100, fill_rate * 100 * (1 - anomaly_count / (total * 5)))

        self._quality_report = DataQualityReport(
            total_records=total,
            missing_count=missing,
            anomaly_count=anomaly_count,
            fill_rate=fill_rate,
            quality_score=quality_score
        )

    def get_quality_report(self) -> Optional[DataQualityReport]:
        """获取数据质量报告"""
        return self._quality_report

    def reset(self):
        """重置数据指针"""
        self._current_idx = 0

    def set_position(self, idx: int):
        """设置数据指针位置"""
        if self._data is None:
            raise ValueError("数据未加载")
        if idx < 0 or idx >= len(self._data):
            raise IndexError(f"索引超出范围: {idx}")
        self._current_idx = idx

    def get_current_bar(self) -> Optional[OHLCV]:
        """
        获取当前K线

        Returns:
            OHLCV: 当前K线数据
        """
        if self._data is None or len(self._data) == 0:
            return None

        row = self._data.iloc[self._current_idx]
        return OHLCV(
            timestamp=row.name,
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume']
        )

    def get_history(self, n: int = None) -> pd.DataFrame:
        """
        获取历史数据

        Args:
            n: 获取最近N条，为None时返回全部

        Returns:
            DataFrame: 历史数据
        """
        if self._data is None:
            return pd.DataFrame()

        if n is None:
            return self._data.iloc[:self._current_idx + 1]

        start_idx = max(0, self._current_idx - n + 1)
        return self._data.iloc[start_idx:self._current_idx + 1]

    def get_bar_at(self, idx: int) -> Optional[OHLCV]:
        """获取指定位置的K线"""
        if self._data is None or idx < 0 or idx >= len(self._data):
            return None

        row = self._data.iloc[idx]
        return OHLCV(
            timestamp=row.name,
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume']
        )

    def advance(self) -> bool:
        """
        前进到下一个K线

        Returns:
            bool: 是否还有更多数据
        """
        if self._current_idx < len(self._data) - 1:
            self._current_idx += 1
            return True
        return False

    def get_close_prices(self, n: int = None) -> np.ndarray:
        """获取收盘价序列"""
        if self._data is None:
            return np.array([])

        if n is None:
            return self._data['close'].iloc[:self._current_idx + 1].values

        start_idx = max(0, self._current_idx - n + 1)
        return self._data['close'].iloc[start_idx:self._current_idx + 1].values

    def get_volumes(self, n: int = None) -> np.ndarray:
        """获取成交量序列"""
        if self._data is None:
            return np.array([])

        if n is None:
            return self._data['volume'].iloc[:self._current_idx + 1].values

        start_idx = max(0, self._current_idx - n + 1)
        return self._data['volume'].iloc[start_idx:self._current_idx + 1].values

    def get_highs(self, n: int = None) -> np.ndarray:
        """获取最高价序列"""
        if self._data is None:
            return np.array([])

        if n is None:
            return self._data['high'].iloc[:self._current_idx + 1].values

        start_idx = max(0, self._current_idx - n + 1)
        return self._data['high'].iloc[start_idx:self._current_idx + 1].values

    def get_lows(self, n: int = None) -> np.ndarray:
        """获取最低价序列"""
        if self._data is None:
            return np.array([])

        if n is None:
            return self._data['low'].iloc[:self._current_idx + 1].values

        start_idx = max(0, self._current_idx - n + 1)
        return self._data['low'].iloc[start_idx:self._current_idx + 1].values

    def get_current_price(self) -> float:
        """获取当前价格"""
        if self._data is None or self._current_idx >= len(self._data):
            return 0.0
        return self._data['close'].iloc[self._current_idx]

    def get_current_volume(self) -> float:
        """获取当前成交量"""
        if self._data is None or self._current_idx >= len(self._data):
            return 0.0
        return self._data['volume'].iloc[self._current_idx]

    def get_timestamp(self) -> Optional[pd.Timestamp]:
        """获取当前时间戳"""
        if self._data is None or self._current_idx >= len(self._data):
            return None
        return self._data.index[self._current_idx]

    def __len__(self) -> int:
        """返回数据总长度"""
        return len(self._data) if self._data is not None else 0

    def remaining(self) -> int:
        """返回剩余数据量"""
        if self._data is None:
            return 0
        return len(self._data) - self._current_idx - 1

    def progress(self) -> float:
        """返回当前进度 (0-1)"""
        if self._data is None or len(self._data) == 0:
            return 0.0
        return self._current_idx / (len(self._data) - 1)


class DataService:
    """
    数据服务类
    提供更高级的数据查询功能
    """

    def __init__(self, data_layer: DataLayer):
        self._data_layer = data_layer

    def calculate_returns(self, n: int = 1) -> float:
        """计算收益率"""
        closes = self._data_layer.get_close_prices(n + 1)
        if len(closes) < 2:
            return 0.0
        return (closes[-1] - closes[-2]) / closes[-2]

    def calculate_cumulative_return(self, n: int = None) -> float:
        """计算累计收益率"""
        closes = self._data_layer.get_close_prices(n)
        if len(closes) < 2:
            return 0.0
        return (closes[-1] - closes[0]) / closes[0]

    def get_price_change_pct(self) -> float:
        """获取当前价格变化百分比"""
        closes = self._data_layer.get_close_prices(2)
        if len(closes) < 2:
            return 0.0
        return (closes[-1] - closes[-2]) / closes[-2] * 100
