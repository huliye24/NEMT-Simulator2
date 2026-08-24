"""
层级锁定机制

通过接口冻结实现层级间的有序递进。
"""

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class LockStatus(Enum):
    """锁定状态"""

    UNLOCKED = "unlocked"
    FROZEN = "frozen"  # 接口冻结
    FINALIZED = "finalized"  # 最终确认
    DEPRECATED = "deprecated"  # 已废弃


@dataclass
class LayerContract:
    """
    层级契约

    定义某个层级或模块的接口契约及其锁定状态。
    """

    layer: str  # L0, L1, L2, L3
    owner: str  # 负责的胶囊/模块
    name: str  # 契约名称
    status: LockStatus = LockStatus.UNLOCKED
    frozen_at: datetime | None = None
    finalized_at: datetime | None = None
    interfaces: set[str] = field(default_factory=set)
    dependents: set[str] = field(default_factory=set)  # 依赖此契约的下游
    changelog: list[dict] = field(default_factory=list)
    description: str = ""
    version: str = "1.0.0"

    def freeze(self, reason: str = "") -> bool:
        """
        冻结接口

        Args:
            reason: 冻结原因

        Returns:
            是否成功冻结
        """
        if self.status != LockStatus.UNLOCKED:
            return False

        self.status = LockStatus.FROZEN
        self.frozen_at = datetime.now()
        self._log_change("freeze", {"reason": reason})
        return True

    def finalize(self, reason: str = "") -> bool:
        """
        最终确认契约

        Args:
            reason: 确认原因

        Returns:
            是否成功确认
        """
        if self.status not in [LockStatus.FROZEN, LockStatus.UNLOCKED]:
            return False

        self.status = LockStatus.FINALIZED
        self.finalized_at = datetime.now()
        self._log_change("finalize", {"reason": reason})
        return True

    def deprecate(self, reason: str = "", replacement: str = "") -> bool:
        """
        废弃契约

        Args:
            reason: 废弃原因
            replacement: 替代契约名称

        Returns:
            是否成功废弃
        """
        if self.status == LockStatus.DEPRECATED:
            return False

        self.status = LockStatus.DEPRECATED
        self._log_change("deprecate", {"reason": reason, "replacement": replacement})
        return True

    def add_interface(self, interface: str) -> bool:
        """
        添加接口

        如果已冻结则返回 False

        Args:
            interface: 接口名称

        Returns:
            是否添加成功
        """
        if self.status != LockStatus.UNLOCKED:
            return False
        self.interfaces.add(interface)
        return True

    def remove_interface(self, interface: str) -> bool:
        """
        移除接口

        如果已冻结则返回 False

        Args:
            interface: 接口名称

        Returns:
            是否移除成功
        """
        if self.status != LockStatus.UNLOCKED:
            return False
        self.interfaces.discard(interface)
        return True

    def change_interface(self, old: str, new: str) -> bool:
        """
        变更接口

        只能在冻结前执行。

        Args:
            old: 旧接口
            new: 新接口

        Returns:
            是否变更成功
        """
        if old not in self.interfaces:
            return False

        self.interfaces.discard(old)
        self.interfaces.add(new)
        self._log_change("interface_change", {"old": old, "new": new})
        return True

    def add_dependent(self, dependent: str) -> None:
        """添加依赖者"""
        self.dependents.add(dependent)

    def _log_change(self, change_type: str, data: dict) -> None:
        """记录变更"""
        self.changelog.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": change_type,
                "data": data,
            }
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "layer": self.layer,
            "owner": self.owner,
            "name": self.name,
            "status": self.status.value,
            "frozen_at": self.frozen_at.isoformat() if self.frozen_at else None,
            "finalized_at": self.finalized_at.isoformat() if self.finalized_at else None,
            "interfaces": list(self.interfaces),
            "dependents": list(self.dependents),
            "changelog": self.changelog,
            "description": self.description,
            "version": self.version,
        }


class LayerLockManager:
    """
    层级锁定管理器

    管理各层级的接口契约和锁定状态。
    确保层级间的依赖关系和有序递进。
    """

    _instance: Optional["LayerLockManager"] = None

    def __init__(self):
        self._contracts: dict[str, LayerContract] = {}
        self._lock = threading.RLock()
        self._listeners: list[Callable] = []

        # 层级依赖关系定义
        self._dependencies = {
            "L0": [],  # L0 无上游
            "L1": ["L0"],  # L1 依赖 L0
            "L2": ["L1"],  # L2 依赖 L1
            "L3": ["L2"],  # L3 依赖 L2
        }

    @classmethod
    def get_instance(cls) -> "LayerLockManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_contract(
        self,
        layer: str,
        owner: str,
        name: str,
        interfaces: list[str] = None,
        description: str = "",
    ) -> LayerContract:
        """
        注册层级契约

        Args:
            layer: 层级 (L0, L1, L2, L3)
            owner: 所有者
            name: 契约名称
            interfaces: 接口列表
            description: 描述

        Returns:
            创建的契约
        """
        key = self._make_key(layer, owner, name)

        with self._lock:
            if key in self._contracts:
                return self._contracts[key]

            contract = LayerContract(
                layer=layer,
                owner=owner,
                name=name,
                interfaces=set(interfaces) if interfaces else set(),
                description=description,
            )
            self._contracts[key] = contract
            self._notify_listeners("register", contract)
            return contract

    def get_contract(self, layer: str = None, owner: str = None, name: str = None) -> LayerContract | None:
        """
        获取契约

        Args:
            layer: 层级
            owner: 所有者
            name: 契约名称

        Returns:
            契约，如果不存在则返回 None
        """
        if name:
            # 按名称精确查找
            for contract in self._contracts.values():
                if contract.name == name:
                    return contract
            return None

        key = self._make_key(layer, owner, name)
        return self._contracts.get(key)

    def list_contracts(self, layer: str = None, status: LockStatus = None) -> list[LayerContract]:
        """
        列出契约

        Args:
            layer: 可选，按层级过滤
            status: 可选，按状态过滤

        Returns:
            契约列表
        """
        with self._lock:
            result = list(self._contracts.values())

            if layer:
                result = [c for c in result if c.layer == layer]

            if status:
                result = [c for c in result if c.status == status]

            return result

    def freeze_contract(self, layer: str, owner: str = None, name: str = None) -> bool:
        """
        冻结契约

        只有在依赖层级已冻结后才能冻结。

        Args:
            layer: 层级
            owner: 所有者
            name: 契约名称

        Returns:
            是否成功冻结
        """
        contract = self.get_contract(layer, owner, name)
        if contract is None:
            return False

        # 检查依赖层级是否已冻结
        for dep_layer in self._dependencies.get(layer, []):
            if not self._is_layer_frozen(dep_layer):
                return False

        result = contract.freeze()
        if result:
            self._notify_listeners("freeze", contract)
        return result

    def finalize_contract(self, layer: str, owner: str = None, name: str = None) -> bool:
        """
        最终确认契约

        Args:
            layer: 层级
            owner: 所有者
            name: 契约名称

        Returns:
            是否成功确认
        """
        contract = self.get_contract(layer, owner, name)
        if contract is None:
            return False

        result = contract.finalize()
        if result:
            self._notify_listeners("finalize", contract)
        return result

    def _make_key(self, layer: str, owner: str, name: str = None) -> str:
        """生成契约键"""
        if name:
            return f"{layer}:{owner}:{name}"
        return f"{layer}:{owner}"

    def _is_layer_frozen(self, layer: str) -> bool:
        """检查层级是否已冻结"""
        for contract in self._contracts.values():
            if contract.layer == layer and contract.status in [
                LockStatus.FROZEN,
                LockStatus.FINALIZED,
            ]:
                return True
        return False

    def can_start_layer(self, layer: str) -> bool:
        """
        检查是否可以开始某层级的工作

        规则：
        - L0 永远可以开始
        - L1 需要 L0 已冻结
        - L2 需要 L1 已冻结
        - L3 需要 L2 已冻结

        Args:
            layer: 层级

        Returns:
            是否可以开始
        """
        if layer == "L0":
            return True

        deps = self._dependencies.get(layer, [])
        return all(self._is_layer_frozen(dep) for dep in deps)

    def get_layer_status(self, layer: str) -> dict:
        """
        获取层级状态

        Args:
            layer: 层级

        Returns:
            状态字典
        """
        contracts = self.list_contracts(layer=layer)
        frozen_count = sum(1 for c in contracts if c.status in [LockStatus.FROZEN, LockStatus.FINALIZED])

        return {
            "layer": layer,
            "total_contracts": len(contracts),
            "frozen_contracts": frozen_count,
            "can_start": self.can_start_layer(layer),
            "is_frozen": self._is_layer_frozen(layer),
            "dependencies": self._dependencies.get(layer, []),
            "contracts": [c.to_dict() for c in contracts],
        }

    def get_overall_status(self) -> dict:
        """获取整体状态"""
        layers = {}
        for layer in ["L0", "L1", "L2", "L3"]:
            layers[layer] = self.get_layer_status(layer)

        return {
            "total_contracts": len(self._contracts),
            "layers": layers,
        }

    def export_json(self, filepath: str) -> None:
        """
        导出为 JSON 文件

        Args:
            filepath: 文件路径
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.get_overall_status(), f, indent=2, ensure_ascii=False)

    def add_listener(self, listener: Callable) -> None:
        """添加监听器"""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable) -> None:
        """移除监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self, event: str, contract: LayerContract) -> None:
        """通知监听器"""
        for listener in self._listeners:
            try:
                listener(event, contract)
            except Exception:
                pass

    def reset(self) -> None:
        """重置所有契约"""
        with self._lock:
            self._contracts.clear()


# 便捷函数
def get_lock_manager() -> LayerLockManager:
    """获取层级锁定管理器实例"""
    return LayerLockManager.get_instance()


def freeze_layer(layer: str) -> bool:
    """冻结层级"""
    return get_lock_manager().freeze_contract(layer)
