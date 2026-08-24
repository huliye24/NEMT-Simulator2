"""
ErrorHandler - 错误处理器

提供统一的错误处理和报告功能。
"""

import threading
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from nemt.core.errors.error_codes import ErrorCode, NEMTError

__all__ = ["ErrorHandler", "ErrorRecord", "get_error_handler"]


class ErrorLevel(Enum):
    """错误级别"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """错误记录"""

    error_id: str
    code: ErrorCode
    message: str
    level: ErrorLevel
    source: str
    details: dict[str, Any]
    traceback: str
    timestamp: float
    resolved: bool = False
    resolved_at: float = None


class ErrorHandler:
    """
    错误处理器

    管理错误记录、报告和统计。

    示例:
    ```python
    handler = ErrorHandler()

    try:
        risky_operation()
    except Exception as e:
        handler.handle(e, source="my_module")
    ```
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._records: list[ErrorRecord] = []
        self._max_records = 1000
        self._listeners: list[Callable] = []
        self._handlers: dict[str, Callable] = {}
        self._stats: dict[str, int] = {}
        self._lock = threading.Lock()
        self._initialized = True

    def handle(
        self,
        error: Exception,
        source: str = None,
        details: dict[str, Any] = None,
        context: Any = None,
    ) -> ErrorRecord:
        """
        处理错误

        Args:
            error: 异常对象
            source: 来源
            details: 详情
            context: 上下文

        Returns:
            错误记录
        """
        # 创建错误记录
        if isinstance(error, NEMTError):
            code = error.code
            message = error.message
            error_details = error.details
        else:
            code = ErrorCode.SYS_003
            message = str(error)
            error_details = {"type": type(error).__name__}

        if details:
            error_details.update(details)

        # 获取堆栈跟踪
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        # 创建记录
        record = ErrorRecord(
            error_id=self._generate_id(),
            code=code,
            message=message,
            level=self._get_level(code),
            source=source or "unknown",
            details=error_details,
            traceback=tb,
            timestamp=time.time(),
        )

        # 存储记录
        with self._lock:
            self._records.append(record)
            if len(self._records) > self._max_records:
                self._records.pop(0)

        # 更新统计
        self._update_stats(code)

        # 通知监听器
        self._notify_listeners(record)

        # 调用特定处理器
        if code.full_code in self._handlers:
            self._handlers[code.full_code](record)

        return record

    def _generate_id(self) -> str:
        """生成错误 ID"""
        import uuid

        return str(uuid.uuid4())[:8]

    def _get_level(self, code: ErrorCode) -> ErrorLevel:
        """获取错误级别"""
        category = code.category.value
        if category in ("system", "internal"):
            return ErrorLevel.ERROR
        elif category == "security":
            return ErrorLevel.WARNING
        else:
            return ErrorLevel.INFO

    def _update_stats(self, code: ErrorCode) -> None:
        """更新统计"""
        key = code.full_code
        self._stats[key] = self._stats.get(key, 0) + 1

    def _notify_listeners(self, record: ErrorRecord) -> None:
        """通知监听器"""
        for listener in self._listeners:
            try:
                listener(record)
            except Exception:
                pass

    def add_listener(self, listener: Callable[[ErrorRecord], None]) -> None:
        """添加错误监听器"""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable) -> None:
        """移除错误监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def register_handler(self, error_code: str, handler: Callable[[ErrorRecord], None]) -> None:
        """注册特定错误码的处理器"""
        self._handlers[error_code] = handler

    def get_records(
        self,
        level: ErrorLevel = None,
        code: ErrorCode = None,
        source: str = None,
        limit: int = 100,
    ) -> list[ErrorRecord]:
        """获取错误记录"""
        records = self._records

        if level:
            records = [r for r in records if r.level == level]
        if code:
            records = [r for r in records if r.code == code]
        if source:
            records = [r for r in records if r.source == source]

        return records[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """获取错误统计"""
        return {
            "total": len(self._records),
            "by_code": self._stats.copy(),
            "recent": [r.to_dict() if hasattr(r, "to_dict") else r for r in self._records[-10:]],
        }

    def clear(self) -> None:
        """清除错误记录"""
        with self._lock:
            self._records.clear()
            self._stats.clear()

    def resolve(self, error_id: str) -> bool:
        """标记错误已解决"""
        with self._lock:
            for record in self._records:
                if record.error_id == error_id:
                    record.resolved = True
                    record.resolved_at = time.time()
                    return True
        return False


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    return ErrorHandler()
