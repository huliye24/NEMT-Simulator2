"""
DistributedLock - 分布式锁

提供分布式锁实现:
- Redis 分布式锁
- 可重入锁
- 锁超时
"""

import logging
import threading
import time
import uuid
from contextlib import contextmanager

__all__ = [
    "DistributedLock",
    "RedisLock",
    "LockAcquisitionError",
]


class LockAcquisitionError(Exception):
    """锁获取失败异常"""

    pass


class DistributedLock:
    """
    分布式锁基类
    """

    def __init__(self, name: str, timeout: float = 30.0, retry_times: int = 0, retry_delay: float = 0.1):
        self.name = name
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self._lock_id = str(uuid.uuid4())
        self._acquired = False

    def acquire(self) -> bool:
        """获取锁"""
        raise NotImplementedError

    def release(self) -> bool:
        """释放锁"""
        raise NotImplementedError

    def extend(self, additional_time: float) -> bool:
        """延长锁的持有时间"""
        raise NotImplementedError

    @contextmanager
    def lock(self, blocking: bool = True):
        """上下文管理器"""
        if blocking:
            acquired = self.acquire()
            if not acquired:
                raise LockAcquisitionError(f"Failed to acquire lock: {self.name}")
        else:
            acquired = self.acquire()
            if not acquired:
                yield False
                return

        try:
            yield True
        finally:
            if acquired:
                self.release()


class RedisLock(DistributedLock):
    """
    Redis 分布式锁

    基于 Redis 实现的分布式锁，支持:
    - 自动过期
    - 可重入
    - 锁续期

    示例:
    ```python
    lock = RedisLock("my_lock", timeout=30)

    # 阻塞获取
    if lock.acquire():
        try:
            # 临界区代码
            pass
        finally:
            lock.release()

    # 使用上下文管理器
    with lock.lock():
        # 临界区代码
        pass
    ```
    """

    def __init__(
        self,
        name: str,
        timeout: float = 30.0,
        retry_times: int = 0,
        retry_delay: float = 0.1,
        redis_client=None,
        prefix: str = "nemt:lock:",
    ):
        super().__init__(name, timeout, retry_times, retry_delay)
        self.redis_client = redis_client
        self.prefix = prefix
        self.full_name = f"{prefix}{name}"
        self._local_thread_lock = threading.Lock()
        self._thread_lock_count = {}

    def _get_client(self):
        """获取 Redis 客户端"""
        if self.redis_client is None:
            try:
                import redis

                self.redis_client = redis.Redis(decode_responses=True)
            except ImportError:
                logging.warning("Redis 未安装，分布式锁不可用")
                return None
        return self.redis_client

    def acquire(self) -> bool:
        """获取锁"""
        client = self._get_client()
        if client is None:
            # 回退到本地锁
            return self._acquire_local()

        for attempt in range(self.retry_times + 1):
            try:
                # 使用 SET NX EX 原子操作
                acquired = client.set(
                    self.full_name,
                    self._lock_id,
                    nx=True,
                    ex=int(self.timeout),
                )

                if acquired:
                    self._acquired = True
                    return True

                if attempt < self.retry_times:
                    time.sleep(self.retry_delay)

            except Exception as e:
                logging.error(f"获取分布式锁失败: {e}")
                return self._acquire_local()

        return self._acquire_local()

    def _acquire_local(self) -> bool:
        """获取本地锁（后备）"""
        with self._local_thread_lock:
            thread_id = threading.get_ident()
            count = self._thread_lock_count.get(thread_id, 0)

            if count > 0:
                # 可重入
                self._thread_lock_count[thread_id] = count + 1
                self._acquired = True
                return True

            # 新锁
            self._thread_lock_count[thread_id] = 1
            self._acquired = True
            return True

    def release(self) -> bool:
        """释放锁"""
        if not self._acquired:
            return False

        client = self._get_client()
        if client is None:
            return self._release_local()

        try:
            # 使用 Lua 脚本确保原子性删除
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = client.eval(lua_script, 1, self.full_name, self._lock_id)
            self._acquired = False
            return bool(result)

        except Exception as e:
            logging.error(f"释放分布式锁失败: {e}")
            return self._release_local()

    def _release_local(self) -> bool:
        """释放本地锁"""
        with self._local_thread_lock:
            thread_id = threading.get_ident()
            count = self._thread_lock_count.get(thread_id, 0)

            if count > 1:
                self._thread_lock_count[thread_id] = count - 1
            elif count == 1:
                del self._thread_lock_count[thread_id]
                self._acquired = False
            return True

    def extend(self, additional_time: float) -> bool:
        """延长锁的持有时间"""
        client = self._get_client()
        if client is None:
            return True  # 本地锁不需要续期

        try:
            # 使用 Lua 脚本确保原子性续期
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            result = client.eval(lua_script, 1, self.full_name, self._lock_id, int(additional_time))
            return bool(result)

        except Exception as e:
            logging.error(f"延长锁时间失败: {e}")
            return False

    def is_locked(self) -> bool:
        """检查锁是否被持有"""
        client = self._get_client()
        if client is None:
            return self._acquired

        try:
            return bool(client.exists(self.full_name))
        except Exception:
            return self._acquired


class LockManager:
    """
    锁管理器

    管理多个分布式锁。

    示例:
    ```python
    manager = LockManager()

    with manager.acquire("lock1"):
        with manager.acquire("lock2"):
            # 同时持有两个锁
            pass
    ```
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._locks = {}
        self._logger = logging.getLogger("LockManager")

    def get_lock(self, name: str, **kwargs) -> RedisLock:
        """获取或创建锁"""
        if name not in self._locks:
            self._locks[name] = RedisLock(name, redis_client=self.redis_client, **kwargs)
        return self._locks[name]

    def acquire(self, *names, timeout: float = 30.0) -> bool:
        """批量获取锁（全部成功才返回）"""
        acquired = []
        try:
            for name in names:
                lock = self.get_lock(name)
                if not lock.acquire():
                    raise LockAcquisitionError(f"Failed to acquire lock: {name}")
                acquired.append(name)
            return True

        except LockAcquisitionError:
            # 释放已获取的锁
            for name in acquired:
                self._locks[name].release()
            return False

    @contextmanager
    def lock_multiple(self, *names, timeout: float = 30.0):
        """上下文管理器批量获取锁"""
        if self.acquire(*names, timeout=timeout):
            try:
                yield True
            finally:
                for name in names:
                    self._locks[name].release()
        else:
            yield False

    def release_all(self) -> None:
        """释放所有锁"""
        for lock in self._locks.values():
            lock.release()


# 全局锁管理器
_lock_manager: LockManager | None = None


def get_lock_manager() -> LockManager:
    """获取全局锁管理器"""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = LockManager()
    return _lock_manager
