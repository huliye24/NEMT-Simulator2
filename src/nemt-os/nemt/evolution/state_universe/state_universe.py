"""
L-State: 状态管理层 - 状态宇宙

状态宇宙是整个系统状态的全局视图，它不仅仅是数据的存储，
而是状态的本体论——定义什么是状态、状态如何存在、状态之间的关系。

核心概念:
- StateUniverse: 状态宇宙容器
- StateEntity: 状态实体
- StateRelation: 状态关系
- StateEvent: 状态事件 (用于溯源)
- StateSnapshot: 状态快照
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
)

logger = logging.getLogger(__name__)

# =============================================================================
# 基础类型定义
# =============================================================================

EntityId = str
RelationId = str
EventId = str
SnapshotId = str
PropertyId = str


class EntityType(Enum):
    """实体类型"""

    # 基础类型
    PRIMITIVE = auto()  # 原始值
    OBJECT = auto()  # 对象
    COLLECTION = auto()  # 集合

    # 业务类型
    MARKET_DATA = auto()  # 市场数据
    STRATEGY = auto()  # 策略
    SIGNAL = auto()  # 信号
    ORDER = auto()  # 订单
    POSITION = auto()  # 持仓
    ACCOUNT = auto()  # 账户

    # 系统类型
    RULE = auto()  # 规则
    CONSTRAINT = auto()  # 约束
    METRIC = auto()  # 指标
    EVENT = auto()  # 事件

    # 元类型
    META_RULE = auto()  # 元规则
    EVOLUTION = auto()  # 演化状态


class RelationType(Enum):
    """关系类型"""

    # 基础关系
    DEPENDS_ON = auto()  # 依赖于
    COMPOSES = auto()  # 组合
    IMPLEMENTS = auto()  # 实现
    INHERITS = auto()  # 继承

    # 业务关系
    GENERATES = auto()  # 生成
    TRIGGERS = auto()  # 触发
    VALIDATES = auto()  # 验证
    EXECUTES = auto()  # 执行

    # 状态关系
    EVOLVED_FROM = auto()  # 从...演化
    SNAPSHOT_OF = auto()  # ...的快照
    VERSION_OF = auto()  # ...的版本


class EventType(Enum):
    """事件类型"""

    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    RELATE = auto()
    UNRELATE = auto()
    SNAPSHOT = auto()
    RESTORE = auto()
    EVOLVE = auto()


class Severity(Enum):
    """严重程度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# 状态实体模型
# =============================================================================


@dataclass
class Property:
    """属性定义"""

    name: str
    value: Any
    type: str = "any"  # 类型提示
    is_nullable: bool = True
    default: Any = None
    constraints: list[Constraint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> tuple[bool, str | None]:
        """验证属性值"""
        if self.value is None and not self.is_nullable:
            return False, f"Property {self.name} cannot be null"

        for constraint in self.constraints:
            valid, msg = constraint.validate(self.value)
            if not valid:
                return False, msg

        return True, None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.type,
            "is_nullable": self.is_nullable,
            "default": self.default,
        }


@dataclass
class Constraint:
    """约束定义"""

    name: str
    validator: Callable[[Any], bool]
    error_message: str = "Constraint violated"

    def validate(self, value: Any) -> tuple[bool, str | None]:
        try:
            if self.validator(value):
                return True, None
            return False, self.error_message
        except Exception as e:
            return False, f"Validation error: {e}"


@dataclass
class StateRelation:
    """状态关系"""

    id: RelationId
    source_id: EntityId
    target_id: EntityId
    type: RelationType
    properties: dict[str, Property] = field(default_factory=dict)
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.name,
            "properties": {k: v.to_dict() for k, v in self.properties.items()},
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class StateEntity:
    """
    状态实体

    代表系统中的一个可识别实体，如策略、信号、订单等。
    实体具有唯一ID、类型、属性和关系。
    """

    id: EntityId
    type: EntityType
    name: str
    properties: dict[str, Property] = field(default_factory=dict)
    relations: dict[str, RelationId] = field(default_factory=dict)  # relation_name -> relation_id
    version: int = 1
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_property(self, name: str) -> Any | None:
        """获取属性值"""
        prop = self.properties.get(name)
        return prop.value if prop else None

    def set_property(self, name: str, value: Any, type_hint: str = "any"):
        """设置属性"""
        prop = Property(name=name, value=value, type=type_hint)
        valid, msg = prop.validate()
        if not valid:
            raise ValueError(msg)
        self.properties[name] = prop
        self.updated_at = datetime.now()
        self.version += 1

    def get_related_entities(self, relation_type: RelationType) -> list[EntityId]:
        """获取指定关系的实体ID列表"""
        result = []
        for rel_id in self.relations.values():
            if hasattr(rel_id, "type") and rel_id.type == relation_type:
                result.append(rel_id.target_id)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.name,
            "name": self.name,
            "properties": {k: {"name": v.name, "value": v.value, "type": v.type} for k, v in self.properties.items()},
            "relations": self.relations,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateEntity:
        """从字典创建"""
        properties = {}
        for k, v in data.get("properties", {}).items():
            if isinstance(v, dict):
                properties[k] = Property(
                    name=v.get("name", k),
                    value=v.get("value"),
                    type=v.get("type", "any"),
                )
            else:
                properties[k] = Property(name=k, value=v)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=EntityType[data.get("type", "OBJECT")],
            name=data.get("name", ""),
            properties=properties,
            relations=data.get("relations", {}),
            version=data.get("version", 1),
            status=data.get("status", "active"),
        )


# =============================================================================
# 状态事件 (用于溯源)
# =============================================================================


@dataclass
class StateDiff:
    """状态差异"""

    added: dict[str, Any] = field(default_factory=dict)
    removed: dict[str, Any] = field(default_factory=dict)
    changed: dict[str, tuple[Any, Any]] = field(default_factory=dict)  # old, new

    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "added": self.added,
            "removed": self.removed,
            "changed": {k: {"old": v[0], "new": v[1]} for k, v in self.changed.items()},
        }


@dataclass
class StateEvent:
    """
    状态事件

    记录所有状态变更，用于溯源和回滚。
    """

    id: EventId
    entity_id: EntityId
    event_type: EventType
    previous_state: dict[str, Any] | None
    current_state: dict[str, Any]
    diff: StateDiff
    timestamp: datetime = field(default_factory=datetime.now)
    actor: str = "system"  # system, human, ai, evolution
    cause: str | None = None  # 变更原因
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "event_type": self.event_type.name,
            "previous_state": self.previous_state,
            "current_state": self.current_state,
            "diff": self.diff.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "cause": self.cause,
        }


# =============================================================================
# 状态快照
# =============================================================================


@dataclass
class StateSnapshot:
    """
    状态快照

    保存实体的完整状态，用于回滚。
    """

    id: SnapshotId
    entity_id: EntityId
    state: dict[str, Any]
    checksum: str
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    actor: str = "system"
    tags: list[str] = field(default_factory=list)

    def verify(self) -> bool:
        """验证快照完整性"""
        current_checksum = self.compute_checksum(self.state)
        return current_checksum == self.checksum

    @staticmethod
    def compute_checksum(state: dict[str, Any]) -> str:
        """计算状态校验和"""
        import json

        state_str = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]

    @classmethod
    def create(
        cls,
        entity: StateEntity,
        description: str = "",
        actor: str = "system",
    ) -> StateSnapshot:
        """创建快照"""
        state = entity.to_dict()
        return cls(
            id=str(uuid.uuid4()),
            entity_id=entity.id,
            state=state,
            checksum=cls.compute_checksum(state),
            description=description,
            actor=actor,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "state": self.state,
            "checksum": self.checksum,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "actor": self.actor,
            "tags": self.tags,
        }


# =============================================================================
# 状态宇宙
# =============================================================================


class StateUniverse:
    """
    状态宇宙

    统一管理所有状态实体、关系、事件和快照。
    提供完整的溯源和回滚能力。

    核心功能:
    - create_entity: 创建实体
    - get_entity: 获取实体
    - evolve: 演化实体状态
    - relate: 建立关系
    - snapshot: 创建快照
    - rollback: 回滚到指定快照
    - diff: 计算差异
    """

    def __init__(self, name: str = "default"):
        self.name = name

        # 核心存储
        self._entities: dict[EntityId, StateEntity] = {}
        self._relations: dict[RelationId, StateRelation] = {}
        self._events: list[StateEvent] = []
        self._snapshots: dict[EntityId, list[StateSnapshot]] = defaultdict(list)

        # 索引
        self._entities_by_type: dict[EntityType, set[EntityId]] = defaultdict(set)
        self._relations_by_source: dict[EntityId, set[RelationId]] = defaultdict(set)
        self._relations_by_target: dict[EntityId, set[RelationId]] = defaultdict(set)

        # 配置
        self._max_events = 10000
        self._max_snapshots_per_entity = 100

        self._logger = logging.getLogger(f"{__name__}.Universe.{name}")
        self._logger.info(f"StateUniverse '{name}' initialized")

    # =========================================================================
    # 实体管理
    # =========================================================================

    def create_entity(
        self,
        entity_type: EntityType,
        name: str,
        properties: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StateEntity:
        """
        创建新实体

        Args:
            entity_type: 实体类型
            name: 实体名称
            properties: 初始属性
            metadata: 元数据

        Returns:
            创建的实体
        """
        entity_id = str(uuid.uuid4())
        entity = StateEntity(
            id=entity_id,
            type=entity_type,
            name=name,
            properties={k: Property(name=k, value=v) for k, v in (properties or {}).items()},
            metadata=metadata or {},
        )

        # 存储
        self._entities[entity_id] = entity
        self._entities_by_type[entity_type].add(entity_id)

        # 记录事件
        self._record_event(
            entity_id=entity_id,
            event_type=EventType.CREATE,
            previous_state=None,
            current_state=entity.to_dict(),
            actor="system",
            cause="entity_created",
        )

        self._logger.info(f"Created entity: {entity_id} ({entity_type.name})")
        return entity

    def get_entity(self, entity_id: EntityId) -> StateEntity | None:
        """获取实体"""
        return self._entities.get(entity_id)

    def get_entities(
        self,
        entity_type: EntityType | None = None,
        status: str | None = None,
    ) -> list[StateEntity]:
        """获取实体列表"""
        entities = list(self._entities.values())

        if entity_type:
            entities = [e for e in entities if e.type == entity_type]
        if status:
            entities = [e for e in entities if e.status == status]

        return entities

    def update_entity(
        self,
        entity_id: EntityId,
        changes: dict[str, Any],
        actor: str = "system",
        cause: str | None = None,
    ) -> StateEvent | None:
        """
        更新实体

        Args:
            entity_id: 实体ID
            changes: 变更内容
            actor: 变更执行者
            cause: 变更原因

        Returns:
            状态事件，如果实体不存在返回None
        """
        entity = self._entities.get(entity_id)
        if not entity:
            self._logger.warning(f"Entity not found: {entity_id}")
            return None

        # 计算差异
        previous_state = entity.to_dict()
        diff = self._compute_diff(entity, changes)

        # 应用变更
        for key, value in changes.items():
            entity.set_property(key, value)

        # 记录事件
        event = self._record_event(
            entity_id=entity_id,
            event_type=EventType.UPDATE,
            previous_state=previous_state,
            current_state=entity.to_dict(),
            diff=diff,
            actor=actor,
            cause=cause,
        )

        self._logger.info(f"Updated entity: {entity_id}, changes: {list(changes.keys())}")
        return event

    def delete_entity(self, entity_id: EntityId, actor: str = "system") -> bool:
        """删除实体"""
        entity = self._entities.get(entity_id)
        if not entity:
            return False

        # 断开所有关系
        for rel_id in list(entity.relations.values()):
            self._delete_relation(rel_id)

        # 记录事件
        self._record_event(
            entity_id=entity_id,
            event_type=EventType.DELETE,
            previous_state=entity.to_dict(),
            current_state=None,
            actor=actor,
            cause="entity_deleted",
        )

        # 移除索引
        self._entities_by_type[entity.type].discard(entity_id)

        # 删除实体
        del self._entities[entity_id]

        self._logger.info(f"Deleted entity: {entity_id}")
        return True

    def _compute_diff(self, entity: StateEntity, changes: dict[str, Any]) -> StateDiff:
        """计算差异"""
        added = {}
        removed = {}
        changed = {}

        for key, new_value in changes.items():
            if key not in entity.properties:
                added[key] = new_value
            else:
                old_value = entity.properties[key].value
                if old_value != new_value:
                    changed[key] = (old_value, new_value)

        return StateDiff(added=added, removed=removed, changed=changed)

    # =========================================================================
    # 关系管理
    # =========================================================================

    def relate(
        self,
        source_id: EntityId,
        target_id: EntityId,
        relation_type: RelationType,
        properties: dict[str, Any] | None = None,
        weight: float = 1.0,
    ) -> StateRelation | None:
        """
        建立关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 关系属性
            weight: 关系权重

        Returns:
            创建的关系
        """
        # 验证实体存在
        if source_id not in self._entities:
            self._logger.error(f"Source entity not found: {source_id}")
            return None
        if target_id not in self._entities:
            self._logger.error(f"Target entity not found: {target_id}")
            return None

        relation_id = str(uuid.uuid4())
        relation = StateRelation(
            id=relation_id,
            source_id=source_id,
            target_id=target_id,
            type=relation_type,
            properties={k: Property(name=k, value=v) for k, v in (properties or {}).items()},
            weight=weight,
        )

        # 存储
        self._relations[relation_id] = relation
        self._relations_by_source[source_id].add(relation_id)
        self._relations_by_target[target_id].add(relation_id)

        # 更新实体
        self._entities[source_id].relations[relation_type.name] = relation_id

        # 记录事件
        source_entity = self._entities[source_id]
        self._record_event(
            entity_id=source_id,
            event_type=EventType.RELATE,
            previous_state=None,
            current_state={"relation_id": relation_id, "target_id": target_id},
            actor="system",
            cause=f"related_to_{relation_type.name}",
        )

        self._logger.info(f"Created relation: {source_id} -> {target_id} ({relation_type.name})")
        return relation

    def unrelate(self, relation_id: RelationId, actor: str = "system") -> bool:
        """删除关系"""
        relation = self._relations.get(relation_id)
        if not relation:
            return False

        # 从索引移除
        self._relations_by_source[relation.source_id].discard(relation_id)
        self._relations_by_target[relation.target_id].discard(relation_id)

        # 从实体移除
        if relation.type.name in self._entities[relation.source_id].relations:
            del self._entities[relation.source_id].relations[relation.type.name]

        # 删除关系
        del self._relations[relation_id]

        self._logger.info(f"Deleted relation: {relation_id}")
        return True

    def _delete_relation(self, relation_id: RelationId):
        """内部删除关系"""
        self.unrelate(relation_id)

    def get_relations(
        self,
        source_id: EntityId | None = None,
        target_id: EntityId | None = None,
        relation_type: RelationType | None = None,
    ) -> list[StateRelation]:
        """获取关系列表"""
        relations = list(self._relations.values())

        if source_id:
            relations = [r for r in relations if r.source_id == source_id]
        if target_id:
            relations = [r for r in relations if r.target_id == target_id]
        if relation_type:
            relations = [r for r in relations if r.type == relation_type]

        return relations

    # =========================================================================
    # 快照和回滚
    # =========================================================================

    def snapshot(
        self,
        entity_id: EntityId,
        description: str = "",
        actor: str = "system",
        tags: list[str] | None = None,
    ) -> StateSnapshot | None:
        """
        创建快照

        Args:
            entity_id: 实体ID
            description: 快照描述
            actor: 创建者
            tags: 标签

        Returns:
            创建的快照
        """
        entity = self._entities.get(entity_id)
        if not entity:
            return None

        snapshot = StateSnapshot.create(
            entity=entity,
            description=description,
            actor=actor,
        )
        if tags:
            snapshot.tags = tags

        # 存储
        self._snapshots[entity_id].append(snapshot)

        # 限制数量
        if len(self._snapshots[entity_id]) > self._max_snapshots_per_entity:
            self._snapshots[entity_id] = self._snapshots[entity_id][-self._max_snapshots_per_entity :]

        # 记录事件
        self._record_event(
            entity_id=entity_id,
            event_type=EventType.SNAPSHOT,
            previous_state=None,
            current_state={"snapshot_id": snapshot.id},
            actor=actor,
            cause="snapshot_created",
        )

        self._logger.info(f"Created snapshot: {snapshot.id} for {entity_id}")
        return snapshot

    def rollback(
        self,
        entity_id: EntityId,
        snapshot_id: SnapshotId | None = None,
        target_version: int | None = None,
        actor: str = "system",
    ) -> StateEvent | None:
        """
        回滚到指定快照

        Args:
            entity_id: 实体ID
            snapshot_id: 快照ID，如果为None则回滚到上一个快照
            target_version: 目标版本号
            actor: 执行者

        Returns:
            状态事件
        """
        entity = self._entities.get(entity_id)
        if not entity:
            return None

        # 找到目标快照
        snapshots = self._snapshots.get(entity_id, [])
        if not snapshots:
            self._logger.warning(f"No snapshots for entity: {entity_id}")
            return None

        if snapshot_id:
            target_snapshot = next((s for s in snapshots if s.id == snapshot_id), None)
        elif target_version:
            target_snapshot = next((s for s in snapshots if s.state.get("version") == target_version), None)
        else:
            target_snapshot = snapshots[-1]  # 最新的快照

        if not target_snapshot:
            return None

        # 验证快照
        if not target_snapshot.verify():
            self._logger.error(f"Snapshot verification failed: {snapshot_id}")
            return None

        # 创建回滚前的快照
        self.snapshot(entity_id, description="pre_rollback", actor=actor)

        # 应用回滚
        previous_state = entity.to_dict()
        restored_data = target_snapshot.state

        # 更新实体
        for key, value in restored_data.get("properties", {}).items():
            if isinstance(value, dict):
                entity.set_property(key, value.get("value"))
            else:
                entity.set_property(key, value)

        entity.version = restored_data.get("version", 1)

        # 记录事件
        event = self._record_event(
            entity_id=entity_id,
            event_type=EventType.RESTORE,
            previous_state=previous_state,
            current_state=entity.to_dict(),
            actor=actor,
            cause=f"rollback_to_{target_snapshot.id}",
        )

        self._logger.info(f"Rolled back {entity_id} to snapshot {target_snapshot.id}")
        return event

    def get_snapshots(
        self,
        entity_id: EntityId,
        limit: int = 100,
    ) -> list[StateSnapshot]:
        """获取快照列表"""
        snapshots = self._snapshots.get(entity_id, [])
        return snapshots[-limit:]

    # =========================================================================
    # 事件记录
    # =========================================================================

    def _record_event(
        self,
        entity_id: EntityId,
        event_type: EventType,
        previous_state: dict[str, Any] | None,
        current_state: dict[str, Any] | None,
        diff: StateDiff | None = None,
        actor: str = "system",
        cause: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StateEvent:
        """记录事件"""
        if diff is None:
            diff = StateDiff()

        event = StateEvent(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
            event_type=event_type,
            previous_state=previous_state,
            current_state=current_state or {},
            diff=diff,
            actor=actor,
            cause=cause,
            metadata=metadata or {},
        )

        self._events.append(event)

        # 限制事件数量
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

        return event

    def get_events(
        self,
        entity_id: EntityId | None = None,
        event_type: EventType | None = None,
        actor: str | None = None,
        limit: int = 100,
    ) -> list[StateEvent]:
        """获取事件列表"""
        events = list(self._events)

        if entity_id:
            events = [e for e in events if e.entity_id == entity_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if actor:
            events = [e for e in events if e.actor == actor]

        return events[-limit:]

    # =========================================================================
    # 差异计算
    # =========================================================================

    def diff(
        self,
        entity_id: EntityId,
        snapshot_a: SnapshotId,
        snapshot_b: SnapshotId,
    ) -> StateDiff | None:
        """计算两个快照之间的差异"""
        snapshots = self._snapshots.get(entity_id, [])

        snap_a = next((s for s in snapshots if s.id == snapshot_a), None)
        snap_b = next((s for s in snapshots if s.id == snapshot_b), None)

        if not snap_a or not snap_b:
            return None

        diff = StateDiff()

        # 比较属性
        props_a = snap_a.state.get("properties", {})
        props_b = snap_b.state.get("properties", {})

        all_keys = set(props_a.keys()) | set(props_b.keys())

        for key in all_keys:
            val_a = props_a.get(key, {}).get("value") if isinstance(props_a.get(key), dict) else props_a.get(key)
            val_b = props_b.get(key, {}).get("value") if isinstance(props_b.get(key), dict) else props_b.get(key)

            if key not in props_a:
                diff.added[key] = val_b
            elif key not in props_b:
                diff.removed[key] = val_a
            elif val_a != val_b:
                diff.changed[key] = (val_a, val_b)

        return diff

    # =========================================================================
    # 查询
    # =========================================================================

    def query(
        self,
        entity_type: EntityType | None = None,
        property_filters: dict[str, Any] | None = None,
        relation_filters: dict[tuple[EntityId, RelationType]] | None = None,
        limit: int = 100,
    ) -> list[StateEntity]:
        """查询实体"""
        entities = self.get_entities(entity_type=entity_type)

        if property_filters:
            filtered = []
            for entity in entities:
                match = True
                for key, value in property_filters.items():
                    if entity.get_property(key) != value:
                        match = False
                        break
                if match:
                    filtered.append(entity)
            entities = filtered

        return entities[:limit]

    def search(
        self,
        keyword: str,
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[StateEntity]:
        """搜索实体"""
        keyword_lower = keyword.lower()
        entities = []

        for entity in self._entities.values():
            # 搜索名称
            if keyword_lower in entity.name.lower():
                entities.append(entity)
                continue

            # 搜索属性
            if fields is None:
                search_fields = ["properties"]
            else:
                search_fields = fields

            for field in search_fields:
                if field == "properties":
                    for prop in entity.properties.values():
                        if keyword_lower in str(prop.value).lower():
                            entities.append(entity)
                            break

        return entities[:limit]

    # =========================================================================
    # 状态订阅
    # =========================================================================

    def subscribe(
        self,
        event_types: list[EventType],
        handler: Callable[[StateEvent], None],
    ):
        """订阅状态变更"""
        # TODO: 实现订阅机制
        pass

    # =========================================================================
    # 统计和元数据
    # =========================================================================

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "entities_count": len(self._entities),
            "relations_count": len(self._relations),
            "events_count": len(self._events),
            "snapshots_count": sum(len(s) for s in self._snapshots.values()),
            "entities_by_type": {t.name: len(ids) for t, ids in self._entities_by_type.items()},
        }

    def export(self) -> dict[str, Any]:
        """导出完整状态"""
        return {
            "name": self.name,
            "exported_at": datetime.now().isoformat(),
            "entities": {eid: entity.to_dict() for eid, entity in self._entities.items()},
            "relations": {rid: rel.to_dict() for rid, rel in self._relations.items()},
        }

    def import_state(self, data: dict[str, Any]):
        """导入状态"""
        # TODO: 实现导入
        pass


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 类型别名
    "EntityId",
    "RelationId",
    "EventId",
    "SnapshotId",
    "PropertyId",
    # 枚举
    "EntityType",
    "RelationType",
    "EventType",
    "Severity",
    # 数据类
    "Property",
    "Constraint",
    "StateRelation",
    "StateEntity",
    "StateDiff",
    "StateEvent",
    "StateSnapshot",
    # 核心类
    "StateUniverse",
]
