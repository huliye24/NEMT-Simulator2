"""
Decorators - 装饰器工具

提供:
- @timeout: 超时装饰器
- @retry: 重试装饰器
- @circuit_breaker: 熔断器装饰器
- @rate_limit: 限流装饰器
"""

import functools
import threading
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

__all__ = [
    "timeout",
    "retry",
    "circuit_breaker",
    "rate_limit",
    "CircuitState",
]


class CircuitState(Enum):
    """熔断状态"""

    CLOSED = "closed"  # 正常
    OPEN = "open"  # 熔断中
    HALF_OPEN = "half_open"  # 半开


def timeout(seconds: float, default: Any = None, exception: type[Exception] = TimeoutError):
    """
    超时装饰器

    Args:
        seconds: 超时秒数
        default: 超时时的默认值
        exception: 超时时抛出的异常

    示例:
    ```python
    @timeout(5.0)
    def slow_operation():
        time.sleep(10)
        return "done"
    ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            error = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    error[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                if default is not None:
                    return default
                raise exception(f"Function {func.__name__} timed out after {seconds}s")

            if error[0]:
                raise error[0]

            return result[0]

        return wrapper

    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable | None = None,
):
    """
    重试装饰器

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟秒数
        backoff: 退避倍数
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数

    示例:
    ```python
    @retry(max_attempts=5, delay=1.0, backoff=2.0)
    def unreliable_operation():
        # 可能失败的操作
        pass
    ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        if on_retry:
                            on_retry(attempt + 1, e)
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception

            raise last_exception

        return wrapper

    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type[Exception] = Exception,
):
    """
    熔断器装饰器

    Args:
        failure_threshold: 失败次数阈值
        recovery_timeout: 恢复超时秒数
        expected_exception: 预期的异常类型

    示例:
    ```python
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    def fragile_operation():
        # 可能失败的操作
        pass
    ```
    """

    def decorator(func: Callable) -> Callable:
        # 状态
        state = {"circuit_state": CircuitState.CLOSED, "failure_count": 0, "last_failure_time": None}
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                # 检查是否应该进入半开状态
                if state["circuit_state"] == CircuitState.OPEN:
                    if time.time() - state["last_failure_time"] >= recovery_timeout:
                        state["circuit_state"] = CircuitState.HALF_OPEN

            # 根据状态决定是否执行
            with lock:
                current_state = state["circuit_state"]

            if current_state == CircuitState.OPEN:
                raise Exception(f"Circuit breaker is OPEN. Function {func.__name__} is temporarily unavailable.")

            try:
                result = func(*args, **kwargs)

                # 成功后关闭熔断器
                with lock:
                    if state["circuit_state"] == CircuitState.HALF_OPEN:
                        state["circuit_state"] = CircuitState.CLOSED
                        state["failure_count"] = 0

                return result

            except expected_exception as e:
                with lock:
                    state["failure_count"] += 1
                    state["last_failure_time"] = time.time()

                    if state["failure_count"] >= failure_threshold:
                        state["circuit_state"] = CircuitState.OPEN

                raise e

        # 添加状态访问方法
        wrapper.get_circuit_state = lambda: state["circuit_state"]
        wrapper.get_failure_count = lambda: state["failure_count"]
        wrapper.reset = lambda: (
            state.update({"circuit_state": CircuitState.CLOSED, "failure_count": 0, "last_failure_time": None})
        )

        return wrapper

    return decorator


def rate_limit(calls: int, period: float):
    """
    限流装饰器

    Args:
        calls: 每周期最大调用次数
        period: 周期秒数

    示例:
    ```python
    @rate_limit(calls=100, period=60.0)
    def api_call():
        # API 调用
        pass
    ```
    """

    def decorator(func: Callable) -> Callable:
        calls_history = []
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.time()
                # 清除过期的调用记录
                calls_history[:] = [t for t in calls_history if now - t < period]

                if len(calls_history) >= calls:
                    sleep_time = period - (now - calls_history[0])
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        now = time.time()
                        calls_history[:] = [t for t in calls_history if now - t < period]

                calls_history.append(now)

            return func(*args, **kwargs)

        return wrapper

    return decorator


class CircuitBreaker:
    """
    独立熔断器类

    示例:
    ```python
    cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

    with cb:
        result = fragile_operation()
    ```
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """获取熔断状态"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
            return self._state

    def record_success(self) -> None:
        """记录成功"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._failure_count = 0

    def record_failure(self) -> None:
        """记录失败"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def reset(self) -> None:
        """重置熔断器"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def __enter__(self):
        """上下文管理器入口"""
        if self.state == CircuitState.OPEN:
            raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type:
            self.record_failure()
        else:
            self.record_success()
        return False  # 不抑制异常
