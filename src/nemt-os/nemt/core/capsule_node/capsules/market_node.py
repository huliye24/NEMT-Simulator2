"""
MarketNode - 市场数据胶囊节点

示范：基于 CapsuleNode 的完整实现

融合了：
- CapsuleNode 基类 (Schema 验证 + AI 可读状态)
- 五阶段迭代 (看画填验连)
- 事件驱动
- 健康检查
"""

import threading
from datetime import datetime
from typing import Any

from nemt.core.capsule_node import (
    ConstraintSchema,
    FractalCapsuleNode,
    PortSchema,
)


class MarketNode(FractalCapsuleNode):
    """
    MarketNode - 市场数据胶囊节点

    职责：
    - 获取市场原始数据
    - 计算 OHLCV K线
    - 检测市场相位
    - 发布市场事件

    AI 可直接读取：
    - state: 当前状态 (Phase, 输入, 输出, 约束)
    - export_json(): 导出完整状态
    """

    # ═══════════════════════════════════════════════════════════════════════════════
    # 节点身份
    # ═══════════════════════════════════════════════════════════════════════════════
    NODE_ID = "market_node"
    NODE_NAME = "Market Data Node"
    NODE_VERSION = "1.0.0"

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输入端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    INPUT_PORTS = [
        PortSchema(
            name="raw_feed",
            data_type="object",
            required=True,
            description="Raw market feed from exchange",
            properties={
                "symbol": {"type": "string", "description": "Trading pair symbol"},
                "price": {"type": "number", "description": "Current price"},
                "volume": {"type": "number", "description": "Trading volume"},
                "timestamp": {"type": "integer", "description": "Unix timestamp"},
            },
            required_fields=["symbol", "price", "timestamp"],
            constraints={},
        ),
        PortSchema(
            name="kline_request",
            data_type="object",
            required=False,
            description="Request for historical klines",
            properties={
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["1m", "5m", "15m", "1h", "4h", "1d"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
            },
            required_fields=["symbol"],
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输出端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    OUTPUT_PORTS = [
        PortSchema(
            name="ohlcv",
            data_type="object",
            required=True,
            description="Processed OHLCV bars",
            properties={
                "symbol": {"type": "string"},
                "timestamp": {"type": "integer"},
                "open": {"type": "number"},
                "high": {"type": "number"},
                "low": {"type": "number"},
                "close": {"type": "number"},
                "volume": {"type": "number"},
            },
            required_fields=["symbol", "open", "high", "low", "close", "volume"],
            constraints={},
        ),
        PortSchema(
            name="price_update",
            data_type="object",
            required=False,
            description="Price update event",
            properties={
                "symbol": {"type": "string"},
                "price": {"type": "number"},
                "change_24h": {"type": "number"},
                "volume_24h": {"type": "number"},
            },
            required_fields=["symbol", "price"],
        ),
        PortSchema(
            name="phase",
            data_type="string",
            required=True,
            description="Detected market phase",
            enum_values=["UNKNOWN", "TREND_UP", "TREND_DOWN", "RANGE", "VOLATILE"],
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 约束 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    CONSTRAINTS = [
        ConstraintSchema(
            name="max_latency_ms",
            constraint_type="runtime",
            value=1000,
            description="Maximum processing latency",
            min_value=0,
            max_value=10000,
        ),
        ConstraintSchema(
            name="min_confidence",
            constraint_type="validation",
            value=0.5,
            description="Minimum confidence threshold",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="max_cache_size",
            constraint_type="runtime",
            value=1000,
            description="Maximum bar cache size",
            min_value=1,
            max_value=10000,
        ),
        ConstraintSchema(
            name="symbols_case",
            constraint_type="immutable",
            value="uppercase",
            description="Symbol case normalization",
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 初始化
    # ═══════════════════════════════════════════════════════════════════════════════

    def __init__(self, node_id: str = "market_node"):
        super().__init__(node_id)

        # 内部状态
        self._symbols: list[str] = []
        self._bars_cache: dict[str, list[dict]] = {}
        self._subscribers: dict[str, list] = {}
        self._lock = threading.Lock()

        # 相位检测
        self._current_phase = "UNKNOWN"
        self._phase_history: list[str] = []
        self._bar_count = 0

    # ═══════════════════════════════════════════════════════════════════════════════
    # 处理实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _process_impl(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        处理市场数据

        Args:
            inputs = {
                "raw_feed": {
                    "symbol": "BTCUSDT",
                    "price": 50000,
                    "volume": 100,
                    "timestamp": 1714281600
                }
            }

        Returns:
            {
                "ohlcv": {...},
                "price_update": {...},
                "phase": "RANGE"
            }
        """
        raw_feed = inputs.get("raw_feed")
        if not raw_feed:
            raise ValueError("Missing required input: raw_feed")

        symbol = raw_feed["symbol"].upper()
        price = raw_feed["price"]
        volume = raw_feed.get("volume", 0)
        timestamp = raw_feed.get("timestamp")

        # 添加到缓存
        self._add_bar(symbol, price, volume, timestamp)

        # 计算 OHLCV
        ohlcv = self._compute_ohlcv(symbol)

        # 检测相位
        phase = self._detect_phase(symbol)

        # 构建输出
        outputs = {
            "ohlcv": ohlcv,
            "phase": phase,
        }

        # 如果有足够数据，添加价格更新
        if len(self._bars_cache.get(symbol, [])) > 1:
            prev_price = self._bars_cache[symbol][-2]["close"]
            change_24h = (price - prev_price) / prev_price if prev_price > 0 else 0
            outputs["price_update"] = {
                "symbol": symbol,
                "price": price,
                "change_24h": change_24h,
                "volume_24h": sum(b["volume"] for b in self._bars_cache.get(symbol, [])),
            }

        return outputs

    def _add_bar(self, symbol: str, price: float, volume: float, timestamp: int) -> None:
        """添加 K 线到缓存"""
        with self._lock:
            if symbol not in self._bars_cache:
                self._bars_cache[symbol] = []
                self._symbols.append(symbol)

            bar = {
                "symbol": symbol,
                "open": price * 0.998,
                "high": price * 1.002,
                "low": price * 0.997,
                "close": price,
                "volume": volume,
                "timestamp": timestamp or int(datetime.now().timestamp()),
            }

            self._bars_cache[symbol].append(bar)
            self._bar_count += 1

            # 保持缓存大小
            max_size = self.get_config("max_cache_size", 1000)
            if len(self._bars_cache[symbol]) > max_size:
                self._bars_cache[symbol] = self._bars_cache[symbol][-max_size:]

    def _compute_ohlcv(self, symbol: str) -> dict[str, Any]:
        """计算 OHLCV"""
        bars = self._bars_cache.get(symbol, [])
        if not bars:
            return {}

        latest_bar = bars[-1]
        return latest_bar.copy()

    def _detect_phase(self, symbol: str) -> str:
        """检测市场相位"""
        bars = self._bars_cache.get(symbol, [])
        if len(bars) < 20:
            return "UNKNOWN"

        # 简单相位检测
        recent_bars = bars[-20:]
        closes = [b["close"] for b in recent_bars]

        # 计算趋势
        first_close = closes[0]
        last_close = closes[-1]
        change = (last_close - first_close) / first_close if first_close > 0 else 0

        # 计算波动率
        import statistics

        if len(closes) > 1:
            volatility = statistics.stdev(closes) / statistics.mean(closes) if statistics.mean(closes) > 0 else 0
        else:
            volatility = 0

        # 判断相位
        if abs(change) > 0.02:
            return "TREND_UP" if change > 0 else "TREND_DOWN"
        elif volatility > 0.01:
            return "VOLATILE"
        else:
            return "RANGE"

    # ═══════════════════════════════════════════════════════════════════════════════
    # 五阶段实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _observe_phase_impl(self) -> dict[str, Any]:
        """观察阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "raw_feed": {
                    "type": "object",
                    "required_fields": ["symbol", "price", "timestamp"],
                    "source": "exchange_api",
                },
                "kline_request": {
                    "type": "object",
                    "required_fields": ["symbol"],
                    "source": "internal",
                },
            },
            "outputs": {
                "ohlcv": {
                    "type": "object",
                    "produced_fields": ["symbol", "open", "high", "low", "close", "volume"],
                    "destination": "signal_node",
                },
                "price_update": {
                    "type": "object",
                    "produced_fields": ["symbol", "price", "change_24h", "volume_24h"],
                    "destination": "brain_node",
                },
                "phase": {
                    "type": "string",
                    "enum": ["UNKNOWN", "TREND_UP", "TREND_DOWN", "RANGE", "VOLATILE"],
                    "destination": "risk_node",
                },
            },
            "constraints": {
                "max_latency_ms": {"value": 1000, "reason": "Real-time requirement"},
                "max_cache_size": {"value": 1000, "reason": "Memory limit"},
            },
            "dependencies": ["EventBus", "ConfigCenter"],
            "risks": [
                {"type": "API不稳定", "mitigation": "重试机制"},
                {"type": "数据延迟", "mitigation": "本地缓存"},
            ],
        }

    def _design_phase_impl(self) -> dict[str, Any]:
        """设计阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "run(inputs)": "Process raw feed and return OHLCV",
                "get_price(symbol)": "Get latest price for symbol",
                "get_klines(symbol, limit)": "Get historical klines",
                "subscribe(symbol, callback)": "Subscribe to price updates",
            },
            "internal_structure": {
                "_bars_cache": "Dict[str, List[Dict]] - K线缓存",
                "_symbols": "List[str] - 跟踪的符号",
                "_subscribers": "Dict[str, List] - 订阅者",
            },
            "event_contracts": {
                "publishes": ["market.ohlcv", "market.price_update", "market.phase"],
                "subscribes": ["market.subscribe_request", "market.kline_update"],
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 公开 API
    # ═══════════════════════════════════════════════════════════════════════════════

    def get_price(self, symbol: str) -> float | None:
        """获取最新价格"""
        with self._lock:
            bars = self._bars_cache.get(symbol.upper(), [])
            return bars[-1]["close"] if bars else None

    def get_klines(self, symbol: str, limit: int = 100) -> list[dict]:
        """获取 K 线数据"""
        with self._lock:
            bars = self._bars_cache.get(symbol.upper(), [])
            return bars[-limit:] if bars else []

    def subscribe(self, symbol: str, callback) -> None:
        """订阅价格更新"""
        with self._lock:
            symbol = symbol.upper()
            if symbol not in self._subscribers:
                self._subscribers[symbol] = []
            if callback not in self._subscribers[symbol]:
                self._subscribers[symbol].append(callback)

    def unsubscribe(self, symbol: str, callback) -> None:
        """取消订阅"""
        with self._lock:
            symbol = symbol.upper()
            if symbol in self._subscribers and callback in self._subscribers[symbol]:
                self._subscribers[symbol].remove(callback)

    def get_cached_symbols(self) -> list[str]:
        """获取已缓存的符号"""
        return list(self._symbols)

    def get_metrics(self) -> dict[str, Any]:
        """获取指标"""
        return {
            "bar_count": self._bar_count,
            "symbols_count": len(self._symbols),
            "cache_size": sum(len(bars) for bars in self._bars_cache.values()),
            **super().metrics,
        }
