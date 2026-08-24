"""
Profiler - 性能分析器

提供性能分析、瓶颈识别能力。
"""

import functools
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

__all__ = [
    "ProfileStats",
    "Profiler",
]


@dataclass
class ProfileStats:
    """性能统计"""

    name: str
    call_count: int = 0
    total_time_ms: float = 0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0
    avg_time_ms: float = 0
    last_call_time: float = 0

    def add_sample(self, duration_ms: float) -> None:
        """添加样本"""
        self.call_count += 1
        self.total_time_ms += duration_ms
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        self.avg_time_ms = self.total_time_ms / self.call_count
        self.last_call_time = time.time()


class Profiler:
    """
    性能分析器

    示例:
    ```python
    profiler = Profiler()

    # 装饰器方式
    @profiler.profile("my_function")
    def my_function():
        do_something()

    # 上下文管理器
    with profiler.profile("operation"):
        do_operation()

    # 获取报告
    report = profiler.get_report()
    ```
    """

    def __init__(self):
        self._stats: dict[str, ProfileStats] = {}
        self._enabled = True
        self._lock = threading.RLock()
        self._logger = logging.getLogger("Profiler")

    def profile(self, name: str = None) -> Callable:
        """装饰器：性能分析"""

        def decorator(func: Callable) -> Callable:
            stats_name = name or f"{func.__module__}.{func.__qualname__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self._enabled:
                    return func(*args, **kwargs)

                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = (time.time() - start) * 1000
                    self._record(stats_name, duration)

            return wrapper

        return decorator

    def record(self, name: str, duration_ms: float) -> None:
        """记录执行时间"""
        self._record(name, duration_ms)

    def _record(self, name: str, duration_ms: float) -> None:
        """内部记录"""
        with self._lock:
            if name not in self._stats:
                self._stats[name] = ProfileStats(name=name)
            self._stats[name].add_sample(duration_ms)

    def get_stats(self, name: str) -> ProfileStats | None:
        """获取统计"""
        return self._stats.get(name)

    def get_all_stats(self) -> list[ProfileStats]:
        """获取所有统计"""
        with self._lock:
            return sorted(
                self._stats.values(),
                key=lambda s: s.total_time_ms,
                reverse=True,
            )

    def get_report(self, limit: int = 20) -> dict[str, Any]:
        """生成报告"""
        stats = self.get_all_stats()

        return {
            "total_functions": len(stats),
            "total_calls": sum(s.call_count for s in stats),
            "total_time_ms": sum(s.total_time_ms for s in stats),
            "top_by_time": [
                {
                    "name": s.name,
                    "total_ms": s.total_time_ms,
                    "avg_ms": s.avg_time_ms,
                    "calls": s.call_count,
                }
                for s in stats[:limit]
            ],
            "top_by_calls": [
                {
                    "name": s.name,
                    "calls": s.call_count,
                    "avg_ms": s.avg_time_ms,
                }
                for s in sorted(stats, key=lambda x: x.call_count, reverse=True)[:limit]
            ],
            "slowest": [
                {
                    "name": s.name,
                    "max_ms": s.max_time_ms,
                    "avg_ms": s.avg_time_ms,
                }
                for s in sorted(stats, key=lambda x: x.max_time_ms, reverse=True)[:10]
            ],
        }

    def reset(self) -> None:
        """重置统计"""
        with self._lock:
            self._stats.clear()

    def enable(self) -> None:
        """启用"""
        self._enabled = True

    def disable(self) -> None:
        """禁用"""
        self._enabled = False

    def __call__(self, name: str = None) -> Callable:
        """支持直接作为装饰器使用"""
        return self.profile(name)

    def __enter__(self):
        """上下文管理器入口"""
        self._start_time = time.time()
        self._name = "block"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        duration = (time.time() - self._start_time) * 1000
        self._record(self._name, duration)


# 全局实例
_profiler: Profiler | None = None


def get_profiler() -> Profiler:
    """获取全局分析器"""
    global _profiler
    if _profiler is None:
        _profiler = Profiler()
    return _profiler
