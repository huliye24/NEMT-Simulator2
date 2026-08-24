"""
ConfigHotReload - 配置热更新

提供配置热更新功能:
- 配置监听
- 配置推送
- 配置回滚
- 配置版本化
"""

import json
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

__all__ = ["ConfigHotReloader", "ConfigVersion", "get_config_reloader"]


@dataclass
class ConfigVersion:
    """配置版本"""

    version: int
    key: str
    old_value: Any
    new_value: Any
    timestamp: float
    changed_by: str = "system"


@dataclass
class ConfigChange:
    """配置变更"""

    key: str
    old_value: Any
    new_value: Any
    timestamp: float
    version: int
    callback_results: list[Any] = field(default_factory=list)


class ConfigHotReloader:
    """
    配置热更新器

    示例:
    ```python
    reloader = ConfigHotReloader(config_center)

    # 监听配置变化
    reloader.watch("strategy.params", on_change)

    # 推送配置更新
    reloader.push("strategy.params", {"threshold": 0.8})

    # 回滚配置
    reloader.rollback("strategy.params")

    # 获取版本历史
    history = reloader.get_version_history("strategy.params")
    ```
    """

    def __init__(self, config_center, max_versions: int = 100):
        self._config = config_center
        self._max_versions = max_versions
        self._watchers: dict[str, list[Callable]] = {}
        self._pattern_watchers: list[tuple] = []
        self._version_history: dict[str, list[ConfigVersion]] = {}
        self._current_version: dict[str, int] = {}
        self._lock = threading.Lock()
        self._is_enabled = True

        # 文件监听
        self._file_watchers: dict[str, float] = {}
        self._watch_thread: threading.Thread | None = None

    def watch(self, key: str, callback: Callable[[ConfigChange], None]) -> None:
        """
        监听配置变化

        Args:
            key: 配置键
            callback: 变化回调
        """
        with self._lock:
            if key not in self._watchers:
                self._watchers[key] = []
            self._watchers[key].append(callback)

    def unwatch(self, key: str, callback: Callable) -> None:
        """取消监听"""
        with self._lock:
            if key in self._watchers:
                self._watchers[key].remove(callback)

    def watch_pattern(self, pattern: str, callback: Callable[[ConfigChange], None]) -> None:
        """
        通配符监听

        Args:
            pattern: 通配符模式，如 "strategy.*"
            callback: 回调
        """
        with self._lock:
            self._pattern_watchers.append((pattern, callback))

    def push(self, key: str, value: Any, changed_by: str = "system") -> bool:
        """
        推送配置更新

        Args:
            key: 配置键
            value: 新值
            changed_by: 变更者

        Returns:
            是否推送成功
        """
        if not self._is_enabled:
            return False

        # 获取旧值
        old_value = self._config.get(key)

        # 检查是否有变化
        if old_value == value:
            return False

        # 记录版本
        with self._lock:
            version = self._current_version.get(key, 0) + 1
            self._current_version[key] = version

            if key not in self._version_history:
                self._version_history[key] = []

            config_version = ConfigVersion(
                version=version,
                key=key,
                old_value=old_value,
                new_value=value,
                timestamp=time.time(),
                changed_by=changed_by,
            )

            self._version_history[key].append(config_version)

            # 限制历史长度
            if len(self._version_history[key]) > self._max_versions:
                self._version_history[key].pop(0)

        # 更新配置
        self._config.set(key, value)

        # 触发回调
        change = ConfigChange(
            key=key,
            old_value=old_value,
            new_value=value,
            timestamp=time.time(),
            version=version,
        )

        self._notify_watchers(key, change)
        self._notify_pattern_watchers(key, change)

        return True

    def _notify_watchers(self, key: str, change: ConfigChange) -> None:
        """通知直接监听器"""
        with self._lock:
            watchers = self._watchers.get(key, []).copy()

        for callback in watchers:
            try:
                result = callback(change)
                change.callback_results.append(result)
            except Exception:
                pass

    def _notify_pattern_watchers(self, key: str, change: ConfigChange) -> None:
        """通知通配符监听器"""
        with self._lock:
            patterns = self._pattern_watchers.copy()

        for pattern, callback in patterns:
            if self._match_pattern(key, pattern):
                try:
                    result = callback(change)
                    change.callback_results.append(result)
                except Exception:
                    pass

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """匹配通配符模式"""
        import fnmatch

        return fnmatch.fnmatch(key, pattern)

    def rollback(self, key: str, steps: int = 1) -> bool:
        """
        回滚配置

        Args:
            key: 配置键
            steps: 回滚步数

        Returns:
            是否回滚成功
        """
        with self._lock:
            history = self._version_history.get(key, [])
            if len(history) < steps:
                return False

            # 获取要回滚到的版本
            target_version = history[-steps - 1] if len(history) > steps else history[0]
            target_value = target_version.new_value

        # 更新配置
        return self.push(key, target_value, changed_by="rollback")

    def get_version_history(self, key: str, limit: int = 10) -> list[ConfigVersion]:
        """获取版本历史"""
        with self._lock:
            history = self._version_history.get(key, [])
            return history[-limit:]

    def get_current_version(self, key: str) -> int:
        """获取当前版本号"""
        with self._lock:
            return self._current_version.get(key, 0)

    def enable(self) -> None:
        """启用热更新"""
        self._is_enabled = True

    def disable(self) -> None:
        """禁用热更新"""
        self._is_enabled = False

    # ========================================================================
    # 文件监听
    # ========================================================================

    def watch_file(self, filepath: str, callback: Callable[[], None], interval: float = 5.0) -> None:
        """
        监听配置文件变化

        Args:
            filepath: 文件路径
            callback: 变化回调
            interval: 检查间隔（秒）
        """
        if not os.path.exists(filepath):
            return

        self._file_watchers[filepath] = {
            "callback": callback,
            "mtime": os.path.getmtime(filepath),
            "interval": interval,
            "last_check": time.time(),
        }

        self._start_file_watcher()

    def _start_file_watcher(self) -> None:
        """启动文件监听线程"""
        if self._watch_thread and self._watch_thread.is_alive():
            return

        def watch_loop():
            while self._file_watchers:
                time.sleep(1)
                now = time.time()

                for filepath, info in list(self._file_watchers.items()):
                    if now - info["last_check"] >= info["interval"]:
                        try:
                            if os.path.exists(filepath):
                                current_mtime = os.path.getmtime(filepath)
                                if current_mtime != info["mtime"]:
                                    info["mtime"] = current_mtime
                                    info["callback"]()
                        except Exception:
                            pass
                        info["last_check"] = now

        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()

    # ========================================================================
    # 导入导出
    # ========================================================================

    def export_versions(self, filepath: str) -> None:
        """
        导出版本历史

        Args:
            filepath: 导出文件路径
        """
        with self._lock:
            data = {
                key: [
                    {
                        "version": v.version,
                        "old_value": v.old_value,
                        "new_value": v.new_value,
                        "timestamp": v.timestamp,
                        "changed_by": v.changed_by,
                    }
                    for v in versions
                ]
                for key, versions in self._version_history.items()
            }

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_versions(self, filepath: str) -> int:
        """
        导入版本历史

        Args:
            filepath: 导入文件路径

        Returns:
            导入的版本数量
        """
        if not os.path.exists(filepath):
            return 0

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        with self._lock:
            for key, versions in data.items():
                if key not in self._version_history:
                    self._version_history[key] = []

                for v in versions:
                    config_version = ConfigVersion(
                        version=v["version"],
                        key=key,
                        old_value=v.get("old_value"),
                        new_value=v["new_value"],
                        timestamp=v["timestamp"],
                        changed_by=v.get("changed_by", "import"),
                    )
                    self._version_history[key].append(config_version)
                    self._current_version[key] = max(self._current_version.get(key, 0), v["version"])
                    count += 1

        return count


# 全局实例
_config_reloader: ConfigHotReloader | None = None


def get_config_reloader(config_center=None) -> ConfigHotReloader:
    """获取全局配置热更新器"""
    global _config_reloader
    if _config_reloader is None and config_center is not None:
        _config_reloader = ConfigHotReloader(config_center)
    return _config_reloader
