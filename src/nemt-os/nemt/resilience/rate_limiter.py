"""
RateLimiter - 限流器

实现多种限流算法，保护系统不被过载。
"""

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "RateLimitAlgorithm",
    "RateLimitConfig",
    "RateLimiter",
    "TokenBucketLimiter",
    "SlidingWindowLimiter",
]


class RateLimitAlgorithm(Enum):
    """限流算法"""

    TOKEN_BUCKET = "token_bucket"  # 令牌桶
    SLIDING_WINDOW = "sliding_window"  # 滑动窗口
    FIXED_WINDOW = "fixed_window"  # 固定窗口
    LEAKY_BUCKET = "leaky_bucket"  # 漏桶


@dataclass
class RateLimitConfig:
    """限流配置"""

    rate: float  # 每秒允许的请求数
    capacity: int  # 容量/桶大小
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET


class RateLimiter:
    """
    限流器基类
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self._logger = logging.getLogger(f"RateLimiter.{name}")

    def allow(self, key: str = "default") -> bool:
        """检查是否允许请求"""
        raise NotImplementedError

    def acquire(self, key: str = "default", blocking: bool = True, timeout: float = None) -> bool:
        """获取令牌，blocking 模式下会等待"""
        if blocking:
            start_time = time.time()
            while True:
                if self.allow(key):
                    return True
                if timeout and (time.time() - start_time) >= timeout:
                    return False
                time.sleep(0.01)
        return self.allow(key)

    def reset(self, key: str = None) -> None:
        """重置限流器"""
        raise NotImplementedError


class TokenBucketLimiter(RateLimiter):
    """
    令牌桶限流器

    示例:
    ```python
    limiter = TokenBucketLimiter(rate=100, capacity=100)

    if limiter.allow("user1"):
        # 处理请求
        pass
    else:
        # 拒绝请求
        pass
    ```
    """

    def __init__(self, rate: float, capacity: int, name: str = "token_bucket"):
        super().__init__(name)
        self.rate = rate  # 每秒添加的令牌数
        self.capacity = capacity

        self._buckets: dict[str, dict] = {}
        self._lock = threading.RLock()

    def allow(self, key: str = "default") -> bool:
        with self._lock:
            now = time.time()

            if key not in self._buckets:
                self._buckets[key] = {
                    "tokens": self.capacity,
                    "last_update": now,
                }

            bucket = self._buckets[key]

            # 添加令牌
            elapsed = now - bucket["last_update"]
            bucket["tokens"] = min(self.capacity, bucket["tokens"] + elapsed * self.rate)
            bucket["last_update"] = now

            # 检查是否有足够的令牌
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True

            return False

    def reset(self, key: str = None) -> None:
        with self._lock:
            if key:
                if key in self._buckets:
                    del self._buckets[key]
            else:
                self._buckets.clear()


class SlidingWindowLimiter(RateLimiter):
    """
    滑动窗口限流器

    示例:
    ```python
    limiter = SlidingWindowLimiter(rate=100, window_size=60)

    if limiter.allow("user1"):
        # 处理请求
        pass
    ```
    """

    def __init__(self, rate: float, window_size: float = 60.0, name: str = "sliding_window"):
        super().__init__(name)
        self.rate = rate
        self.window_size = window_size

        self._windows: dict[str, list] = {}
        self._lock = threading.RLock()

    def allow(self, key: str = "default") -> bool:
        with self._lock:
            now = time.time()
            window_start = now - self.window_size

            if key not in self._windows:
                self._windows[key] = []

            # 清理过期的请求记录
            self._windows[key] = [t for t in self._windows[key] if t > window_start]

            # 检查是否超过限制
            if len(self._windows[key]) < self.rate * self.window_size:
                self._windows[key].append(now)
                return True

            return False

    def get_remaining(self, key: str = "default") -> int:
        """获取剩余请求数"""
        with self._lock:
            if key not in self._windows:
                return int(self.rate * self.window_size)

            now = time.time()
            window_start = now - self.window_size
            current = [t for t in self._windows[key] if t > window_start]
            return max(0, int(self.rate * self.window_size) - len(current))

    def reset(self, key: str = None) -> None:
        with self._lock:
            if key:
                if key in self._windows:
                    del self._windows[key]
            else:
                self._windows.clear()


class FixedWindowLimiter(RateLimiter):
    """
    固定窗口限流器

    示例:
    ```python
    limiter = FixedWindowLimiter(rate=100, window_size=60)

    if limiter.allow("user1"):
        # 处理请求
        pass
    ```
    """

    def __init__(self, rate: float, window_size: float = 60.0, name: str = "fixed_window"):
        super().__init__(name)
        self.rate = rate
        self.window_size = window_size

        self._windows: dict[str, dict] = {}
        self._lock = threading.RLock()

    def allow(self, key: str = "default") -> bool:
        with self._lock:
            now = time.time()
            window_start = int(now / self.window_size) * self.window_size

            if key not in self._windows:
                self._windows[key] = {"count": 0, "window_start": window_start}

            window = self._windows[key]

            # 检查是否在新窗口
            if window["window_start"] != window_start:
                window["count"] = 0
                window["window_start"] = window_start

            # 检查是否超过限制
            if window["count"] < self.rate:
                window["count"] += 1
                return True

            return False

    def reset(self, key: str = None) -> None:
        with self._lock:
            if key:
                if key in self._windows:
                    del self._windows[key]
            else:
                self._windows.clear()


def create_rate_limiter(
    algorithm: RateLimitAlgorithm,
    rate: float,
    capacity: int = None,
    name: str = "default",
) -> RateLimiter:
    """工厂函数：创建限流器"""
    if algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
        return TokenBucketLimiter(rate=rate, capacity=capacity or int(rate * 2), name=name)
    elif algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
        window_size = capacity or 60
        return SlidingWindowLimiter(rate=rate, window_size=window_size, name=name)
    elif algorithm == RateLimitAlgorithm.FIXED_WINDOW:
        window_size = capacity or 60
        return FixedWindowLimiter(rate=rate, window_size=window_size, name=name)
    else:
        return TokenBucketLimiter(rate=rate, capacity=capacity or int(rate * 2), name=name)
