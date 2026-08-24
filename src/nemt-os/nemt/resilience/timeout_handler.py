"""
TimeoutHandler - 超时处理器

提供超时控制机制。
"""

import concurrent.futures
import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

__all__ = [
    "TimeoutError",
    "TimeoutHandler",
]


class TimeoutError(Exception):
    """超时异常"""

    def __init__(self, message: str = "Operation timed out"):
        self.message = message
        super().__init__(self.message)


@dataclass
class TimeoutConfig:
    """超时配置"""

    default_timeout: float = 30.0
    max_timeout: float = 300.0


class TimeoutHandler:
    """
    超时处理器

    示例:
    ```python
    handler = TimeoutHandler()

    try:
        result = handler.execute(my_func, arg1, arg2, timeout=10.0)
    except TimeoutError:
        print("操作超时")

    # 使用装饰器
    @handler.timeout(5.0)
    def my_func():
        return do_something()
    ```
    """

    def __init__(self, config: TimeoutConfig = None):
        self.config = config or TimeoutConfig()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self._logger = logging.getLogger("TimeoutHandler")

    def execute(self, func: Callable, *args, timeout: float = None, **kwargs) -> Any:
        """
        执行函数，设置超时

        Args:
            func: 要执行的函数
            *args: 函数参数
            timeout: 超时时间（秒）
            **kwargs: 函数关键字参数

        Returns:
            函数返回值

        Raises:
            TimeoutError: 如果操作超时
        """
        timeout = timeout or self.config.default_timeout
        timeout = min(timeout, self.config.max_timeout)

        future = self._executor.submit(func, *args, **kwargs)

        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout}s")
        except Exception:
            # 保留原始异常
            raise

    def execute_with_default(self, func: Callable, *args, **kwargs) -> Any:
        """使用默认超时执行"""
        return self.execute(func, *args, timeout=self.config.default_timeout, **kwargs)

    def timeout(self, seconds: float):
        """装饰器：设置超时"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute(func, *args, timeout=seconds, **kwargs)

            return wrapper

        return decorator

    def shutdown(self, wait: bool = True) -> None:
        """关闭处理器"""
        self._executor.shutdown(wait=wait)


# 全局实例
_timeout_handler: TimeoutHandler | None = None


def get_timeout_handler() -> TimeoutHandler:
    """获取全局超时处理器"""
    global _timeout_handler
    if _timeout_handler is None:
        _timeout_handler = TimeoutHandler()
    return _timeout_handler


# 便捷函数
def with_timeout(timeout: float):
    """装饰器：设置超时"""
    handler = get_timeout_handler()
    return handler.timeout(timeout)


def run_with_timeout(func: Callable, *args, timeout: float = 30.0, **kwargs) -> Any:
    """运行函数带超时"""
    handler = get_timeout_handler()
    return handler.execute(func, *args, timeout=timeout, **kwargs)
