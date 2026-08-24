"""
Dependency Injection - 依赖注入模块

提供依赖注入容器和相关工具。
"""

from .container import DIContainer, Lifetime

__all__ = [
    "DIContainer",
    "Lifetime",
]
