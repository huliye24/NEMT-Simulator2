#!/usr/bin/env python3
# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
结构化日志系统
"""

import os
import sys
import json
import logging
import traceback
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Dict


class StructuredFormatter(logging.Formatter):
    """JSON 结构化日志格式化器"""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
        self._thread_local = threading.local()

    def set_request_id(self, request_id: Optional[str]):
        """设置当前请求的 ID"""
        self._thread_local.request_id = request_id

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(self._thread_local, "request_id"):
            log_data["request_id"] = self._thread_local.request_id

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        if self.include_extra and hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False, default=str)


class HumanFormatter(logging.Formatter):
    """人类可读的日志格式"""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S")
        level = record.levelname

        parts = [
            f"[{ts}]",
            f"[{level:8s}]",
            f"[{record.name}]",
            record.getMessage(),
        ]

        if hasattr(record, "extra_data"):
            parts.append(json.dumps(record.extra_data, ensure_ascii=False, default=str))

        if record.exc_info:
            parts.append("".join(traceback.format_exception(*record.exc_info)))

        return " ".join(parts)


class StructuredLogger(logging.Logger):
    """带结构化能力的 Logger"""

    def __init__(self, name: str):
        super().__init__(name)
        self._request_id: Optional[str] = None

    def set_request_id(self, request_id: Optional[str]):
        self._request_id = request_id
        for handler in self.handlers:
            if isinstance(handler.formatter, StructuredFormatter):
                handler.formatter.set_request_id(request_id)

    def extra(self, message: str, **kwargs):
        """记录带额外字段的日志"""
        extra_record = logging.makeLogRecord({
            "msg": message,
            "extra": {"extra_data": kwargs},
            "exc_info": None,
        })
        extra_record.extra_data = kwargs
        self.handle(extra_record)

    def _log_with_extra(self, level: int, message: str, kwargs: Dict[str, Any]):
        """带额外字段的日志"""
        record = self.makeRecord(
            self.name, level, "(unknown)", 0, message, (), None
        )
        record.extra_data = kwargs
        self.handle(record)


def setup_logging(
    level: str = "INFO",
    use_json: bool = False,
    log_file: Optional[str] = None,
    request_id: Optional[str] = None,
) -> logging.Logger:
    """
    配置结构化日志系统

    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        use_json: 是否输出 JSON 格式
        log_file: 日志文件路径 (可选)
        request_id: 请求 ID (可选)
    """
    import sys

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    formatter = StructuredFormatter() if use_json else HumanFormatter()

    # Console handler with encoding error handling
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Override emit to handle GBK on Windows
    _orig_emit = console_handler.emit

    def _safe_emit(record):
        try:
            _orig_emit(record)
        except UnicodeEncodeError:
            pass  # Skip unencodable characters on Windows console

    console_handler.emit = _safe_emit
    root_logger.addHandler(console_handler)

    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

    if use_json and request_id:
        for handler in root_logger.handlers:
            if isinstance(handler.formatter, StructuredFormatter):
                handler.formatter.set_request_id(request_id)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取结构化 Logger"""
    return logging.getLogger(name)
