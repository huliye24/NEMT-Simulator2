"""
Dark Matter Framework - 隐性基础设施与隐式设计

NEMT Simulator 的暗物质基础设施，为系统提供:
- 错误处理 (error_types, error_handler)
- 结构化日志 (structured_logger)
- 日志分析 (log_analyzer)
- 监控指标 (metrics_collector)
- 告警系统 (alert_handler)
- 重试机制 (retry_decorator)
- 熔断器 (circuit_breaker)
- 限流器 (rate_limiter)
- 安全 (auth, encryption, input_validation, audit_logger)
- 通信 (event_schemas)
- 健康检查 (health_check)
- 容灾备份 (backup_manager)
- 暗物质健康度自检 (dark_matter_health_checker)
"""

# =============================================================================
# 已实现的模块
# =============================================================================

from nemt.core.dark_matter.error_handler import (
    ErrorHandler,
    error_context,
    get_error_handler,
    handle_error,
    reset_error_handler,
)
from nemt.core.dark_matter.error_types import (
    ERROR_CODES,
    CapsuleInitError,
    ConfigLoadError,
    DailyLossLimitError,
    DataValidationError,
    DrawdownExceededError,
    ErrorContext,
    ErrorFactory,
    EventBusError,
    ExchangeConnectionError,
    ExchangeDataError,
    ExchangeError,
    ExchangeRateLimitError,
    ExchangeServerError,
    InsufficientBalanceError,
    InvalidOrderParamError,
    LeverageExceededError,
    MarketClosedError,
    NEMTError,
    OrderRejectedError,
    PositionLimitExceededError,
    RecoveryStrategy,
    RiskError,
    RiskLimitExceededError,
    SeverityLevel,
    SystemError,
    TradingError,
    format_error_for_logging,
    get_error_code_info,
    is_retryable_error,
)
from nemt.core.dark_matter.log_analyzer import (
    ErrorSummary,
    LogAnalyzer,
    LogStats,
    quick_analyze,
    quick_report,
)
from nemt.core.dark_matter.structured_logger import (
    LOG_BAR_INDEX,
    LOG_CAPSULE_ID,
    LOG_DURATION_MS,
    LOG_ERROR_CODE,
    LOG_EVENT_TYPE,
    LOG_FUNCTION,
    LOG_LEVEL,
    LOG_LINE,
    LOG_MESSAGE,
    LOG_MODULE,
    LOG_SYMBOL,
    LOG_TIMESTAMP,
    LOG_TRACE_ID,
    ColoredFormatter,
    JSONFormatter,
    LogContext,
    LogContextManager,
    LogLevel,
    StructuredLogger,
    clear_loggers,
    get_logger,
    log_context,
)

# =============================================================================
# 尚未实现的模块 - 使用延迟导入或存根
# =============================================================================


def __getattr__(name):
    """延迟导入尚未实现的模块"""
    _pending = {
        "MetricsCollector": "metrics_collector",
        "MetricsRegistry": "metrics_collector",
        "AlertHandler": "alert_handler",
        "AlertChannel": "alert_handler",
        "EmailChannel": "alert_handler",
        "SlackChannel": "alert_handler",
        "WebhookChannel": "alert_handler",
        "LogChannel": "alert_handler",
        "CircuitBreaker": "circuit_breaker",
        "CircuitState": "circuit_breaker",
        "CircuitOpenError": "circuit_breaker",
        "CircuitBreakerRegistry": "circuit_breaker",
        "TokenBucketRateLimiter": "rate_limiter",
        "SlidingWindowRateLimiter": "rate_limiter",
        "DistributedRateLimiter": "rate_limiter",
        "RetryStrategy": "retry_decorator",
        "retry": "retry_decorator",
        "HealthChecker": "health_check",
        "HealthReport": "health_check",
        "DarkMatterHealthChecker": "dark_matter_health_checker",
    }

    if name in _pending:
        module_name = _pending[name]
        try:
            module = __import__(f"nemt.core.dark_matter.{module_name}", fromlist=[name])
            return getattr(module, name)
        except ImportError:
            raise AttributeError(f"模块 'nemt.core.dark_matter.{module_name}' 尚未实现，" f"'{name}' 不可用")

    raise AttributeError(f"模块 'nemt.core.dark_matter' 没有属性 '{name}'")


__all__ = [
    # 版本
    "__version__",
    # 错误类型
    "NEMTError",
    "TradingError",
    "InsufficientBalanceError",
    "MarketClosedError",
    "OrderRejectedError",
    "PositionLimitExceededError",
    "InvalidOrderParamError",
    "ExchangeError",
    "ExchangeConnectionError",
    "ExchangeRateLimitError",
    "ExchangeServerError",
    "ExchangeDataError",
    "RiskError",
    "RiskLimitExceededError",
    "DrawdownExceededError",
    "LeverageExceededError",
    "DailyLossLimitError",
    "SystemError",
    "ConfigLoadError",
    "EventBusError",
    "CapsuleInitError",
    "DataValidationError",
    "ErrorContext",
    "RecoveryStrategy",
    "ErrorFactory",
    "ERROR_CODES",
    "is_retryable_error",
    "get_error_code_info",
    "format_error_for_logging",
    "SeverityLevel",
    # 错误处理器
    "ErrorHandler",
    "get_error_handler",
    "reset_error_handler",
    "error_context",
    "handle_error",
    # 结构化日志
    "StructuredLogger",
    "LogContext",
    "LogContextManager",
    "LogLevel",
    "JSONFormatter",
    "ColoredFormatter",
    "LOG_CAPSULE_ID",
    "LOG_TRACE_ID",
    "LOG_BAR_INDEX",
    "LOG_SYMBOL",
    "LOG_EVENT_TYPE",
    "LOG_DURATION_MS",
    "LOG_ERROR_CODE",
    "LOG_LEVEL",
    "LOG_TIMESTAMP",
    "LOG_MESSAGE",
    "LOG_MODULE",
    "LOG_FUNCTION",
    "LOG_LINE",
    "get_logger",
    "clear_loggers",
    "log_context",
    # 日志分析
    "LogAnalyzer",
    "LogStats",
    "ErrorSummary",
    "quick_analyze",
    "quick_report",
]
