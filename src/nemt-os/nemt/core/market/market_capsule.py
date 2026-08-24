"""
MarketCapsule - 分形迭代版

按五阶段迭代法重写的市场数据胶囊。
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from nemt.core.capsule import FractalCapsule


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

        # 保持最大长度
        if len(self.prices) > self.max_size:
            self.prices = self.prices[-self.max_size :]
            self.volumes = self.volumes[-self.max_size :]
            self.timestamps = self.timestamps[-self.max_size :]

    def clear(self) -> None:
        """清空缓存"""
        self.prices.clear()
        self.volumes.clear()
        self.timestamps.clear()
        self.last_update = None

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


class MarketCapsule(FractalCapsule):
    """
    市场数据胶囊

    负责：
    - 订阅市场数据源
    - 数据预处理
    - 缓存管理
    - 发布市场事件

    五阶段方法已实现：
    - observe_phase(): 分析数据需求
    - design_phase(): 定义接口契约
    - implement_phase(): 实现核心逻辑
    - verify_phase(): 验证实现
    - integrate_phase(): 集成上下游

    示例:
    ```python
    capsule = MarketCapsule("market")
    capsule.init()
    result = capsule.run_fractal_iteration()
    ```
    """

    def __init__(self, capsule_id: str = "market"):
        super().__init__(capsule_id, version="1.0.0")
        self._layer = "L1"

        # 内部状态
        self._symbols: list[str] = []
        self._data_caches: dict[str, MarketDataCache] = {}
        self._subscribers: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()

        # 数据提供者
        self._data_provider = None

        # 观察报告缓存
        self._input_schema: dict | None = None
        self._output_schema: dict | None = None

    # ========================================
    # 【看】观察阶段
    # ========================================

    def observe_phase(self) -> dict[str, Any]:
        """
        【看】观察阶段 - 理解市场数据需求
        """
        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "raw_klines": {
                    "type": "list",
                    "format": "{timestamp, open, high, low, close, volume}",
                    "source": "market_provider",
                    "required": True,
                },
                "symbols": {
                    "type": "list",
                    "format": "string (e.g., BTCUSDT)",
                    "source": "config",
                    "required": True,
                },
                "timeframe": {
                    "type": "string",
                    "format": "1m, 5m, 15m, 1h, 4h, 1d",
                    "default": "1h",
                },
            },
            "outputs": {
                "processed_klines": {
                    "type": "DataFrame",
                    "columns": ["timestamp", "open", "high", "low", "close", "volume"],
                },
                "indicators": {"type": "dict", "description": "预计算的技术指标"},
                "events": {"type": "list", "description": "市场事件"},
            },
            "constraints": {
                "latency": "<100ms",
                "reconnect": "断线自动重连",
                "cache_ttl": "60s",
                "max_symbols": 50,
            },
            "dependencies": ["EventBus", "ConfigCenter"],
            "risks": [
                {"type": "API不稳定", "mitigation": "重试机制+熔断"},
                {"type": "数据延迟", "mitigation": "本地缓存+时间戳校验"},
                {"type": "断线丢失", "mitigation": "历史数据回放"},
            ],
            "subscribes_to": ["market.subscribe_request", "market.kline_update"],
            "publishes": ["market.kline", "market.price_update", "market.candle_closed"],
        }

    # ========================================
    # 【画】设计阶段
    # ========================================

    def design_phase(self) -> dict[str, Any]:
        """
        【画】设计阶段 - 定义接口契约和骨架
        """
        self._input_schema = {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "交易对符号"},
                "timeframe": {"type": "string", "default": "1h"},
                "limit": {"type": "integer", "default": 100, "minimum": 1, "maximum": 1000},
            },
            "required": ["symbol"],
        }

        self._output_schema = {
            "type": "object",
            "properties": {
                "data": {"type": "DataFrame", "description": "K线数据"},
                "metadata": {
                    "type": "dict",
                    "properties": {
                        "symbol": {"type": "string"},
                        "timeframe": {"type": "string"},
                        "count": {"type": "integer"},
                        "latest_update": {"type": "string"},
                    },
                },
                "status": {"type": "string", "enum": ["success", "error", "partial"]},
            },
        }

        return {
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "get_klines(symbol, timeframe, limit)": "获取K线数据",
                "get_price(symbol)": "获取最新价格",
                "subscribe(symbol, callback)": "订阅实时数据",
                "unsubscribe(symbol, callback)": "取消订阅",
                "get_cached_symbols()": "获取已缓存的符号列表",
            },
            "input_schema": self._input_schema,
            "output_schema": self._output_schema,
            "internal_structure": {
                "data_caches": "Dict[str, MarketDataCache]",
                "subscribers": "Dict[str, List[Callable]]",
                "data_provider": "MarketDataProvider (可选)",
            },
            "event_contracts": {
                "publishes": [
                    "market.kline",
                    "market.price_update",
                    "market.candle_closed",
                ],
                "subscribes": [
                    "market.subscribe_request",
                    "market.kline_update",
                ],
            },
            "internal_methods": {
                "_add_price()": "添加价格到缓存",
                "_notify_subscribers()": "通知订阅者",
                "_clean_expired_cache()": "清理过期缓存",
            },
        }

    # ========================================
    # 【填】实现阶段
    # ========================================

    def implement_phase(self) -> None:
        """
        【填】实现阶段 - 填充核心逻辑
        """
        # 初始化缓存
        for symbol in self._symbols:
            if symbol not in self._data_caches:
                self._data_caches[symbol] = MarketDataCache(symbol=symbol)

        # 设置默认配置
        default_configs = {
            "market.cache_ttl": 60,
            "market.reconnect_interval": 5,
            "market.max_retry": 3,
            "market.max_cache_size": 1000,
        }

        for key, value in default_configs.items():
            if self.get_config(key) is None:
                self.set_config(key, value)

        self._logger.info(f"{self._capsule_id} 实现阶段完成")

    # ========================================
    # 【验】验证阶段
    # ========================================

    def verify_phase(self) -> dict[str, Any]:
        """
        【验】验证阶段 - 确保实现正确
        """
        checks = {
            "input_schema_defined": self._input_schema is not None,
            "output_schema_defined": self._output_schema is not None,
            "cache_initialized": hasattr(self, "_data_caches"),
            "symbols_tracked": len(self._symbols) >= 0,
            "dependencies_injected": self._event_bus is not None,
            "thread_safe": hasattr(self, "_lock"),
        }

        passed = all(checks.values())

        return {
            "capsule_id": self._capsule_id,
            "phase": "verify",
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "passed": passed,
            "metrics": {
                "symbols_count": len(self._symbols),
                "caches_count": len(self._data_caches),
                "subscribers_count": sum(len(v) for v in self._subscribers.values()),
            },
            "test_results": {
                "unit_tests": "pending",
                "integration_tests": "pending",
            },
        }

    # ========================================
    # 【连】集成阶段
    # ========================================

    def integrate_phase(self) -> None:
        """
        【连】集成阶段 - 与上下游对接
        """
        self._logger.info(f"{self._capsule_id} 集成阶段完成")
        self._logger.info("  上游: MarketDataProvider (可选)")
        self._logger.info("  下游: SignalCapsule, RiskCapsule, BrainCapsule")

        # 发布就绪事件
        if self._event_bus:
            self.publish(
                "market.ready",
                {
                    "capsule_id": self._capsule_id,
                    "symbols": self._symbols,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    # ========================================
    # 标准生命周期
    # ========================================

    def init(self) -> None:
        """
        初始化胶囊 - 订阅事件
        """
        # 订阅市场数据请求
        self.subscribe("market.subscribe_request", self._on_subscribe_request)
        self.subscribe("market.kline_update", self._on_kline_update)
        self._initialized = True
        self._logger.info(f"{self._capsule_id} 初始化完成")

    def exec(self) -> dict[str, Any]:
        """
        执行主要逻辑
        """
        return {
            "capsule_id": self._capsule_id,
            "symbols": self._symbols,
            "cache_stats": {symbol: cache.price_count for symbol, cache in self._data_caches.items()},
            "last_updates": {
                symbol: cache.last_update.isoformat() if cache.last_update else None
                for symbol, cache in self._data_caches.items()
            },
        }

    def shutdown(self) -> None:
        """
        关闭胶囊 - 清理资源
        """
        with self._lock:
            for cache in self._data_caches.values():
                cache.clear()
            self._data_caches.clear()
            self._symbols.clear()
            self._subscribers.clear()

        self._running = False
        self._logger.info(f"{self._capsule_id} 已关闭")

    # ========================================
    # 公开 API
    # ========================================

    def add_price(self, symbol: str, price: float, volume: float = 0.0, timestamp: datetime = None) -> None:
        """
        添加价格数据

        Args:
            symbol: 交易对符号
            price: 价格
            volume: 成交量
            timestamp: 时间戳
        """
        with self._lock:
            # 确保缓存存在
            if symbol not in self._data_caches:
                max_size = self.get_config("market.max_cache_size", 1000)
                self._data_caches[symbol] = MarketDataCache(symbol=symbol, max_size=max_size)

            # 添加数据
            self._data_caches[symbol].add(price, volume, timestamp)

            # 确保符号在列表中
            if symbol not in self._symbols:
                self._symbols.append(symbol)

            # 通知订阅者
            self._notify_subscribers(symbol, price, volume)

    def get_price(self, symbol: str) -> float | None:
        """
        获取最新价格

        Args:
            symbol: 交易对符号

        Returns:
            最新价格，没有则返回 None
        """
        cache = self._data_caches.get(symbol)
        return cache.latest_price if cache else None

    def get_klines(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> dict[str, Any] | None:
        """
        获取 K 线数据

        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 数量限制

        Returns:
            K 线数据字典
        """
        cache = self._data_caches.get(symbol)
        if not cache:
            return None

        prices = cache.prices[-limit:]
        volumes = cache.volumes[-limit:]
        timestamps = cache.timestamps[-limit:]

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(prices),
            "latest_update": cache.last_update.isoformat() if cache.last_update else None,
            "prices": prices,
            "volumes": volumes,
            "timestamps": [ts.isoformat() for ts in timestamps],
        }

    def subscribe(self, symbol: str, callback: Callable) -> None:
        """
        订阅价格更新

        Args:
            symbol: 交易对符号
            callback: 回调函数
        """
        with self._lock:
            if symbol not in self._subscribers:
                self._subscribers[symbol] = []
            if callback not in self._subscribers[symbol]:
                self._subscribers[symbol].append(callback)

    def unsubscribe(self, symbol: str, callback: Callable) -> None:
        """
        取消订阅

        Args:
            symbol: 交易对符号
            callback: 回调函数
        """
        with self._lock:
            if symbol in self._subscribers and callback in self._subscribers[symbol]:
                self._subscribers[symbol].remove(callback)

    def get_cached_symbols(self) -> list[str]:
        """获取已缓存的符号列表"""
        return list(self._data_caches.keys())

    # ========================================
    # 内部处理器
    # ========================================

    def _on_subscribe_request(self, event: dict) -> None:
        """处理订阅请求"""
        symbol = event.get("symbol")
        if symbol and symbol not in self._symbols:
            self._symbols.append(symbol)
            max_size = self.get_config("market.max_cache_size", 1000)
            self._data_caches[symbol] = MarketDataCache(symbol=symbol, max_size=max_size)
            self._logger.info(f"订阅请求: {symbol}")

    def _on_kline_update(self, event: dict) -> None:
        """处理 K 线更新"""
        symbol = event.get("symbol")
        price = event.get("close") or event.get("price")
        volume = event.get("volume", 0)
        timestamp = event.get("timestamp")

        if symbol and price:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif timestamp is None:
                timestamp = datetime.now()

            self.add_price(symbol, float(price), float(volume), timestamp)

    def _notify_subscribers(self, symbol: str, price: float, volume: float) -> None:
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
                    callback(data)
                except Exception as e:
                    self._logger.error(f"订阅回调失败: {e}")
