"""
MarketCapsule - 市场数据胶囊

提供市场数据:
- 数据加载
- 数据回放
- K线生成
- 市场数据提供者集成
"""

from typing import Dict, List, Any, Optional, Callable, Union
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ["MarketCapsule"]


# 延迟导入避免循环依赖
def _get_binance_provider():
    try:
        from nemt.market_providers.binance_provider import BinanceMarketProvider

        return BinanceMarketProvider
    except ImportError:
        return None


class MarketCapsule(ModuleCapsule):
    """
    市场数据胶囊

    发布事件:
    - market.bar: K线数据
    - market.tick: Tick 数据
    - market.backtest_start: 回测开始
    - market.backtest_end: 回测结束
    - market.provider_connected: 提供者已连接
    - market.provider_error: 提供者错误
    """

    def __init__(self, provider=None):
        super().__init__("market")

        # 数据存储
        self._bars: Dict[str, List[Dict[str, Any]]] = {}
        self._ticks: Dict[str, List[Dict[str, Any]]] = {}

        # 配置
        self._symbols: List[str] = ["BTC"]

        # 回测状态
        self._is_backtesting: bool = False
        self._current_index: int = 0

        # 回调
        self._bar_callbacks: List[Callable] = []

        # 市场数据提供者
        self._provider = provider
        self._provider_type: str = "none"

        # 实时数据状态
        self._realtime_enabled: bool = False
        self._realtime_callbacks: List[Callable] = []

    def set_provider(self, provider) -> None:
        """
        设置市场数据提供者

        Args:
            provider: BaseMarketProvider 实例
        """
        # 断开旧提供者
        if self._provider and self._provider.is_connected:
            self._provider.disconnect()

        self._provider = provider
        self._provider_type = getattr(provider, "name", type(provider).__name__)

        # 如果提供者有连接，订阅其数据
        if self._provider and self._provider.is_connected:
            self._setup_provider_subscriptions()

    def get_provider(self):
        """获取当前的市场数据提供者"""
        return self._provider

    def _setup_provider_subscriptions(self) -> None:
        """设置提供者订阅"""
        if not self._provider:
            return

        def on_kline(kline):
            """处理新的K线数据"""
            bar = {
                "symbol": kline.symbol,
                "timestamp": kline.timestamp.timestamp() if hasattr(kline.timestamp, "timestamp") else kline.timestamp,
                "open": kline.open,
                "high": kline.high,
                "low": kline.low,
                "close": kline.close,
                "volume": kline.volume,
            }

            # 存储
            symbol = bar["symbol"]
            if symbol not in self._bars:
                self._bars[symbol] = []
            self._bars[symbol].append(bar)

            # 发布事件
            self.publish("market.bar", bar)

            # 调用回调
            for callback in self._realtime_callbacks:
                try:
                    callback(bar)
                except Exception as e:
                    pass

        # 订阅所有符号
        for symbol in self._symbols:
            self._provider.subscribe(symbol, on_kline)

    def init(self) -> None:
        """初始化"""
        self._symbols = self.get_config("market.symbols", ["BTC"])

        # 初始化数据存储
        for symbol in self._symbols:
            if symbol not in self._bars:
                self._bars[symbol] = []
            if symbol not in self._ticks:
                self._ticks[symbol] = []

    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回市场状态

        Returns:
            市场状态字典
        """
        return {
            "symbols": self._symbols,
            "is_backtesting": self._is_backtesting,
            "current_index": self._current_index,
            "data_count": {symbol: len(self._bars.get(symbol, [])) for symbol in self._symbols},
        }

    def load_data(self, symbol: str, data: List[Dict[str, Any]]) -> None:
        """
        加载 K线数据

        Args:
            symbol: 交易品种
            data: K线数据列表
        """
        self._bars[symbol] = data.copy()
        self._logger.info(f"加载 {len(data)} 条 {symbol} 数据")

    def load_data_from_csv(self, filepath: str, symbol: str = None) -> int:
        """
        从 CSV 文件加载数据

        Args:
            filepath: 文件路径
            symbol: 交易品种，默认使用文件名

        Returns:
            加载的数据条数
        """
        import csv
        import os

        if symbol is None:
            symbol = os.path.basename(filepath).split(".")[0]

        data = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    bar = {
                        "symbol": symbol,
                        "timestamp": float(row.get("timestamp", 0)),
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": float(row.get("volume", 0)),
                    }
                    data.append(bar)
                except (ValueError, KeyError):
                    continue

        self.load_data(symbol, data)
        return len(data)

    def generate_test_data(
        self, symbol: str, count: int, base_price: float = 50000, volatility: float = 0.02
    ) -> List[Dict[str, Any]]:
        """
        生成测试数据

        Args:
            symbol: 交易品种
            count: 数据条数
            base_price: 基础价格
            volatility: 波动率

        Returns:
            K线数据列表
        """
        import random
        import time

        data = []
        current_price = base_price
        timestamp = int(time.time()) - count * 3600

        for i in range(count):
            # 随机波动
            change = random.gauss(0, volatility)
            close = current_price * (1 + change)
            high = max(current_price, close) * (1 + abs(random.uniform(0, 0.005)))
            low = min(current_price, close) * (1 - abs(random.uniform(0, 0.005)))
            open_price = current_price

            bar = {
                "symbol": symbol,
                "timestamp": timestamp + i * 3600,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": random.uniform(100, 1000),
            }
            data.append(bar)

            current_price = close

        self.load_data(symbol, data)
        return data

    def start_backtest(self) -> None:
        """开始回测"""
        self._is_backtesting = True
        self._current_index = 0

        self.publish(
            "market.backtest_start",
            {"symbols": self._symbols, "total_bars": sum(len(self._bars.get(s, [])) for s in self._symbols)},
        )

    def stop_backtest(self) -> None:
        """停止回测"""
        self._is_backtesting = False

        self.publish("market.backtest_end", {"symbols": self._symbols, "processed_bars": self._current_index})

    def next_bar(self) -> bool:
        """
        获取下一个 K线

        Returns:
            是否还有数据
        """
        if not self._is_backtesting:
            return False

        has_data = False

        for symbol in self._symbols:
            bars = self._bars.get(symbol, [])

            if self._current_index < len(bars):
                bar = bars[self._current_index].copy()
                bar["symbol"] = symbol

                # 发布 bar 事件
                self.publish("market.bar", bar)
                has_data = True

        self._current_index += 1
        return has_data

    def reset(self) -> None:
        """重置回测状态"""
        self._current_index = 0
        self._is_backtesting = False

    # ============ 市场数据提供者集成 ============

    def connect_provider(self, **kwargs) -> bool:
        """
        连接市场数据提供者

        支持多种配置方式:
        - connect_provider(type='binance', symbols=['BTCUSDT'])
        - connect_provider(type='csv', filepath='data/btc.csv')
        - connect_provider(provider=existing_provider_instance)

        Returns:
            bool: 连接是否成功
        """
        from nemt.market_providers import (
            MarketProviderFactory,
            MockMarketProvider,
            BinanceMarketProvider,
            CSVFileProvider,
        )

        # 如果传入了现成的提供者
        if "provider" in kwargs:
            self.set_provider(kwargs["provider"])
            return self._provider.connect() if self._provider else False

        # 根据类型创建提供者
        provider_type = kwargs.get("type", "mock")
        symbols = kwargs.get("symbols", self._symbols)

        if provider_type == "binance":
            provider = MarketProviderFactory.create_binance(
                symbols=symbols, default_interval=kwargs.get("interval", "1h")
            )
        elif provider_type == "csv":
            from nemt.market_providers import CSVConfig

            config = CSVConfig(
                filepath=kwargs.get("filepath", "data.csv"),
                default_symbol=kwargs.get("symbol", symbols[0] if symbols else "DEFAULT"),
                datetime_format=kwargs.get("datetime_format"),
            )
            provider = CSVFileProvider(config=config, auto_watch=kwargs.get("auto_watch", False))
        else:
            provider = MarketProviderFactory.create_mock(
                symbols=symbols, base_prices=kwargs.get("base_prices"), volatility=kwargs.get("volatility", 0.002)
            )

        self.set_provider(provider)
        connected = provider.connect()

        if connected:
            self.publish("market.provider_connected", {"type": provider_type, "symbols": symbols})

        return connected

    def start_realtime(self, symbols: List[str] = None, interval: str = "1h") -> bool:
        """
        启动实时数据流

        Args:
            symbols: 交易对列表
            interval: K线周期

        Returns:
            bool: 启动是否成功
        """
        if not self._provider:
            print("[MarketCapsule] No provider set")
            return False

        symbols = symbols or self._symbols
        self._realtime_enabled = True

        # 如果是Binance提供者，启动WebSocket
        BinanceProvider = _get_binance_provider()
        if BinanceProvider and isinstance(self._provider, BinanceProvider):
            return self._provider.subscribe_websocket(symbols, [interval])
        else:
            # 对于其他提供者，设置订阅
            self._setup_provider_subscriptions()
            return True

    def stop_realtime(self) -> None:
        """停止实时数据流"""
        self._realtime_enabled = False

        BinanceProvider = _get_binance_provider()
        if self._provider and BinanceProvider and isinstance(self._provider, BinanceProvider):
            self._provider.unsubscribe_websocket()

    def load_history_from_provider(
        self, symbol: str = None, interval: str = "1h", limit: int = 100, days: int = 30
    ) -> int:
        """
        从提供者加载历史数据

        Args:
            symbol: 交易对
            interval: K线周期
            limit: 数据条数
            days: 天数 (用于Binance API)

        Returns:
            加载的数据条数
        """
        if not self._provider or not self._provider.is_connected:
            print("[MarketCapsule] Provider not connected")
            return 0

        symbol = symbol or (self._symbols[0] if self._symbols else "BTC")

        # 根据提供者类型获取数据
        BinanceProvider = _get_binance_provider()
        if BinanceProvider and isinstance(self._provider, BinanceProvider):
            if days > 0:
                klines = self._provider.get_history_by_days(symbol, interval, days)
            else:
                klines = self._provider.get_history(symbol, interval, limit)
        else:
            klines = self._provider.get_history(symbol, interval, limit)

        if klines:
            # 转换为bar格式
            bars = []
            for k in klines:
                ts = k.timestamp.timestamp() if hasattr(k.timestamp, "timestamp") else k.timestamp
                bars.append(
                    {
                        "symbol": k.symbol,
                        "timestamp": ts,
                        "open": k.open,
                        "high": k.high,
                        "low": k.low,
                        "close": k.close,
                        "volume": k.volume,
                    }
                )

            self.load_data(symbol, bars)
            return len(bars)

        return 0

    def add_realtime_callback(self, callback: Callable[[Dict], None]) -> None:
        """添加实时数据回调"""
        if callback not in self._realtime_callbacks:
            self._realtime_callbacks.append(callback)

    def remove_realtime_callback(self, callback: Callable[[Dict], None]) -> None:
        """移除实时数据回调"""
        if callback in self._realtime_callbacks:
            self._realtime_callbacks.remove(callback)

    def get_provider_status(self) -> Dict[str, Any]:
        """获取提供者状态"""
        status = {
            "provider_type": self._provider_type,
            "has_provider": self._provider is not None,
            "realtime_enabled": self._realtime_enabled,
        }

        if self._provider:
            status.update(self._provider.get_status())

        return status

    def shutdown(self) -> None:
        """关闭"""
        self._is_backtesting = False
        self.stop_realtime()

        if self._provider:
            self._provider.disconnect()
            self._provider = None
