"""
Market Node - 市场数据节点

示范：基于 Schema 的自描述节点

每个节点同时是：
  - 代码 (可执行)
  - 状态 (可读取)
  - Schema (可验证)
"""

from typing import Any

from .node import Node, Port


class MarketNode(Node):
    """
    Market Node - 市场数据节点

    职责:
    - 获取市场原始数据
    - 计算 OHLCV K线
    - 检测市场相位

    Schema 定义:
      输入: raw_feed
      输出: ohlcv
    """

    # ═══════════════════════════════════════════════════════════════
    # NODE 元数据 (AI 直接读取这里)
    # ═══════════════════════════════════════════════════════════════
    NODE: dict[str, Any] = {
        # 身份
        "id": "market_node",
        "name": "Market Data Node",
        "type": "source",  # NodeType.SOURCE
        "version": "1.0.0",
        # 状态
        "status": "created",  # created -> initialized -> running -> idle
        # 描述
        "description": "Market data source node - fetches and processes market data",
        "module": "nemt.core.market",
        # 接口定义
        "interface": {
            "inputs": [
                {
                    "name": "raw_feed",
                    "type": "raw_feed",
                    "required": True,
                    "description": "Raw market feed from exchange",
                }
            ],
            "outputs": [{"name": "ohlcv", "type": "ohlcv", "required": True, "description": "Processed OHLCV bars"}],
        },
        # 约束
        "constraints": {
            "immutable": {
                "output_format": "ohlcv",
                "frequencies": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                "symbols_case": "uppercase",
            },
            "runtime": {"max_latency_ms": 1000, "min_volume": 0, "timestamp_monotonic": True},
        },
        # 状态数据
        "state": {
            "phase": "UNKNOWN",  # UNKNOWN | TREND_UP | TREND_DOWN | RANGE | VOLATILE
            "symbols": [],
            "last_update": None,
            "data_quality": 1.0,
            "bars_generated": 0,
        },
        # 技术债
        "debt": None,
        # 标签
        "tags": ["market", "data", "source"],
    }

    # ═══════════════════════════════════════════════════════════════
    # 端口定义
    # ═══════════════════════════════════════════════════════════════
    INPUT_PORTS = [Port(name="raw_feed", type="raw_feed", required=True)]

    OUTPUT_PORTS = [Port(name="ohlcv", type="ohlcv", required=True)]

    # ═══════════════════════════════════════════════════════════════
    # 初始化
    # ═══════════════════════════════════════════════════════════════
    def __init__(self):
        super().__init__()
        self._bars_cache = []

    # ═══════════════════════════════════════════════════════════════
    # 执行逻辑
    # ═══════════════════════════════════════════════════════════════
    def exec(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        处理市场数据

        Args:
            inputs = {"raw_feed": {...}}

        Returns:
            {"ohlcv": {...}}
        """
        raw_feed = inputs["raw_feed"]

        # 计算 OHLCV
        ohlcv = self._compute_ohlcv(raw_feed)

        # 更新状态
        self.update_state("phase", self._detect_phase())
        self.update_state("last_update", raw_feed.get("timestamp"))
        self.update_state("bars_generated", self.get_state("bars_generated", 0) + 1)

        if raw_feed["symbol"] not in self.get_state("symbols", []):
            self.update_state("symbols", self.get_state("symbols", []) + [raw_feed["symbol"]])

        return {"ohlcv": ohlcv}

    def _compute_ohlcv(self, raw_feed: dict) -> dict:
        """计算 OHLCV"""
        price = raw_feed["price"]
        volume = raw_feed.get("volume", 0)

        # 简单模拟
        return {
            "symbol": raw_feed["symbol"].upper(),
            "timestamp": raw_feed["timestamp"],
            "open": price * 0.998,
            "high": price * 1.002,
            "low": price * 0.997,
            "close": price,
            "volume": volume,
        }

    def _detect_phase(self) -> str:
        """检测市场相位"""
        bars_count = self.get_state("bars_generated", 0)
        if bars_count < 20:
            return "UNKNOWN"
        return "RANGE"  # 简化实现


# ═══════════════════════════════════════════════════════════════
# 便捷访问 (AI 可以直接用)
# ═══════════════════════════════════════════════════════════════

# AI 可以直接读取这些
NODE_INFO = MarketNode.NODE
NODE_STATUS = NODE_INFO["status"]
NODE_PHASE = NODE_INFO["state"]["phase"]
NODE_CONSTRAINTS = NODE_INFO["constraints"]
