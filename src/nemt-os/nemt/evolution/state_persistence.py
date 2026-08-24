"""
状态持久化模块

将状态宇宙中的状态持久化到磁盘或数据库。
支持:
- JSON 文件存储
- SQLite 数据库
- 增量备份
- 状态快照管理
"""

from __future__ import annotations

import json
import logging
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    """存储后端"""

    JSON_FILE = "json_file"
    SQLITE = "sqlite"
    MEMORY = "memory"


@dataclass
class StorageConfig:
    """存储配置"""

    backend: StorageBackend = StorageBackend.JSON_FILE
    base_path: str = "./data/evolution"
    max_snapshots: int = 100
    auto_backup_interval: int = 3600  # 秒
    compression: bool = True


class StateSerializer:
    """状态序列化器"""

    @staticmethod
    def serialize_state(state: Any) -> str:
        """序列化状态为 JSON"""
        return json.dumps(state, default=str, ensure_ascii=False, indent=2)

    @staticmethod
    def deserialize_state(data: str) -> Any:
        """从 JSON 反序列化"""
        return json.loads(data)

    @staticmethod
    def serialize_snapshot(snapshot: Any) -> dict[str, Any]:
        """序列化快照"""
        if hasattr(snapshot, "to_dict"):
            return snapshot.to_dict()
        return snapshot

    @staticmethod
    def serialize_entity(entity: Any) -> dict[str, Any]:
        """序列化实体"""
        if hasattr(entity, "to_dict"):
            return entity.to_dict()
        return entity


class JSONStorage:
    """JSON 文件存储"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.entities_file = self.base_path / "entities.json"
        self.relations_file = self.base_path / "relations.json"
        self.events_file = self.base_path / "events.json"
        self.snapshots_dir = self.base_path / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)

        # 初始化文件
        self._init_files()

    def _init_files(self):
        """初始化存储文件"""
        for f in [self.entities_file, self.relations_file, self.events_file]:
            if not f.exists():
                with open(f, "w", encoding="utf-8") as fp:
                    json.dump({}, fp)

    def save_entities(self, entities: dict[str, Any]):
        """保存实体"""
        data = {entity_id: StateSerializer.serialize_entity(entity) for entity_id, entity in entities.items()}
        with open(self.entities_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_entities(self) -> dict[str, Any]:
        """加载实体"""
        if not self.entities_file.exists():
            return {}
        with open(self.entities_file, encoding="utf-8") as f:
            return json.load(f)

    def save_relations(self, relations: dict[str, Any]):
        """保存关系"""
        data = {rel_id: rel.to_dict() if hasattr(rel, "to_dict") else rel for rel_id, rel in relations.items()}
        with open(self.relations_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_relations(self) -> dict[str, Any]:
        """加载关系"""
        if not self.relations_file.exists():
            return {}
        with open(self.relations_file, encoding="utf-8") as f:
            return json.load(f)

    def save_events(self, events: list[Any]):
        """保存事件"""
        data = [e.to_dict() if hasattr(e, "to_dict") else e for e in events]
        with open(self.events_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_events(self, limit: int = 1000) -> list[Any]:
        """加载事件"""
        if not self.events_file.exists():
            return []
        with open(self.events_file, encoding="utf-8") as f:
            data = json.load(f)
        return data[-limit:]

    def save_snapshot(self, snapshot_id: str, snapshot_data: dict[str, Any]):
        """保存快照"""
        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

    def load_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        """加载快照"""
        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        if not snapshot_file.exists():
            return None
        with open(snapshot_file, encoding="utf-8") as f:
            return json.load(f)

    def list_snapshots(self) -> list[str]:
        """列出所有快照"""
        return [f.stem for f in self.snapshots_dir.glob("*.json")]

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        if snapshot_file.exists():
            snapshot_file.unlink()
            return True
        return False

    def cleanup_old_snapshots(self, max_count: int):
        """清理旧快照"""
        snapshots = self.list_snapshots()
        if len(snapshots) > max_count:
            # 按文件名排序，删除最旧的
            for snapshot_id in snapshots[:-max_count]:
                self.delete_snapshot(snapshot_id)


class SQLiteStorage:
    """SQLite 数据库存储"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        """初始化数据库模式"""
        cursor = self.conn.cursor()

        # 实体表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT,
                name TEXT,
                data TEXT,
                version INTEGER,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """
        )

        # 关系表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS relations (
                relation_id TEXT PRIMARY KEY,
                source_id TEXT,
                target_id TEXT,
                relation_type TEXT,
                data TEXT,
                created_at TEXT
            )
        """
        )

        # 事件表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                entity_id TEXT,
                event_type TEXT,
                data TEXT,
                actor TEXT,
                timestamp TEXT
            )
        """
        )

        # 快照表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                entity_id TEXT,
                data TEXT,
                description TEXT,
                created_at TEXT
            )
        """
        )

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_entity ON snapshots(entity_id)")

        self.conn.commit()

    def save_entity(self, entity_id: str, entity_data: dict[str, Any]):
        """保存实体"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO entities
            (entity_id, entity_type, name, data, version, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entity_id,
                entity_data.get("type"),
                entity_data.get("name"),
                json.dumps(entity_data, default=str),
                entity_data.get("version", 1),
                entity_data.get("status", "active"),
                entity_data.get("created_at"),
                entity_data.get("updated_at"),
            ),
        )
        self.conn.commit()

    def load_entity(self, entity_id: str) -> dict[str, Any] | None:
        """加载实体"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM entities WHERE entity_id = ?", (entity_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def load_all_entities(self) -> dict[str, Any]:
        """加载所有实体"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT entity_id, data FROM entities")
        return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

    def save_relation(self, relation_id: str, relation_data: dict[str, Any]):
        """保存关系"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO relations
            (relation_id, source_id, target_id, relation_type, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                relation_id,
                relation_data.get("source_id"),
                relation_data.get("target_id"),
                relation_data.get("type"),
                json.dumps(relation_data, default=str),
                relation_data.get("created_at"),
            ),
        )
        self.conn.commit()

    def load_all_relations(self) -> dict[str, Any]:
        """加载所有关系"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT relation_id, data FROM relations")
        return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

    def save_event(self, event_data: dict[str, Any]):
        """保存事件"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (event_id, entity_id, event_type, data, actor, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                event_data.get("id"),
                event_data.get("entity_id"),
                event_data.get("event_type"),
                json.dumps(event_data, default=str),
                event_data.get("actor"),
                event_data.get("timestamp"),
            ),
        )
        self.conn.commit()

    def load_events(self, entity_id: str | None = None, limit: int = 1000) -> list[dict[str, Any]]:
        """加载事件"""
        cursor = self.conn.cursor()
        if entity_id:
            cursor.execute(
                "SELECT data FROM events WHERE entity_id = ? ORDER BY timestamp DESC LIMIT ?", (entity_id, limit)
            )
        else:
            cursor.execute("SELECT data FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [json.loads(row[0]) for row in cursor.fetchall()]

    def save_snapshot(self, snapshot_data: dict[str, Any]):
        """保存快照"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO snapshots (snapshot_id, entity_id, data, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                snapshot_data.get("id"),
                snapshot_data.get("entity_id"),
                json.dumps(snapshot_data, default=str),
                snapshot_data.get("description", ""),
                snapshot_data.get("timestamp"),
            ),
        )
        self.conn.commit()

    def load_snapshots(self, entity_id: str | None = None) -> list[dict[str, Any]]:
        """加载快照"""
        cursor = self.conn.cursor()
        if entity_id:
            cursor.execute("SELECT data FROM snapshots WHERE entity_id = ? ORDER BY created_at DESC", (entity_id,))
        else:
            cursor.execute("SELECT data FROM snapshots ORDER BY created_at DESC")
        return [json.loads(row[0]) for row in cursor.fetchall()]

    def close(self):
        """关闭连接"""
        self.conn.close()


class StatePersistence:
    """
    状态持久化管理器

    统一管理状态宇宙的持久化。
    """

    def __init__(self, config: StorageConfig | None = None):
        self.config = config or StorageConfig()
        self._storage = self._create_storage()
        self._serializer = StateSerializer()
        self._last_backup_time = datetime.now()
        self._logger = logging.getLogger(f"{__name__}.Persistence")

    def _create_storage(self):
        """创建存储后端"""
        if self.config.backend == StorageBackend.JSON_FILE:
            return JSONStorage(self.config.base_path)
        elif self.config.backend == StorageBackend.SQLITE:
            return SQLiteStorage(f"{self.config.base_path}.db")
        else:
            return None  # Memory storage (no-op)

    def save_state(
        self,
        entities: dict[str, Any],
        relations: dict[str, Any],
        events: list[Any],
    ):
        """保存完整状态"""
        try:
            # 保存实体
            self._storage.save_entities(entities)

            # 保存关系
            self._storage.save_relations(relations)

            # 保存事件
            self._storage.save_events(events)

            self._logger.info(f"Saved state: {len(entities)} entities, {len(relations)} relations")

        except Exception as e:
            self._logger.error(f"Failed to save state: {e}")
            raise

    def load_state(self) -> dict[str, Any]:
        """加载完整状态"""
        try:
            entities = self._storage.load_entities()
            relations = self._storage.load_relations()
            events = self._storage.load_events()

            self._logger.info(f"Loaded state: {len(entities)} entities, {len(relations)} relations")

            return {
                "entities": entities,
                "relations": relations,
                "events": events,
            }

        except Exception as e:
            self._logger.error(f"Failed to load state: {e}")
            raise

    def save_snapshot(self, snapshot: Any):
        """保存快照"""
        snapshot_data = self._serializer.serialize_snapshot(snapshot)
        self._storage.save_snapshot(snapshot_data.get("id", ""), snapshot_data)

        # 清理旧快照
        if hasattr(self._storage, "cleanup_old_snapshots"):
            self._storage.cleanup_old_snapshots(self.config.max_snapshots)

        self._logger.info(f"Saved snapshot: {snapshot_data.get('id')}")

    def load_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        """加载快照"""
        return self._storage.load_snapshot(snapshot_id)

    def list_snapshots(self) -> list[str]:
        """列出所有快照"""
        if hasattr(self._storage, "list_snapshots"):
            return self._storage.list_snapshots()
        return []

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        if hasattr(self._storage, "delete_snapshot"):
            return self._storage.delete_snapshot(snapshot_id)
        return False

    def create_backup(self, backup_name: str | None = None) -> str:
        """创建备份"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = Path(self.config.base_path) / "backups" / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        source_path = Path(self.config.base_path)

        # 复制所有文件
        if source_path.exists():
            for item in source_path.iterdir():
                if item.is_file() and item.suffix == ".json":
                    shutil.copy2(item, backup_path / item.name)

        self._logger.info(f"Created backup: {backup_name}")
        return str(backup_path)

    def restore_backup(self, backup_name: str) -> bool:
        """恢复备份"""
        backup_path = Path(self.config.base_path) / "backups" / backup_name

        if not backup_path.exists():
            self._logger.error(f"Backup not found: {backup_name}")
            return False

        source_path = Path(self.config.base_path)

        # 复制所有文件
        for item in backup_path.iterdir():
            if item.is_file():
                shutil.copy2(item, source_path / item.name)

        self._logger.info(f"Restored backup: {backup_name}")
        return True

    def list_backups(self) -> list[str]:
        """列出所有备份"""
        backup_dir = Path(self.config.base_path) / "backups"
        if not backup_dir.exists():
            return []
        return [d.name for d in backup_dir.iterdir() if d.is_dir()]

    def auto_backup_if_needed(self):
        """检查是否需要自动备份"""
        elapsed = (datetime.now() - self._last_backup_time).total_seconds()
        if elapsed >= self.config.auto_backup_interval:
            self.create_backup()
            self._last_backup_time = datetime.now()

    def close(self):
        """关闭存储"""
        if hasattr(self._storage, "close"):
            self._storage.close()


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "StorageBackend",
    "StorageConfig",
    "StateSerializer",
    "JSONStorage",
    "SQLiteStorage",
    "StatePersistence",
]
