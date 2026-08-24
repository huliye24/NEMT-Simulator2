"""
EventSourcing - 事件溯源

提供事件溯源模式实现:
- 事件存储
- 聚合根
- 事件处理
- 快照
"""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "DomainEvent",
    "EventStore",
    "AggregateRoot",
    "EventPublisher",
    "SnapshotStore",
]


@dataclass
class DomainEvent:
    """领域事件"""

    event_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    version: int
    timestamp: float
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self, event_type: str, aggregate_id: str, aggregate_type: str, version: int, data: dict, metadata: dict = None
    ):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = version
        self.timestamp = time.time()
        self.data = data
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "version": self.version,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DomainEvent":
        event = cls(
            event_type=data["event_type"],
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            version=data["version"],
            data=data["data"],
            metadata=data.get("metadata", {}),
        )
        event.event_id = data["event_id"]
        event.timestamp = data["timestamp"]
        return event


class EventStore:
    """
    事件存储

    存储和管理领域事件。

    示例:
    ```python
    store = EventStore()

    # 保存事件
    store.append(event)

    # 获取聚合的所有事件
    events = store.get_events(aggregate_id)

    # 获取聚合在特定版本之后的事件
    events = store.get_events(aggregate_id, from_version=10)
    ```
    """

    def __init__(self):
        self._events: list[DomainEvent] = []
        self._by_aggregate: dict[str, list[DomainEvent]] = {}
        self._logger = logging.getLogger("EventStore")

    def append(self, event: DomainEvent) -> None:
        """追加事件"""
        self._events.append(event)

        if event.aggregate_id not in self._by_aggregate:
            self._by_aggregate[event.aggregate_id] = []
        self._by_aggregate[event.aggregate_id].append(event)

    def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
    ) -> list[DomainEvent]:
        """获取聚合的事件"""
        events = self._by_aggregate.get(aggregate_id, [])
        return [e for e in events if e.version > from_version]

    def get_all_events(
        self,
        event_type: str = None,
        from_timestamp: float = 0,
        limit: int = 1000,
    ) -> list[DomainEvent]:
        """获取所有事件"""
        events = self._events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if from_timestamp:
            events = [e for e in events if e.timestamp >= from_timestamp]

        return events[-limit:]

    def get_version(self, aggregate_id: str) -> int:
        """获取聚合的当前版本"""
        events = self._by_aggregate.get(aggregate_id, [])
        if not events:
            return 0
        return max(e.version for e in events)

    def clear(self) -> None:
        """清除所有事件（测试用）"""
        self._events.clear()
        self._by_aggregate.clear()


class EventPublisher:
    """
    事件发布器

    发布领域事件到事件总线。

    示例:
    ```python
    publisher = EventPublisher()

    # 订阅事件
    publisher.subscribe("OrderCreated", handle_order_created)

    # 发布事件
    publisher.publish(event)
    ```
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._all_subscribers: list[Callable] = []
        self._logger = logging.getLogger("EventPublisher")

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅特定事件类型"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable) -> None:
        """订阅所有事件"""
        self._all_subscribers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    def publish(self, event: DomainEvent) -> None:
        """发布事件"""
        # 调用特定类型订阅者
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"事件处理失败: {event.event_type}: {e}")

        # 调用全局订阅者
        for handler in self._all_subscribers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"全局事件处理失败: {event.event_type}: {e}")


class AggregateRoot(ABC):
    """
    聚合根基类

    实现事件溯源的聚合根。

    示例:
    ```python
    class Order(AggregateRoot):
        def __init__(self, order_id: str):
            super().__init__(order_id)
            self._items = []
            self._status = "draft"

        def add_item(self, product_id: str, quantity: int, price: float):
            self.raise_event("OrderItemAdded", {
                "product_id": product_id,
                "quantity": quantity,
                "price": price
            })

        def apply(self, event: DomainEvent):
            if event.event_type == "OrderItemAdded":
                self._items.append(event.data)
    ```
    """

    def __init__(self, aggregate_id: str, aggregate_type: str = None):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type or self.__class__.__name__
        self._version = 0
        self._pending_events: list[DomainEvent] = []
        self._event_store: EventStore | None = None

    @property
    def version(self) -> int:
        return self._version

    def set_event_store(self, event_store: EventStore) -> None:
        self._event_store = event_store

    def raise_event(self, event_type: str, data: dict, metadata: dict = None) -> None:
        """引发事件"""
        event = DomainEvent(
            event_type=event_type,
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            version=self._version + 1,
            data=data,
            metadata=metadata,
        )
        self._pending_events.append(event)

    def load_from_history(self, events: list[DomainEvent]) -> None:
        """从历史事件加载"""
        for event in events:
            self.apply(event)
            self._version = event.version

    def _apply_pending_events(self) -> list[DomainEvent]:
        """应用待处理事件"""
        applied = []
        for event in self._pending_events:
            self.apply(event)
            self._version = event.version
            applied.append(event)

            if self._event_store:
                self._event_store.append(event)

        self._pending_events.clear()
        return applied

    @abstractmethod
    def apply(self, event: DomainEvent) -> None:
        """应用事件"""
        pass

    def get_uncommitted_events(self) -> list[DomainEvent]:
        """获取未提交的事件"""
        return self._pending_events.copy()


class SnapshotStore:
    """
    快照存储

    存储聚合的快照以优化加载速度。

    示例:
    ```python
    snapshot_store = SnapshotStore()

    # 保存快照
    snapshot_store.save("order-123", {
        "status": "completed",
        "items": [...],
        "version": 100
    })

    # 加载快照
    snapshot = snapshot_store.load("order-123")
    ```
    """

    def __init__(self):
        self._snapshots: dict[str, dict] = {}
        self._logger = logging.getLogger("SnapshotStore")

    def save(self, aggregate_id: str, state: dict, version: int) -> None:
        """保存快照"""
        self._snapshots[aggregate_id] = {
            "aggregate_id": aggregate_id,
            "state": state,
            "version": version,
            "timestamp": time.time(),
        }

    def load(self, aggregate_id: str) -> dict | None:
        """加载快照"""
        return self._snapshots.get(aggregate_id)

    def delete(self, aggregate_id: str) -> bool:
        """删除快照"""
        if aggregate_id in self._snapshots:
            del self._snapshots[aggregate_id]
            return True
        return False

    def get_latest_version(self, aggregate_id: str) -> int:
        """获取最新快照版本"""
        snapshot = self._snapshots.get(aggregate_id)
        if snapshot:
            return snapshot.get("version", 0)
        return 0
