"""
Distributed Module - 分布式模块

提供分布式系统组件:
- 缓存 (MemoryCache, RedisCache, MultiLevelCache)
- 分布式锁 (RedisLock)
- 消息队列 (InMemoryQueue, RedisQueue)
"""

from nemt.distributed.cache import (
    CacheBackend,
    CacheEntry,
    CacheEvictionPolicy,
    CacheStats,
    MemoryCache,
    MultiLevelCache,
    RedisCache,
    get_memory_cache,
    get_redis_cache,
)
from nemt.distributed.lock import (
    DistributedLock,
    LockAcquisitionError,
    LockManager,
    RedisLock,
    get_lock_manager,
)
from nemt.distributed.queue import (
    InMemoryQueue,
    Message,
    MessagePriority,
    MessageQueue,
    QueueConsumer,
    RedisQueue,
    get_queue,
    register_queue,
)

__all__ = [
    # 缓存
    "CacheBackend",
    "CacheEvictionPolicy",
    "CacheStats",
    "CacheEntry",
    "MemoryCache",
    "RedisCache",
    "MultiLevelCache",
    "get_memory_cache",
    "get_redis_cache",
    # 锁
    "DistributedLock",
    "RedisLock",
    "LockAcquisitionError",
    "LockManager",
    "get_lock_manager",
    # 队列
    "Message",
    "MessagePriority",
    "MessageQueue",
    "QueueConsumer",
    "InMemoryQueue",
    "RedisQueue",
    "get_queue",
    "register_queue",
]
