"""
NEMT Platform - Market Service
市场数据服务

职责：
- 订阅市场数据源（WebSocket）
- K线数据聚合
- 价格/成交量缓存
- 发布市场事件
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from ..base import BaseService
from ..common.types import EventTypes


@dataclass
class MarketDataCache:
    """市场数据缓存"""

    symbol: str
    prices: list[float] = field(default_factory=list)
    volumes: list[float] = field(default_factory=list)
    timestamps: list[datetime] = field(default_factory=list)
    last_update: datetime | None = None
    max_size: int = 1000

    def add(self, price: float, volume: float = 0.0, timestamp: datetime = None) -> None:
        """添加数据"""
        self.prices.append(price)
        self.volumes.append(volume)
        self.timestamps.append(timestamp or datetime.now())
        self.last_update = datetime.now()

        if len(self.prices) > self.max_size:
            self.prices = self.prices[-self.max_size :]
            self.volumes = self.volumes[-self.max_size :]
            self.timestamps = self.timestamps[-self.max_size :]

    def get_latest(self) -> dict | None:
        """获取最新数据"""
        if not self.prices:
            return None
        return {
            "symbol": self.symbol,
            "price": self.prices[-1],
            "volume": self.volumes[-1] if self.volumes else 0,
            "timestamp": self.timestamps[-1].isoformat() if self.timestamps else None,
        }


class MarketService(BaseService):
    """
    Market Service

    订阅事件：
    - (无上游依赖)

    发布事件：
    - market.bar: K线更新
    - market.price: 价格更新
    - market.candle_closed: 蜡烛图完成
    """

    def __init__(self):
        super().__init__("market", port=8001)

        # 数据缓存
        self._data_caches: dict[str, MarketDataCache] = {}

        # 订阅者
        self._subscribers: dict[str, list[Callable]] = {}

        # WebSocket 连接（模拟）
        self._ws_connected = False

    async def on_init(self):
        """初始化"""
        self.logger.info("Market Service 初始化中...")

        # 初始化缓存
        self._data_caches = {}

        self.logger.info("Market Service 初始化完成")

    async def on_start(self):
        """启动"""
        self.logger.info("Market Service 启动中...")

        # 订阅默认交易对
        await self.subscribe_symbols(["BTCUSDT", "ETHUSDT"])

        # 启动数据模拟（实际应该连接真实 WebSocket）
        asyncio.create_task(self._simulate_data())

        self.logger.info("Market Service 启动完成")

    async def subscribe_symbols(self, symbols: list[str]):
        """
        订阅交易对

        Args:
            symbols: 交易对列表
        """
        for symbol in symbols:
            if symbol not in self._data_caches:
                self._data_caches[symbol] = MarketDataCache(symbol=symbol)
                self.logger.info(f"订阅: {symbol}")

    async def unsubscribe_symbols(self, symbols: list[str]):
        """
        取消订阅

        Args:
            symbols: 交易对列表
        """
        for symbol in symbols:
            if symbol in self._data_caches:
                del self._data_caches[symbol]
                self.logger.info(f"取消订阅: {symbol}")

    async def get_price(self, symbol: str) -> float | None:
        """
        获取最新价格

        Args:
            symbol: 交易对

        Returns:
            最新价格
        """
        cache = self._data_caches.get(symbol)
        return cache.prices[-1] if cache and cache.prices else None

    async def get_klines(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> dict | None:
        """
        获取 K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            limit: 数量限制

        Returns:
            K线数据
        """
        cache = self._data_caches.get(symbol)
        if not cache:
            return None

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(cache.prices),
            "prices": cache.prices[-limit:],
            "volumes": cache.volumes[-limit:],
            "timestamps": [ts.isoformat() for ts in cache.timestamps[-limit:]],
        }

    async def subscribe(self, symbol: str, callback: Callable) -> None:
        """
        订阅价格更新

        Args:
            symbol: 交易对
            callback: 回调函数
        """
        if symbol not in self._subscribers:
            self._subscribers[symbol] = []
        if callback not in self._subscribers[symbol]:
            self._subscribers[symbol].append(callback)

    async def unsubscribe(self, symbol: str, callback: Callable) -> None:
        """
        取消订阅

        Args:
            symbol: 交易对
            callback: 回调函数
        """
        if symbol in self._subscribers and callback in self._subscribers[symbol]:
            self._subscribers[symbol].remove(callback)

    async def _notify_subscribers(self, symbol: str, price: float, volume: float):
        """通知订阅者"""
        if symbol in self._subscribers:
            data = {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": datetime.now().isoformat(),
            }

            for callback in self._subscribers[symbol]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"回调执行失败: {e}")

    async def _publish_bar(self, symbol: str, price: float, volume: float):
        """发布 K线事件"""
        await self.publish(
            EventTypes.MARKET_BAR,
            {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _publish_price(self, symbol: str, price: float):
        """发布价格事件"""
        await self.publish(
            EventTypes.MARKET_PRICE,
            {
                "symbol": symbol,
                "price": price,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _simulate_data(self):
        """模拟数据（实际应该连接 WebSocket）"""
        import random

        base_prices = {
            "BTCUSDT": 65000.0,
            "ETHUSDT": 3500.0,
        }

        while self.status.value == "healthy":
            for symbol in list(self._data_caches.keys()):
                # 模拟价格变动
                base_price = base_prices.get(symbol, 100.0)
                price_change = random.uniform(-0.005, 0.005)
                new_price = base_price * (1 + price_change)

                # 更新缓存
                cache = self._data_caches[symbol]
                cache.add(new_price, random.uniform(100, 1000))

                # 更新基准价格
                base_prices[symbol] = new_price

                # 发布事件
                await self._publish_price(symbol, new_price)
                await self._publish_bar(symbol, new_price, cache.volumes[-1])

                # 通知订阅者
                await self._notify_subscribers(symbol, new_price, cache.volumes[-1])

            await asyncio.sleep(5)  # 每 5 秒更新一次


async def main():
    """入口"""
    service = MarketService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
