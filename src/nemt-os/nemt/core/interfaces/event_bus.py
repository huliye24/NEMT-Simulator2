"""
IEventBus - 事件总线接口定义

定义事件总线的标准接口。
"""

from collections.abc import Callable
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class EventPriority(Enum):
    """事件优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2


class Event:
    """事件对象"""

    def __init__(
        self,
        type: str,
        data: Any = None,
        timestamp: float = None,
        source: str = "",
        priority: EventPriority = EventPriority.NORMAL,
    ):
        import time

        self.type = type
        self.data = data
        self.timestamp = timestamp or time.time()
        self.source = source
        self.priority = priority

    def __repr__(self) -> str:
        return f"Event(type={self.type}, source={self.source})"


@runtime_checkable
class IEventBus(Protocol):
    """
    事件总线接口

    定义事件总线的标准操作。
    """

    def subscribe(self, event_type: str, handler: Callable[[Event], None], priority: EventPriority = None) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 处理函数
            priority: 优先级
        """
        ...

    def subscribe_once(self, event_type: str, handler: Callable[[Event], None], priority: EventPriority = None) -> None:
        """
        订阅一次性事件 - 处理后自动取消订阅

        Args:
            event_type: 事件类型
            handler: 处理函数
            priority: 优先级
        """
        ...

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        ...

    def subscribe_pattern(self, pattern: str, handler: Callable[[Event], None]) -> None:
        """
        订阅事件 (支持通配符)

        Args:
            pattern: 通配符模式，如 'market.*' 匹配所有 market.* 事件
            handler: 处理函数
        """
        ...

    def publish(
        self,
        event_type: str,
        data: Any = None,
        source: str = "",
        priority: EventPriority = None,
    ) -> None:
        """
        发布事件

        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件来源
            priority: 优先级
        """
        ...

    def clear(self, event_type: str = None) -> None:
        """
        清除处理器

        Args:
            event_type: 要清除的事件类型，None 表示清除所有
        """
        ...

    def get_history(self, event_type: str = None, limit: int = 100) -> list[Event]:
        """
        获取事件历史

        Args:
            event_type: 过滤的事件类型
            limit: 返回数量限制

        Returns:
            事件列表
        """
        ...

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计字典
        """
        ...

    def shutdown(self) -> None:
        """关闭事件总线"""
        ...


class IEventPublisher(Protocol):
    """事件发布者接口"""

    def publish(self, event_type: str, data: Any = None) -> None:
        """
        发布事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        ...


class IEventSubscriber(Protocol):
    """事件订阅者接口"""

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        ...

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        ...
