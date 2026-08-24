"""
EventBus - 事件总线模块

提供发布-订阅模式的事件处理，支持:
- 事件订阅与取消订阅
- 通配符模式订阅
- 线程安全
- 错误隔离与重试
- 事件历史记录
- 异步事件处理
- 事件过滤与转换
"""

from typing import Any, Callable, Dict, List, Set, Optional, TypeVar, Generic
from dataclasses import dataclass, field
import threading
import time
import logging
import queue
from collections import deque
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
import fnmatch
import weakref

__all__ = ["EventBus", "Event", "EventPriority", "EventFilter"]


class EventPriority(Enum):
    """事件优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2


@dataclass
class Event:
    """
    事件对象

    Attributes:
        type: 事件类型
        data: 事件数据
        timestamp: 时间戳
        source: 事件来源
        priority: 优先级
    """

    type: str
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    priority: EventPriority = EventPriority.NORMAL


class EventFilter:
    """事件过滤器"""

    def __init__(self, event_type: str = None, filter_func: Callable[[Event], bool] = None):
        self.event_type = event_type
        self.filter_func = filter_func

    def match(self, event: Event) -> bool:
        """检查事件是否匹配"""
        if self.event_type and event.type != self.event_type:
            return False
        if self.filter_func and not self.filter_func(event):
            return False
        return True


class EventBus:
    """
    事件总线 - 发布-订阅模式的事件处理中心

    支持特性:
    - 线程安全
    - 错误隔离 (一个 handler 错误不影响其他 handler)
    - 通配符订阅 (如 'market.*')
    - 事件历史记录
    - 异步事件处理
    - 优先级处理
    - 事件过滤
    """

    def __init__(
        self,
        max_history: int = 1000,
        enable_history: bool = True,
        max_queue_size: int = 10000,
        enable_async: bool = False,
        max_workers: int = 4,
    ):
        """
        初始化事件总线

        Args:
            max_history: 最大历史记录数
            enable_history: 是否启用历史记录
            max_queue_size: 最大队列大小
            enable_async: 是否启用异步处理
            max_workers: 异步处理线程数
        """
        self._handlers: Dict[str, List[tuple[Callable, EventPriority]]] = {}
        self._pattern_handlers: List[tuple[str, Callable]] = []
        self._lock = threading.RLock()
        self._logger = logging.getLogger("EventBus")

        # 历史记录
        self._enable_history = enable_history
        self._max_history = max_history
        self._history: deque = deque(maxlen=max_history)

        # 异步处理
        self._enable_async = enable_async
        self._executor: Optional[ThreadPoolExecutor] = None
        if enable_async:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
            self._event_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
            self._async_thread = threading.Thread(target=self._process_async_events, daemon=True)
            self._async_thread.start()

        # 统计
        self._event_count = 0
        self._handler_count = 0
        self._error_count = 0
        self._dropped_count = 0

        # 过滤器
        self._filters: Dict[str, List[EventFilter]] = {}

    def subscribe(
        self, event_type: str, handler: Callable[[Event], None], priority: EventPriority = EventPriority.NORMAL
    ) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 处理函数
            priority: 优先级
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []

            # 检查是否已存在
            for existing_handler, _ in self._handlers[event_type]:
                if existing_handler == handler:
                    return

            self._handlers[event_type].append((handler, priority))
            # 按优先级排序
            self._handlers[event_type].sort(key=lambda x: x[1].value, reverse=True)
            self._update_handler_count()

    def subscribe_once(
        self, event_type: str, handler: Callable[[Event], None], priority: EventPriority = EventPriority.NORMAL
    ) -> None:
        """
        订阅一次性事件 - 处理后自动取消订阅

        Args:
            event_type: 事件类型
            handler: 处理函数
            priority: 优先级
        """

        def wrapper(event: Event):
            handler(event)
            self.unsubscribe(event_type, wrapper)

        self.subscribe(event_type, wrapper, priority)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type] = [(h, p) for h, p in self._handlers[event_type] if h != handler]
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
                self._update_handler_count()

    def subscribe_pattern(self, pattern: str, handler: Callable[[Event], None]) -> None:
        """
        订阅事件 (支持通配符)

        Args:
            pattern: 通配符模式，如 'market.*' 匹配所有 market.* 事件
            handler: 处理函数
        """
        with self._lock:
            self._pattern_handlers.append((pattern, handler))

    def unsubscribe_pattern(self, pattern: str, handler: Callable) -> None:
        """
        取消订阅 (通配符)

        Args:
            pattern: 通配符模式
            handler: 处理函数
        """
        with self._lock:
            self._pattern_handlers = [(p, h) for p, h in self._pattern_handlers if p != pattern or h != handler]

    def add_filter(self, event_type: str, event_filter: EventFilter) -> None:
        """
        添加事件过滤器

        Args:
            event_type: 事件类型
            event_filter: 过滤器
        """
        with self._lock:
            if event_type not in self._filters:
                self._filters[event_type] = []
            self._filters[event_type].append(event_filter)

    def publish(
        self,
        event_type: str,
        data: Any = None,
        source: str = "",
        priority: EventPriority = EventPriority.NORMAL,
        async_: bool = None,
    ) -> None:
        """
        发布事件

        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件来源
            priority: 优先级
            async_: 是否异步处理，默认使用全局设置
        """
        event = Event(type=event_type, data=data, timestamp=time.time(), source=source, priority=priority)
        self._event_count += 1

        # 检查过滤器
        if self._should_filter(event):
            return

        # 记录历史
        if self._enable_history:
            self._history.append(event)

        # 异步处理
        if async_ if async_ is not None else self._enable_async:
            self._publish_async(event)
        else:
            self._dispatch(event)

    def _should_filter(self, event: Event) -> bool:
        """检查是否应该过滤"""
        with self._lock:
            filters = self._filters.get(event.type, [])
            for event_filter in filters:
                if not event_filter.match(event):
                    return True
        return False

    def _publish_async(self, event: Event) -> None:
        """异步发布"""
        try:
            self._event_queue.put_nowait(event)
        except queue.Full:
            self._dropped_count += 1
            self._logger.warning(f"事件队列已满，丢弃事件: {event.type}")

    def _process_async_events(self) -> None:
        """异步事件处理线程"""
        while True:
            try:
                event = self._event_queue.get(timeout=1)
                self._dispatch(event)
            except queue.Empty:
                continue
            except Exception as e:
                self._logger.error(f"异步事件处理错误: {e}")

    def _dispatch(self, event: Event) -> None:
        """分发事件到处理器"""
        # 获取处理器
        handlers = []
        with self._lock:
            # 精确匹配
            if event.type in self._handlers:
                handlers.extend(self._handlers[event.type])

            # 模式匹配
            for pattern, handler in self._pattern_handlers:
                if fnmatch.fnmatch(event.type, pattern):
                    handlers.append((handler, EventPriority.NORMAL))

        # 去重并按优先级排序
        seen = set()
        unique_handlers = []
        for handler, priority in handlers:
            handler_id = id(handler)
            if handler_id not in seen:
                seen.add(handler_id)
                unique_handlers.append((handler, priority))

        unique_handlers.sort(key=lambda x: x[1].value, reverse=True)

        # 执行
        for handler, _ in unique_handlers:
            try:
                handler(event)
            except Exception as e:
                self._error_count += 1
                self._logger.error(f"事件处理错误 [{event.type}]: {e}")

    def publish_batch(self, events: List[tuple[str, Any]]) -> None:
        """
        批量发布事件

        Args:
            events: 事件列表 [(event_type, data), ...]
        """
        for event_type, data in events:
            self.publish(event_type, data)

    def clear(self, event_type: str = None) -> None:
        """
        清除处理器

        Args:
            event_type: 要清除的事件类型，None 表示清除所有
        """
        with self._lock:
            if event_type:
                self._handlers.pop(event_type, None)
                self._filters.pop(event_type, None)
            else:
                self._handlers.clear()
                self._filters.clear()
                self._pattern_handlers.clear()
            self._update_handler_count()

    def clear_history(self) -> None:
        """清除历史记录"""
        self._history.clear()

    def get_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """
        获取事件历史

        Args:
            event_type: 过滤的事件类型
            limit: 返回数量限制

        Returns:
            事件列表
        """
        history = list(self._history)

        if event_type:
            history = [e for e in history if e.type == event_type]

        return history[-limit:]

    def replay_history(self, limit: int = None, handler: Callable[[Event], None] = None) -> None:
        """
        重放历史事件

        Args:
            limit: 重放数量限制
            handler: 自定义处理器
        """
        history = self.get_history(limit=limit) if limit else list(self._history)

        for event in history:
            if handler:
                handler(event)
            else:
                self._dispatch(event)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "event_count": self._event_count,
                "handler_count": self._handler_count,
                "error_count": self._error_count,
                "dropped_count": self._dropped_count,
                "event_types": len(self._handlers),
                "patterns": len(self._pattern_handlers),
                "history_size": len(self._history),
                "history_max": self._max_history,
                "queue_size": self._event_queue.qsize() if self._enable_async else 0,
            }

    def get_subscription_count(self, event_type: str) -> int:
        """获取指定事件类型的订阅者数量"""
        with self._lock:
            return len(self._handlers.get(event_type, []))

    def is_subscribed(self, event_type: str, handler: Callable) -> bool:
        """检查是否已订阅"""
        with self._lock:
            return any(h == handler for h, _ in self._handlers.get(event_type, []))

    def _update_handler_count(self) -> None:
        """更新处理器计数"""
        self._handler_count = sum(len(h) for h in self._handlers.values())

    def wait_for_event(self, event_type: str, timeout: float = None) -> Optional[Event]:
        """
        等待特定事件

        Args:
            event_type: 事件类型
            timeout: 超时时间

        Returns:
            事件或 None
        """
        result = [None]
        event_set = threading.Event()

        def handler(event):
            result[0] = event
            event_set.set()

        self.subscribe_once(event_type, handler)

        if event_set.wait(timeout=timeout):
            return result[0]
        return None

    def shutdown(self) -> None:
        """关闭事件总线"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def __repr__(self) -> str:
        return f"EventBus(events={self._event_count}, handlers={self._handler_count})"
