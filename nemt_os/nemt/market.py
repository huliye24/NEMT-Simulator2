"""
NEMT 市场层 (Market Layer)
负责市场数据加载、市场状态感知、品种配置
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass


class MarketState(Enum):
    """市场状态枚举"""
    TRENDING_UP = "TRENDING_UP"       # 趋势上涨
    TRENDING_DOWN = "TRENDING_DOWN"   # 趋势下跌
    RANGING = "RANGING"               # 震荡
    HIGH_VOLATILITY = "HIGH_VOLATILITY"  # 高波动
    LOW_LIQUIDITY = "LOW_LIQUIDITY"   # 低流动性


@dataclass
class MarketConfig:
    """市场配置"""
    name: str = "BTC/USDT"
    volatility_threshold: float = 0.02  # 高波动阈值 (ATR百分比)
    trend_threshold: float = 0.01        # 趋势强度阈值
    liquidity_threshold: float = 0.001   # 低流动性阈值


class MarketLayer:
    """
    市场层：加载数据，感知市场状态

    核心功能：
    1. 加载历史数据
    2. 分割训练/测试集
    3. 检测市场状态
    4. 计算市场指标
    """

    def __init__(self, config: MarketConfig = None):
        self.config = config or MarketConfig()
        self.data: Optional[pd.DataFrame] = None
        self.train_data: Optional[pd.DataFrame] = None
        self.test_data: Optional[pd.DataFrame] = None
        self.current_state: MarketState = MarketState.RANGING

        # 市场指标缓存
        self._indicators_cache = {}

    def load_data(self, filepath: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        加载市场数据

        Args:
            filepath: 数据文件路径
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame: 加载的数据
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"数据文件不存在: {filepath}")

        # 读取CSV
        df = pd.read_csv(path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()

        # 按日期过滤
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        # 数据质量检查
        df = self._validate_data(df)

        self.data = df
        print(f"[OK] Data loaded: {len(df)} records")
        print(f"  Time range: {df.index[0]} ~ {df.index[-1]}")
        print(f"  Data shape: {df.shape}")

        return df

    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据质量验证"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']

        # 检查列是否存在
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"缺少必要的列: {missing_cols}")

        # 检查OHLC逻辑
        invalid_rows = df[(df['high'] < df['low']) |
                         (df['high'] < df['close']) |
                         (df['low'] > df['open']) |
                         (df['volume'] < 0)]

        if len(invalid_rows) > 0:
            print(f"[WARN] Found {len(invalid_rows)} invalid rows, filtered")
            df = df[(df['high'] >= df['low']) &
                   (df['high'] >= df['close']) &
                   (df['low'] <= df['open']) &
                   (df['volume'] >= 0)]

        # 填充缺失值
        df = df.ffill()

        return df

    def split_train_test(self, train_ratio: float = 0.7) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        分割训练集和测试集

        Args:
            train_ratio: 训练集比例

        Returns:
            (train_data, test_data)
        """
        if self.data is None:
            raise ValueError("请先加载数据")

        split_idx = int(len(self.data) * train_ratio)

        self.train_data = self.data.iloc[:split_idx].copy()
        self.test_data = self.data.iloc[split_idx:].copy()

        print(f"[OK] Data split complete")
        print(f"  Train: {len(self.train_data)} bars ({self.train_data.index[0]} ~ {self.train_data.index[-1]})")
        print(f"  Test: {len(self.test_data)} bars ({self.test_data.index[0]} ~ {self.test_data.index[-1]})")

        return self.train_data, self.test_data

    def detect_regime(self, data: pd.DataFrame = None, lookback: int = 20) -> MarketState:
        """
        检测市场状态

        Args:
            data: 数据，默认使用完整数据
            lookback: 回顾周期

        Returns:
            MarketState: 市场状态
        """
        if data is None:
            if self.data is None:
                # 返回默认值，不抛出错误
                return MarketState.RANGING
            data = self.data

        # 计算市场指标
        volatility = self._calculate_volatility(data, lookback)
        trend_strength = self._calculate_trend_strength(data, lookback)
        liquidity = self._calculate_liquidity(data, lookback)

        # 状态判断
        if volatility > self.config.volatility_threshold:
            self.current_state = MarketState.HIGH_VOLATILITY
        elif liquidity < self.config.liquidity_threshold:
            self.current_state = MarketState.LOW_LIQUIDITY
        elif abs(trend_strength) > self.config.trend_threshold:
            if trend_strength > 0:
                self.current_state = MarketState.TRENDING_UP
            else:
                self.current_state = MarketState.TRENDING_DOWN
        else:
            self.current_state = MarketState.RANGING

        # 缓存指标
        self._indicators_cache = {
            'volatility': volatility,
            'trend_strength': trend_strength,
            'liquidity': liquidity
        }

        return self.current_state

    def _calculate_volatility(self, data: pd.DataFrame, lookback: int = 20) -> float:
        """计算波动率 (ATR百分比)"""
        if len(data) < lookback:
            return 0.0

        # 计算 True Range
        high = data['high'].iloc[-lookback:]
        low = data['low'].iloc[-lookback:]
        close = data['close'].iloc[-lookback:]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.mean()

        # 返回ATR与价格的百分比
        current_price = close.iloc[-1]
        return atr / current_price

    def _calculate_trend_strength(self, data: pd.DataFrame, lookback: int = 20) -> float:
        """计算趋势强度 (使用线性回归斜率)"""
        if len(data) < lookback:
            return 0.0

        close_prices = data['close'].iloc[-lookback:].values
        x = np.arange(len(close_prices))

        # 线性回归
        x_mean = x.mean()
        y_mean = close_prices.mean()

        numerator = np.sum((x - x_mean) * (close_prices - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if denominator == 0:
            return 0.0

        slope = numerator / denominator

        # 返回斜率与价格的百分比
        return slope / y_mean

    def _calculate_liquidity(self, data: pd.DataFrame, lookback: int = 20) -> float:
        """计算流动性指标 (成交量变化率)"""
        if len(data) < lookback:
            return 0.0

        volumes = data['volume'].iloc[-lookback:]

        # 使用成交量稳定性作为流动性指标
        # 标准差/均值越小，流动性越稳定
        cv = volumes.std() / volumes.mean() if volumes.mean() > 0 else float('inf')

        # 返回流动性的逆指标 (越小流动性越好)
        return 1.0 / (1.0 + cv)

    def get_current_bar(self, data: pd.DataFrame = None) -> Optional[pd.Series]:
        """获取当前K线"""
        if data is None:
            data = self.data

        if data is None or len(data) == 0:
            return None

        return data.iloc[-1]

    def get_history(self, data: pd.DataFrame = None, n: int = 100) -> pd.DataFrame:
        """获取最近N条K线"""
        if data is None:
            data = self.data

        if data is None or len(data) < n:
            return data if data is not None else pd.DataFrame()

        return data.iloc[-n:]

    def get_market_indicators(self) -> dict:
        """获取市场指标"""
        return self._indicators_cache.copy()


def create_market_layer(
    data_path: str,
    start_date: str = None,
    end_date: str = None,
    train_ratio: float = 0.7
) -> Tuple[MarketLayer, pd.DataFrame, pd.DataFrame]:
    """
    创建市场层的便捷函数

    Returns:
        (market_layer, train_data, test_data)
    """
    market = MarketLayer()

    # 加载数据
    market.load_data(data_path, start_date, end_date)

    # 分割数据
    train_data, test_data = market.split_train_test(train_ratio)

    return market, train_data, test_data
