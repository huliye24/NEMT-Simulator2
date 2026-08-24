"""
Plugin System - 插件系统

提供动态插件加载和生命周期管理。
"""

import importlib
import importlib.util
import json
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginState",
    "PluginManager",
    "PluginRegistry",
]


class PluginState(Enum):
    """插件状态"""

    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    UNLOADED = "unloaded"


@dataclass
class PluginMetadata:
    """插件元数据"""

    name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    entry_point: str = "main"
    min_nemt_version: str = "1.0.0"
    config_schema: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "PluginMetadata":
        return cls(**data)


class Plugin:
    """
    插件基类

    示例:
    ```python
    class MyPlugin(Plugin):
        metadata = PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="My plugin",
        )

        def on_load(self) -> bool:
            # 初始化
            return True

        def on_enable(self) -> None:
            # 启用
            pass

        def on_disable(self) -> None:
            # 禁用
            pass

        def execute(self, context: Dict) -> Any:
            # 执行
            pass
    ```
    """

    metadata: PluginMetadata = None

    def __init__(self):
        self._state = PluginState.DISCOVERED
        self._manager = None
        self._config = {}
        self._logger = logging.getLogger(f"Plugin.{self.metadata.name}")

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def version(self) -> str:
        return self.metadata.version

    @property
    def state(self) -> PluginState:
        return self._state

    def set_manager(self, manager: "PluginManager") -> None:
        self._manager = manager

    def set_config(self, config: dict) -> None:
        self._config = config

    def get_config(self, key: str = None, default: Any = None) -> Any:
        if key is None:
            return self._config
        return self._config.get(key, default)

    def on_load(self) -> bool:
        """加载时调用，返回 True 表示加载成功"""
        return True

    def on_unload(self) -> None:
        """卸载时调用"""
        pass

    def on_enable(self) -> None:
        """启用时调用"""
        self._state = PluginState.INITIALIZED

    def on_disable(self) -> None:
        """禁用时调用"""
        pass

    def on_start(self) -> None:
        """启动时调用"""
        self._state = PluginState.RUNNING

    def on_stop(self) -> None:
        """停止时调用"""
        self._state = PluginState.STOPPED

    def execute(self, context: dict = None) -> Any:
        """执行插件逻辑"""
        raise NotImplementedError


class PluginRegistry:
    """
    插件注册表

    管理插件类型注册。
    """

    def __init__(self):
        self._plugins: dict[str, type[Plugin]] = {}
        self._lock = None

    def register(self, plugin_class: type[Plugin]) -> None:
        """注册插件类"""
        if not issubclass(plugin_class, Plugin):
            raise TypeError("必须继承自 Plugin 类")
        self._plugins[plugin_class.metadata.name] = plugin_class

    def unregister(self, name: str) -> None:
        """注销插件"""
        if name in self._plugins:
            del self._plugins[name]

    def get(self, name: str) -> type[Plugin] | None:
        """获取插件类"""
        return self._plugins.get(name)

    def list_all(self) -> list[type[Plugin]]:
        """列出所有插件"""
        return list(self._plugins.values())


class PluginManager:
    """
    插件管理器

    管理插件的加载、初始化、启用和禁用。

    示例:
    ```python
    manager = PluginManager(plugin_dir="plugins")

    # 发现插件
    manager.discover()

    # 加载所有插件
    manager.load_all()

    # 启用插件
    manager.enable("my_plugin")

    # 执行插件
    result = manager.execute("my_plugin", {"data": "test"})
    ```
    """

    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self._plugins: dict[str, Plugin] = {}
        self._hooks: dict[str, list[Callable]] = {}
        self._logger = logging.getLogger("PluginManager")
        self._registry = PluginRegistry()

    def discover(self) -> list[PluginMetadata]:
        """发现插件"""
        discovered = []

        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            return discovered

        for item in self.plugin_dir.iterdir():
            if item.is_dir() and (item / "plugin.json").exists():
                metadata = self._load_metadata(item)
                if metadata:
                    discovered.append(metadata)

        return discovered

    def _load_metadata(self, plugin_path: Path) -> PluginMetadata | None:
        """加载插件元数据"""
        try:
            with open(plugin_path / "plugin.json", encoding="utf-8") as f:
                data = json.load(f)
            return PluginMetadata.from_dict(data)
        except Exception as e:
            self._logger.error(f"加载插件元数据失败: {plugin_path}: {e}")
            return None

    def load(self, name: str) -> bool:
        """加载插件"""
        if name in self._plugins:
            return True

        plugin_path = self.plugin_dir / name
        if not plugin_path.exists():
            self._logger.error(f"插件不存在: {name}")
            return False

        try:
            # 加载元数据
            metadata = self._load_metadata(plugin_path)
            if not metadata:
                return False

            # 动态导入
            spec = importlib.util.spec_from_file_location(f"plugins.{name}", plugin_path / "__init__.py")
            if spec is None:
                # 尝试查找主文件
                main_file = plugin_path / f"{metadata.entry_point}.py"
                if main_file.exists():
                    spec = importlib.util.spec_from_file_location(f"plugins.{name}", main_file)

            if spec is None or spec.loader is None:
                self._logger.error(f"无法加载插件模块: {name}")
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugins.{name}"] = module
            spec.loader.exec_module(module)

            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                    plugin_class = attr
                    break

            if plugin_class is None:
                self._logger.error(f"未找到插件类: {name}")
                return False

            # 创建实例
            plugin = plugin_class()
            plugin.set_manager(self)
            plugin._state = PluginState.LOADED

            # 加载配置
            config = self._load_config(plugin_path)
            plugin.set_config(config)

            # 执行 on_load
            if not plugin.on_load():
                self._logger.error(f"插件加载失败: {name}")
                return False

            self._plugins[name] = plugin
            self._logger.info(f"加载插件: {name} v{plugin.version}")
            return True

        except Exception as e:
            self._logger.error(f"加载插件失败: {name}: {e}")
            return False

    def _load_config(self, plugin_path: Path) -> dict:
        """加载插件配置"""
        config_file = plugin_path / "config.json"
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def unload(self, name: str) -> bool:
        """卸载插件"""
        plugin = self._plugins.get(name)
        if plugin is None:
            return False

        try:
            plugin.on_unload()
            del self._plugins[name]
            self._logger.info(f"卸载插件: {name}")
            return True
        except Exception as e:
            self._logger.error(f"卸载插件失败: {name}: {e}")
            return False

    def enable(self, name: str) -> bool:
        """启用插件"""
        plugin = self._plugins.get(name)
        if plugin is None:
            if not self.load(name):
                return False
            plugin = self._plugins.get(name)

        try:
            plugin.on_enable()
            plugin._state = PluginState.INITIALIZED
            plugin.on_start()
            self._logger.info(f"启用插件: {name}")
            return True
        except Exception as e:
            plugin._state = PluginState.ERROR
            self._logger.error(f"启用插件失败: {name}: {e}")
            return False

    def disable(self, name: str) -> bool:
        """禁用插件"""
        plugin = self._plugins.get(name)
        if plugin is None:
            return False

        try:
            plugin._state = PluginState.STOPPING
            plugin.on_stop()
            plugin.on_disable()
            plugin._state = PluginState.STOPPED
            self._logger.info(f"禁用插件: {name}")
            return True
        except Exception as e:
            self._logger.error(f"禁用插件失败: {name}: {e}")
            return False

    def execute(self, name: str, context: dict = None) -> Any:
        """执行插件"""
        plugin = self._plugins.get(name)
        if plugin is None or plugin.state != PluginState.RUNNING:
            raise ValueError(f"插件未运行: {name}")

        return plugin.execute(context)

    def register_hook(self, hook_name: str, handler: Callable) -> None:
        """注册钩子"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(handler)

    def call_hooks(self, hook_name: str, *args, **kwargs) -> list[Any]:
        """调用钩子"""
        results = []
        for handler in self._hooks.get(hook_name, []):
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self._logger.error(f"钩子执行失败: {hook_name}: {e}")
        return results

    def load_all(self) -> int:
        """加载所有发现的插件"""
        count = 0
        for metadata in self.discover():
            if self.load(metadata.name):
                count += 1
        return count

    def enable_all(self) -> int:
        """启用所有插件"""
        count = 0
        for name in list(self._plugins.keys()):
            if self.enable(name):
                count += 1
        return count

    def disable_all(self) -> int:
        """禁用所有插件"""
        count = 0
        for name in list(self._plugins.keys()):
            if self.disable(name):
                count += 1
        return count

    def get_plugin(self, name: str) -> Plugin | None:
        """获取插件实例"""
        return self._plugins.get(name)

    def list_plugins(self, state: PluginState = None) -> list[dict]:
        """列出插件"""
        result = []
        for name, plugin in self._plugins.items():
            if state is None or plugin.state == state:
                result.append(
                    {
                        "name": plugin.name,
                        "version": plugin.version,
                        "state": plugin.state.value,
                        "description": plugin.metadata.description,
                    }
                )
        return result


# 全局实例
_plugin_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
