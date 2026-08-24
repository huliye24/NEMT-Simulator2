"""
RetryPolicy - 重试策略

提供可配置的重试机制，包括指数退避。
"""

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

__all__ = [
    "RetryStrategy",
    "RetryConfig",
    "RetryResult",
    "RetryPolicy",
]


class RetryStrategy:
    """重试策略"""

    @staticmethod
    def fixed(delay: float) -> Callable[[int], float]:
        """固定延迟"""
        return lambda attempt: delay

    @staticmethod
    def linear(delay: float, increment: float = 0) -> Callable[[int], float]:
        """线性递增延迟"""
        return lambda attempt: delay + attempt * increment

    @staticmethod
    def exponential(base_delay: float, max_delay: float = 60.0, multiplier: float = 2.0) -> Callable[[int], float]:
        """指数退避"""

        def delay(attempt: int) -> float:
            exp_delay = min(base_delay * (multiplier**attempt), max_delay)
            return exp_delay

        return delay

    @staticmethod
    def exponential_jitter(
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: float = 0.1,
    ) -> Callable[[int], float]:
        """带抖动的指数退避"""

        def delay(attempt: int) -> float:
            exp_delay = min(base_delay * (multiplier**attempt), max_delay)
            jitter_amount = exp_delay * jitter * random.random()
            return exp_delay + jitter_amount

        return delay


@dataclass
class RetryConfig:
    """重试配置"""

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: float = 0.1
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)
    retryable_predicate: Callable[[Exception], bool] = None
    on_retry: Callable[[int, Exception], None] = None


@dataclass
class RetryResult:
    """重试结果"""

    success: bool
    result: Any = None
    error: Exception | None = None
    attempts: int = 0
    total_time: float = 0.0


class RetryPolicy:
    """
    重试策略

    示例:
    ```python
    policy = RetryPolicy(
        max_attempts=3,
        initial_delay=1.0,
        multiplier=2.0,
    )

    result = policy.execute(callable_func, arg1, arg2)

    if result.success:
        print(result.result)
    else:
        print(f"失败: {result.error}")
    ```
    """

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self._logger = logging.getLogger("RetryPolicy")

    def execute(self, func: Callable, *args, **kwargs) -> RetryResult:
        """执行带重试的函数"""
        start_time = time.time()
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempt + 1,
                    total_time=elapsed,
                )

            except Exception as e:
                last_exception = e

                # 检查是否应该重试
                if not self._should_retry(e, attempt):
                    elapsed = time.time() - start_time
                    return RetryResult(
                        success=False,
                        error=e,
                        attempts=attempt + 1,
                        total_time=elapsed,
                    )

                # 检查是否还有重试机会
                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    self._logger.warning(
                        f"重试 {attempt + 1}/{self.config.max_attempts} 失败: {e}, " f"等待 {delay:.2f}s 后重试"
                    )

                    if self.config.on_retry:
                        try:
                            self.config.on_retry(attempt + 1, e)
                        except Exception:
                            pass

                    time.sleep(delay)
                else:
                    self._logger.error(f"重试次数耗尽: {e}")

        elapsed = time.time() - start_time
        return RetryResult(
            success=False,
            error=last_exception,
            attempts=self.config.max_attempts,
            total_time=elapsed,
        )

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        # 检查异常类型
        if isinstance(exception, self.config.retryable_exceptions):
            # 检查自定义断言
            if self.config.retryable_predicate:
                return self.config.retryable_predicate(exception)
            return True
        return False

    def _calculate_delay(self, attempt: int) -> float:
        """计算延迟时间"""
        delay = min(self.config.initial_delay * (self.config.multiplier**attempt), self.config.max_delay)

        # 添加抖动
        if self.config.jitter > 0:
            jitter_range = delay * self.config.jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def __call__(self, func: Callable) -> Callable:
        """装饰器"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(func, *args, **kwargs)

        return wrapper


# 便捷函数
def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """装饰器：简化的重试装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            policy = RetryPolicy(
                RetryConfig(
                    max_attempts=max_attempts,
                    initial_delay=delay,
                    retryable_exceptions=exceptions,
                )
            )
            result = policy.execute(func, *args, **kwargs)
            if result.success:
                return result.result
            else:
                raise result.error

        return wrapper

    return decorator
