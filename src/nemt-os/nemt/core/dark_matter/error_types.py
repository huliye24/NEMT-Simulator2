"""
Error Types - NEMT 错误类型层次体系

定义统一的错误层次结构，覆盖:
- NEMTError: 所有错误的基类
- TradingError: 交易相关错误（不可重试）
- ExchangeError: 交易所相关错误（可重试）
- RiskError: 风控相关错误（不可重试）
- SystemError: 系统相关错误（不可重试）

参考: Notion 暗物质框架 第二章「错误即信号，处理即恢复」
"""

from __future__ import annotations

import time
import traceback
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ============================================================================
# 错误码规范
# ============================================================================

# 错误码 -> (中文描述, 是否可重试, 严重等级)
ERROR_CODES: dict[str, tuple[str, bool, str]] = {
    # 交易错误 (不可重试)
    "INSUFFICIENT_BALANCE": ("余额不足", False, "WARNING"),
    "MARKET_CLOSED": ("市场已关闭", False, "WARNING"),
    "ORDER_REJECTED": ("订单被拒绝", False, "ERROR"),
    "POSITION_LIMIT_EXCEEDED": ("仓位超限", False, "WARNING"),
    "INVALID_ORDER_PARAM": ("无效订单参数", False, "ERROR"),
    "ORDER_TIMEOUT": ("订单超时", False, "WARNING"),
    # 交易所错误 (可重试)
    "EXCHANGE_CONNECTION_ERROR": ("交易所连接失败", True, "ERROR"),
    "EXCHANGE_RATE_LIMIT": ("交易所限流", True, "WARNING"),
    "EXCHANGE_SERVER_ERROR": ("交易所服务器错误", True, "ERROR"),
    "EXCHANGE_DATA_ERROR": ("交易所数据格式错误", True, "WARNING"),
    "EXCHANGE_AUTH_ERROR": ("交易所认证失败", False, "ERROR"),
    "EXCHANGE_TIMEOUT": ("交易所请求超时", True, "WARNING"),
    # 风控错误 (不可重试)
    "RISK_LIMIT_EXCEEDED": ("风控限制超限", False, "ERROR"),
    "DRAWDOWN_EXCEEDED": ("回撤超限", False, "CRITICAL"),
    "LEVERAGE_EXCEEDED": ("杠杆超限", False, "ERROR"),
    "DAILY_LOSS_LIMIT": ("日内亏损超限", False, "CRITICAL"),
    "POSITION_SIZE_VIOLATION": ("仓位大小违规", False, "WARNING"),
    "RISK_CHECK_FAILED": ("风控检查失败", False, "ERROR"),
    # 系统错误 (不可重试)
    "CONFIG_LOAD_ERROR": ("配置加载失败", False, "CRITICAL"),
    "EVENTBUS_ERROR": ("事件总线错误", False, "CRITICAL"),
    "CAPSULE_INIT_ERROR": ("胶囊初始化失败", False, "CRITICAL"),
    "DATA_VALIDATION_ERROR": ("数据校验失败", False, "WARNING"),
    "INVALID_STATE": ("无效状态", False, "ERROR"),
    "UNKNOWN_ERROR": ("未知错误", False, "ERROR"),
}


class SeverityLevel(Enum):
    """严重等级"""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ============================================================================
# 恢复策略枚举
# ============================================================================


class RecoveryStrategy(Enum):
    """错误恢复策略"""

    RETRY = "retry"  # 重试
    FALLBACK = "fallback"  # 降级
    CIRCUIT_BREAK = "circuit_break"  # 熔断
    ISOLATE = "isolate"  # 隔离
    PROPAGATE = "propagate"  # 传播
    IGNORE = "ignore"  # 忽略


# ============================================================================
# 错误上下文
# ============================================================================


@dataclass
class ErrorContext:
    """
    错误上下文

    记录错误发生的完整上下文信息，便于追踪和诊断。

    Attributes:
        error: 原始异常对象
        source: 错误来源（capsule_id 或模块名）
        timestamp: 错误发生时间戳
        attempt: 当前重试次数
        max_attempts: 最大重试次数
        recovery_strategy: 恢复策略
        details: 额外详情字典
    """

    error: Exception
    source: str
    timestamp: float = field(default_factory=time.time)
    attempt: int = 1
    max_attempts: int = 3
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.PROPAGATE
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（可序列化）"""
        return {
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "error_code": getattr(self.error, "code", "UNKNOWN_ERROR"),
            "source": self.source,
            "timestamp": self.timestamp,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "recovery_strategy": self.recovery_strategy.value,
            "details": self.details,
        }

    def with_attempt(self, attempt: int) -> ErrorContext:
        """创建新实例，增加重试次数"""
        return ErrorContext(
            error=self.error,
            source=self.source,
            timestamp=self.timestamp,
            attempt=attempt,
            max_attempts=self.max_attempts,
            recovery_strategy=self.recovery_strategy,
            details=self.details,
        )


# ============================================================================
# NEMT 错误基类
# ============================================================================


class NEMTError(Exception, ABC):
    """
    NEMT 错误基类

    所有 NEMT 系统错误的基类，提供统一的错误接口。

    Attributes:
        code: 错误码，对应 ERROR_CODES 字典
        retryable: 是否可重试
        details: 额外详情字典
    """

    code: str = "UNKNOWN_ERROR"
    retryable: bool = False
    severity: SeverityLevel = SeverityLevel.ERROR

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """
        初始化错误

        Args:
            message: 错误消息
            details: 额外详情字典
        """
        super().__init__(message)
        self._message = message
        self._details = details or {}

    @property
    def message(self) -> str:
        """错误消息"""
        return self._message

    @property
    def details(self) -> dict[str, Any]:
        """额外详情"""
        return self._details

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典（用于日志和事件）

        Returns:
            错误信息字典
        """
        return {
            "error_code": self.code,
            "message": self._message,
            "error_type": type(self).__name__,
            "retryable": self.retryable,
            "severity": self.severity.value,
            "details": self._details,
        }

    def get_recovery_strategy(self) -> RecoveryStrategy:
        """
        获取推荐恢复策略

        Returns:
            RecoveryStrategy 枚举值
        """
        if self.retryable:
            return RecoveryStrategy.RETRY
        return RecoveryStrategy.PROPAGATE

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code}, message={self._message})"


# ============================================================================
# 交易错误类（不可重试）
# ============================================================================


class TradingError(NEMTError):
    """
    交易错误基类

    所有交易相关错误的基类，默认不可重试。
    """

    code = "TRADING_ERROR"
    retryable = False
    severity = SeverityLevel.WARNING


class InsufficientBalanceError(TradingError):
    """
    余额不足错误

    用户账户余额不足以完成交易。
    """

    code = "INSUFFICIENT_BALANCE"
    severity = SeverityLevel.WARNING

    def __init__(self, required: float, available: float, symbol: str = "BTC"):
        """
        Args:
            required: 所需金额
            available: 可用金额
            symbol: 交易品种
        """
        message = f"余额不足: 需要 {required:.2f}, 可用 {available:.2f} ({symbol})"
        super().__init__(message, {"required": required, "available": available, "symbol": symbol})
        self.required = required
        self.available = available


class MarketClosedError(TradingError):
    """
    市场关闭错误

    当前市场已关闭，无法交易。
    """

    code = "MARKET_CLOSED"
    severity = SeverityLevel.WARNING

    def __init__(self, market: str = "CRYPTO"):
        message = f"市场 {market} 已关闭"
        super().__init__(message, {"market": market})
        self.market = market


class OrderRejectedError(TradingError):
    """
    订单被拒绝错误

    订单被交易所或风控系统拒绝。
    """

    code = "ORDER_REJECTED"
    severity = SeverityLevel.ERROR

    def __init__(self, reason: str, order_id: str | None = None):
        """
        Args:
            reason: 拒绝原因
            order_id: 订单 ID
        """
        message = f"订单被拒绝: {reason}"
        details = {"reason": reason}
        if order_id:
            details["order_id"] = order_id
        super().__init__(message, details)
        self.reason = reason
        self.order_id = order_id


class PositionLimitExceededError(TradingError):
    """
    仓位超限错误

    订单会导致仓位超过限制。
    """

    code = "POSITION_LIMIT_EXCEEDED"
    severity = SeverityLevel.WARNING

    def __init__(self, current: float, limit: float, symbol: str = "BTC"):
        message = f"仓位超限: 当前 {current:.4f}, 限制 {limit:.4f} ({symbol})"
        super().__init__(message, {"current": current, "limit": limit, "symbol": symbol})
        self.current = current
        self.limit = limit


class InvalidOrderParamError(TradingError):
    """
    无效订单参数错误

    订单参数不符合要求。
    """

    code = "INVALID_ORDER_PARAM"
    severity = SeverityLevel.ERROR

    def __init__(self, param_name: str, value: Any, reason: str):
        message = f"无效订单参数 {param_name}: {value} - {reason}"
        super().__init__(message, {"param_name": param_name, "value": str(value), "reason": reason})
        self.param_name = param_name
        self.value = value
        self.reason = reason


# ============================================================================
# 交易所错误类（可重试）
# ============================================================================


class ExchangeError(NEMTError):
    """
    交易所错误基类

    所有交易所相关错误的基类，默认可重试。
    """

    code = "EXCHANGE_ERROR"
    retryable = True
    severity = SeverityLevel.ERROR


class ExchangeConnectionError(ExchangeError):
    """
    交易所连接错误

    无法连接到交易所 API。
    """

    code = "EXCHANGE_CONNECTION_ERROR"
    severity = SeverityLevel.ERROR

    def __init__(self, exchange: str = "BINANCE", reason: str | None = None):
        message = f"无法连接交易所 {exchange}" + (f": {reason}" if reason else "")
        super().__init__(message, {"exchange": exchange, "reason": reason})
        self.exchange = exchange


class ExchangeRateLimitError(ExchangeError):
    """
    交易所限流错误

    触发了交易所的 API 限流。
    """

    code = "EXCHANGE_RATE_LIMIT"
    retryable = True
    severity = SeverityLevel.WARNING

    def __init__(self, exchange: str = "BINANCE", retry_after: float | None = None):
        message = f"交易所 {exchange} 限流" + (f", {retry_after:.1f}s 后重试" if retry_after else "")
        details = {"exchange": exchange}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, details)
        self.exchange = exchange
        self.retry_after = retry_after


class ExchangeServerError(ExchangeError):
    """
    交易所服务器错误

    交易所服务器返回 5xx 错误。
    """

    code = "EXCHANGE_SERVER_ERROR"
    retryable = True
    severity = SeverityLevel.ERROR

    def __init__(self, exchange: str = "BINANCE", status_code: int | None = None, message: str | None = None):
        full_message = f"交易所 {exchange} 服务器错误"
        if status_code:
            full_message += f" (HTTP {status_code})"
        if message:
            full_message += f": {message}"
        details = {"exchange": exchange, "status_code": status_code, "server_message": message}
        super().__init__(full_message, details)
        self.exchange = exchange
        self.status_code = status_code


class ExchangeDataError(ExchangeError):
    """
    交易所数据错误

    交易所返回的数据格式不符合预期。
    """

    code = "EXCHANGE_DATA_ERROR"
    retryable = True
    severity = SeverityLevel.WARNING

    def __init__(self, data_type: str = "KLINE", reason: str | None = None):
        message = f"交易所数据格式错误 ({data_type})" + (f": {reason}" if reason else "")
        super().__init__(message, {"data_type": data_type, "reason": reason})
        self.data_type = data_type


# ============================================================================
# 风控错误类（不可重试）
# ============================================================================


class RiskError(NEMTError):
    """
    风控错误基类

    所有风控相关错误的基类，默认不可重试。
    """

    code = "RISK_ERROR"
    retryable = False
    severity = SeverityLevel.ERROR


class RiskLimitExceededError(RiskError):
    """
    风控限制超限错误

    触发了风控系统的某种限制。
    """

    code = "RISK_LIMIT_EXCEEDED"
    severity = SeverityLevel.ERROR

    def __init__(self, limit_type: str, current: float, max_value: float):
        message = f"风控限制 '{limit_type}' 超限: 当前 {current:.4f}, 最大 {max_value:.4f}"
        super().__init__(message, {"limit_type": limit_type, "current": current, "max_value": max_value})
        self.limit_type = limit_type
        self.current = current
        self.max_value = max_value


class DrawdownExceededError(RiskError):
    """
    回撤超限错误

    当前回撤超过了预设的最大回撤限制。
    """

    code = "DRAWDOWN_EXCEEDED"
    severity = SeverityLevel.CRITICAL

    def __init__(self, current_drawdown: float, max_drawdown: float):
        message = f"回撤超限: 当前 {current_drawdown:.2%}, 限制 {max_drawdown:.2%}"
        super().__init__(message, {"current_drawdown": current_drawdown, "max_drawdown": max_drawdown})
        self.current_drawdown = current_drawdown
        self.max_drawdown = max_drawdown


class LeverageExceededError(RiskError):
    """
    杠杆超限错误

    当前杠杆超过了预设的限制。
    """

    code = "LEVERAGE_EXCEEDED"
    severity = SeverityLevel.ERROR

    def __init__(self, current_leverage: float, max_leverage: float):
        message = f"杠杆超限: 当前 {current_leverage:.1f}x, 限制 {max_leverage:.1f}x"
        super().__init__(message, {"current_leverage": current_leverage, "max_leverage": max_leverage})
        self.current_leverage = current_leverage
        self.max_leverage = max_leverage


class DailyLossLimitError(RiskError):
    """
    日内亏损超限错误

    当日累计亏损超过了预设的限制。
    """

    code = "DAILY_LOSS_LIMIT"
    severity = SeverityLevel.CRITICAL

    def __init__(self, daily_pnl: float, limit: float):
        message = f"日内亏损超限: 当前 {daily_pnl:.2f}, 限制 {limit:.2f}"
        super().__init__(message, {"daily_pnl": daily_pnl, "limit": limit})
        self.daily_pnl = daily_pnl
        self.limit = limit


# ============================================================================
# 系统错误类（不可重试）
# ============================================================================


class SystemError(NEMTError):
    """
    系统错误基类

    所有系统相关错误的基类，默认不可重试。
    """

    code = "SYSTEM_ERROR"
    retryable = False
    severity = SeverityLevel.CRITICAL


class ConfigLoadError(SystemError):
    """
    配置加载错误

    无法加载配置文件。
    """

    code = "CONFIG_LOAD_ERROR"
    severity = SeverityLevel.CRITICAL

    def __init__(self, config_path: str, reason: str | None = None):
        message = f"无法加载配置: {config_path}" + (f": {reason}" if reason else "")
        super().__init__(message, {"config_path": config_path, "reason": reason})
        self.config_path = config_path


class EventBusError(SystemError):
    """
    事件总线错误

    事件总线发生错误。
    """

    code = "EVENTBUS_ERROR"
    severity = SeverityLevel.CRITICAL

    def __init__(self, reason: str, event_type: str | None = None):
        message = f"事件总线错误: {reason}"
        details = {"reason": reason}
        if event_type:
            details["event_type"] = event_type
        super().__init__(message, details)
        self.reason = reason
        self.event_type = event_type


class CapsuleInitError(SystemError):
    """
    胶囊初始化错误

    胶囊在初始化阶段失败。
    """

    code = "CAPSULE_INIT_ERROR"
    severity = SeverityLevel.CRITICAL

    def __init__(self, capsule_id: str, reason: str):
        message = f"胶囊 {capsule_id} 初始化失败: {reason}"
        super().__init__(message, {"capsule_id": capsule_id, "reason": reason})
        self.capsule_id = capsule_id


class DataValidationError(SystemError):
    """
    数据校验错误

    数据校验失败。
    """

    code = "DATA_VALIDATION_ERROR"
    severity = SeverityLevel.WARNING

    def __init__(self, field: str, value: Any, expected: str):
        message = f"数据校验失败: {field}={value}, 期望 {expected}"
        super().__init__(message, {"field": field, "value": str(value), "expected": expected})
        self.field = field
        self.value = value
        self.expected = expected


# ============================================================================
# 错误工厂（异常映射）
# ============================================================================


class ErrorFactory:
    """
    错误工厂

    将标准异常自动映射到 NEMT 错误类型。

    Usage:
        nemt_error = ErrorFactory.from_exception(original_error, source="execution")
    """

    # 标准异常 -> NEMT 错误映射
    EXCEPTION_MAPPING: dict[type[Exception], type[NEMTError]] = {
        # 网络相关 -> 交易所连接错误
        ConnectionError: ExchangeConnectionError,
        TimeoutError: ExchangeConnectionError,
        # requests 相关 -> 交易所错误
    }

    # HTTP 状态码 -> NEMT 错误映射
    HTTP_STATUS_MAPPING: dict[int, type[NEMTError]] = {
        400: OrderRejectedError,
        401: ExchangeConnectionError,
        403: ExchangeConnectionError,
        429: ExchangeRateLimitError,
        500: ExchangeServerError,
        502: ExchangeServerError,
        503: ExchangeServerError,
    }

    @classmethod
    def from_exception(
        cls,
        error: Exception,
        source: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> NEMTError:
        """
        从标准异常创建 NEMT 错误

        Args:
            error: 原始异常对象
            source: 错误来源
            details: 额外详情

        Returns:
            NEMTError 子类实例
        """
        # 检查是否有已知的 NEMTError
        if isinstance(error, NEMTError):
            return error

        # 尝试从异常类型映射
        for exc_type, nemt_error_type in cls.EXCEPTION_MAPPING.items():
            if isinstance(error, exc_type):
                return cls._create_from_mapping(error, nemt_error_type, source, details)

        # 检查 HTTP 响应状态码
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            status_code = error.response.status_code
            if status_code in cls.HTTP_STATUS_MAPPING:
                return cls._create_from_mapping(error, cls.HTTP_STATUS_MAPPING[status_code], source, details)

        # 未知错误 -> 通用 NEMTError
        return NEMTError(
            message=str(error),
            details={
                "original_type": type(error).__name__,
                "source": source,
                "traceback": traceback.format_exc(),
                **(details or {}),
            },
        )

    @classmethod
    def _create_from_mapping(
        cls,
        error: Exception,
        nemt_error_type: type[NEMTError],
        source: str,
        details: dict[str, Any] | None,
    ) -> NEMTError:
        """从映射创建 NEMT 错误"""
        try:
            return nemt_error_type(str(error))
        except (TypeError, ValueError):
            return NEMTError(
                message=str(error),
                details={
                    "original_type": type(error).__name__,
                    "source": source,
                    **(details or {}),
                },
            )

    @classmethod
    def register_mapping(cls, exc_type: type[Exception], nemt_error_type: type[NEMTError]) -> None:
        """
        注册新的异常映射

        Args:
            exc_type: 原始异常类型
            nemt_error_type: NEMT 错误类型
        """
        cls.EXCEPTION_MAPPING[exc_type] = nemt_error_type

    @classmethod
    def register_http_mapping(cls, status_code: int, nemt_error_type: type[NEMTError]) -> None:
        """
        注册新的 HTTP 状态码映射

        Args:
            status_code: HTTP 状态码
            nemt_error_type: NEMT 错误类型
        """
        cls.HTTP_STATUS_MAPPING[status_code] = nemt_error_type


# ============================================================================
# 便捷函数
# ============================================================================


def is_retryable_error(error: Exception) -> bool:
    """
    判断错误是否可重试

    Args:
        error: 异常对象

    Returns:
        是否可重试
    """
    if isinstance(error, NEMTError):
        return error.retryable
    return False


def get_error_code_info(code: str) -> tuple[str, bool, str]:
    """
    获取错误码信息

    Args:
        code: 错误码

    Returns:
        (中文描述, 是否可重试, 严重等级)
    """
    return ERROR_CODES.get(code, ("未知错误", False, "ERROR"))


def format_error_for_logging(error: Exception, context: dict[str, Any] | None = None) -> str:
    """
    格式化错误用于日志记录

    Args:
        error: 异常对象
        context: 额外上下文

    Returns:
        格式化的日志字符串
    """
    if isinstance(error, NEMTError):
        error_dict = error.to_dict()
    else:
        error_dict = {
            "error_type": type(error).__name__,
            "message": str(error),
            "retryable": False,
            "severity": "ERROR",
        }

    if context:
        error_dict["context"] = context

    return str(error_dict)
