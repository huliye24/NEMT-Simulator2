"""
NEMT 日志系统

统一的日志记录和格式化。
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record):
        if sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class NEMTLogger:
    """NEMT 日志记录器"""

    _loggers = {}

    @classmethod
    def get_logger(cls, name: str, level: int = logging.INFO) -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 记录器名称
            level: 日志级别

        Returns:
            日志记录器
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level)

        # 避免重复添加处理器
        if not logger.handlers:
            # 控制台处理器
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(level)

            # 格式化
            fmt = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
            date_fmt = "%H:%M:%S"
            formatter = ColoredFormatter(fmt, date_fmt)
            console.setFormatter(formatter)

            logger.addHandler(console)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def setup_file_logger(cls, name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
        """
        设置文件日志记录器

        Args:
            name: 记录器名称
            log_file: 日志文件路径
            level: 日志级别

        Returns:
            日志记录器
        """
        logger = cls.get_logger(name, level)

        # 文件处理器
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)

        # 文件格式化
        fmt = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
        date_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(fmt, date_fmt)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        return logger

    @classmethod
    def set_level(cls, name: str, level: int) -> None:
        """设置日志级别"""
        if name in cls._loggers:
            cls._loggers[name].setLevel(level)

    @classmethod
    def add_handler(cls, name: str, handler: logging.Handler) -> None:
        """添加处理器"""
        if name in cls._loggers:
            cls._loggers[name].addHandler(handler)


class LogContext:
    """日志上下文"""

    def __init__(self, logger: logging.Logger, message: str, level: int = logging.INFO):
        self.logger = logger
        self.message = message
        self.level = level
        self.start_time = datetime.now()

    def __enter__(self):
        self.logger.log(self.level, f"[开始] {self.message}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.error(f"[失败] {self.message} ({elapsed:.2f}s): {exc_val}")
        else:
            self.logger.log(self.level, f"[完成] {self.message} ({elapsed:.2f}s)")


# ==================== 便捷函数 ====================


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return NEMTLogger.get_logger(name)


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """设置日志记录器"""
    if log_file:
        return NEMTLogger.setup_file_logger(name, log_file)
    return NEMTLogger.get_logger(name)


def log_context(logger: logging.Logger, message: str, level: int = logging.INFO) -> LogContext:
    """创建日志上下文"""
    return LogContext(logger, message, level)
