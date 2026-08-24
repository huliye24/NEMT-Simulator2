"""
LogAggregator - 日志聚合系统

提供分布式日志收集、存储、搜索能力。
"""

import json
import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "LogLevel",
    "LogEntry",
    "LogQuery",
    "LogAggregator",
]


class LogLevel(Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """日志条目"""

    timestamp: float
    level: LogLevel
    message: str
    source: str
    capsule_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    user_id: str = ""
    metadata: dict = field(default_factory=dict)

    def __init__(
        self,
        level: LogLevel,
        message: str,
        source: str = "default",
        **kwargs,
    ):
        self.timestamp = time.time()
        self.level = level
        self.message = message
        self.source = source
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp)),
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "capsule_id": self.capsule_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class LogQuery:
    """日志查询"""

    start_time: float = 0
    end_time: float = 0
    levels: list[LogLevel] = None
    sources: list[str] = None
    capsule_id: str = ""
    trace_id: str = ""
    keywords: list[str] = None
    limit: int = 100
    offset: int = 0
    sort_order: str = "desc"  # asc, desc


class LogAggregator:
    """
    日志聚合器

    示例:
    ```python
    aggregator = LogAggregator()

    # 记录日志
    aggregator.log(LogLevel.INFO, "Strategy executed", source="trader")

    # 查询日志
    query = LogQuery(
        start_time=time.time() - 3600,
        levels=[LogLevel.ERROR, LogLevel.CRITICAL],
        keywords=["failed", "timeout"],
    )
    logs = aggregator.query(query)

    # 实时订阅
    aggregator.subscribe(lambda entry: print(entry.message))
    ```
    """

    def __init__(self, max_entries: int = 100000):
        self.max_entries = max_entries
        self._logs: list[LogEntry] = []
        self._logs_by_source: dict[str, list[LogEntry]] = defaultdict(list)
        self._logs_by_capsule: dict[str, list[LogEntry]] = defaultdict(list)
        self._lock = threading.RLock()
        self._subscribers: list[Callable] = []
        self._logger = logging.getLogger("LogAggregator")

    def log(
        self,
        level: LogLevel,
        message: str,
        source: str = "default",
        capsule_id: str = "",
        trace_id: str = "",
        **metadata,
    ) -> LogEntry:
        """记录日志"""
        entry = LogEntry(
            level=level,
            message=message,
            source=source,
            capsule_id=capsule_id,
            trace_id=trace_id,
            metadata=metadata,
        )

        with self._lock:
            self._logs.append(entry)
            self._logs_by_source[source].append(entry)

            if capsule_id:
                self._logs_by_capsule[capsule_id].append(entry)

            # 保持数量限制
            if len(self._logs) > self.max_entries:
                removed = self._logs[: len(self._logs) - self.max_entries]
                self._logs = self._logs[len(removed) :]
                self._cleanup_old_entries(removed)

        # 通知订阅者
        for subscriber in self._subscribers:
            try:
                subscriber(entry)
            except Exception as e:
                self._logger.error(f"日志订阅者执行失败: {e}")

        return entry

    def debug(self, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> LogEntry:
        return self.log(LogLevel.CRITICAL, message, **kwargs)

    def query(self, q: LogQuery) -> list[LogEntry]:
        """查询日志"""
        with self._lock:
            results = self._logs

        # 时间过滤
        if q.start_time > 0:
            results = [e for e in results if e.timestamp >= q.start_time]
        if q.end_time > 0:
            results = [e for e in results if e.timestamp <= q.end_time]

        # 级别过滤
        if q.levels:
            results = [e for e in results if e.level in q.levels]

        # 来源过滤
        if q.sources:
            results = [e for e in results if e.source in q.sources]

        # 胶囊过滤
        if q.capsule_id:
            results = [e for e in results if e.capsule_id == q.capsule_id]

        # 链路过滤
        if q.trace_id:
            results = [e for e in results if e.trace_id == q.trace_id]

        # 关键词过滤
        if q.keywords:
            for keyword in q.keywords:
                results = [e for e in results if keyword.lower() in e.message.lower()]

        # 排序
        if q.sort_order == "desc":
            results = sorted(results, key=lambda e: e.timestamp, reverse=True)
        else:
            results = sorted(results, key=lambda e: e.timestamp)

        # 分页
        return results[q.offset : q.offset + q.limit]

    def get_logs_by_capsule(self, capsule_id: str, limit: int = 100) -> list[LogEntry]:
        """获取胶囊日志"""
        with self._lock:
            logs = self._logs_by_capsule.get(capsule_id, [])
            return sorted(logs, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_recent_logs(self, limit: int = 100) -> list[LogEntry]:
        """获取最近日志"""
        with self._lock:
            return sorted(self._logs, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_stats(self) -> dict[str, Any]:
        """获取统计"""
        with self._lock:
            stats = {
                "total_logs": len(self._logs),
                "by_level": {},
                "by_source": {},
                "sources": list(self._logs_by_source.keys()),
            }

            for level in LogLevel:
                stats["by_level"][level.value] = len([e for e in self._logs if e.level == level])

            for source, logs in self._logs_by_source.items():
                stats["by_source"][source] = len(logs)

            return stats

    def subscribe(self, callback: Callable[[LogEntry], None]) -> None:
        """订阅日志"""
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable) -> bool:
        """取消订阅"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            return True
        return False

    def export(
        self,
        start_time: float = 0,
        end_time: float = 0,
        format: str = "json",
    ) -> str:
        """导出日志"""
        query = LogQuery(start_time=start_time, end_time=end_time, limit=100000)
        logs = self.query(query)

        if format == "json":
            return json.dumps([e.to_dict() for e in logs], ensure_ascii=False)
        elif format == "text":
            lines = []
            for e in logs:
                dt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e.timestamp))
                lines.append(f"[{dt}] [{e.level.value}] [{e.source}] {e.message}")
            return "\n".join(lines)
        return ""

    def clear(self, older_than: float = None) -> int:
        """清除日志"""
        with self._lock:
            if older_than:
                count = len([e for e in self._logs if e.timestamp < older_than])
                self._logs = [e for e in self._logs if e.timestamp >= older_than]
                return count
            else:
                count = len(self._logs)
                self._logs.clear()
                self._logs_by_source.clear()
                self._logs_by_capsule.clear()
                return count

    def _cleanup_old_entries(self, entries: list[LogEntry]) -> None:
        """清理旧条目"""
        for entry in entries:
            if entry.source in self._logs_by_source:
                try:
                    self._logs_by_source[entry.source].remove(entry)
                except ValueError:
                    pass
            if entry.capsule_id and entry.capsule_id in self._logs_by_capsule:
                try:
                    self._logs_by_capsule[entry.capsule_id].remove(entry)
                except ValueError:
                    pass


# 全局实例
_log_aggregator: LogAggregator | None = None


def get_log_aggregator() -> LogAggregator:
    """获取全局日志聚合器"""
    global _log_aggregator
    if _log_aggregator is None:
        _log_aggregator = LogAggregator()
    return _log_aggregator
