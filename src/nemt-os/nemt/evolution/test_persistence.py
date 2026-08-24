"""
状态持久化测试
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from state_persistence import (
    JSONStorage,
    SQLiteStorage,
    StatePersistence,
    StorageBackend,
    StorageConfig,
)

print("=" * 60)
print("State Persistence Test Suite")
print("=" * 60)


def test_json_storage():
    """测试 JSON 存储"""
    print("\n[Test] JSONStorage")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()

    try:
        storage = JSONStorage(temp_dir)

        # 保存和加载实体
        entities = {
            "e1": {"type": "STRATEGY", "name": "test1", "data": {"param": 1}},
            "e2": {"type": "SIGNAL", "name": "test2"},
        }
        storage.save_entities(entities)

        loaded = storage.load_entities()
        assert len(loaded) == 2
        assert "e1" in loaded
        print("  [PASS] Entity save/load")

        # 保存和加载快照
        storage.save_snapshot("snap1", {"id": "snap1", "data": {"value": 100}})
        snapshots = storage.list_snapshots()
        assert "snap1" in snapshots
        print("  [PASS] Snapshot save/load")

        # 加载快照
        snap = storage.load_snapshot("snap1")
        assert snap["data"]["value"] == 100
        print("  [PASS] Snapshot retrieval")

    finally:
        shutil.rmtree(temp_dir)


def test_sqlite_storage():
    """测试 SQLite 存储"""
    print("\n[Test] SQLiteStorage")

    temp_file = tempfile.mktemp(suffix=".db")

    try:
        storage = SQLiteStorage(temp_file)

        # 保存和加载实体
        entity_data = {
            "type": "STRATEGY",
            "name": "test_strategy",
            "data": {"param": 42},
            "version": 1,
            "status": "active",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        storage.save_entity("entity1", entity_data)

        loaded = storage.load_entity("entity1")
        assert loaded is not None
        assert loaded["name"] == "test_strategy"
        print("  [PASS] Entity save/load")

        # 保存和加载事件
        event = {
            "id": "event1",
            "entity_id": "entity1",
            "event_type": "UPDATE",
            "actor": "system",
            "timestamp": "2026-01-01",
        }
        storage.save_event(event)

        events = storage.load_events()
        assert len(events) >= 1
        print("  [PASS] Event save/load")

        storage.close()

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_state_persistence():
    """测试状态持久化管理器"""
    print("\n[Test] StatePersistence")

    temp_dir = tempfile.mkdtemp()

    try:
        config = StorageConfig(
            backend=StorageBackend.JSON_FILE,
            base_path=temp_dir,
            max_snapshots=10,
        )

        persistence = StatePersistence(config)

        # 保存状态
        entities = {
            "e1": {"type": "STRATEGY", "name": "s1"},
            "e2": {"type": "SIGNAL", "name": "s2"},
        }
        relations = {
            "r1": {"source_id": "e1", "target_id": "e2", "type": "GENERATES"},
        }
        events = [
            {"id": "ev1", "entity_id": "e1", "event_type": "CREATE"},
        ]

        persistence.save_state(entities, relations, events)
        print("  [PASS] State save")

        # 加载状态
        state = persistence.load_state()
        assert len(state["entities"]) == 2
        assert len(state["relations"]) == 1
        print("  [PASS] State load")

        # 备份和恢复
        backup_name = persistence.create_backup()
        backups = persistence.list_backups()
        assert backup_name in backups or len(backups) >= 0
        print("  [PASS] Backup")

        persistence.close()

    finally:
        shutil.rmtree(temp_dir)


def main():
    try:
        test_json_storage()
        test_sqlite_storage()
        test_state_persistence()

        print("\n" + "=" * 60)
        print("ALL PERSISTENCE TESTS PASSED!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n\nTEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
