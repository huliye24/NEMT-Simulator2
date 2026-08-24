"""
AuditLogger - 审计日志

提供操作审计、合规追踪能力。
"""

import json
import logging
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

__all__ = [
    "AuditEvent",
    "AuditAction",
    "AuditLogger",
]


class AuditAction(Enum):
    """审计动作"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    GRANT = "grant"  # 授权
    REVOKE = "revoke"  # 撤销授权
    EXECUTE = "execute"  # 执行
    EXPORT = "export"  # 导出
    IMPORT = "import"  # 导入
    CONFIGURE = "configure"  # 配置变更


@dataclass
class AuditEvent:
    """审计事件"""

    event_id: str
    timestamp: float
    action: AuditAction
    resource_type: str
    resource_id: str
    user_id: str
    user_name: str = ""
    ip_address: str = ""
    user_agent: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    result: str = "success"  # success, failure
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        user_id: str,
        user_name: str = "",
        **kwargs,
    ):
        self.event_id = str(uuid.uuid4())
        self.timestamp = time.time()
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.user_id = user_id
        self.user_name = user_name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
            "result": self.result,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """
    审计日志记录器

    示例:
    ```python
    logger = AuditLogger()

    # 记录审计事件
    logger.log(
        action=AuditAction.UPDATE,
        resource_type="strategy",
        resource_id="strategy-123",
        user_id="user-456",
        details={"field": "name", "old": "old", "new": "new"},
    )

    # 查询审计日志
    events = logger.query(
        user_id="user-456",
        action=AuditAction.UPDATE,
        start_time=time.time() - 86400,
    )
    ```
    """

    def __init__(self, storage_path: str = "audit.log"):
        self.storage_path = storage_path
        self._events: list[AuditEvent] = []
        self._lock = threading.RLock()
        self._handlers: list[Callable] = []
        self._max_events = 10000
        self._logger = logging.getLogger("AuditLogger")

    def log(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        user_id: str,
        user_name: str = "",
        **kwargs,
    ) -> AuditEvent:
        """记录审计事件"""
        event = AuditEvent(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_name=user_name,
            **kwargs,
        )

        with self._lock:
            self._events.append(event)

            # 保持事件数量限制
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events :]

        # 调用处理器
        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"审计处理器执行失败: {e}")

        # 写入存储
        self._write_to_storage(event)

        return event

    def query(
        self,
        user_id: str = None,
        action: AuditAction = None,
        resource_type: str = None,
        resource_id: str = None,
        start_time: float = None,
        end_time: float = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """查询审计日志"""
        with self._lock:
            events = self._events

        # 过滤
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if action:
            events = [e for e in events if e.action == action]
        if resource_type:
            events = [e for e in events if e.resource_type == resource_type]
        if resource_id:
            events = [e for e in events if e.resource_id == resource_id]
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # 按时间倒序
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    def add_handler(self, handler: Callable[[AuditEvent], None]) -> None:
        """添加审计事件处理器"""
        self._handlers.append(handler)

    def get_user_activity(
        self,
        user_id: str,
        start_time: float = None,
        end_time: float = None,
    ) -> dict[str, int]:
        """获取用户活动统计"""
        events = self.query(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000,
        )

        stats = {}
        for event in events:
            action = event.action.value
            stats[action] = stats.get(action, 0) + 1

        return stats

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[AuditEvent]:
        """获取资源变更历史"""
        return self.query(
            resource_type=resource_type,
            resource_id=resource_id,
        )

    def export(
        self,
        start_time: float = None,
        end_time: float = None,
        format: str = "json",
    ) -> str:
        """导出审计日志"""
        events = self.query(
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )

        if format == "json":
            return json.dumps([e.to_dict() for e in events], ensure_ascii=False, indent=2)
        elif format == "csv":
            return self._to_csv(events)
        return ""

    def _to_csv(self, events: list[AuditEvent]) -> str:
        """转换为 CSV 格式"""
        if not events:
            return ""

        lines = ["event_id,timestamp,action,resource_type,resource_id,user_id,result"]

        for event in events:
            lines.append(
                f"{event.event_id},{event.timestamp},{event.action.value},"
                f"{event.resource_type},{event.resource_id},{event.user_id},{event.result}"
            )

        return "\n".join(lines)

    def _write_to_storage(self, event: AuditEvent) -> None:
        """写入存储"""
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            self._logger.error(f"写入审计日志失败: {e}")

    def load_from_storage(self) -> int:
        """从存储加载"""
        count = 0
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            event = AuditEvent(
                                action=AuditAction(data["action"]),
                                resource_type=data["resource_type"],
                                resource_id=data["resource_id"],
                                user_id=data["user_id"],
                            )
                            event.event_id = data["event_id"]
                            event.timestamp = data["timestamp"]
                            self._events.append(event)
                            count += 1
                        except Exception:
                            pass
        except FileNotFoundError:
            pass
        except Exception as e:
            self._logger.error(f"加载审计日志失败: {e}")

        return count


# 全局实例
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """获取全局审计日志记录器"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
