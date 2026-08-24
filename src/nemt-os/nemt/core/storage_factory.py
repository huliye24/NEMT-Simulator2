"""
Storage 工厂

创建不同实现的 Storage 实例。
"""

from enum import Enum
from typing import Any

from nemt.core.adapters.storage_adapter import SQLiteStorageAdapter
from nemt.core.interfaces import IStorage
from nemt.core.storage.sqlite_storage import SQLiteStorage as OriginalSQLiteStorage


class StorageType(Enum):
    """Storage 类型"""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"  # 预留
    MEMORY = "memory"  # 预留


class StorageFactory:
    """
    Storage 工厂

    创建不同实现的 Storage 实例。
    """

    _instances: dict[str, IStorage] = {}

    @classmethod
    def create(
        cls,
        storage_type: StorageType = StorageType.SQLITE,
        config: dict[str, Any] | None = None,
        name: str = "default",
    ) -> IStorage:
        """
        创建 Storage 实例

        Args:
            storage_type: Storage 类型
            config: 配置参数
            name: 实例名称

        Returns:
            Storage 实例
        """
        if name in cls._instances:
            return cls._instances[name]

        if storage_type == StorageType.SQLITE:
            instance = cls._create_sqlite(config or {})
        elif storage_type == StorageType.POSTGRESQL:
            instance = cls._create_postgresql(config or {})
        elif storage_type == StorageType.MEMORY:
            instance = cls._create_memory(config or {})
        else:
            raise ValueError(f"Unknown Storage type: {storage_type}")

        cls._instances[name] = instance
        return instance

    @classmethod
    def _create_sqlite(cls, config: dict[str, Any]) -> IStorage:
        """创建 SQLite 版 Storage"""
        db_path = config.get("db_path", "data/nemt_storage.db")
        original = OriginalSQLiteStorage(db_path=db_path)
        return SQLiteStorageAdapter(original)

    @classmethod
    def _create_postgresql(cls, config: dict[str, Any]) -> IStorage:
        """创建 PostgreSQL 版 Storage (预留)"""
        raise NotImplementedError("PostgreSQL Storage not implemented yet")

    @classmethod
    def _create_memory(cls, config: dict[str, Any]) -> IStorage:
        """创建内存版 Storage (预留)"""
        raise NotImplementedError("Memory Storage not implemented yet")

    @classmethod
    def get_instance(cls, name: str = "default") -> IStorage | None:
        """获取已创建的实例"""
        return cls._instances.get(name)

    @classmethod
    def clear(cls) -> None:
        """清除所有实例"""
        for instance in cls._instances.values():
            if hasattr(instance, "close"):
                instance.close()
        cls._instances.clear()

    @classmethod
    def list_instances(cls) -> list:
        """列出所有实例"""
        return list(cls._instances.keys())
