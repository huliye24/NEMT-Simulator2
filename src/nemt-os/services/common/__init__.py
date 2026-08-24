"""
NEMT Platform - Common 模块
服务间共享的类型、工具和接口定义
"""

from .config import ServiceConfig
from .logging import get_logger
from .types import (
    EventMessage,
    HealthCheckResponse,
    ServiceInfo,
    ServiceStatus,
)

__all__ = [
    "ServiceInfo",
    "ServiceStatus",
    "HealthCheckResponse",
    "EventMessage",
    "ServiceConfig",
    "get_logger",
]
