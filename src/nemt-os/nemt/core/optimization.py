"""
Performance Optimization Module

提供性能优化功能:
- 对象池
- 缓存
- 批量操作
"""

from typing import Any, Dict, Generic, TypeVar, Optional, Callable, List
from collections import OrderedDict
import threading
import time
import weakref

__all__ = ["ObjectPool", "LRUCache", "BatchProcessor"]


T = TypeVar("T")


class ObjectPool(Generic[T]):
    """
    对象池 - 复用对象减少 GC 压力

    示例:
    ```python
    pool = ObjectPool(factory=lambda: ExpensiveObject())
    obj = pool.acquire()
    # 使用 obj
    pool.release(obj)
    ```
    """

    def __init__(self, factory: Callable[[], T], max_size: int = 1000, cleanup_size: int = 100):
        """
        初始化对象池

        Args:
            factory: 对象工厂函数
            max_size: 最大池大小
            cleanup_size: 清理时释放的对象数量
        """
        self._factory = factory
        self._max_size = max_size
        self._cleanup_size = cleanup_size

        self._pool: List[T] = []
        self._lock = threading.Lock()

        # 统计
        self._created = 0
        self._reused = 0
        self._released = 0

    def acquire(self) -> T:
        """
        获取对象

        Returns:
            对象实例
        """
        with self._lock:
            if self._pool:
                self._reused += 1
                return self._pool.pop()

            self._created += 1
            return self._factory()

    def release(self, obj: T) -> None:
        """
        释放对象回池

        Args:
            obj: 对象实例
        """
        with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(obj)
                self._released += 1
            # 超过最大大小时，对象被丢弃，GC 处理

    def clear(self) -> int:
        """
        清空池

        Returns:
            清空的对象数量
        """
        with self._lock:
            count = len(self._pool)
            self._pool.clear()
            return count

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = self._created + self._reused
            return {
                "pool_size": len(self._pool),
                "max_size": self._max_size,
                "created": self._created,
                "reused": self._reused,
                "released": self._released,
                "reuse_rate": self._reused / total if total > 0 else 0,
            }


class LRUCache(Generic[T]):
    """
    LRU 缓存 - 最近最少使用缓存

    示例:
    ```python
    cache = LRUCache(max_size=100, ttl=3600)
    cache['key'] = 'value'
    value = cache.get('key')
    ```
    """

    def __init__(self, max_size: int = 1000, ttl: float = None, on_evict: Callable[[str, T], None] = None):
        """
        初始化 LRU 缓存

        Args:
            max_size: 最大缓存数量
            ttl: 过期时间(秒)，None 表示永不过期
            on_evict: 驱逐回调
        """
        self._max_size = max_size
        self._ttl = ttl
        self._on_evict = on_evict

        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

        # 统计
        self._hits = 0
        self._misses = 0

    def get(self, key: str, default: T = None) -> T:
        """
        获取缓存

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default

            # 检查过期
            if self._ttl:
                timestamp = self._timestamps.get(key, 0)
                if time.time() - timestamp > self._ttl:
                    self._evict(key)
                    self._misses += 1
                    return default

            # 移到末尾(最近使用)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def set(self, key: str, value: T) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
        """
        with self._lock:
            # 如果已存在，移除旧值
            if key in self._cache:
                self._evict(key)

            # 添加新值
            self._cache[key] = value
            self._timestamps[key] = time.time()

            # 检查容量
            if len(self._cache) > self._max_size:
                self._evict_oldest()

    def _evict(self, key: str) -> None:
        """驱逐指定键"""
        if key in self._cache:
            value = self._cache.pop(key)
            self._timestamps.pop(key, None)

            if self._on_evict:
                try:
                    self._on_evict(key, value)
                except Exception:
                    pass

    def _evict_oldest(self) -> None:
        """驱逐最旧的条目"""
        if self._cache:
            key = next(iter(self._cache))
            self._evict(key)

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                self._evict(key)
                return True
            return False

    def clear(self) -> int:
        """
        清空缓存

        Returns:
            清空的数量
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            return count

    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            return key in self._cache

    def __len__(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0,
            }


class BatchProcessor(Generic[T]):
    """
    批量处理器 - 聚合操作减少调用次数

    示例:
    ```python
    def process_batch(items):
        # 批量处理
        return [process(item) for item in items]

    processor = BatchProcessor(process_batch, batch_size=100, max_delay=0.1)

    for item in items:
        processor.add(item)

    processor.flush()  # 确保处理完成
    ```
    """

    def __init__(
        self,
        processor: Callable[[List[T]], List[Any]],
        batch_size: int = 100,
        max_delay: float = 0.1,
        max_queue_size: int = 10000,
    ):
        """
        初始化批量处理器

        Args:
            processor: 批量处理函数
            batch_size: 批大小
            max_delay: 最大延迟(秒)
            max_queue_size: 最大队列大小
        """
        self._processor = processor
        self._batch_size = batch_size
        self._max_delay = max_delay
        self._max_queue_size = max_queue_size

        self._queue: List[T] = []
        self._lock = threading.Lock()
        self._last_flush = time.time()

        # 统计
        self._batches_processed = 0
        self._items_processed = 0

    def add(self, item: T) -> None:
        """
        添加项目

        Args:
            item: 项目
        """
        with self._lock:
            if len(self._queue) >= self._max_queue_size:
                self.flush()

            self._queue.append(item)

            # 检查是否需要自动刷新
            if len(self._queue) >= self._batch_size:
                self._do_flush()

    def add_batch(self, items: List[T]) -> None:
        """
        批量添加

        Args:
            items: 项目列表
        """
        for item in items:
            self.add(item)

    def flush(self) -> List[Any]:
        """
        刷新队列

        Returns:
            处理结果列表
        """
        with self._lock:
            return self._do_flush()

    def _do_flush(self) -> List[Any]:
        """执行刷新"""
        if not self._queue:
            return []

        batch = self._queue[: self._batch_size]
        self._queue = self._queue[self._batch_size :]

        if batch:
            results = self._processor(batch)
            self._batches_processed += 1
            self._items_processed += len(batch)

        self._last_flush = time.time()
        return results if batch else []

    def should_flush(self) -> bool:
        """检查是否应该刷新"""
        with self._lock:
            if not self._queue:
                return False

            if len(self._queue) >= self._batch_size:
                return True

            if self._max_delay > 0:
                elapsed = time.time() - self._last_flush
                if elapsed >= self._max_delay:
                    return True

            return False

    def __len__(self) -> int:
        """获取队列大小"""
        with self._lock:
            return len(self._queue)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "queue_size": len(self._queue),
                "batches_processed": self._batches_processed,
                "items_processed": self._items_processed,
            }


# 预定义对象池
class EventPool(ObjectPool):
    """Event 对象池"""

    def __init__(self, max_size: int = 1000):
        from nemt.core.event_bus import Event

        def factory():
            return Event("")

        super().__init__(factory, max_size)

    def acquire(self, type_: str, data: Any = None) -> "Event":
        """获取 Event 对象"""
        event = super().acquire()
        event.type = type_
        event.data = data
        event.timestamp = time.time()
        return event
