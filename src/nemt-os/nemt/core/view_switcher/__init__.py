"""
双视角切换模块

导出所有视角相关的类和函数。
"""

from .view_switcher import (
    ViewContext,
    ViewMode,
    ViewSnapshot,
    ViewSwitcher,
    get_view_switcher,
    require_view,
    with_view,
)

__all__ = [
    "ViewMode",
    "ViewContext",
    "ViewSnapshot",
    "ViewSwitcher",
    "get_view_switcher",
    "with_view",
    "require_view",
]
