"""
Errors Module - 错误处理模块
"""

from nemt.core.errors.error_codes import (
    BusinessError,
    ConfigError,
    DataError,
    ErrorCategory,
    ErrorCode,
    NEMTError,
    SystemError,
    ValidationError,
    get_error_message,
    register_error_message,
)
from nemt.core.errors.error_handler import (
    ErrorHandler,
    ErrorLevel,
    ErrorRecord,
    get_error_handler,
)

__all__ = [
    # 错误码
    "ErrorCode",
    "ErrorCategory",
    "NEMTError",
    "get_error_message",
    "register_error_message",
    # 便捷错误类
    "SystemError",
    "ConfigError",
    "DataError",
    "ValidationError",
    "BusinessError",
    # 错误处理器
    "ErrorHandler",
    "ErrorRecord",
    "ErrorLevel",
    "get_error_handler",
]
