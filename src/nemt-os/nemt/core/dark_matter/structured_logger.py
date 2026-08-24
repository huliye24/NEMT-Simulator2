"""
Structured Logger - 结构化日志系统

提供统一的结构化日志接口:
- JSON 格式日志输出
- 上下文传播
- 字段规范（胶囊 ID、K 线索引、交易对等）
- 多输出目标（控制台、文件）
- 日志级别和过滤

参考: Notion 暗物质框架 第一章「日志即宇宙背景辐射，结构化即可见性」
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# ============================================================================
# 日志字段常量
# ============================================================================

LOG_CAPSULE_ID = "capsule_id"  # 胶囊 ID
LOG_TRACE_ID = "trace_id"  # 追踪 ID
LOG_BAR_INDEX = "bar_index"  # K 线索引
LOG_SYMBOL = "symbol"  # 交易品种
LOG_EVENT_TYPE = "event_type"  # 事件类型
LOG_DURATION_MS = "duration_ms"  # 执行时长（毫秒）
LOG_ERROR_CODE = "error_code"  # 错误码
LOG_LEVEL = "level"  # 日志级别
LOG_TIMESTAMP = "timestamp"  # 时间戳
LOG_MESSAGE = "message"  # 日志消息
LOG_MODULE = "module"  # 模块名
LOG_FUNCTION = "function"  # 函数名
LOG_LINE = "line"  # 行号


# ============================================================================
# 日志级别枚举
# ============================================================================


class LogLevel(Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_python_level(cls, level: int) -> LogLevel:
        """从 Python 日志级别转换"""
        if level >= logging.CRITICAL:
            return cls.CRITICAL
        elif level >= logging.ERROR:
            return cls.ERROR
        elif level >= logging.WARNING:
            return cls.WARNING
        elif level >= logging.INFO:
            return cls.INFO
        else:
            return cls.DEBUG


# ============================================================================
# 日志上下文
# ============================================================================


@dataclass
class LogContext:
    """
    日志上下文

    存储当前日志的上下文信息，会自动添加到每条日志中。

    Attributes:
        capsule_id: 胶囊 ID
        trace_id: 追踪 ID（用于跨请求追踪）
        bar_index: K 线索引
        symbol: 交易品种
        event_type: 事件类型
        extra: 额外字段
    """

    capsule_id: str | None = None
    trace_id: str | None = None
    bar_index: int | None = None
    symbol: str | None = None
    event_type: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {}
        if self.capsule_id:
            result[LOG_CAPSULE_ID] = self.capsule_id
        if self.trace_id:
            result[LOG_TRACE_ID] = self.trace_id
        if self.bar_index is not None:
            result[LOG_BAR_INDEX] = self.bar_index
        if self.symbol:
            result[LOG_SYMBOL] = self.symbol
        if self.event_type:
            result[LOG_EVENT_TYPE] = self.event_type
        result.update(self.extra)
        return result

    def with_trace_id(self, trace_id: str) -> LogContext:
        """创建带追踪 ID 的新上下文"""
        return LogContext(
            capsule_id=self.capsule_id,
            trace_id=trace_id,
            bar_index=self.bar_index,
            symbol=self.symbol,
            event_type=self.event_type,
            extra=self.extra.copy(),
        )


# ============================================================================
# 上下文管理器（线程局部存储）
# ============================================================================


class _ContextStorage:
    """线程局部上下文存储"""

    def __init__(self):
        self._local = threading.local()

    def get(self) -> LogContext | None:
        """获取当前上下文"""
        return getattr(self._local, "context", None)

    def set(self, context: LogContext | None) -> None:
        """设置当前上下文"""
        if context is None:
            if hasattr(self._local, "context"):
                delattr(self._local, "context")
        else:
            self._local.context = context

    def clear(self) -> None:
        """清除当前上下文"""
        if hasattr(self._local, "context"):
            delattr(self._local, "context")


# 全局上下文存储
_context_storage = _ContextStorage()


# ============================================================================
# JSON 格式化器
# ============================================================================


class JSONFormatter(logging.Formatter):
    """
    JSON 日志格式化器

    将日志记录格式化为 JSON 字符串，方便日志收集和分析。
    """

    def __init__(self, include_context: bool = True, include_extra: bool = True):
        """
        Args:
            include_context: 是否包含日志上下文
            include_extra: 是否包含额外字段
        """
        super().__init__()
        self.include_context = include_context
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为 JSON 字符串

        Args:
            record: 日志记录

        Returns:
            JSON 格式的日志字符串
        """
        log_entry = {
            LOG_TIMESTAMP: datetime.fromtimestamp(record.created).isoformat(),
            LOG_LEVEL: record.levelname,
            LOG_MESSAGE: record.getMessage(),
            LOG_MODULE: record.module,
            LOG_FUNCTION: record.funcName,
            LOG_LINE: record.lineno,
        }

        # 添加上下文
        if self.include_context:
            context = _context_storage.get()
            if context:
                log_entry.update(context.to_dict())

        # 添加额外字段
        if self.include_extra and hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


# ============================================================================
# 控制台着色格式化器
# ============================================================================


class ColoredFormatter(logging.Formatter):
    """
    带颜色的控制台格式化器

    在终端中显示带颜色的日志。
    """

    # ANSI 颜色码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def __init__(self, include_context: bool = False):
        super().__init__()
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET

        # 基本格式
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        level = record.levelname.ljust(8)
        message = record.getMessage()

        # 添加上下文
        context_str = ""
        if self.include_context:
            context = _context_storage.get()
            if context:
                parts = []
                if context.capsule_id:
                    parts.append(f"[{context.capsule_id}]")
                if context.symbol:
                    parts.append(f"[{context.symbol}]")
                if context.bar_index is not None:
                    parts.append(f"[#{context.bar_index}]")
                context_str = " ".join(parts) + " "

        return f"{color}{timestamp}{reset} {level} {context_str}{message}"


# ============================================================================
# 结构化日志器
# ============================================================================


class StructuredLogger:
    """
    结构化日志器

    提供统一的结构化日志接口，支持:
    - JSON 格式日志
    - 上下文传播
    - 多输出目标
    - 日志级别控制

    Usage:
        logger = StructuredLogger("my_module")
        logger.info("Processing order", context={"order_id": "123"})
    """

    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        output_json: bool = False,
        log_file: str | Path | None = None,
        include_context: bool = True,
    ):
        """
        Args:
            name: 日志名称（通常是模块名）
            level: 日志级别
            output_json: 是否输出 JSON 格式
            log_file: 日志文件路径（可选）
            include_context: 是否包含上下文
        """
        self._name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.propagate = False  # 避免重复输出
        self._include_context = include_context

        # 清除现有处理器
        self._logger.handlers.clear()

        # 添加处理器
        if output_json or log_file:
            # JSON 或文件输出
            json_handler = logging.StreamHandler(sys.stdout if output_json else None)
            json_handler.setFormatter(JSONFormatter(include_context=include_context))
            json_handler.setLevel(level)
            self._logger.addHandler(json_handler)

        if not output_json:
            # 控制台输出（带颜色）
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColoredFormatter(include_context=include_context))
            console_handler.setLevel(level)
            self._logger.addHandler(console_handler)

        # 文件处理器
        if log_file:
            self.add_file_handler(log_file, level, output_json=True)

    def add_file_handler(
        self,
        log_file: str | Path,
        level: int = logging.INFO,
        output_json: bool = True,
    ) -> None:
        """
        添加文件处理器

        Args:
            log_file: 日志文件路径
            level: 日志级别
            output_json: 是否输出 JSON 格式
        """
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        if output_json:
            file_handler.setFormatter(JSONFormatter(include_context=self._include_context))
        else:
            file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        file_handler.setLevel(level)
        self._logger.addHandler(file_handler)

    def set_level(self, level: int) -> None:
        """设置日志级别"""
        self._logger.setLevel(level)

    def set_context(self, context: LogContext) -> None:
        """设置日志上下文"""
        _context_storage.set(context)

    def clear_context(self) -> None:
        """清除日志上下文"""
        _context_storage.clear()

    @property
    def context(self) -> LogContext | None:
        """获取当前上下文"""
        return _context_storage.get()

    def _log(self, level: int, message: str, **kwargs) -> None:
        """内部日志方法"""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs) -> None:
        """DEBUG 级别日志"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """INFO 级别日志"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """WARNING 级别日志"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """ERROR 级别日志"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """CRITICAL 级别日志"""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """记录异常（自动包含堆栈信息）"""
        self._log(logging.ERROR, message, **kwargs)

    def log_with_context(
        self,
        level: int,
        message: str,
        capsule_id: str | None = None,
        trace_id: str | None = None,
        bar_index: int | None = None,
        symbol: str | None = None,
        event_type: str | None = None,
        **kwargs,
    ) -> None:
        """
        带显式上下文的日志记录

        Args:
            level: 日志级别
            message: 日志消息
            capsule_id: 胶囊 ID
            trace_id: 追踪 ID
            bar_index: K 线索引
            symbol: 交易品种
            event_type: 事件类型
            **kwargs: 额外字段
        """
        context = LogContext(
            capsule_id=capsule_id,
            trace_id=trace_id,
            bar_index=bar_index,
            symbol=symbol,
            event_type=event_type,
        )
        _context_storage.set(context)
        try:
            self._log(level, message, **kwargs)
        finally:
            _context_storage.clear()


# ============================================================================
# 全局日志器工厂
# ============================================================================

_loggers: dict[str, StructuredLogger] = {}
_loggers_lock = threading.Lock()


def get_logger(
    name: str,
    level: int = logging.INFO,
    output_json: bool = False,
    log_file: str | Path | None = None,
    include_context: bool = True,
) -> StructuredLogger:
    """
    获取或创建结构化日志器

    Args:
        name: 日志名称（通常是模块名）
        level: 日志级别
        output_json: 是否输出 JSON 格式
        log_file: 日志文件路径（可选）
        include_context: 是否包含上下文

    Returns:
        StructuredLogger 实例
    """
    with _loggers_lock:
        if name not in _loggers:
            _loggers[name] = StructuredLogger(
                name=name,
                level=level,
                output_json=output_json,
                log_file=log_file,
                include_context=include_context,
            )
        return _loggers[name]


def clear_loggers() -> None:
    """清除所有日志器（用于测试）"""
    global _loggers
    with _loggers_lock:
        _loggers.clear()


# ============================================================================
# 便捷上下文管理器
# ============================================================================


class LogContextManager:
    """日志上下文管理器"""

    def __init__(self, logger: StructuredLogger):
        self._logger = logger
        self._old_context: LogContext | None = None

    def __enter__(self) -> LogContextManager:
        self._old_context = _context_storage.get()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        _context_storage.set(self._old_context)

    def set(
        self,
        capsule_id: str | None = None,
        trace_id: str | None = None,
        bar_index: int | None = None,
        symbol: str | None = None,
        event_type: str | None = None,
        **extra,
    ) -> LogContextManager:
        """设置上下文字段"""
        context = LogContext(
            capsule_id=capsule_id,
            trace_id=trace_id,
            bar_index=bar_index,
            symbol=symbol,
            event_type=event_type,
            extra=extra,
        )
        _context_storage.set(context)
        return self


def log_context(
    capsule_id: str | None = None,
    trace_id: str | None = None,
    bar_index: int | None = None,
    symbol: str | None = None,
    event_type: str | None = None,
    **extra,
) -> LogContextManager:
    """
    日志上下文管理器

    Usage:
        logger = get_logger("my_module")
        with log_context(capsule_id="execution", symbol="BTC"):
            logger.info("Processing trade")
    """
    context = LogContext(
        capsule_id=capsule_id,
        trace_id=trace_id,
        bar_index=bar_index,
        symbol=symbol,
        event_type=event_type,
        extra=extra,
    )
    _context_storage.set(context)
    return LogContextManager(get_logger("__internal__"))
