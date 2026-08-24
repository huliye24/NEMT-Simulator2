"""
Cache - 缓存模块

提供多级缓存支持:
- 本地内存缓存
- Redis 分布式缓存
- 缓存策略 (LRU, LFU, TTL)
"""

import json
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    "CacheBackend",
    "MemoryCache",
    "RedisCache",
    "MultiLevelCache",
    "CacheStats",
]


class CacheEvictionPolicy(Enum):
    """缓存淘汰策略"""

    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最不经常使用
    FIFO = "fifo"  # 先进先出
    TTL = "ttl"  # 基于 TTL


@dataclass
class CacheStats:
    """缓存统计"""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: float = -1  # -1 表示永不过期

    def is_expired(self) -> bool:
        if self.ttl < 0:
            return False
        return time.time() - self.created_at > self.ttl


class MemoryCache:
    """
    内存缓存

    示例:
    ```python
    cache = MemoryCache(max_size=1000, ttl=3600)

    cache.set("key", "value")
    value = cache.get("key")
    cache.delete("key")
    ```
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: float = -1,
        eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU,
    ):
        self.max_size = max_size
        self.ttl = ttl
        self.policy = eviction_policy
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.RLock()

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.misses += 1
                return default

            if entry.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return default

            # 更新访问信息
            entry.accessed_at = time.time()
            entry.access_count += 1

            # LRU: 移到末尾
            if self.policy == CacheEvictionPolicy.LRU:
                self._cache.move_to_end(key)

            self._stats.hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: float = None) -> None:
        """设置缓存"""
        with self._lock:
            now = time.time()
            ttl = ttl if ttl is not None else self.ttl

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                access_count=1,
                ttl=ttl,
            )

            # 如果 key 已存在，先删除
            if key in self._cache:
                del self._cache[key]

            # 如果缓存已满，淘汰
            while len(self._cache) >= self.max_size:
                self._evict()

            self._cache[key] = entry
            self._stats.sets += 1

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.deletes += 1
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def _evict(self) -> None:
        """淘汰缓存条目"""
        if not self._cache:
            return

        if self.policy == CacheEvictionPolicy.LRU:
            self._cache.popitem(last=False)
        elif self.policy == CacheEvictionPolicy.LFU:
            # 淘汰访问次数最少的
            min_entry = min(self._cache.values(), key=lambda e: e.access_count)
            del self._cache[min_entry.key]
        elif self.policy == CacheEvictionPolicy.FIFO:
            self._cache.popitem(last=False)
        elif self.policy == CacheEvictionPolicy.TTL:
            # 淘汰最早过期的
            expired = [(k, e) for k, e in self._cache.items() if e.is_expired()]
            if expired:
                del self._cache[expired[0][0]]
            else:
                self._cache.popitem(last=False)

        self._stats.evictions += 1

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self._lock:
            expired = [k for k, e in self._cache.items() if e.is_expired()]
            for key in expired:
                del self._cache[key]
                self._stats.evictions += 1
            return len(expired)

    def get_stats(self) -> CacheStats:
        """获取统计"""
        with self._lock:
            stats = CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                sets=self._stats.sets,
                deletes=self._stats.deletes,
                evictions=self._stats.evictions,
                size=len(self._cache),
            )
        return stats

    def keys(self) -> list[str]:
        """获取所有键"""
        with self._lock:
            return list(self._cache.keys())

    def __contains__(self, key: str) -> bool:
        return key in self._cache and not self._cache[key].is_expired()

    def __len__(self) -> int:
        return len(self._cache)


class RedisCache:
    """
    Redis 缓存

    示例:
    ```python
    cache = RedisCache(host="localhost", port=6379, db=0)

    cache.set("key", "value", ttl=3600)
    value = cache.get("key")
    ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = None,
        prefix: str = "nemt:cache:",
        ttl: float = -1,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self.default_ttl = ttl
        self._client = None
        self._stats = CacheStats()
        self._lock = threading.Lock()
        self._logger = logging.getLogger("RedisCache")

    def _get_client(self):
        """获取 Redis 客户端"""
        if self._client is None:
            try:
                import redis

                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                )
            except ImportError:
                self._logger.warning("Redis 未安装，使用内存缓存作为后备")
                return None
        return self._client

    def _make_key(self, key: str) -> str:
        """生成带前缀的键"""
        return f"{self.prefix}{key}"

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        client = self._get_client()
        if client is None:
            return default

        with self._lock:
            try:
                full_key = self._make_key(key)
                value = client.get(full_key)

                if value is None:
                    self._stats.misses += 1
                    return default

                self._stats.hits += 1
                return json.loads(value)

            except Exception as e:
                self._logger.error(f"Redis get 失败: {e}")
                self._stats.misses += 1
                return default

    def set(self, key: str, value: Any, ttl: float = None) -> None:
        """设置缓存"""
        client = self._get_client()
        if client is None:
            return

        with self._lock:
            try:
                full_key = self._make_key(key)
                serialized = json.dumps(value)

                if ttl is None:
                    ttl = self.default_ttl

                if ttl > 0:
                    client.setex(full_key, ttl, serialized)
                else:
                    client.set(full_key, serialized)

                self._stats.sets += 1

            except Exception as e:
                self._logger.error(f"Redis set 失败: {e}")

    def delete(self, key: str) -> bool:
        """删除缓存"""
        client = self._get_client()
        if client is None:
            return False

        with self._lock:
            try:
                full_key = self._make_key(key)
                result = client.delete(full_key)
                if result:
                    self._stats.deletes += 1
                return bool(result)
            except Exception as e:
                self._logger.error(f"Redis delete 失败: {e}")
                return False

    def clear(self) -> None:
        """清空缓存"""
        client = self._get_client()
        if client is None:
            return

        with self._lock:
            try:
                pattern = f"{self.prefix}*"
                keys = client.keys(pattern)
                if keys:
                    client.delete(*keys)
            except Exception as e:
                self._logger.error(f"Redis clear 失败: {e}")

    def get_stats(self) -> CacheStats:
        """获取统计"""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                sets=self._stats.sets,
                deletes=self._stats.deletes,
                evictions=self._stats.evictions,
            )

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        client = self._get_client()
        if client is None:
            return False

        try:
            return bool(client.exists(self._make_key(key)))
        except Exception:
            return False


class MultiLevelCache:
    """
    多级缓存

    示例:
    ```python
    l1 = MemoryCache(max_size=100)
    l2 = RedisCache(prefix="nemt:l2:")

    cache = MultiLevelCache([l1, l2])

    # 读取: L1 -> L2 -> DB
    value = cache.get("key")

    # 写入: L1 -> L2
    cache.set("key", "value")
    ```
    """

    def __init__(self, levels: list[tuple[CacheBackend, str]]):
        """
        Args:
            levels: [(缓存实例, 描述), ...]，从 L1 到 Ln
        """
        self.levels = levels
        self._stats = CacheStats()

    def get(self, key: str, default: Any = None) -> Any:
        """从所有级别获取缓存"""
        for i, (cache, name) in enumerate(self.levels):
            value = cache.get(key, default=None)
            if value is not None:
                self._stats.hits += 1
                # 写入到更高级别
                for j in range(i):
                    self.levels[j][0].set(key, value)
                return value

        self._stats.misses += 1
        return default

    def set(self, key: str, value: Any, ttl: float = None) -> None:
        """写入所有级别"""
        for cache, _ in self.levels:
            cache.set(key, value, ttl)
        self._stats.sets += 1

    def delete(self, key: str) -> None:
        """从所有级别删除"""
        for cache, _ in self.levels:
            cache.delete(key)
        self._stats.deletes += 1

    def clear(self) -> None:
        """清空所有级别"""
        for cache, _ in self.levels:
            cache.clear()

    def get_stats(self) -> dict[str, CacheStats]:
        """获取所有级别的统计"""
        return {name: cache.get_stats() for cache, name in self.levels}


# 类型别名
CacheBackend = MemoryCache | RedisCache | MultiLevelCache


# 全局缓存实例
_memory_cache: MemoryCache | None = None
_redis_cache: RedisCache | None = None


def get_memory_cache() -> MemoryCache:
    """获取全局内存缓存"""
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache()
    return _memory_cache


def get_redis_cache() -> RedisCache:
    """获取全局 Redis 缓存"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache
