"""
EventBus 适配器

将现有的 EventBus 类适配到 IEventBus 接口。
"""

from collections.abc import Callable
from typing import Any

from nemt.core.event_bus import Event as OriginalEvent
from nemt.core.event_bus import EventBus as OriginalEventBus
from nemt.core.event_bus import EventPriority as OriginalPriority
from nemt.core.interfaces.event_bus import Event, EventPriority, IEventBus


class EventBusAdapter(IEventBus):
    """
    EventBus 适配器

    将原有 EventBus 实现适配到 IEventBus 接口。
    """

    def __init__(self, original: OriginalEventBus):
        self._original = original

    def subscribe(self, event_type: str, handler: Callable[[Event], None], priority: EventPriority = None) -> None:
        orig_priority = self._convert_priority(priority) if priority else None
        wrapped_handler = self._wrap_handler(handler)
        self._original.subscribe(event_type, wrapped_handler, orig_priority)

    def subscribe_once(self, event_type: str, handler: Callable[[Event], None], priority: EventPriority = None) -> None:
        orig_priority = self._convert_priority(priority) if priority else None
        wrapped_handler = self._wrap_handler(handler)
        self._original.subscribe_once(event_type, wrapped_handler, orig_priority)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        # 查找原始处理器
        self._original.unsubscribe(event_type, handler)

    def subscribe_pattern(self, pattern: str, handler: Callable[[Event], None]) -> None:
        wrapped_handler = self._wrap_handler(handler)
        self._original.subscribe_pattern(pattern, wrapped_handler)

    def publish(
        self,
        event_type: str,
        data: Any = None,
        source: str = "",
        priority: EventPriority = None,
    ) -> None:
        orig_priority = self._convert_priority(priority) if priority else None
        self._original.publish(event_type, data, source, orig_priority)

    def clear(self, event_type: str = None) -> None:
        self._original.clear(event_type)

    def get_history(self, event_type: str = None, limit: int = 100) -> list[Event]:
        original_history = self._original.get_history(event_type, limit)
        return [self._convert_event(e) for e in original_history]

    def get_stats(self) -> dict[str, Any]:
        return self._original.get_stats()

    def shutdown(self) -> None:
        self._original.shutdown()

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _wrap_handler(self, handler: Callable[[Event], None]) -> Callable:
        """包装处理器，转换事件类型"""

        def wrapped(original_event: OriginalEvent):
            new_event = self._convert_event(original_event)
            handler(new_event)

        return wrapped

    def _convert_event(self, original: OriginalEvent) -> Event:
        """转换事件类型"""
        priority = self._convert_priority_from_original(original.priority)
        return Event(
            type=original.type,
            data=original.data,
            timestamp=original.timestamp,
            source=original.source,
            priority=priority,
        )

    def _convert_priority(self, priority: EventPriority) -> OriginalPriority:
        """转换优先级"""
        mapping = {
            EventPriority.LOW: OriginalPriority.LOW,
            EventPriority.NORMAL: OriginalPriority.NORMAL,
            EventPriority.HIGH: OriginalPriority.HIGH,
        }
        return mapping.get(priority, OriginalPriority.NORMAL)

    def _convert_priority_from_original(self, original: OriginalPriority) -> EventPriority:
        """从原始优先级转换"""
        mapping = {
            OriginalPriority.LOW: EventPriority.LOW,
            OriginalPriority.NORMAL: EventPriority.NORMAL,
            OriginalPriority.HIGH: EventPriority.HIGH,
        }
        return mapping.get(original, EventPriority.NORMAL)

    # ========================================================================
    # 便捷方法 (原有功能)
    # ========================================================================

    def add_filter(self, event_type: str, event_filter) -> None:
        """添加事件过滤器"""
        self._original.add_filter(event_type, event_filter)

    def publish_batch(self, events: list[tuple]) -> None:
        """批量发布事件"""
        self._original.publish_batch(events)

    def wait_for_event(self, event_type: str, timeout: float = None) -> Event | None:
        """等待特定事件"""
        original = self._original.wait_for_event(event_type, timeout)
        if original:
            return self._convert_event(original)
        return None

    def get_subscription_count(self, event_type: str) -> int:
        """获取订阅者数量"""
        return self._original.get_subscription_count(event_type)

    def is_subscribed(self, event_type: str, handler: Callable) -> bool:
        """检查是否已订阅"""
        return self._original.is_subscribed(event_type, handler)

    def clear_history(self) -> None:
        """清除历史记录"""
        self._original.clear_history()

    def replay_history(self, limit: int = None, handler: Callable[[Event], None] = None) -> None:
        """重放历史事件"""

        def wrapped_handler(event: OriginalEvent):
            if handler:
                handler(self._convert_event(event))

        self._original.replay_history(limit, wrapped_handler)
