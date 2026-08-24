"""
Event Schema Registry - 事件模式注册表

统一管理所有事件的消息格式和版本。

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventVersion(Enum):
    """事件版本"""

    V1 = "v1"
    V2 = "v2"
    CURRENT = "v1"


@dataclass
class EventSchema:
    """事件模式定义"""

    event_type: str
    version: EventVersion
    description: str
    required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)
    field_types: dict[str, str] = field(default_factory=dict)
    examples: list[dict] = field(default_factory=list)

    # 版本信息
    deprecated: bool = False
    replacement_event: str | None = None
    sunset_date: datetime | None = None


@dataclass
class EventSchemaRegistry:
    """事件模式注册表"""

    schemas: dict[str, dict[str, EventSchema]] = field(default_factory=dict)  # event_type -> version -> schema

    def __post_init__(self):
        if not self.schemas:
            self._register_default_schemas()

    def _register_default_schemas(self) -> None:
        """注册默认事件模式"""
        self.register_schema(self._create_market_schemas())
        self.register_schema(self._create_signal_schemas())
        self.register_schema(self._create_risk_schemas())
        self.register_schema(self._create_execution_schemas())
        self.register_schema(self._create_monitor_schemas())

    def _create_market_schemas(self) -> dict[str, EventSchema]:
        return {
            "market.price_update": EventSchema(
                event_type="market.price_update",
                version=EventVersion.V1,
                description="市场价格更新事件",
                required_fields=["symbol", "price", "timestamp"],
                optional_fields=["volume", "bid", "ask"],
                field_types={
                    "symbol": "string",
                    "price": "number",
                    "volume": "number",
                    "timestamp": "string",
                },
                examples=[
                    {
                        "symbol": "BTCUSDT",
                        "price": 50000.0,
                        "volume": 1.5,
                        "timestamp": "2026-04-27T10:00:00Z",
                    }
                ],
            ),
            "market.candle_closed": EventSchema(
                event_type="market.candle_closed",
                version=EventVersion.V1,
                description="K线收线事件",
                required_fields=["symbol", "timeframe", "open", "high", "low", "close", "volume"],
                optional_fields=["trades", "quote_volume"],
                field_types={
                    "symbol": "string",
                    "timeframe": "string",
                    "open": "number",
                    "high": "number",
                    "low": "number",
                    "close": "number",
                    "volume": "number",
                },
            ),
        }

    def _create_signal_schemas(self) -> dict[str, EventSchema]:
        return {
            "signal.generated": EventSchema(
                event_type="signal.generated",
                version=EventVersion.V1,
                description="新信号生成事件",
                required_fields=["signal_id", "signal_type", "symbol", "entry_price", "confidence"],
                optional_fields=["stop_loss", "take_profit", "reason", "metadata"],
                field_types={
                    "signal_id": "string",
                    "signal_type": "string",
                    "symbol": "string",
                    "entry_price": "number",
                    "confidence": "number",
                },
            ),
            "signal.filtered": EventSchema(
                event_type="signal.filtered",
                version=EventVersion.V1,
                description="信号被过滤事件",
                required_fields=["original_signal_id", "filter_reason"],
                optional_fields=["remaining_wait"],
                field_types={
                    "original_signal_id": "string",
                    "filter_reason": "string",
                },
            ),
        }

    def _create_risk_schemas(self) -> dict[str, EventSchema]:
        return {
            "risk.approved": EventSchema(
                event_type="risk.approved",
                version=EventVersion.V1,
                description="风控批准事件",
                required_fields=["signal_id", "symbol", "position_size", "adjusted_entry"],
                optional_fields=["adjusted_stop_loss", "adjusted_take_profit", "reasons", "risk_score"],
                field_types={
                    "signal_id": "string",
                    "symbol": "string",
                    "position_size": "number",
                    "adjusted_entry": "number",
                },
            ),
            "risk.rejected": EventSchema(
                event_type="risk.rejected",
                version=EventVersion.V1,
                description="风控拒绝事件",
                required_fields=["signal_id", "symbol", "reasons"],
                optional_fields=["risk_score"],
                field_types={
                    "signal_id": "string",
                    "symbol": "string",
                    "reasons": "array",
                },
            ),
        }

    def _create_execution_schemas(self) -> dict[str, EventSchema]:
        return {
            "order.submitted": EventSchema(
                event_type="order.submitted",
                version=EventVersion.V1,
                description="订单提交事件",
                required_fields=["order_id", "symbol", "side", "quantity", "price"],
                optional_fields=["order_type", "timestamp"],
                field_types={
                    "order_id": "string",
                    "symbol": "string",
                    "side": "string",
                    "quantity": "number",
                    "price": "number",
                },
            ),
            "order.filled": EventSchema(
                event_type="order.filled",
                version=EventVersion.V1,
                description="订单成交事件",
                required_fields=["order_id", "filled_quantity", "fill_price"],
                optional_fields=["commission", "realized_pnl", "timestamp"],
                field_types={
                    "order_id": "string",
                    "filled_quantity": "number",
                    "fill_price": "number",
                },
            ),
        }

    def _create_monitor_schemas(self) -> dict[str, EventSchema]:
        return {
            "monitor.alert": EventSchema(
                event_type="monitor.alert",
                version=EventVersion.V1,
                description="监控告警事件",
                required_fields=["alert_id", "metric", "value", "severity"],
                optional_fields=["threshold", "message", "timestamp"],
                field_types={
                    "alert_id": "integer",
                    "metric": "string",
                    "value": "number",
                    "severity": "string",
                },
            ),
            "monitor.health": EventSchema(
                event_type="monitor.health",
                version=EventVersion.V1,
                description="健康检查事件",
                required_fields=["health_status", "timestamp"],
                optional_fields=["cpu_usage", "memory_usage", "latency_ms", "error_rate"],
                field_types={
                    "health_status": "string",
                },
            ),
        }

    def register_schema(self, schemas: dict[str, EventSchema]) -> None:
        """注册事件模式"""
        for event_type, schema in schemas.items():
            if event_type not in self.schemas:
                self.schemas[event_type] = {}
            self.schemas[event_type][schema.version.value] = schema

    def get_schema(
        self,
        event_type: str,
        version: EventVersion | None = None,
    ) -> EventSchema | None:
        """获取事件模式"""
        if event_type not in self.schemas:
            return None

        if version is None:
            # 获取最新版本
            versions = self.schemas[event_type]
            if EventVersion.V2.value in versions:
                return versions[EventVersion.V2.value]
            return versions.get(EventVersion.V1.value)

        return self.schemas[event_type].get(version.value)

    def validate_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
    ) -> tuple:
        """
        验证事件数据

        Returns:
            (是否有效, 错误列表)
        """
        schema = self.get_schema(event_type)
        if not schema:
            return False, [f"Unknown event type: {event_type}"]

        errors = []

        # 检查必填字段
        for field_name in schema.required_fields:
            if field_name not in event_data:
                errors.append(f"Missing required field: {field_name}")

        # 检查字段类型
        for field_name, value in event_data.items():
            if field_name in schema.field_types:
                expected_type = schema.field_types[field_name]
                actual_type = type(value).__name__
                if expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field_name}' expected {expected_type}, got {actual_type}")
                elif expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field '{field_name}' expected {expected_type}, got {actual_type}")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Field '{field_name}' expected {expected_type}, got {actual_type}")

        return len(errors) == 0, errors

    def get_all_event_types(self) -> list[str]:
        """获取所有事件类型"""
        return list(self.schemas.keys())

    def get_event_info(self, event_type: str) -> dict | None:
        """获取事件信息"""
        schema = self.get_schema(event_type)
        if not schema:
            return None

        return {
            "event_type": schema.event_type,
            "version": schema.version.value,
            "description": schema.description,
            "required_fields": schema.required_fields,
            "optional_fields": schema.optional_fields,
            "deprecated": schema.deprecated,
        }


# =============================================================================
# Global Registry
# =============================================================================

_global_registry: EventSchemaRegistry | None = None


def get_event_registry() -> EventSchemaRegistry:
    """获取全局事件注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = EventSchemaRegistry()
    return _global_registry
