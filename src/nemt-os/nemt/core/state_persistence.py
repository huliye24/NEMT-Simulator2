"""
StatePersistence - 状态持久化

提供状态持久化功能:
- 检查点机制
- 状态恢复
- 状态导出/导入
- 自动快照
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = ["StatePersistence", "Checkpoint", "SnapshotType", "get_persistence_manager"]


class SnapshotType(Enum):
    """快照类型"""

    FULL = "full"  # 全量快照
    INCREMENTAL = "incremental"  # 增量快照
    DELTA = "delta"  # 差异快照


@dataclass
class Checkpoint:
    """检查点"""

    checkpoint_id: str
    capsule_id: str
    state: dict[str, Any]
    timestamp: float
    snapshot_type: SnapshotType
    version: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SnapshotMetadata:
    """快照元数据"""

    snapshot_id: str
    capsule_id: str
    snapshot_type: SnapshotType
    created_at: float
    size_bytes: int
    version: int
    checksum: str


class StatePersistence:
    """
    状态持久化管理器

    示例:
    ```python
    persistence = StatePersistence("data/checkpoints")

    # 注册需要持久化的 Capsule
    persistence.register("market", market_capsule)
    persistence.register("signal", signal_capsule)

    # 创建检查点
    persistence.checkpoint("market")

    # 恢复状态
    persistence.restore("market")

    # 导出状态
    persistence.export("backup.json")

    # 导入状态
    persistence.import_state("backup.json")
    ```
    """

    def __init__(
        self,
        checkpoint_dir: str = "data/checkpoints",
        max_checkpoints: int = 10,
        auto_checkpoint_interval: float = 300.0,
        compression: bool = True,
    ):
        self.checkpoint_dir = checkpoint_dir
        self.max_checkpoints = max_checkpoints
        self.auto_checkpoint_interval = auto_checkpoint_interval
        self.compression = compression

        # 管理的 Capsule
        self._registered: dict[str, Any] = {}

        # 检查点历史
        self._checkpoints: dict[str, list[Checkpoint]] = {}

        # 自动检查点定时器
        self._auto_checkpoint_thread: threading.Thread | None = None
        self._stop_auto_checkpoint = threading.Event()

        # 锁
        self._lock = threading.Lock()

        # 创建目录
        os.makedirs(checkpoint_dir, exist_ok=True)

    def register(self, capsule_id: str, capsule: Any) -> None:
        """
        注册 Capsule

        Args:
            capsule_id: Capsule ID
            capsule: Capsule 实例
        """
        with self._lock:
            self._registered[capsule_id] = capsule
            self._checkpoints[capsule_id] = []

    def unregister(self, capsule_id: str) -> None:
        """注销 Capsule"""
        with self._lock:
            if capsule_id in self._registered:
                del self._registered[capsule_id]
            if capsule_id in self._checkpoints:
                del self._checkpoints[capsule_id]

    def checkpoint(
        self,
        capsule_id: str = None,
        snapshot_type: SnapshotType = SnapshotType.FULL,
        metadata: dict[str, Any] = None,
    ) -> Checkpoint | None:
        """
        创建检查点

        Args:
            capsule_id: Capsule ID，None 表示所有注册的 Capsule
            snapshot_type: 快照类型
            metadata: 元数据

        Returns:
            检查点列表
        """
        if capsule_id:
            return self._checkpoint_single(capsule_id, snapshot_type, metadata)
        else:
            checkpoints = []
            for cid in list(self._registered.keys()):
                cp = self._checkpoint_single(cid, snapshot_type, metadata)
                if cp:
                    checkpoints.append(cp)
            return checkpoints

    def _checkpoint_single(
        self,
        capsule_id: str,
        snapshot_type: SnapshotType,
        metadata: dict[str, Any],
    ) -> Checkpoint | None:
        """为单个 Capsule 创建检查点"""
        with self._lock:
            if capsule_id not in self._registered:
                return None

            capsule = self._registered[capsule_id]

        # 获取状态
        try:
            if hasattr(capsule, "get_state"):
                state = capsule.get_state()
            elif hasattr(capsule, "__dict__"):
                state = capsule.__dict__.copy()
            else:
                state = {}
        except Exception:
            state = {}

        # 获取版本
        version = 0
        if capsule_id in self._checkpoints:
            version = max(cp.version for cp in self._checkpoints[capsule_id]) + 1

        # 创建检查点
        checkpoint = Checkpoint(
            checkpoint_id=self._generate_id(),
            capsule_id=capsule_id,
            state=state,
            timestamp=time.time(),
            snapshot_type=snapshot_type,
            version=version,
            metadata=metadata or {},
        )

        # 保存到文件
        self._save_checkpoint(checkpoint)

        # 更新内存
        with self._lock:
            if capsule_id not in self._checkpoints:
                self._checkpoints[capsule_id] = []
            self._checkpoints[capsule_id].append(checkpoint)

            # 清理旧检查点
            while len(self._checkpoints[capsule_id]) > self.max_checkpoints:
                self._checkpoints[capsule_id].pop(0)

        return checkpoint

    def _save_checkpoint(self, checkpoint: Checkpoint) -> str:
        """保存检查点到文件"""
        capsule_dir = os.path.join(self.checkpoint_dir, checkpoint.capsule_id)
        os.makedirs(capsule_dir, exist_ok=True)

        filename = f"checkpoint_{checkpoint.version}_{int(checkpoint.timestamp)}.json"
        filepath = os.path.join(capsule_dir, filename)

        data = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "capsule_id": checkpoint.capsule_id,
            "state": checkpoint.state,
            "timestamp": checkpoint.timestamp,
            "snapshot_type": checkpoint.snapshot_type.value,
            "version": checkpoint.version,
            "metadata": checkpoint.metadata,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)

        return filepath

    def restore(self, capsule_id: str, version: int = None) -> bool:
        """
        恢复状态

        Args:
            capsule_id: Capsule ID
            version: 版本号，None 表示最新版本

        Returns:
            是否恢复成功
        """
        with self._lock:
            if capsule_id not in self._registered:
                return False

            capsule = self._registered[capsule_id]

        # 找到检查点
        if capsule_id not in self._checkpoints or not self._checkpoints[capsule_id]:
            # 尝试从文件加载
            self._load_checkpoints_from_disk(capsule_id)

        checkpoints = self._checkpoints.get(capsule_id, [])
        if not checkpoints:
            return False

        if version is None:
            checkpoint = checkpoints[-1]
        else:
            checkpoint = None
            for cp in checkpoints:
                if cp.version == version:
                    checkpoint = cp
                    break

        if checkpoint is None:
            return False

        # 恢复状态
        try:
            if hasattr(capsule, "restore_state"):
                capsule.restore_state(checkpoint.state)
            elif hasattr(capsule, "__dict__"):
                capsule.__dict__.update(checkpoint.state)
            return True
        except Exception:
            return False

    def _load_checkpoints_from_disk(self, capsule_id: str) -> None:
        """从磁盘加载检查点"""
        capsule_dir = os.path.join(self.checkpoint_dir, capsule_id)
        if not os.path.exists(capsule_dir):
            return

        checkpoints = []
        for filename in os.listdir(capsule_dir):
            if filename.startswith("checkpoint_") and filename.endswith(".json"):
                filepath = os.path.join(capsule_dir, filename)
                try:
                    with open(filepath, encoding="utf-8") as f:
                        data = json.load(f)
                    checkpoint = Checkpoint(
                        checkpoint_id=data["checkpoint_id"],
                        capsule_id=data["capsule_id"],
                        state=data["state"],
                        timestamp=data["timestamp"],
                        snapshot_type=SnapshotType(data["snapshot_type"]),
                        version=data["version"],
                        metadata=data.get("metadata", {}),
                    )
                    checkpoints.append(checkpoint)
                except Exception:
                    pass

        checkpoints.sort(key=lambda x: x.version)
        with self._lock:
            self._checkpoints[capsule_id] = checkpoints

    def get_checkpoints(self, capsule_id: str) -> list[Checkpoint]:
        """获取检查点列表"""
        if capsule_id not in self._checkpoints or not self._checkpoints[capsule_id]:
            self._load_checkpoints_from_disk(capsule_id)
        return self._checkpoints.get(capsule_id, [])

    def get_latest_checkpoint(self, capsule_id: str) -> Checkpoint | None:
        """获取最新检查点"""
        checkpoints = self.get_checkpoints(capsule_id)
        return checkpoints[-1] if checkpoints else None

    def delete_checkpoint(self, capsule_id: str, version: int) -> bool:
        """删除检查点"""
        with self._lock:
            checkpoints = self._checkpoints.get(capsule_id, [])
            for i, cp in enumerate(checkpoints):
                if cp.version == version:
                    checkpoints.pop(i)
                    return True
        return False

    # ========================================================================
    # 导出/导入
    # ========================================================================

    def export(self, filepath: str, capsule_ids: list[str] = None) -> None:
        """
        导出状态

        Args:
            filepath: 导出文件路径
            capsule_ids: Capsule ID 列表，None 表示所有
        """
        if capsule_ids is None:
            capsule_ids = list(self._registered.keys())

        data = {}
        for capsule_id in capsule_ids:
            if capsule_id in self._checkpoints and self._checkpoints[capsule_id]:
                latest = self._checkpoints[capsule_id][-1]
                data[capsule_id] = {
                    "state": latest.state,
                    "version": latest.version,
                    "timestamp": latest.timestamp,
                }

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_state(self, filepath: str) -> int:
        """
        导入状态

        Args:
            filepath: 导入文件路径

        Returns:
            导入的 Capsule 数量
        """
        if not os.path.exists(filepath):
            return 0

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for capsule_id, state_data in data.items():
            if capsule_id in self._registered:
                capsule = self._registered[capsule_id]
                try:
                    if hasattr(capsule, "restore_state"):
                        capsule.restore_state(state_data["state"])
                    elif hasattr(capsule, "__dict__"):
                        capsule.__dict__.update(state_data["state"])
                    count += 1
                except Exception:
                    pass

        return count

    # ========================================================================
    # 自动检查点
    # ========================================================================

    def start_auto_checkpoint(self) -> None:
        """启动自动检查点"""
        if self._auto_checkpoint_thread and self._auto_checkpoint_thread.is_alive():
            return

        self._stop_auto_checkpoint.clear()

        def auto_checkpoint_loop():
            while not self._stop_auto_checkpoint.wait(self.auto_checkpoint_interval):
                self.checkpoint()

        self._auto_checkpoint_thread = threading.Thread(target=auto_checkpoint_loop, daemon=True)
        self._auto_checkpoint_thread.start()

    def stop_auto_checkpoint(self) -> None:
        """停止自动检查点"""
        self._stop_auto_checkpoint.set()
        if self._auto_checkpoint_thread:
            self._auto_checkpoint_thread.join(timeout=5)

    def _generate_id(self) -> str:
        """生成 ID"""
        import uuid

        return str(uuid.uuid4())[:8]


# 全局实例
_persistence_manager: StatePersistence | None = None


def get_persistence_manager() -> StatePersistence | None:
    """获取全局持久化管理器"""
    return _persistence_manager


def init_persistence_manager(**kwargs) -> StatePersistence:
    """初始化全局持久化管理器"""
    global _persistence_manager
    _persistence_manager = StatePersistence(**kwargs)
    return _persistence_manager
