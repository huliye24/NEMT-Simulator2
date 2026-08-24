"""
CircuitBreaker - 熔断器

防止级联故障，提供系统弹性。
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    "CircuitState",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "CircuitBreakerError",
]


class CircuitState(Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 正常，调用通过
    OPEN = "open"  # 熔断，调用被拒绝
    HALF_OPEN = "half_open"  # 半开，尝试恢复


class CircuitBreakerOpen(Exception):
    """熔断器打开异常"""

    def __init__(self, message: str = "Circuit breaker is open"):
        self.message = message
        super().__init__(self.message)


class CircuitBreakerError(Exception):
    """熔断器错误"""

    pass


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""

    failure_threshold: int = 5  # 失败次数阈值
    success_threshold: int = 2  # 成功次数阈值
    timeout: float = 60.0  # 熔断超时时间
    half_open_max_calls: int = 3  # 半开状态最大调用数


@dataclass
class CircuitBreakerStats:
    """熔断器统计"""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state: CircuitState = CircuitState.CLOSED


class CircuitBreaker:
    """
    熔断器

    防止级联故障，当失败率达到阈值时打开熔断器。

    示例:
    ```python
    breaker = CircuitBreaker(
        failure_threshold=5,
        timeout=60.0
    )

    @breaker
    def call_service():
        # 可能失败的调用
        return requests.get("http://service/api")

    # 正常使用
    result = breaker.call(call_service)

    # 使用装饰器
    @breaker
    def my_func():
        return do_something()
    ```
    """

    def __init__(
        self,
        name: str = "default",
        config: CircuitBreakerConfig = None,
        on_state_change: Callable[[CircuitState, CircuitState], None] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = threading.RLock()

        self._stats = CircuitBreakerStats()
        self._logger = logging.getLogger(f"CircuitBreaker.{name}")

    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """获取统计"""
        with self._lock:
            return CircuitBreakerStats(
                total_calls=self._stats.total_calls,
                successful_calls=self._stats.successful_calls,
                failed_calls=self._stats.failed_calls,
                rejected_calls=self._stats.rejected_calls,
                state=self._state,
            )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """调用函数，带熔断保护"""
        if self.state == CircuitState.OPEN:
            self._stats.rejected_calls += 1
            raise CircuitBreakerOpen(f"Circuit breaker '{self.name}' is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """记录成功"""
        with self._lock:
            self._failure_count = 0
            self._stats.successful_calls += 1
            self._stats.total_calls += 1

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    def _on_failure(self) -> None:
        """记录失败"""
        with self._lock:
            self._failure_count += 1
            self._stats.failed_calls += 1
            self._stats.total_calls += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # 半开状态失败，回到打开状态
                self._transition_to(CircuitState.OPEN)
            elif self._failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def _check_state_transition(self) -> None:
        """检查状态转换"""
        if self._state == CircuitState.OPEN:
            # 检查是否超时
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.timeout:
                    self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """状态转换"""
        if self._state == new_state:
            return

        old_state = self._state
        self._state = new_state

        self._logger.info(f"Circuit breaker '{self.name}' state: {old_state.value} -> {new_state.value}")

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._success_count = 0
        elif new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.OPEN:
            self._failure_count = 0

        if self.on_state_change:
            try:
                self.on_state_change(old_state, new_state)
            except Exception as e:
                self._logger.error(f"状态变化回调异常: {e}")

    def reset(self) -> None:
        """重置熔断器"""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._stats = CircuitBreakerStats()

    def __call__(self, func: Callable) -> Callable:
        """装饰器"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper


# 需要 functools.wraps
from functools import wraps
