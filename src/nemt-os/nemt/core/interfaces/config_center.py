"""
IConfigCenter - 配置中心接口定义

定义配置中心的标准接口。
"""

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IConfigCenter(Protocol):
    """
    配置中心接口

    定义配置管理的标准操作。
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        ...

    def set(self, key: str, value: Any, notify: bool = True, validate: bool = True) -> bool:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            notify: 是否通知监听器
            validate: 是否验证

        Returns:
            是否设置成功
        """
        ...

    def has(self, key: str) -> bool:
        """检查配置键是否存在"""
        ...

    def delete(self, key: str) -> bool:
        """删除配置项"""
        ...

    def get_keys(self, pattern: str = None) -> list[str]:
        """
        获取所有或匹配的配置键

        Args:
            pattern: 通配符模式

        Returns:
            配置键列表
        """
        ...

    def get_all(self) -> dict[str, Any]:
        """获取所有配置"""
        ...

    def set_batch(self, updates: dict[str, Any], notify: bool = True) -> None:
        """批量设置配置"""
        ...

    def clear(self) -> None:
        """清空所有配置"""
        ...

    def watch(self, key: str, callback: Callable) -> None:
        """
        监听配置变化

        Args:
            key: 要监听的配置键
            callback: 回调函数
        """
        ...

    def unwatch(self, key: str, callback: Callable) -> None:
        """取消监听"""
        ...

    def watch_pattern(self, pattern: str, callback: Callable) -> None:
        """
        通配符监听配置变化

        Args:
            pattern: 通配符模式
            callback: 回调函数
        """
        ...

    def validate(self, key: str = None) -> dict[str, Any]:
        """
        验证配置

        Args:
            key: 要验证的键

        Returns:
            验证结果
        """
        ...

    def is_valid(self) -> bool:
        """检查配置是否有效"""
        ...

    def load(self, filepath: str = None, merge: bool = True) -> None:
        """从文件加载配置"""
        ...

    def save(self, filepath: str = None) -> None:
        """保存配置到文件"""
        ...


class IConfigWatcher(Protocol):
    """配置监听器接口"""

    def on_config_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """配置变化回调"""
        ...


class IConfigValidator(Protocol):
    """配置验证器接口"""

    def validate(self, key: str, value: Any) -> bool:
        """验证配置"""
        ...
