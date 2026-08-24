"""
Resilience Module - 弹性模式模块

提供容错和弹性机制:
- 熔断器 (CircuitBreaker)
- 限流器 (RateLimiter)
- 重试策略 (RetryPolicy)
- 超时处理 (TimeoutHandler)
"""

from nemt.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerOpen,
    CircuitBreakerStats,
    CircuitState,
)
from nemt.resilience.rate_limiter import (
    FixedWindowLimiter,
    RateLimitAlgorithm,
    RateLimitConfig,
    RateLimiter,
    SlidingWindowLimiter,
    TokenBucketLimiter,
    create_rate_limiter,
)
from nemt.resilience.retry_policy import (
    RetryConfig,
    RetryPolicy,
    RetryResult,
    RetryStrategy,
    retry,
)
from nemt.resilience.timeout_handler import (
    TimeoutConfig,
    TimeoutError,
    TimeoutHandler,
    get_timeout_handler,
    run_with_timeout,
    with_timeout,
)

__all__ = [
    # 熔断器
    "CircuitState",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "CircuitBreakerError",
    "CircuitBreakerConfig",
    "CircuitBreakerStats",
    # 限流器
    "RateLimitAlgorithm",
    "RateLimitConfig",
    "RateLimiter",
    "TokenBucketLimiter",
    "SlidingWindowLimiter",
    "FixedWindowLimiter",
    "create_rate_limiter",
    # 重试策略
    "RetryStrategy",
    "RetryConfig",
    "RetryResult",
    "RetryPolicy",
    "retry",
    # 超时处理
    "TimeoutError",
    "TimeoutHandler",
    "TimeoutConfig",
    "get_timeout_handler",
    "with_timeout",
    "run_with_timeout",
]
