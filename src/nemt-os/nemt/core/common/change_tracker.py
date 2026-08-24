"""
Change Tracker - 实体变更追踪器

提供实体变更历史的记录和查询功能。

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


class ChangeType(Enum):
    """变更类型"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    FIELD_CHANGE = "field_change"


@dataclass
class FieldChange:
    """字段变更"""

    field_name: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "old_value": self._serialize(self.old_value),
            "new_value": self._serialize(self.new_value),
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def _serialize(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, "to_dict"):
            return value.to_dict()
        return value


@dataclass
class EntityChange:
    """实体变更记录"""

    entity_type: str
    entity_id: str
    change_type: ChangeType
    timestamp: datetime = field(default_factory=datetime.now)

    # 变更详情
    field_changes: list[FieldChange] = field(default_factory=list)
    old_state: dict[str, Any] | None = None
    new_state: dict[str, Any] | None = None

    # 元数据
    version: int = 1
    changed_by: str = ""
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "change_type": self.change_type.value,
            "timestamp": self.timestamp.isoformat(),
            "field_changes": [fc.to_dict() for fc in self.field_changes],
            "old_state": self.old_state,
            "new_state": self.new_state,
            "version": self.version,
            "changed_by": self.changed_by,
            "reason": self.reason,
            "metadata": self.metadata,
        }


class ChangeTracker:
    """
    变更追踪器

    线程安全的变更历史记录器。
    """

    def __init__(self, max_history: int = 1000):
        self._changes: list[EntityChange] = []
        self._max_history = max_history
        self._lock = threading.RLock()
        self._entity_index: dict[str, list[int]] = {}  # entity_id -> change indices

    def record_create(
        self,
        entity_type: str,
        entity_id: str,
        state: dict[str, Any],
        changed_by: str = "",
    ) -> EntityChange:
        """记录创建"""
        with self._lock:
            change = EntityChange(
                entity_type=entity_type,
                entity_id=entity_id,
                change_type=ChangeType.CREATE,
                new_state=state,
                changed_by=changed_by,
            )
            self._add_change(change)
            return change

    def record_update(
        self,
        entity_type: str,
        entity_id: str,
        old_state: dict[str, Any],
        new_state: dict[str, Any],
        changed_by: str = "",
        reason: str = "",
    ) -> EntityChange:
        """记录更新"""
        with self._lock:
            field_changes = self._compute_field_changes(old_state, new_state)
            change = EntityChange(
                entity_type=entity_type,
                entity_id=entity_id,
                change_type=ChangeType.UPDATE,
                field_changes=field_changes,
                old_state=old_state,
                new_state=new_state,
                changed_by=changed_by,
                reason=reason,
            )
            self._add_change(change)
            return change

    def record_delete(
        self,
        entity_type: str,
        entity_id: str,
        old_state: dict[str, Any],
        changed_by: str = "",
    ) -> EntityChange:
        """记录删除"""
        with self._lock:
            change = EntityChange(
                entity_type=entity_type,
                entity_id=entity_id,
                change_type=ChangeType.DELETE,
                old_state=old_state,
                changed_by=changed_by,
            )
            self._add_change(change)
            return change

    def _add_change(self, change: EntityChange) -> None:
        """添加变更记录"""
        change.version = len(self._changes) + 1
        self._changes.append(change)

        # 更新索引
        if change.entity_id not in self._entity_index:
            self._entity_index[change.entity_id] = []
        self._entity_index[change.entity_id].append(len(self._changes) - 1)

        # 清理超长历史
        if len(self._changes) > self._max_history:
            self._cleanup_old_changes()

    def _cleanup_old_changes(self) -> None:
        """清理旧变更"""
        keep_count = self._max_history // 2
        self._changes = self._changes[-keep_count:]
        # 重建索引
        self._entity_index.clear()
        for i, change in enumerate(self._changes):
            if change.entity_id not in self._entity_index:
                self._entity_index[change.entity_id] = []
            self._entity_index[change.entity_id].append(i)

    def _compute_field_changes(self, old_state: dict[str, Any], new_state: dict[str, Any]) -> list[FieldChange]:
        """计算字段变更"""
        changes = []
        all_keys = set(old_state.keys()) | set(new_state.keys())

        for key in all_keys:
            old_val = old_state.get(key)
            new_val = new_state.get(key)
            if old_val != new_val:
                changes.append(
                    FieldChange(
                        field_name=key,
                        old_value=old_val,
                        new_value=new_val,
                    )
                )

        return changes

    def get_entity_history(self, entity_id: str, limit: int = 100) -> list[EntityChange]:
        """获取实体的变更历史"""
        with self._lock:
            indices = self._entity_index.get(entity_id, [])
            changes = [self._changes[i] for i in indices[-limit:]]
            return changes

    def get_recent_changes(self, limit: int = 100) -> list[EntityChange]:
        """获取最近的变更"""
        with self._lock:
            return self._changes[-limit:]

    def get_changes_by_type(
        self, change_type: ChangeType, entity_type: str | None = None, limit: int = 100
    ) -> list[EntityChange]:
        """按类型获取变更"""
        with self._lock:
            result = [
                c
                for c in self._changes
                if c.change_type == change_type and (entity_type is None or c.entity_type == entity_type)
            ]
            return result[-limit:]

    def get_changes_in_range(self, start: datetime, end: datetime) -> list[EntityChange]:
        """获取时间范围内的变更"""
        with self._lock:
            return [c for c in self._changes if start <= c.timestamp <= end]

    def get_entity_state_at(self, entity_id: str, before: datetime) -> dict[str, Any] | None:
        """获取实体在指定时间之前的状态"""
        with self._lock:
            for change in reversed(self._changes):
                if change.entity_id == entity_id and change.timestamp <= before:
                    if change.change_type == ChangeType.DELETE:
                        return None
                    return change.new_state
            return None

    def export_changes(self, format: str = "json") -> str:
        """导出变更历史"""
        with self._lock:
            if format == "json":
                return json.dumps([c.to_dict() for c in self._changes], indent=2, default=str)
            return str(self._changes)

    def clear(self) -> None:
        """清空变更历史"""
        with self._lock:
            self._changes.clear()
            self._entity_index.clear()


# =============================================================================
# Entity Mixin for Change Tracking
# =============================================================================


class ChangeTrackingMixin:
    """变更追踪混入类"""

    _change_tracker: ChangeTracker = None  # 类级别共享

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if ChangeTracker._change_tracker is None:
            ChangeTracker._change_tracker = ChangeTracker()

    def _get_change_tracker(self) -> ChangeTracker:
        if ChangeTracker._change_tracker is None:
            ChangeTracker._change_tracker = ChangeTracker()
        return ChangeTracker._change_tracker

    def _track_create(self, state: dict[str, Any]) -> None:
        tracker = self._get_change_tracker()
        entity_id = self._get_entity_id()
        entity_type = self.__class__.__name__
        tracker.record_create(entity_type, entity_id, state)

    def _track_update(self, old_state: dict[str, Any], new_state: dict[str, Any]) -> None:
        tracker = self._get_change_tracker()
        entity_id = self._get_entity_id()
        entity_type = self.__class__.__name__
        tracker.record_update(entity_type, entity_id, old_state, new_state)

    def _track_delete(self, old_state: dict[str, Any]) -> None:
        tracker = self._get_change_tracker()
        entity_id = self._get_entity_id()
        entity_type = self.__class__.__name__
        tracker.record_delete(entity_type, entity_id, old_state)

    def _get_entity_id(self) -> str:
        """子类应实现此方法返回实体ID"""
        raise NotImplementedError("Subclass must implement _get_entity_id()")

    def get_change_history(self, limit: int = 100) -> list[EntityChange]:
        """获取此实体的变更历史"""
        tracker = self._get_change_tracker()
        return tracker.get_entity_history(self._get_entity_id(), limit)
