"""
NEMT Platform - NEMT 容器平台

提供完整的容器化、隔离、监控、安全和 API 网关能力。
"""

# 核心模块
from .core import (
    CapsuleManager,
    CapsuleState,
    ConfigCenter,
    DIContainer,
    Event,
    EventBus,
    FractalCapsule,
    HealthStatus,
    ICapsule,
    IEventBus,
    IStorage,
    ModuleCapsule,
)

__version__ = "2.0.0"

__all__ = [
    # 核心
    "ModuleCapsule",
    "FractalCapsule",
    "CapsuleState",
    "EventBus",
    "Event",
    "DIContainer",
    "ConfigCenter",
    "CapsuleManager",
    "ICapsule",
    "HealthStatus",
    "IEventBus",
    "IStorage",
]
