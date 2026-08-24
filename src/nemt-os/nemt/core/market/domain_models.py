"""
Market Domain Models - 市场数据领域模型

定义市场数据上下文中所有业务实体：
- MarketDataCache: 价格缓存聚合根
- KlineData: K线数据实体
- PriceTick: 价格快照值对象

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PriceTick:
    """
    价格快照值对象

    表示某一时刻的市场价格瞬间，无唯一标识，通过属性值相等。

    INVARIANTS:
    - price > 0
    - bid <= ask
    """

    symbol: str
    price: float
    bid: float
    ask: float
    bid_volume: float = 0.0
    ask_volume: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.bid > self.ask:
            raise ValueError("bid must be <= ask")

    @property
    def spread(self) -> float:
        """买卖价差"""
        return self.ask - self.bid

    @property
    def spread_percent(self) -> float:
        """买卖价差百分比"""
        return self.spread / self.price if self.price > 0 else 0.0

    @property
    def mid_price(self) -> float:
        """中间价"""
        return (self.bid + self.ask) / 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "bid": self.bid,
            "ask": self.ask,
            "bid_volume": self.bid_volume,
            "ask_volume": self.ask_volume,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PriceTick:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now()
        return cls(
            symbol=data.get("symbol", ""),
            price=float(data.get("price", 0)),
            bid=float(data.get("bid", 0)),
            ask=float(data.get("ask", 0)),
            bid_volume=float(data.get("bid_volume", 0)),
            ask_volume=float(data.get("ask_volume", 0)),
            timestamp=ts,
        )


@dataclass
class KlineData:
    """
    K线数据实体

    表示一根特定时间周期的 OHLCV 蜡烛图数据。
    实体，有唯一性但可修改（添加新K线时）。

    INVARIANTS:
    - high >= low
    - high >= open
    - high >= close
    - low <= open
    - low <= close
    - volume >= 0
    """

    symbol: str
    timestamp: datetime
    timeframe: str  # 1m, 5m, 15m, 1h, 4h, 1d
    open: float
    high: float
    low: float
    close: float
    volume: float

    # 元数据
    version: int = 1
    is_closed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # OHLC 不变性检查
        if not (self.high >= self.low):
            raise ValueError("high must be >= low")
        if not (self.high >= self.open >= self.low):
            raise ValueError("open must be between high and low")
        if not (self.high >= self.close >= self.low):
            raise ValueError("close must be between high and low")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")

    @property
    def body(self) -> float:
        """K线实体大小"""
        return abs(self.close - self.open)

    @property
    def upper_shadow(self) -> float:
        """上影线长度"""
        return self.high - max(self.open, self.close)

    @property
    def lower_shadow(self) -> float:
        """下影线长度"""
        return min(self.open, self.close) - self.low

    @property
    def is_bullish(self) -> bool:
        """是否阳线"""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """是否阴线"""
        return self.close < self.open

    @property
    def change_percent(self) -> float:
        """涨跌幅百分比"""
        return (self.close - self.open) / self.open if self.open > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "version": self.version,
            "is_closed": self.is_closed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KlineData:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now()
        return cls(
            symbol=data.get("symbol", ""),
            timestamp=ts,
            timeframe=data.get("timeframe", "1h"),
            open=float(data.get("open", 0)),
            high=float(data.get("high", 0)),
            low=float(data.get("low", 0)),
            close=float(data.get("close", 0)),
            volume=float(data.get("volume", 0)),
            version=int(data.get("version", 1)),
            is_closed=data.get("is_closed", False),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_pipeline_input(cls, symbol: str, timeframe: str, data: dict[str, Any]) -> KlineData:
        """从 PipelineInput 数据创建 KlineData"""
        return cls(
            symbol=symbol,
            timestamp=data.get("timestamp", datetime.now()),
            timeframe=timeframe,
            open=float(data.get("open", 0)),
            high=float(data.get("high", 0)),
            low=float(data.get("low", 0)),
            close=float(data.get("price", data.get("close", 0))),
            volume=float(data.get("volume", 0)),
        )


@dataclass
class MarketDataCache:
    """
    市场数据缓存聚合根

    负责管理单一交易对的价格历史缓存。
    聚合根：外部只能通过此类访问内部价格数据。

    INVARIANTS:
    - len(prices) == len(volumes) == len(timestamps)
    - timestamps 严格递增
    - len(prices) <= max_size

    VERSION: 支持乐观锁
    """

    symbol: str
    prices: list[float] = field(default_factory=list)
    volumes: list[float] = field(default_factory=list)
    timestamps: list[datetime] = field(default_factory=list)

    # 聚合根元数据
    max_size: int = 1000
    last_update: datetime | None = None
    version: int = 1  # 乐观锁版本

    # 变更追踪
    _change_history: list[dict] = field(default_factory=list, repr=False)

    # 线程安全锁 (外部管理)
    _lock: threading.Lock | None = field(default=None, repr=False)

    def __post_init__(self):
        # 确保三个列表长度一致
        if len(self.prices) != len(self.volumes):
            raise ValueError("prices and volumes must have same length")
        if len(self.prices) != len(self.timestamps):
            raise ValueError("prices and timestamps must have same length")

    def _track_change(self, action: str, data: dict[str, Any]) -> None:
        """记录变更历史"""
        self._change_history.append(
            {
                "action": action,
                "timestamp": datetime.now(),
                "data": data,
                "version": self.version,
            }
        )
        # 限制历史长度
        if len(self._change_history) > 100:
            self._change_history = self._change_history[-100:]

    def add(self, price: float, volume: float = 0.0, timestamp: datetime | None = None) -> None:
        """
        添加价格数据

        Args:
            price: 价格
            volume: 成交量
            timestamp: 时间戳，默认当前时间
        """
        if price <= 0:
            raise ValueError("price must be positive")

        ts = timestamp or datetime.now()

        # 检查时间递增
        if self.timestamps and ts <= self.timestamps[-1]:
            raise ValueError("timestamp must be strictly increasing")

        self.prices.append(price)
        self.volumes.append(volume)
        self.timestamps.append(ts)
        self.last_update = ts

        # 缓存溢出处理
        if len(self.prices) > self.max_size:
            self.prices = self.prices[-self.max_size :]
            self.volumes = self.volumes[-self.max_size :]
            self.timestamps = self.timestamps[-self.max_size :]

        # 版本递增
        self.version += 1

        # 追踪变更
        self._track_change(
            "add",
            {
                "price": price,
                "volume": volume,
                "timestamp": ts.isoformat(),
            },
        )

    def clear(self) -> None:
        """清空缓存"""
        self.prices.clear()
        self.volumes.clear()
        self.timestamps.clear()
        self.last_update = None
        self.version += 1
        self._track_change("clear", {})

    @property
    def latest_price(self) -> float | None:
        """最新价格"""
        return self.prices[-1] if self.prices else None

    @property
    def latest_volume(self) -> float:
        """最新成交量"""
        return self.volumes[-1] if self.volumes else 0.0

    @property
    def price_count(self) -> int:
        """价格数据数量"""
        return len(self.prices)

    @property
    def price_range(self) -> float | None:
        """价格范围 (max - min)"""
        if not self.prices:
            return None
        return max(self.prices) - min(self.prices)

    @property
    def change_history(self) -> list[dict]:
        """获取变更历史"""
        return self._change_history.copy()

    def get_snapshot(self, count: int = 100) -> dict[str, Any]:
        """
        获取缓存快照

        Args:
            count: 获取最近N条数据

        Returns:
            包含 prices, volumes, timestamps 的字典
        """
        return {
            "symbol": self.symbol,
            "prices": self.prices[-count:],
            "volumes": self.volumes[-count:],
            "timestamps": [ts.isoformat() for ts in self.timestamps[-count:]],
            "count": count,
            "total_count": len(self.prices),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "version": self.version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "prices": self.prices,
            "volumes": self.volumes,
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "max_size": self.max_size,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketDataCache:
        timestamps = [datetime.fromisoformat(ts) if isinstance(ts, str) else ts for ts in data.get("timestamps", [])]
        return cls(
            symbol=data.get("symbol", ""),
            prices=data.get("prices", []),
            volumes=data.get("volumes", []),
            timestamps=timestamps,
            max_size=int(data.get("max_size", 1000)),
            version=int(data.get("version", 1)),
        )


# =============================================================================
# Factory Methods
# =============================================================================


def create_market_data_cache(symbol: str, max_size: int = 1000) -> MarketDataCache:
    """
    工厂方法：创建市场数据缓存

    Args:
        symbol: 交易对符号
        max_size: 最大缓存条数

    Returns:
        MarketDataCache 实例
    """
    return MarketDataCache(
        symbol=symbol,
        max_size=max_size,
    )


def create_kline_from_tick(symbol: str, tick: PriceTick, timeframe: str = "1m") -> KlineData:
    """
    工厂方法：从价格快照创建K线

    Args:
        symbol: 交易对
        tick: 价格快照
        timeframe: 时间周期

    Returns:
        KlineData 实例
    """
    return KlineData(
        symbol=symbol,
        timestamp=tick.timestamp,
        timeframe=timeframe,
        open=tick.price,
        high=tick.price,
        low=tick.price,
        close=tick.price,
        volume=tick.bid_volume + tick.ask_volume,
    )


# =============================================================================
# Domain Services
# =============================================================================


def calculate_volatility(cache: MarketDataCache, period: int = 20) -> float | None:
    """
    计算历史波动率

    Args:
        cache: 市场数据缓存
        period: 计算周期

    Returns:
        波动率值，或 None
    """
    if len(cache.prices) < period:
        return None

    prices = cache.prices[-period:]
    returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]

    if not returns:
        return None

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    return variance**0.5
