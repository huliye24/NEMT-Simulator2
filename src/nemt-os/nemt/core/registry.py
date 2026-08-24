"""
ModuleRegistry - 模块注册表

提供模块的注册、发现和管理功能。
"""

import importlib
import logging
from collections.abc import Callable
from typing import Any

__all__ = ["ModuleRegistry", "ModuleInfo"]


class ModuleInfo:
    """模块信息"""

    def __init__(
        self,
        name: str,
        module_class: type,
        version: str = "1.0.0",
        description: str = "",
        dependencies: list[str] = None,
        metadata: dict[str, Any] = None,
    ):
        self.name = name
        self.module_class = module_class
        self.version = version
        self.description = description
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self._instance: Any | None = None
        self._is_registered = False

    def __repr__(self) -> str:
        return f"ModuleInfo(name={self.name}, version={self.version})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }


class ModuleRegistry:
    """
    模块注册表

    管理模块的注册、发现和加载。

    示例:
    ```python
    registry = ModuleRegistry()

    # 注册模块
    registry.register_module(ModuleInfo("market", MarketCapsule))

    # 延迟加载
    registry.register_factory("signal", lambda: SignalCapsule())

    # 发现模块
    market = registry.get_module("market")

    # 按依赖排序
    sorted_modules = registry.get_modules_topological()
    ```
    """

    def __init__(self):
        self._modules: dict[str, ModuleInfo] = {}
        self._factories: dict[str, Callable] = {}
        self._logger = logging.getLogger("ModuleRegistry")
        self._loaded = False

    # ========================================================================
    # 注册
    # ========================================================================

    def register_module(self, module_info: ModuleInfo) -> "ModuleRegistry":
        """
        注册模块

        Args:
            module_info: 模块信息

        Returns:
            self
        """
        if module_info.name in self._modules:
            self._logger.warning(f"模块 {module_info.name} 已存在，将被替换")

        self._modules[module_info.name] = module_info
        module_info._is_registered = True
        self._loaded = False
        return self

    def register_factory(self, name: str, factory: Callable) -> "ModuleRegistry":
        """
        注册工厂函数

        Args:
            name: 模块名称
            factory: 工厂函数

        Returns:
            self
        """
        self._factories[name] = factory
        return self

    def register_module_class(
        self,
        name: str,
        module_class: type,
        version: str = "1.0.0",
        description: str = "",
        dependencies: list[str] = None,
    ) -> "ModuleRegistry":
        """
        注册模块类 (便捷方法)

        Args:
            name: 模块名称
            module_class: 模块类
            version: 版本
            description: 描述
            dependencies: 依赖

        Returns:
            self
        """
        module_info = ModuleInfo(
            name=name,
            module_class=module_class,
            version=version,
            description=description,
            dependencies=dependencies,
        )
        return self.register_module(module_info)

    def unregister_module(self, name: str) -> bool:
        """
        注销模块

        Args:
            name: 模块名称

        Returns:
            是否成功
        """
        if name in self._modules:
            del self._modules[name]
            self._loaded = False
            return True
        return False

    # ========================================================================
    # 发现
    # ========================================================================

    def get_module(self, name: str) -> ModuleInfo | None:
        """
        获取模块信息

        Args:
            name: 模块名称

        Returns:
            模块信息
        """
        return self._modules.get(name)

    def get_module_instance(self, name: str) -> Any | None:
        """
        获取模块实例 (懒加载)

        Args:
            name: 模块名称

        Returns:
            模块实例
        """
        module_info = self._modules.get(name)
        if module_info is None:
            return None

        # 懒加载实例
        if module_info._instance is None:
            if name in self._factories:
                module_info._instance = self._factories[name]()
            elif module_info.module_class is not None:
                module_info._instance = module_info.module_class()

        return module_info._instance

    def has_module(self, name: str) -> bool:
        """检查模块是否存在"""
        return name in self._modules

    def list_modules(self) -> list[str]:
        """列出所有模块名称"""
        return list(self._modules.keys())

    def list_module_infos(self) -> list[ModuleInfo]:
        """列出所有模块信息"""
        return list(self._modules.values())

    # ========================================================================
    # 依赖管理
    # ========================================================================

    def get_dependencies(self, name: str) -> list[str]:
        """
        获取模块依赖

        Args:
            name: 模块名称

        Returns:
            依赖列表
        """
        module_info = self._modules.get(name)
        if module_info is None:
            return []
        return module_info.dependencies

    def get_dependents(self, name: str) -> list[str]:
        """
        获取依赖该模块的所有模块

        Args:
            name: 模块名称

        Returns:
            依赖者列表
        """
        dependents = []
        for module_name, module_info in self._modules.items():
            if name in module_info.dependencies:
                dependents.append(module_name)
        return dependents

    def get_modules_topological(self) -> list[str]:
        """
        按依赖拓扑排序获取模块名称

        Returns:
            排序后的模块名称列表

        Raises:
            ValueError: 存在循环依赖
        """
        # Kahn 算法
        in_degree = {name: 0 for name in self._modules}
        adj_list = {name: [] for name in self._modules}

        for name, module_info in self._modules.items():
            for dep in module_info.dependencies:
                if dep in self._modules:
                    adj_list[dep].append(name)
                    in_degree[name] += 1

        # 找到入度为0的节点
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 检查循环依赖
        if len(result) != len(self._modules):
            raise ValueError("存在循环依赖")

        return result

    def check_circular_dependency(self) -> bool:
        """
        检查是否存在循环依赖

        Returns:
            是否存在循环依赖
        """
        try:
            self.get_modules_topological()
            return False
        except ValueError:
            return True

    def get_circular_dependencies(self) -> list[list[str]]:
        """
        获取循环依赖

        Returns:
            循环依赖列表
        """
        # DFS 查找环
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: list[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            module_info = self._modules.get(node)
            if module_info:
                for dep in module_info.dependencies:
                    if dep not in self._modules:
                        continue
                    if dep not in visited:
                        dfs(dep, path.copy())
                    elif dep in rec_stack:
                        idx = path.index(dep)
                        cycles.append(path[idx:] + [dep])

            rec_stack.remove(node)

        for name in self._modules:
            if name not in visited:
                dfs(name, [])

        return cycles

    # ========================================================================
    # 延迟加载
    # ========================================================================

    def discover_modules(self, package_name: str) -> int:
        """
        自动发现模块

        Args:
            package_name: 包名

        Returns:
            发现的数量
        """
        try:
            module = importlib.import_module(package_name)
            count = 0

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and hasattr(attr, "__bases__"):
                    # 检查是否是 Capsule 子类
                    from nemt.core.capsule import ModuleCapsule

                    if issubclass(attr, ModuleCapsule) and attr != ModuleCapsule:
                        self.register_module_class(
                            name=attr_name.lower(),
                            module_class=attr,
                        )
                        count += 1

            self._logger.info(f"发现 {count} 个模块")
            return count

        except ImportError as e:
            self._logger.error(f"无法导入 {package_name}: {e}")
            return 0

    # ========================================================================
    # 诊断
    # ========================================================================

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "module_count": len(self._modules),
            "factory_count": len(self._factories),
            "modules": [m.to_dict() for m in self._modules.values()],
            "has_circular_dep": self.check_circular_dependency(),
        }

    def clear(self) -> None:
        """清除所有注册"""
        self._modules.clear()
        self._factories.clear()
        self._loaded = False

    def __repr__(self) -> str:
        return f"ModuleRegistry(modules={len(self._modules)})"

    def __len__(self) -> int:
        return len(self._modules)

    def __contains__(self, name: str) -> bool:
        return name in self._modules
