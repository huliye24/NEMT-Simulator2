"""
NEMT 市场数据抽象层 (Market Provider Layer)
提供统一的市场数据接口，支持多种数据源切换
"""

from .base import BaseMarketProvider, MarketData, KLine
from .mock_provider import MockMarketProvider, DeterministicMockProvider
from .binance_provider import BinanceMarketProvider, BinanceKlinesIterator, fetch_binance_data, stream_binance_realtime
from .csv_provider import CSVFileProvider, CSVConfig, load_csv_data, create_csv_provider
from .factory import (
    ProviderType,
    MarketProviderFactory,
    MarketDataSource,
    create_data_source,
    create_multi_source,
    create_market_layer,
)

__all__ = [
    # 基础类
    "BaseMarketProvider",
    "MarketData",
    "KLine",
    # 提供者类型
    "ProviderType",
    # Mock提供者
    "MockMarketProvider",
    "DeterministicMockProvider",
    # Binance提供者
    "BinanceMarketProvider",
    "BinanceKlinesIterator",
    "fetch_binance_data",
    "stream_binance_realtime",
    # CSV提供者
    "CSVFileProvider",
    "CSVConfig",
    "load_csv_data",
    "create_csv_provider",
    # 工厂
    "MarketProviderFactory",
    "MarketDataSource",
    "create_data_source",
    "create_multi_source",
    "create_market_layer",
]
