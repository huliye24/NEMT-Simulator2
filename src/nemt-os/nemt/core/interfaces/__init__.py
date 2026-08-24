"""
Core Interfaces - 核心接口定义

提供系统核心组件的标准接口。
"""

from .capsule import (
    CapsuleState,
    HealthStatus,
    ICapsule,
    IHealthCheckable,
    IInitializable,
    IMetricsCollector,
    IStartable,
)
from .config_center import (
    IConfigCenter,
    IConfigValidator,
    IConfigWatcher,
)
from .event_bus import (
    Event,
    EventPriority,
    IEventBus,
    IEventPublisher,
    IEventSubscriber,
)
from .storage import (
    IDocumentStorage,
    IKVStorage,
    IStorage,
)

__all__ = [
    # Capsule
    "ICapsule",
    "CapsuleState",
    "HealthStatus",
    "IInitializable",
    "IStartable",
    "IHealthCheckable",
    "IMetricsCollector",
    # EventBus
    "IEventBus",
    "IEventPublisher",
    "IEventSubscriber",
    "Event",
    "EventPriority",
    # Storage
    "IStorage",
    "IKVStorage",
    "IDocumentStorage",
    # ConfigCenter
    "IConfigCenter",
    "IConfigWatcher",
    "IConfigValidator",
]
