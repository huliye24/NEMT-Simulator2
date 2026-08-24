"""
StructuredLogger - 结构化日志系统

提供:
- JSON 格式日志
- 结构化日志
- 请求 ID 追踪
- ELK 集成支持
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime

# 请求上下文
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")

__all__ = [
    "StructuredLogger",
    "JSONFormatter",
    "get_logger",
    "set_request_context",
    "get_request_context",
    "clear_request_context",
]


class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加请求上下文
        request_id = request_id_var.get()
        trace_id = trace_id_var.get()
        user_id = user_id_var.get()

        if request_id:
            log_data["request_id"] = request_id
        if trace_id:
            log_data["trace_id"] = trace_id
        if user_id:
            log_data["user_id"] = user_id

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if self.include_extra:
            extra = getattr(record, "extra", {})
            if extra:
                log_data["extra"] = extra

            # 添加 metrics
            metrics = getattr(record, "metrics", {})
            if metrics:
                log_data["metrics"] = metrics

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台格式化器"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET

        # 基础信息
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        logger = record.name
        message = record.getMessage()

        # 请求上下文
        request_id = request_id_var.get()
        trace_id = trace_id_var.get()

        context = ""
        if request_id:
            context += f"[{request_id[:8]}]"
        if trace_id:
            context += f"[{trace_id[:8]}]"

        result = f"{color}{timestamp}{reset} {level} {logger} {context} {message}"

        if record.exc_info:
            result += "\n" + self.formatException(record.exc_info)

        return result


class StructuredLogger:
    """
    结构化日志记录器

    示例:
    ```python
    logger = get_logger("my_module")

    # 普通日志
    logger.info("Processing request")

    # 结构化日志
    logger.info("Request completed", extra={
        "request_id": "12345",
        "duration_ms": 150,
        "status": 200
    })

    # 带 metrics
    logger.info("Batch processed", metrics={
        "processed": 100,
        "failed": 5
    })
    ```

    ELK 集成:
    ```python
    setup_logging(format="json")
    ```
    """

    def __init__(self, name: str, logger: logging.Logger = None):
        self.name = name
        self._logger = logger or logging.getLogger(name)

    def debug(self, msg: str, *args, **kwargs):
        """调试日志"""
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """信息日志"""
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """警告日志"""
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """错误日志"""
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """严重错误日志"""
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """异常日志（自动包含堆栈）"""
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, *args, **kwargs)

    def _log(self, level: int, msg: str, *args, **kwargs):
        """内部日志方法"""
        extra = kwargs.pop("extra", None)
        metrics = kwargs.pop("metrics", None)

        record = self._logger.makeRecord(
            self._logger.name,
            level,
            "(unknown)",
            0,
            msg,
            args,
            None,
        )

        if extra:
            record.extra = extra
        if metrics:
            record.metrics = metrics

        self._logger.handle(record)


def get_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器"""
    return StructuredLogger(name)


# ============================================================================
# 日志配置
# ============================================================================

_logging_configured = False


def setup_logging(
    level: str = "INFO",
    format: str = "colored",
    log_file: str = None,
    log_dir: str = "logs",
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别
        format: 格式类型 ("json", "colored", "simple")
        log_file: 日志文件路径
        log_dir: 日志目录
    """
    global _logging_configured

    if _logging_configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)

    if format == "json":
        console_handler.setFormatter(JSONFormatter())
    elif format == "colored":
        console_handler.setFormatter(ColoredFormatter())
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        import os

        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, log_file)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    _logging_configured = True


# ============================================================================
# 请求上下文管理
# ============================================================================


def set_request_context(request_id: str = None, trace_id: str = None, user_id: str = None) -> None:
    """
    设置请求上下文

    Args:
        request_id: 请求 ID
        trace_id: 追踪 ID
        user_id: 用户 ID
    """
    if request_id:
        request_id_var.set(request_id)
    if trace_id:
        trace_id_var.set(trace_id)
    if user_id:
        user_id_var.set(user_id)


def get_request_context() -> dict[str, str]:
    """获取当前请求上下文"""
    return {
        "request_id": request_id_var.get(),
        "trace_id": trace_id_var.get(),
        "user_id": user_id_var.get(),
    }


def clear_request_context() -> None:
    """清除请求上下文"""
    request_id_var.set("")
    trace_id_var.set("")
    user_id_var.set("")


def generate_request_id() -> str:
    """生成请求 ID"""
    return str(uuid.uuid4())


class RequestContextManager:
    """请求上下文管理器"""

    def __init__(self, request_id: str = None, trace_id: str = None, user_id: str = None):
        self.request_id = request_id or generate_request_id()
        self.trace_id = trace_id or generate_request_id()
        self.user_id = user_id
        self._old_context = {}

    def __enter__(self):
        self._old_context = get_request_context()
        set_request_context(self.request_id, self.trace_id, self.user_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        set_request_context(
            self._old_context.get("request_id", ""),
            self._old_context.get("trace_id", ""),
            self._old_context.get("user_id", ""),
        )
