"""
市场数据提供者工厂 (Market Provider Factory)
统一管理多种数据源，提供便捷的实例化接口
"""

from typing import Optional, List, Dict, Any, Union
from enum import Enum

from .base import BaseMarketProvider, KLine, MarketData
from .mock_provider import MockMarketProvider
from .binance_provider import BinanceMarketProvider, BinanceKlinesIterator
from .csv_provider import CSVFileProvider, CSVConfig, load_csv_data


class ProviderType(Enum):
    """数据提供者类型枚举"""

    MOCK = "mock"
    BINANCE = "binance"
    CSV = "csv"


class MarketProviderFactory:
    """
    市场数据提供者工厂

    提供统一的接口来创建和管理各种数据源:
    - Mock: 测试用模拟数据
    - Binance: 真实交易所API
    - CSV: 本地CSV文件

    使用示例:
        # 创建Binance提供者
        provider = MarketProviderFactory.create(
            ProviderType.BINANCE,
            symbols=['BTCUSDT', 'ETHUSDT']
        )

        # 创建CSV提供者
        provider = MarketProviderFactory.create(
            ProviderType.CSV,
            filepath='data/btc.csv',
            auto_watch=True
        )

        # 使用提供者
        provider.connect()
        klines = provider.get_history('BTCUSDT', '1h', limit=100)
        provider.disconnect()
    """

    # 提供者类型映射
    _provider_classes = {
        ProviderType.MOCK: MockMarketProvider,
        ProviderType.BINANCE: BinanceMarketProvider,
        ProviderType.CSV: CSVFileProvider,
    }

    @classmethod
    def create(cls, provider_type: Union[str, ProviderType], **kwargs) -> BaseMarketProvider:
        """
        创建数据提供者

        Args:
            provider_type: 提供者类型 (字符串或枚举)
            **kwargs: 传递给提供者的参数

        Returns:
            BaseMarketProvider 实例

        Raises:
            ValueError: 无效的提供者类型
        """
        # 转换字符串到枚举
        if isinstance(provider_type, str):
            try:
                provider_type = ProviderType(provider_type.lower())
            except ValueError:
                valid_types = [t.value for t in ProviderType]
                raise ValueError(f"Invalid provider type: {provider_type}. " f"Valid types: {valid_types}")

        # 获取提供者类
        provider_class = cls._provider_classes.get(provider_type)
        if provider_class is None:
            raise ValueError(f"Unknown provider type: {provider_type}")

        return provider_class(**kwargs)

    @classmethod
    def create_mock(
        cls,
        name: str = "MockProvider",
        symbols: Optional[List[str]] = None,
        base_prices: Optional[Dict[str, float]] = None,
        volatility: float = 0.002,
    ) -> MockMarketProvider:
        """创建Mock提供者"""
        return cls.create(ProviderType.MOCK, name=name, symbols=symbols, base_prices=base_prices, volatility=volatility)

    @classmethod
    def create_binance(
        cls, name: str = "BinanceProvider", symbols: Optional[List[str]] = None, default_interval: str = "1h"
    ) -> BinanceMarketProvider:
        """创建Binance提供者"""
        return cls.create(ProviderType.BINANCE, name=name, symbols=symbols, default_interval=default_interval)

    @classmethod
    def create_csv(
        cls,
        filepath: str,
        name: str = "CSVProvider",
        symbol: str = "DEFAULT",
        auto_watch: bool = False,
        datetime_format: Optional[str] = None,
    ) -> CSVFileProvider:
        """创建CSV提供者"""
        config = CSVConfig(filepath=filepath, default_symbol=symbol, datetime_format=datetime_format)
        return cls.create(ProviderType.CSV, name=name, config=config, auto_watch=auto_watch)

    @classmethod
    def register_provider(cls, provider_type: Union[str, ProviderType], provider_class: type) -> None:
        """
        注册自定义提供者

        Args:
            provider_type: 提供者类型标识
            provider_class: 提供者类（必须是 BaseMarketProvider 的子类）
        """
        if isinstance(provider_type, str):
            provider_type = ProviderType(provider_type.lower())

        if not issubclass(provider_class, BaseMarketProvider):
            raise TypeError("Provider class must be a subclass of BaseMarketProvider")

        cls._provider_classes[provider_type] = provider_class

    @classmethod
    def list_providers(cls) -> List[str]:
        """列出所有可用的提供者类型"""
        return [t.value for t in cls._provider_classes.keys()]


class MarketDataSource:
    """
    市场数据源管理器

    统一管理多个数据源，支持:
    - 主数据源和备用数据源
    - 自动切换
    - 数据同步
    """

    def __init__(self, primary: BaseMarketProvider, fallback: Optional[BaseMarketProvider] = None):
        """
        Args:
            primary: 主数据源
            fallback: 备用数据源
        """
        self.primary = primary
        self.fallback = fallback
        self._active: BaseMarketProvider = primary

    def connect(self) -> bool:
        """连接数据源"""
        if self.primary.connect():
            self._active = self.primary
            return True

        if self.fallback and self.fallback.connect():
            self._active = self.fallback
            return True

        return False

    def disconnect(self) -> None:
        """断开所有数据源"""
        self.primary.disconnect()
        if self.fallback:
            self.fallback.disconnect()

    def get_latest(self, symbol: str, interval: str = "1h") -> Optional[KLine]:
        """获取最新K线"""
        return self._active.get_latest(symbol, interval)

    def get_history(
        self, symbol: str, interval: str = "1h", limit: int = 100, start_time=None, end_time=None
    ) -> List[KLine]:
        """获取历史K线"""
        return self._active.get_history(symbol, interval, limit, start_time, end_time)

    def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """获取实时行情"""
        return self._active.get_ticker(symbol)

    @property
    def active_provider(self) -> BaseMarketProvider:
        """获取当前活动的数据源"""
        return self._active

    def switch_to_primary(self) -> bool:
        """切换到主数据源"""
        if self.primary.is_connected:
            self._active = self.primary
            return True
        return False

    def switch_to_fallback(self) -> bool:
        """切换到备用数据源"""
        if self.fallback and self.fallback.is_connected:
            self._active = self.fallback
            return True
        return False


# 便捷函数
def create_data_source(source_type: str = "mock", **kwargs) -> BaseMarketProvider:
    """
    创建数据源的便捷函数

    Args:
        source_type: 源类型 ('mock', 'binance', 'csv')
        **kwargs: 其他参数

    Returns:
        数据提供者实例
    """
    return MarketProviderFactory.create(source_type, **kwargs)


def create_multi_source(primary_type: str = "mock", fallback_type: Optional[str] = None, **kwargs) -> MarketDataSource:
    """
    创建多数据源

    Args:
        primary_type: 主数据源类型
        fallback_type: 备用数据源类型
        **kwargs: 其他参数

    Returns:
        MarketDataSource 实例
    """
    primary = MarketProviderFactory.create(primary_type, **kwargs.get("primary", {}))
    fallback = None

    if fallback_type:
        fallback = MarketProviderFactory.create(fallback_type, **kwargs.get("fallback", {}))

    return MarketDataSource(primary, fallback)


def create_market_layer(
    data_source: str = "csv",
    filepath: str = None,
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    days: int = 30,
    **kwargs,
):
    """
    创建配置好的 MarketLayer

    Args:
        data_source: 数据源类型 ('csv', 'binance', 'mock')
        filepath: CSV文件路径 (用于csv类型)
        symbol: 交易对
        interval: K线周期
        days: 数据天数
        **kwargs: 其他参数

    Returns:
        配置好的 MarketLayer 实例
    """
    from nemt.market import MarketLayer, MarketConfig

    config = MarketConfig(name=symbol, default_symbol=symbol, default_interval=interval)
    market_layer = MarketLayer(config=config)

    if data_source == "csv" and filepath:
        market_layer.load_from_csv(filepath)

    elif data_source == "binance":
        provider = MarketProviderFactory.create_binance(symbols=[symbol], default_interval=interval)
        market_layer.load_from_provider(provider, symbol=symbol, interval=interval, days=days)

    elif data_source == "mock":
        provider = MarketProviderFactory.create_mock(symbols=[symbol])
        provider.connect()
        # 生成模拟数据并加载
        klines = provider.get_history(symbol, interval, limit=min(days * 24, 1000))
        import pandas as pd
        from datetime import datetime

        data = []
        for k in klines:
            ts = k.timestamp if hasattr(k.timestamp, "timestamp") else datetime.fromtimestamp(k.timestamp)
            data.append(
                {
                    "timestamp": ts,
                    "open": k.open,
                    "high": k.high,
                    "low": k.low,
                    "close": k.close,
                    "volume": k.volume,
                }
            )

        if data:
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
            market_layer.data = df

    return market_layer
