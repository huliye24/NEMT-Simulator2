"""
双视角切换器

支持在宏观（全局）和微观（细节）视角间自由切换。
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any


class ViewMode(Enum):
    """视角模式"""

    MACRO = "macro"  # 宏观视角 - 系统全局视图
    MICRO = "micro"  # 微观视角 - 细节实现视图
    FRACTAL = "fractal"  # 分形视角 - 自相似层级视图
    LAYER_0 = "layer_0"  # 项目级
    LAYER_1 = "layer_1"  # 模块级
    LAYER_2 = "layer_2"  # 函数级
    LAYER_3 = "layer_3"  # 语句级


@dataclass
class ViewContext:
    """视角上下文"""

    mode: ViewMode
    layer: str
    capsule_id: str | None = None
    focus_area: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class ViewSnapshot:
    """视角快照"""

    context: ViewContext
    capsules: list[str] = field(default_factory=list)
    layers: list[str] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)


class ViewSwitcher:
    """
    双视角切换器

    允许在不同视角间切换，查看同一系统的不同层面。
    支持视角历史记录和快照功能。
    """

    def __init__(self):
        self._current_view: ViewContext = ViewContext(mode=ViewMode.FRACTAL, layer="L1", timestamp=self._now())
        self._view_history: list[ViewContext] = []
        self._snapshots: dict[str, ViewSnapshot] = {}
        self._lock = threading.Lock()

        # 视角处理器
        self._view_handlers: dict[ViewMode, Callable] = {}

        # 视角切换监听器
        self._listeners: list[Callable] = []

    @staticmethod
    def _now() -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def switch_to(
        self,
        mode: ViewMode,
        layer: str = "L1",
        capsule_id: str = None,
        focus_area: str = None,
        metadata: dict[str, Any] = None,
    ) -> ViewContext:
        """
        切换视角

        Args:
            mode: 目标视角
            layer: 目标层级
            capsule_id: 目标胶囊 ID
            focus_area: 关注区域
            metadata: 额外元数据

        Returns:
            新的视角上下文
        """
        with self._lock:
            # 保存当前视图到历史
            self._view_history.append(self._current_view)

            # 限制历史记录长度
            if len(self._view_history) > 100:
                self._view_history = self._view_history[-100:]

            # 创建新视图
            self._current_view = ViewContext(
                mode=mode,
                layer=layer,
                capsule_id=capsule_id,
                focus_area=focus_area,
                metadata=metadata or {},
                timestamp=self._now(),
            )

            # 触发监听器
            self._notify_listeners()

            return self._current_view

    def macro_view(self, capsule_id: str = None) -> ViewContext:
        """
        切换到宏观视角

        查看系统整体：
        - 所有胶囊的状态
        - 模块间的依赖关系
        - 系统健康状态

        Args:
            capsule_id: 可选，关注的胶囊

        Returns:
            新的视角上下文
        """
        return self.switch_to(
            mode=ViewMode.MACRO,
            layer="L0",
            capsule_id=capsule_id,
            focus_area="system_overview",
        )

    def micro_view(self, capsule_id: str, layer: str = "L2") -> ViewContext:
        """
        切换到微观视角

        查看特定胶囊的细节：
        - 函数实现
        - 内部状态
        - 代码行级别

        Args:
            capsule_id: 胶囊 ID
            layer: 目标层级

        Returns:
            新的视角上下文
        """
        return self.switch_to(
            mode=ViewMode.MICRO,
            layer=layer,
            capsule_id=capsule_id,
            focus_area="implementation",
        )

    def fractal_view(self, capsule_id: str = None, layer: str = "L1") -> ViewContext:
        """
        切换到分形视角

        自相似视图：
        - 当前层级的结构
        - 与其他层级的自相似关系

        Args:
            capsule_id: 胶囊 ID
            layer: 层级

        Returns:
            新的视角上下文
        """
        return self.switch_to(
            mode=ViewMode.FRACTAL,
            layer=layer,
            capsule_id=capsule_id,
            focus_area="self_similar",
        )

    def layer_view(self, layer: str, capsule_id: str = None) -> ViewContext:
        """
        切换到指定层级视角

        Args:
            layer: 层级 (L0, L1, L2, L3)
            capsule_id: 可选，胶囊 ID

        Returns:
            新的视角上下文
        """
        mode_map = {
            "L0": ViewMode.LAYER_0,
            "L1": ViewMode.LAYER_1,
            "L2": ViewMode.LAYER_2,
            "L3": ViewMode.LAYER_3,
        }
        return self.switch_to(
            mode=mode_map.get(layer, ViewMode.FRACTAL),
            layer=layer,
            capsule_id=capsule_id,
            focus_area=f"layer_{layer}",
        )

    def go_back(self) -> ViewContext | None:
        """
        返回上一个视角

        Returns:
            上一个视角上下文，如果没有则返回 None
        """
        with self._lock:
            if self._view_history:
                self._current_view = self._view_history.pop()
                self._notify_listeners()
                return self._current_view
            return None

    @property
    def current_view(self) -> ViewContext:
        """当前视角"""
        return self._current_view

    @property
    def view_history(self) -> list[ViewContext]:
        """视角历史"""
        return self._view_history.copy()

    def get_view_info(self) -> dict[str, Any]:
        """
        获取视角信息

        Returns:
            视角信息字典
        """
        return {
            "mode": self._current_view.mode.value,
            "layer": self._current_view.layer,
            "capsule_id": self._current_view.capsule_id,
            "focus_area": self._current_view.focus_area,
            "timestamp": self._current_view.timestamp,
            "history_length": len(self._view_history),
        }

    def save_snapshot(self, name: str, **kwargs) -> ViewSnapshot:
        """
        保存当前视角快照

        Args:
            name: 快照名称
            **kwargs: 额外数据

        Returns:
            保存的快照
        """
        snapshot = ViewSnapshot(
            context=self._current_view,
            capsules=kwargs.get("capsules", []),
            layers=kwargs.get("layers", []),
            state=kwargs.get("state", {}),
        )
        self._snapshots[name] = snapshot
        return snapshot

    def load_snapshot(self, name: str) -> ViewSnapshot | None:
        """
        加载视角快照

        Args:
            name: 快照名称

        Returns:
            快照，如果不存在则返回 None
        """
        snapshot = self._snapshots.get(name)
        if snapshot:
            self.switch_to(
                mode=snapshot.context.mode,
                layer=snapshot.context.layer,
                capsule_id=snapshot.context.capsule_id,
                focus_area=snapshot.context.focus_area,
            )
        return snapshot

    def list_snapshots(self) -> list[str]:
        """列出所有快照名称"""
        return list(self._snapshots.keys())

    def add_listener(self, listener: Callable) -> None:
        """
        添加视角切换监听器

        Args:
            listener: 监听函数，接收 ViewContext 参数
        """
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable) -> None:
        """移除视角切换监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """通知所有监听器"""
        for listener in self._listeners:
            try:
                listener(self._current_view)
            except Exception:
                pass

    def set_view_handler(self, mode: ViewMode, handler: Callable) -> None:
        """
        设置视角处理器

        Args:
            mode: 视角模式
            handler: 处理函数
        """
        self._view_handlers[mode] = handler

    def get_view_handler(self, mode: ViewMode) -> Callable | None:
        """获取视角处理器"""
        return self._view_handlers.get(mode)


# 全局实例
_view_switcher: ViewSwitcher | None = None


def get_view_switcher() -> ViewSwitcher:
    """获取全局视角切换器实例"""
    global _view_switcher
    if _view_switcher is None:
        _view_switcher = ViewSwitcher()
    return _view_switcher


def with_view(mode: ViewMode):
    """
    视角装饰器

    在执行函数时临时切换视角。

    Usage:
        @with_view(ViewMode.MACRO)
        def show_system_overview():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            vs = get_view_switcher()
            old_view = vs.current_view
            vs.switch_to(mode)
            try:
                return func(*args, **kwargs)
            finally:
                vs.switch_to(
                    old_view.mode,
                    layer=old_view.layer,
                    capsule_id=old_view.capsule_id,
                )

        return wrapper

    return decorator


def require_view(*modes: ViewMode):
    """
    视角要求装饰器

    确保函数在指定的视角下执行。

    Usage:
        @require_view(ViewMode.MACRO)
        def system_dashboard():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            vs = get_view_switcher()
            if vs.current_view.mode not in modes:
                raise RuntimeError(f"此函数需要在 {modes} 视角下执行，当前视角: {vs.current_view.mode}")
            return func(*args, **kwargs)

        return wrapper

    return decorator
