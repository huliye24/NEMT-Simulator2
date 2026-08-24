"""
NEMT Platform - 通用类型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ServiceStatus(Enum):
    """服务状态"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceInfo:
    """服务信息"""

    service_name: str
    host: str
    port: int
    status: ServiceStatus = ServiceStatus.STARTING
    version: str = "1.0.0"
    started_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "host": self.host,
            "port": self.port,
            "status": self.status.value,
            "version": self.version,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "metadata": self.metadata,
        }


@dataclass
class HealthCheckResponse:
    """健康检查响应"""

    service_name: str
    status: ServiceStatus
    timestamp: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0.0
    version: str = "1.0.0"
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "version": self.version,
            "checks": self.checks,
        }


@dataclass
class EventMessage:
    """事件消息"""

    event_type: str
    source: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }


# 事件类型常量
class EventTypes:
    """事件类型定义"""

    # Market 事件
    MARKET_BAR = "market.bar"
    MARKET_PRICE = "market.price"
    MARKET_CANDLE_CLOSED = "market.candle_closed"

    # Signal 事件
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_CONFIDENCE_UPDATE = "signal.confidence_update"

    # Risk 事件
    RISK_APPROVED = "risk.approved"
    RISK_REJECTED = "risk.rejected"
    RISK_ALERT = "risk.alert"

    # Execution 事件
    EXECUTION_ORDER_SENT = "execution.order_sent"
    EXECUTION_FILLED = "execution.filled"
    EXECUTION_POSITION_UPDATE = "execution.position_update"

    # Brain 事件
    BRAIN_DECISION = "brain.decision"
    BRAIN_EVOLUTION = "brain.evolution"
