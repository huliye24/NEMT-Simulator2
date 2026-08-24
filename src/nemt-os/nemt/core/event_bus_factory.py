"""
EventBus 工厂

创建不同实现的 EventBus 实例。
"""

from enum import Enum
from typing import Any

from nemt.core.adapters.event_bus_adapter import EventBusAdapter
from nemt.core.event_bus import EventBus as OriginalEventBus
from nemt.core.interfaces import IEventBus


class EventBusType(Enum):
    """EventBus 类型"""

    IN_MEMORY = "in_memory"
    REDIS = "redis"  # 预留
    KAFKA = "kafka"  # 预留


class EventBusFactory:
    """
    EventBus 工厂

    创建不同实现的 EventBus 实例。
    """

    _instances: dict[str, IEventBus] = {}

    @classmethod
    def create(
        cls,
        bus_type: EventBusType = EventBusType.IN_MEMORY,
        config: dict[str, Any] | None = None,
        name: str = "default",
    ) -> IEventBus:
        """
        创建 EventBus 实例

        Args:
            bus_type: EventBus 类型
            config: 配置参数
            name: 实例名称

        Returns:
            EventBus 实例
        """
        if name in cls._instances:
            return cls._instances[name]

        if bus_type == EventBusType.IN_MEMORY:
            instance = cls._create_in_memory(config or {})
        elif bus_type == EventBusType.REDIS:
            instance = cls._create_redis(config or {})
        elif bus_type == EventBusType.KAFKA:
            instance = cls._create_kafka(config or {})
        else:
            raise ValueError(f"Unknown EventBus type: {bus_type}")

        cls._instances[name] = instance
        return instance

    @classmethod
    def _create_in_memory(cls, config: dict[str, Any]) -> IEventBus:
        """创建内存版 EventBus"""
        original = OriginalEventBus(
            max_history=config.get("max_history", 1000),
            enable_history=config.get("enable_history", True),
            max_queue_size=config.get("max_queue_size", 10000),
            enable_async=config.get("enable_async", False),
            max_workers=config.get("max_workers", 4),
        )
        return EventBusAdapter(original)

    @classmethod
    def _create_redis(cls, config: dict[str, Any]) -> IEventBus:
        """创建 Redis 版 EventBus (预留)"""
        raise NotImplementedError("Redis EventBus not implemented yet")

    @classmethod
    def _create_kafka(cls, config: dict[str, Any]) -> IEventBus:
        """创建 Kafka 版 EventBus (预留)"""
        raise NotImplementedError("Kafka EventBus not implemented yet")

    @classmethod
    def get_instance(cls, name: str = "default") -> IEventBus | None:
        """获取已创建的实例"""
        return cls._instances.get(name)

    @classmethod
    def clear(cls) -> None:
        """清除所有实例"""
        for instance in cls._instances.values():
            if hasattr(instance, "shutdown"):
                instance.shutdown()
        cls._instances.clear()

    @classmethod
    def list_instances(cls) -> list:
        """列出所有实例"""
        return list(cls._instances.keys())
