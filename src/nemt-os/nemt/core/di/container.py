"""
DIContainer - 依赖注入容器

提供依赖注入功能，支持:
- 类型注册与解析
- 单例与瞬态模式
- 构造函数注入
- 属性注入
"""

from collections.abc import Callable
from enum import Enum
from typing import Any, Optional, TypeVar, get_type_hints

T = TypeVar("T")


class Lifetime(Enum):
    """生命周期模式"""

    TRANSIENT = "transient"  # 每次请求创建新实例
    SINGLETON = "singleton"  # 全局单例
    SCOPED = "scoped"  # 作用域内单例


class DIContainer:
    """
    依赖注入容器

    示例:
    ```python
    container = DIContainer()

    # 注册服务
    container.register(IEventBus, InMemoryEventBus, Lifetime.SINGLETON)

    # 注册 Capsule
    container.register_capsule(MarketCapsule)

    # 获取实例
    event_bus = container.resolve(IEventBus)
    market = container.resolve(MarketCapsule)
    ```
    """

    def __init__(self, parent: Optional["DIContainer"] = None):
        self._parent = parent
        self._registrations: dict[type, Callable] = {}
        self._lifetimes: dict[type, Lifetime] = {}
        self._singletons: dict[type, Any] = {}
        self._capsules: dict[str, type] = {}
        self._capsule_instances: dict[str, Any] = {}

    # ========================================================================
    # 服务注册
    # ========================================================================

    def register(
        self,
        interface: type[T],
        implementation: type[T] = None,
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> "DIContainer":
        """
        注册服务

        Args:
            interface: 接口类型
            implementation: 实现类型
            lifetime: 生命周期

        Returns:
            self (支持链式调用)
        """
        if implementation is None:
            implementation = interface

        self._registrations[interface] = implementation
        self._lifetimes[interface] = lifetime
        return self

    def register_instance(self, interface: type[T], instance: T) -> "DIContainer":
        """
        注册实例 (自动单例)

        Args:
            interface: 接口类型
            instance: 实例

        Returns:
            self
        """
        self._singletons[interface] = instance
        self._lifetimes[interface] = Lifetime.SINGLETON
        return self

    def register_factory(
        self, interface: type[T], factory: Callable[["DIContainer"], T], lifetime: Lifetime = Lifetime.TRANSIENT
    ) -> "DIContainer":
        """
        注册工厂函数

        Args:
            interface: 接口类型
            factory: 工厂函数
            lifetime: 生命周期

        Returns:
            self
        """
        self._registrations[interface] = factory
        self._lifetimes[interface] = lifetime
        return self

    # ========================================================================
    # Capsule 注册
    # ========================================================================

    def register_capsule(self, capsule_class: type) -> "DIContainer":
        """
        注册胶囊类

        Args:
            capsule_class: 胶囊类

        Returns:
            self
        """
        capsule_id = getattr(capsule_class, "capsule_id", None) or capsule_class.__name__
        self._capsules[capsule_id] = capsule_class
        return self

    def get_capsule_class(self, capsule_id: str) -> type | None:
        """获取胶囊类"""
        if capsule_id in self._capsules:
            return self._capsules[capsule_id]
        if self._parent:
            return self._parent.get_capsule_class(capsule_id)
        return None

    def get_capsule_ids(self) -> list:
        """获取所有胶囊 ID"""
        ids = list(self._capsules.keys())
        if self._parent:
            ids.extend(self._parent.get_capsule_ids())
        return list(set(ids))

    # ========================================================================
    # 服务解析
    # ========================================================================

    def resolve(self, interface: type[T]) -> T:
        """
        解析服务

        Args:
            interface: 接口类型

        Returns:
            实例

        Raises:
            KeyError: 未注册的服务
        """
        # 查找实现
        implementation = self._find_implementation(interface)
        if implementation is None:
            raise KeyError(f"未注册的服务: {interface}")

        # 检查单例
        lifetime = self._lifetimes.get(interface, Lifetime.TRANSIENT)
        if lifetime == Lifetime.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]

        # 创建实例
        instance = self._create_instance(implementation)

        # 缓存单例
        if lifetime == Lifetime.SINGLETON:
            self._singletons[interface] = instance

        return instance

    def resolve_capsule(self, capsule_id: str) -> Any:
        """
        解析胶囊

        Args:
            capsule_id: 胶囊 ID

        Returns:
            胶囊实例
        """
        # 检查实例缓存
        if capsule_id in self._capsule_instances:
            return self._capsule_instances[capsule_id]

        # 查找类
        capsule_class = self.get_capsule_class(capsule_id)
        if capsule_class is None:
            raise KeyError(f"未注册的胶囊: {capsule_id}")

        # 创建实例
        instance = self._create_instance(capsule_class)
        self._capsule_instances[capsule_id] = instance
        return instance

    def _find_implementation(self, interface: type) -> type | None:
        """查找实现"""
        if interface in self._registrations:
            return self._registrations[interface]
        if self._parent:
            return self._parent._find_implementation(interface)
        return None

    def _create_instance(self, implementation: Any) -> Any:
        """创建实例"""
        # 如果是工厂函数
        if callable(implementation) and not isinstance(implementation, type):
            return implementation(self)

        # 获取构造函数参数
        try:
            hints = get_type_hints(implementation.__init__)
        except Exception:
            hints = {}

        # 构建参数
        args = []
        kwargs = {}
        for param_name, param_type in hints.items():
            if param_name == "self":
                continue
            try:
                param_instance = self.resolve(param_type)
                kwargs[param_name] = param_instance
            except KeyError:
                pass  # 可选参数

        # 创建实例
        try:
            return implementation(*args, **kwargs)
        except TypeError:
            # 尝试不传递参数
            return implementation()

    # ========================================================================
    # 生命周期管理
    # ========================================================================

    def create_scope(self) -> "DIContainer":
        """
        创建作用域容器

        Returns:
            子容器
        """
        return DIContainer(parent=self)

    def clear_scope(self) -> None:
        """清除当前作用域"""
        self._capsule_instances.clear()

    def clear(self) -> None:
        """清除所有注册和实例"""
        self._registrations.clear()
        self._lifetimes.clear()
        self._singletons.clear()
        self._capsules.clear()
        self._capsule_instances.clear()

    # ========================================================================
    # 诊断
    # ========================================================================

    def is_registered(self, interface: type) -> bool:
        """检查是否已注册"""
        return self._find_implementation(interface) is not None

    def get_registrations(self) -> dict[type, type]:
        """获取所有注册"""
        return self._registrations.copy()

    def __repr__(self) -> str:
        return f"DIContainer(registrations={len(self._registrations)}, singletons={len(self._singletons)})"
