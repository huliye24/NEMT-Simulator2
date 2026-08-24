"""
ConfigLoader - 配置加载器

提供多来源配置加载、验证和热更新能力。
"""

import hashlib
import json
import logging
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "ConfigSource",
    "ConfigLoader",
    "ConfigWatcher",
]


class ConfigSource(Enum):
    """配置来源"""

    FILE = "file"
    ENV = "env"
    REMOTE = "remote"
    DEFAULT = "default"


@dataclass
class ConfigEntry:
    """配置项"""

    key: str
    value: Any
    source: ConfigSource
    version: int = 1
    timestamp: float = field(default_factory=time.time)


class ConfigLoader:
    """
    配置加载器

    示例:
    ```python
    loader = ConfigLoader()

    # 添加配置源
    loader.add_file("config.yaml")
    loader.add_env_prefix("NEMT_")
    loader.add_default({"debug": False})

    # 加载配置
    config = loader.load()

    # 获取值
    debug = config.get("debug", False)
    db_url = config.get("database.url")

    # 监听变更
    loader.watch("database.url", lambda old, new: print(f"DB URL changed: {new}"))
    ```
    """

    def __init__(self):
        self._configs: dict[str, ConfigEntry] = {}
        self._sources: list[dict] = []
        self._watchers: dict[str, list[Callable]] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("ConfigLoader")
        self._version = 0

    def add_file(self, path: str, format: str = None) -> "ConfigLoader":
        """添加文件配置源"""
        self._sources.append(
            {
                "type": ConfigSource.FILE,
                "path": path,
                "format": format or self._detect_format(path),
            }
        )
        return self

    def add_env_prefix(self, prefix: str) -> "ConfigLoader":
        """添加环境变量配置源"""
        self._sources.append(
            {
                "type": ConfigSource.ENV,
                "prefix": prefix,
            }
        )
        return self

    def add_default(self, defaults: dict) -> "ConfigLoader":
        """添加默认配置"""
        self._sources.append(
            {
                "type": ConfigSource.DEFAULT,
                "values": defaults,
            }
        )
        return self

    def add_remote(self, url: str, refresh_interval: float = 60) -> "ConfigLoader":
        """添加远程配置源"""
        self._sources.append(
            {
                "type": ConfigSource.REMOTE,
                "url": url,
                "refresh_interval": refresh_interval,
            }
        )
        return self

    def load(self) -> "ConfigDict":
        """加载所有配置"""
        with self._lock:
            self._configs.clear()

            # 按优先级加载（低优先级先加载）
            for source in reversed(self._sources):
                self._load_source(source)

            self._version += 1
            return ConfigDict(self._configs, self._watchers)

    def _load_source(self, source: dict) -> None:
        """加载单个配置源"""
        source_type = source["type"]

        if source_type == ConfigSource.DEFAULT:
            self._merge_dict(source["values"], ConfigSource.DEFAULT)

        elif source_type == ConfigSource.FILE:
            self._load_file(source["path"], source.get("format"))

        elif source_type == ConfigSource.ENV:
            self._load_env(source["prefix"])

        elif source_type == ConfigSource.REMOTE:
            self._load_remote(source["url"])

    def _load_file(self, path: str, format: str = None) -> None:
        """加载配置文件"""
        try:
            p = Path(path)
            if not p.exists():
                self._logger.warning(f"配置文件不存在: {path}")
                return

            with open(p, encoding="utf-8") as f:
                if format == "json" or path.endswith(".json"):
                    data = json.load(f)
                elif format == "yaml" or path.endswith((".yaml", ".yml")):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            self._merge_dict(data, ConfigSource.FILE)
            self._logger.info(f"加载配置文件: {path}")

        except Exception as e:
            self._logger.error(f"加载配置文件失败: {path}: {e}")

    def _load_env(self, prefix: str) -> None:
        """加载环境变量"""
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower().replace("_", ".")
                self._set_config(config_key, value, ConfigSource.ENV)

    def _load_remote(self, url: str) -> None:
        """加载远程配置"""
        try:
            import requests

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self._merge_dict(data, ConfigSource.REMOTE)
            self._logger.info(f"加载远程配置: {url}")
        except Exception as e:
            self._logger.error(f"加载远程配置失败: {url}: {e}")

    def _merge_dict(self, data: dict, source: ConfigSource, prefix: str = "") -> None:
        """合并字典到配置"""
        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict):
                self._merge_dict(value, source, f"{full_key}.")
            else:
                self._set_config(full_key, value, source)

    def _set_config(self, key: str, value: Any, source: ConfigSource) -> None:
        """设置配置项"""
        old_entry = self._configs.get(key)
        old_value = old_entry.value if old_entry else None

        self._configs[key] = ConfigEntry(
            key=key,
            value=value,
            source=source,
            version=self._version,
        )

        # 触发监听器
        if old_value != value and key in self._watchers:
            for callback in self._watchers[key]:
                try:
                    callback(old_value, value)
                except Exception as e:
                    self._logger.error(f"配置监听器执行失败: {key}: {e}")

    def watch(self, key: str, callback: Callable) -> None:
        """监听配置变更"""
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        with self._lock:
            entry = self._configs.get(key)
            return entry.value if entry else default

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        with self._lock:
            self._set_config(key, value, ConfigSource.DEFAULT)

    def to_dict(self) -> dict:
        """导出为字典"""
        with self._lock:
            return {k: v.value for k, v in self._configs.items()}


class ConfigDict:
    """配置字典（不可变）"""

    def __init__(self, configs: dict[str, ConfigEntry], watchers: dict[str, list]):
        self._configs = configs
        self._watchers = watchers

    def get(self, key: str, default: Any = None) -> Any:
        """获取值，支持点号路径"""
        keys = key.split(".")
        value = self._configs

        for k in keys:
            if isinstance(value, dict):
                if k in value:
                    entry = (
                        value[k]
                        if isinstance(value[k], ConfigEntry)
                        else ConfigEntry(k, value[k], ConfigSource.DEFAULT)
                    )
                    value = entry.value
                else:
                    return default
            elif isinstance(value, ConfigEntry):
                if k in value.value:
                    value = value.value[k]
                else:
                    return default
            else:
                return default

        if isinstance(value, ConfigEntry):
            return value.value
        return value

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def to_dict(self) -> dict:
        result = {}
        for key, entry in self._configs.items():
            keys = key.split(".")
            d = result
            for k in keys[:-1]:
                if k not in d:
                    d[k] = {}
                d = d[k]
            d[keys[-1]] = entry.value
        return result




class ConfigWatcher:
    """
    配置监视器

    监视配置文件变更并自动重新加载。
    """

    def __init__(self, loader: ConfigLoader):
        self.loader = loader
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_hashes: dict[str, str] = {}

    def start(self) -> None:
        """启动监视"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止监视"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _watch_loop(self) -> None:
        """监视循环"""
        while self._running:
            try:
                for source in self.loader._sources:
                    if source["type"] == ConfigSource.FILE:
                        self._check_file(source["path"])
            except Exception as e:
                logging.getLogger("ConfigWatcher").error(f"监视异常: {e}")

            time.sleep(5)

    def _check_file(self, path: str) -> None:
        """检查文件变更"""
        try:
            p = Path(path)
            if not p.exists():
                return

            content = p.read_bytes()
            file_hash = hashlib.md5(content).hexdigest()

            if path in self._last_hashes:
                if self._last_hashes[path] != file_hash:
                    logging.getLogger("ConfigWatcher").info(f"配置变更检测: {path}")
                    self.loader.load()

            self._last_hashes[path] = file_hash

        except Exception as e:
            logging.getLogger("ConfigWatcher").error(f"检查文件失败: {path}: {e}")
