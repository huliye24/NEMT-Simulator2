"""
ConfigCenter 适配器

将现有的 ConfigCenter 类适配到 IConfigCenter 接口。
"""

from collections.abc import Callable
from typing import Any

from nemt.core.config_center import ConfigCenter as OriginalConfigCenter
from nemt.core.interfaces.config_center import IConfigCenter


class ConfigCenterAdapter(IConfigCenter):
    """
    ConfigCenter 适配器

    将原有 ConfigCenter 实现适配到 IConfigCenter 接口。
    """

    def __init__(self, original: OriginalConfigCenter):
        self._original = original

    def get(self, key: str, default: Any = None) -> Any:
        return self._original.get(key, default)

    def set(self, key: str, value: Any, notify: bool = True, validate: bool = True) -> bool:
        return self._original.set(key, value, notify, validate)

    def has(self, key: str) -> bool:
        return self._original.has(key)

    def delete(self, key: str) -> bool:
        return self._original.delete(key)

    def get_keys(self, pattern: str = None) -> list[str]:
        return self._original.get_keys(pattern)

    def get_all(self) -> dict[str, Any]:
        return self._original.get_all()

    def set_batch(self, updates: dict[str, Any], notify: bool = True) -> None:
        self._original.set_batch(updates, notify)

    def clear(self) -> None:
        self._original.clear()

    def watch(self, key: str, callback: Callable) -> None:
        self._original.watch(key, callback)

    def unwatch(self, key: str, callback: Callable) -> None:
        self._original.unwatch(key, callback)

    def watch_pattern(self, pattern: str, callback: Callable) -> None:
        self._original.watch_pattern(pattern, callback)

    def validate(self, key: str = None) -> dict[str, Any]:
        return self._original.validate(key)

    def is_valid(self) -> bool:
        return self._original.is_valid()

    def load(self, filepath: str = None, merge: bool = True) -> None:
        self._original.load(filepath, merge)

    def save(self, filepath: str = None) -> None:
        self._original.save(filepath)

    # ========================================================================
    # 便捷方法 (原有功能)
    # ========================================================================

    def get_by_prefix(self, prefix: str) -> dict[str, Any]:
        """获取以指定前缀开头的所有配置"""
        return self._original.get_by_prefix(prefix)

    def apply_profile(self, profile_name: str) -> None:
        """应用配置模板"""
        self._original.apply_profile(profile_name)

    def save_profile(self, name: str) -> None:
        """保存当前配置为模板"""
        self._original.save_profile(name)

    def export_json(self, filepath: str) -> None:
        """导出为 JSON 格式"""
        self._original.export_json(filepath)

    def import_json(self, filepath: str, merge: bool = True) -> None:
        """从 JSON 导入"""
        self._original.import_json(filepath, merge)

    @property
    def is_dirty(self) -> bool:
        """是否有未保存的更改"""
        return self._original.is_dirty

    def get_error_count(self) -> int:
        """获取监听器错误计数"""
        return self._original.get_error_count()
