"""
ErrorCode - 错误码体系

提供统一的错误处理机制:
- 错误码定义
- 错误类层次结构
- 国际化支持
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    "ErrorCode",
    "ErrorCategory",
    "NEMTError",
    "get_error_message",
    "register_error_message",
]


class ErrorCategory(Enum):
    """错误类别"""

    SYSTEM = "system"  # 系统错误
    CONFIG = "config"  # 配置错误
    NETWORK = "network"  # 网络错误
    DATA = "data"  # 数据错误
    VALIDATION = "validation"  # 验证错误
    BUSINESS = "business"  # 业务错误
    SECURITY = "security"  # 安全错误
    INTERNAL = "internal"  # 内部错误


class ErrorCode(Enum):
    """
    NEMT 错误码定义

    格式: NEMT-{Category}-{Number}
    示例: NEMT-SYS-001, NEMT-DATA-001
    """

    # 系统错误 (1000-1999)
    SYS_001 = ("system", 1001, "系统初始化失败")
    SYS_002 = ("system", 1002, "系统关闭失败")
    SYS_003 = ("system", 1003, "系统内部错误")
    SYS_004 = ("system", 1004, "系统资源不足")
    SYS_005 = ("system", 1005, "系统超时")

    # 配置错误 (2000-2999)
    CFG_001 = ("config", 2001, "配置缺失")
    CFG_002 = ("config", 2002, "配置格式错误")
    CFG_003 = ("config", 2003, "配置验证失败")
    CFG_004 = ("config", 2004, "配置加载失败")
    CFG_005 = ("config", 2005, "配置保存失败")

    # 网络错误 (3000-3999)
    NET_001 = ("network", 3001, "网络连接失败")
    NET_002 = ("network", 3002, "网络请求超时")
    NET_003 = ("network", 3003, "网络响应错误")
    NET_004 = ("network", 3004, "网络断开")
    NET_005 = ("network", 3005, "API 调用失败")

    # 数据错误 (4000-4999)
    DAT_001 = ("data", 4001, "数据不存在")
    DAT_002 = ("data", 4002, "数据格式错误")
    DAT_003 = ("data", 4003, "数据验证失败")
    DAT_004 = ("data", 4004, "数据存储失败")
    DAT_005 = ("data", 4005, "数据查询失败")
    DAT_006 = ("data", 4006, "数据重复")
    DAT_007 = ("data", 4007, "数据为空")

    # 验证错误 (5000-5999)
    VAL_001 = ("validation", 5001, "参数缺失")
    VAL_002 = ("validation", 5002, "参数格式错误")
    VAL_003 = ("validation", 5003, "参数范围错误")
    VAL_004 = ("validation", 5004, "参数类型错误")
    VAL_005 = ("validation", 5005, "参数验证失败")

    # 业务错误 (6000-6999)
    BUS_001 = ("business", 6001, "业务逻辑错误")
    BUS_002 = ("business", 6002, "操作不支持")
    BUS_003 = ("business", 6003, "状态错误")
    BUS_004 = ("business", 6004, "资源不足")
    BUS_005 = ("business", 6005, "配额超限")

    # 安全错误 (7000-7999)
    SEC_001 = ("security", 7001, "认证失败")
    SEC_002 = ("security", 7002, "授权失败")
    SEC_003 = ("security", 7003, "权限不足")
    SEC_004 = ("security", 7004, "Token 过期")
    SEC_005 = ("security", 7005, "签名验证失败")

    # 内部错误 (8000-8999)
    INT_001 = ("internal", 8001, "模块未找到")
    INT_002 = ("internal", 8002, "模块初始化失败")
    INT_003 = ("internal", 8003, "模块执行失败")
    INT_004 = ("internal", 8004, "服务不可用")
    INT_005 = ("internal", 8005, "服务未注册")

    def __init__(self, category: str, code: int, message: str):
        self._category = category
        self._code = code
        self._message = message

    @property
    def code(self) -> int:
        """错误码数字"""
        return self._code

    @property
    def full_code(self) -> str:
        """完整错误码"""
        return f"NEMT-{self._category.upper()}-{self._code}"

    @property
    def message(self) -> str:
        """错误消息"""
        return self._message

    @property
    def category(self) -> ErrorCategory:
        """错误类别"""
        return ErrorCategory(self._category)


@dataclass
class ErrorDetail:
    """错误详情"""

    code: ErrorCode
    message: str
    details: dict[str, Any]
    source: str
    timestamp: float


# 错误消息映射 (支持国际化)
_error_messages: dict[str, dict[str, str]] = {}


def register_error_message(error_code: ErrorCode, message: str, locale: str = "zh") -> None:
    """
    注册错误消息 (支持国际化)

    Args:
        error_code: 错误码
        message: 错误消息
        locale: 语言
    """
    if error_code.full_code not in _error_messages:
        _error_messages[error_code.full_code] = {}
    _error_messages[error_code.full_code][locale] = message


def get_error_message(error_code: ErrorCode, locale: str = "zh", **kwargs) -> str:
    """
    获取错误消息

    Args:
        error_code: 错误码
        locale: 语言
        **kwargs: 格式化参数

    Returns:
        错误消息
    """
    messages = _error_messages.get(error_code.full_code, {})
    message = messages.get(locale) or error_code.message
    if kwargs:
        message = message.format(**kwargs)
    return message


class NEMTError(Exception):
    """
    NEMT 异常基类

    示例:
    ```python
    raise NEMTError(
        code=ErrorCode.DAT_001,
        message="K线数据不存在",
        details={"symbol": "BTC", "interval": "1h"}
    )
    ```
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str = None,
        details: dict[str, Any] = None,
        source: str = None,
        cause: Exception = None,
    ):
        self.code = code
        self.message = message or code.message
        self.details = details or {}
        self.source = source
        self.cause = cause

        super().__init__(self.message)

    @property
    def full_code(self) -> str:
        """完整错误码"""
        return self.code.full_code

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.full_code,
            "message": self.message,
            "details": self.details,
            "source": self.source,
        }

    def __str__(self) -> str:
        return f"[{self.full_code}] {self.message}"


# 便捷方法
def raise_error(code: ErrorCode, message: str = None, **details) -> None:
    """抛出错误"""
    raise NEMTError(code=code, message=message, details=details)


# 子类便捷错误
class SystemError(NEMTError):
    """系统错误"""

    def __init__(self, message: str = None, **details):
        super().__init__(ErrorCode.SYS_003, message, details)


class ConfigError(NEMTError):
    """配置错误"""

    def __init__(self, message: str = None, **details):
        super().__init__(ErrorCode.CFG_001, message, details)


class DataError(NEMTError):
    """数据错误"""

    def __init__(self, message: str = None, **details):
        super().__init__(ErrorCode.DAT_001, message, details)


class ValidationError(NEMTError):
    """验证错误"""

    def __init__(self, message: str = None, **details):
        super().__init__(ErrorCode.VAL_001, message, details)


class BusinessError(NEMTError):
    """业务错误"""

    def __init__(self, message: str = None, **details):
        super().__init__(ErrorCode.BUS_001, message, details)
