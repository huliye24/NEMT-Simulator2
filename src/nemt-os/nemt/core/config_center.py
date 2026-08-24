"""
ConfigCenter - 配置中心模块

提供统一的配置管理，支持:
- 嵌套键访问 (如 'risk.max_drawdown')
- 配置监听与热更新
- YAML 文件加载与保存
- 线程安全
- 配置验证
- 配置导入/导出
- 通配符监听
"""

from typing import Any, Dict, List, Callable, Optional, Union, Pattern
import copy
import threading
import time
import os
import re
import fnmatch

__all__ = ["ConfigCenter", "ConfigValidator", "ConfigProfile"]


class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_int(value: Any, min_val: int = None, max_val: int = None) -> bool:
        if not isinstance(value, int):
            return False
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True

    @staticmethod
    def validate_float(value: Any, min_val: float = None, max_val: float = None) -> bool:
        if not isinstance(value, (int, float)):
            return False
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True

    @staticmethod
    def validate_string(value: Any, pattern: str = None, choices: List[str] = None) -> bool:
        if not isinstance(value, str):
            return False
        if pattern and not re.match(pattern, value):
            return False
        if choices and value not in choices:
            return False
        return True

    @staticmethod
    def validate_list(value: Any, item_type: type = None, min_len: int = None, max_len: int = None) -> bool:
        if not isinstance(value, list):
            return False
        if min_len is not None and len(value) < min_len:
            return False
        if max_len is not None and len(value) > max_len:
            return False
        if item_type:
            for item in value:
                if not isinstance(item, item_type):
                    return False
        return True


class ConfigProfile:
    """配置模板"""

    PROFILES = {
        "aggressive": {
            "risk.max_drawdown": 0.3,
            "risk.stop_loss": 0.08,
            "execution.base_size": 0.2,
            "execution.max_order_size": 1.0,
        },
        "moderate": {
            "risk.max_drawdown": 0.2,
            "risk.stop_loss": 0.05,
            "execution.base_size": 0.1,
            "execution.max_order_size": 0.5,
        },
        "conservative": {
            "risk.max_drawdown": 0.1,
            "risk.stop_loss": 0.03,
            "execution.base_size": 0.05,
            "execution.max_order_size": 0.2,
        },
        "test": {
            "risk.max_drawdown": 0.5,
            "risk.stop_loss": 0.1,
            "execution.base_size": 1.0,
            "execution.max_order_size": 5.0,
        },
    }

    @classmethod
    def get_profile(cls, name: str) -> Dict[str, Any]:
        """获取配置模板"""
        return cls.PROFILES.get(name, {}).copy()

    @classmethod
    def get_profile_names(cls) -> List[str]:
        """获取所有模板名称"""
        return list(cls.PROFILES.keys())


class ConfigCenter:
    """
    配置中心 - 管理应用程序配置

    支持特性:
    - 嵌套键访问: config.get('risk.max_drawdown')
    - 配置监听: config.watch('key', callback)
    - 通配符监听: config.watch_pattern('risk.*', callback)
    - 文件持久化: config.load(), config.save()
    - 配置验证: config.validate()
    - 配置模板: config.apply_profile()
    - 线程安全
    """

    # 默认配置
    DEFAULT_CONFIG = {
        "risk.max_drawdown": 0.2,
        "risk.stop_loss": 0.05,
        "risk.daily_loss_limit": 0.1,
        "risk.max_position_size": 0.2,
        "risk.max_leverage": 3.0,
        "signal.dci.period": 14,
        "signal.vortex.period": 14,
        "signal.resonance.period": 20,
        "signal.confidence_threshold": 0.6,
        "execution.min_order_size": 0.001,
        "execution.max_order_size": 1.0,
        "execution.commission_rate": 0.001,
        "execution.base_size": 0.1,
        "execution.slippage": 0.0005,
        "brain.strategies": ["trend", "mean_reversion"],
        "brain.high_vol_threshold": 0.3,
        "brain.low_vol_threshold": 0.1,
        "market.symbols": ["BTC"],
        "market.timeframe": "1h",
        "evolution.enabled": False,
        "evolution.population_size": 10,
        "evolution.mutation_rate": 0.1,
        "evolution.crossover_rate": 0.7,
        "evolution.elite_count": 2,
        "evolution.max_generations": 100,
    }

    # 配置验证规则
    VALIDATION_RULES = {
        "risk.max_drawdown": lambda v: ConfigValidator.validate_float(v, 0.0, 1.0),
        "risk.stop_loss": lambda v: ConfigValidator.validate_float(v, 0.0, 1.0),
        "risk.max_leverage": lambda v: ConfigValidator.validate_float(v, 1.0, 100.0),
        "signal.dci.period": lambda v: ConfigValidator.validate_int(v, 1, 1000),
        "execution.commission_rate": lambda v: ConfigValidator.validate_float(v, 0.0, 1.0),
        "evolution.population_size": lambda v: ConfigValidator.validate_int(v, 1, 1000),
    }

    def __init__(self):
        """初始化配置中心"""
        self._data: Dict[str, Any] = {}
        self._watchers: Dict[str, List[Callable]] = {}
        self._pattern_watchers: List[tuple[Pattern, Callable]] = []
        self._lock = threading.RLock()
        self._config_path: Optional[str] = None
        self._error_count = 0
        self._initialized = False
        self._dirty = False  # 标记是否有未保存的更改

        # 加载默认配置
        self._load_defaults()

    def _load_defaults(self) -> None:
        """加载默认配置"""
        if self._initialized:
            return
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self._data:
                self._data[key] = copy.deepcopy(value)
        self._initialized = True

    # ==================== 核心操作 ====================

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持嵌套键访问

        Args:
            key: 配置键，支持点分隔的嵌套键，如 'risk.max_drawdown'
            default: 默认值，当键不存在时返回此值

        Returns:
            配置值，或 default
        """
        with self._lock:
            # 先尝试直接获取
            if key in self._data:
                return self._data[key]

            # 再尝试嵌套获取
            keys = key.split(".")
            value = self._data
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
            return value if value is not None else default

    def set(self, key: str, value: Any, notify: bool = True, validate: bool = True) -> bool:
        """
        设置配置值

        Args:
            key: 配置键，支持嵌套键
            value: 配置值
            notify: 是否通知监听器，默认 True
            validate: 是否验证，默认 True

        Returns:
            是否设置成功
        """
        # 验证
        if validate and key in self.VALIDATION_RULES:
            if not self.VALIDATION_RULES[key](value):
                self._logger.warning(f"配置验证失败: {key} = {value}")
                return False

        with self._lock:
            old = self.get(key)

            # 直接键 (包括带点的复合键名如 'risk.max_drawdown')
            self._data[key] = copy.deepcopy(value)

            self._dirty = True

            if notify:
                self._notify_watchers(key, old, value)

            return True

    def has(self, key: str) -> bool:
        """检查配置键是否存在"""
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """删除配置项"""
        with self._lock:
            if key in self._data:
                del self._data[key]
                self._dirty = True
                return True
            return False

    def get_keys(self, pattern: str = None) -> List[str]:
        """
        获取所有或匹配的配置键

        Args:
            pattern: 通配符模式，如 'risk.*'

        Returns:
            配置键列表
        """
        with self._lock:
            if pattern is None:
                return list(self._data.keys())

            return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]

    def get_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        获取以指定前缀开头的所有配置

        Args:
            prefix: 前缀

        Returns:
            配置字典
        """
        with self._lock:
            return {k: v for k, v in self._data.items() if k.startswith(prefix + ".") or k == prefix}

    # ==================== 监听器 ====================

    def watch(self, key: str, callback: Callable) -> None:
        """
        监听配置变化

        Args:
            key: 要监听的配置键
            callback: 回调函数，签名: (key, old_value, new_value)
        """
        with self._lock:
            if key not in self._watchers:
                self._watchers[key] = []
            if callback not in self._watchers[key]:
                self._watchers[key].append(callback)

    def watch_pattern(self, pattern: str, callback: Callable) -> None:
        """
        通配符监听配置变化

        Args:
            pattern: 通配符模式，如 'risk.*'
            callback: 回调函数
        """
        with self._lock:
            compiled_pattern = re.compile(fnmatch.translate(pattern))
            self._pattern_watchers.append((compiled_pattern, callback))

    def unwatch(self, key: str, callback: Callable) -> None:
        """取消监听"""
        with self._lock:
            if key in self._watchers and callback in self._watchers[key]:
                self._watchers[key].remove(callback)

    def unwatch_pattern(self, pattern: str, callback: Callable) -> None:
        """取消通配符监听"""
        with self._lock:
            compiled_pattern = re.compile(fnmatch.translate(pattern))
            self._pattern_watchers = [
                (p, c) for p, c in self._pattern_watchers if p.pattern != compiled_pattern.pattern or c != callback
            ]

    def _notify_watchers(self, key: str, old: Any, new: Any) -> None:
        """通知监听器"""
        with self._lock:
            # 精确匹配
            watchers = list(self._watchers.get(key, []))

        for callback in watchers:
            try:
                callback(key, old, new)
            except Exception:
                self._error_count += 1

        # 模式匹配
        with self._lock:
            pattern_watchers = list(self._pattern_watchers)

        for pattern, callback in pattern_watchers:
            if pattern.match(key):
                try:
                    callback(key, old, new)
                except Exception:
                    self._error_count += 1

    # ==================== 批量操作 ====================

    def set_batch(self, updates: Dict[str, Any], notify: bool = True) -> None:
        """批量设置配置"""
        with self._lock:
            for key, value in updates.items():
                self._data[key] = copy.deepcopy(value)
            self._dirty = True

            if notify:
                for key, value in updates.items():
                    self._notify_watchers(key, None, value)

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置的深拷贝"""
        with self._lock:
            return copy.deepcopy(self._data)

    def clear(self) -> None:
        """清空所有配置"""
        with self._lock:
            self._data.clear()
            self._watchers.clear()
            self._pattern_watchers.clear()
            self._dirty = True

    # ==================== 验证 ====================

    def validate(self, key: str = None) -> Dict[str, Any]:
        """
        验证配置

        Args:
            key: 要验证的键，None 表示验证所有

        Returns:
            验证结果 {'valid': bool, 'errors': list}
        """
        errors = []

        with self._lock:
            keys = [key] if key else list(self._data.keys())

        for k in keys:
            if k in self.VALIDATION_RULES:
                value = self.get(k)
                if not self.VALIDATION_RULES[k](value):
                    errors.append(f"配置验证失败: {k} = {value}")

        return {"valid": len(errors) == 0, "errors": errors}

    def is_valid(self) -> bool:
        """检查所有配置是否有效"""
        return self.validate()["valid"]

    # ==================== 模板 ====================

    def apply_profile(self, profile_name: str) -> None:
        """
        应用配置模板

        Args:
            profile_name: 模板名称 (aggressive/moderate/conservative/test)
        """
        profile = ConfigProfile.get_profile(profile_name)
        if profile:
            self.set_batch(profile)

    def save_profile(self, name: str) -> None:
        """保存当前配置为模板"""
        ConfigProfile.PROFILES[name] = self.get_all()

    # ==================== 文件操作 ====================

    def load(self, filepath: str = None, merge: bool = True) -> None:
        """
        从 YAML 文件加载配置

        Args:
            filepath: 配置文件路径
            merge: 是否合并到现有配置，False 表示替换
        """
        import yaml

        if filepath:
            self._config_path = os.path.abspath(filepath)

        if not self._config_path:
            raise ValueError("未指定配置文件路径")

        path = self._config_path
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config:
            if merge:
                self._data.update(config)
            else:
                self._data = config

        self._dirty = False

    def save(self, filepath: str = None) -> None:
        """
        保存配置到 YAML 文件

        Args:
            filepath: 目标文件路径，默认使用 load() 时的路径
        """
        import yaml

        if filepath:
            self._config_path = os.path.abspath(filepath)
        elif not self._config_path:
            raise ValueError("未指定保存路径")

        # 确保目录存在
        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)

        with open(self._config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        self._dirty = False

    def export_json(self, filepath: str) -> None:
        """导出为 JSON 格式"""
        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def import_json(self, filepath: str, merge: bool = True) -> None:
        """从 JSON 导入"""
        import json

        with open(filepath, "r", encoding="utf-8") as f:
            config = json.load(f)

        if merge:
            self._data.update(config)
        else:
            self._data = config

    # ==================== 工具方法 ====================

    @property
    def is_dirty(self) -> bool:
        """是否有未保存的更改"""
        return self._dirty

    def get_error_count(self) -> int:
        """获取监听器错误计数"""
        return self._error_count

    @property
    def _logger(self):
        """获取日志记录器"""
        import logging

        return logging.getLogger("ConfigCenter")

    def __repr__(self) -> str:
        return f"ConfigCenter(keys={len(self._data)}, dirty={self._dirty})"

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)
