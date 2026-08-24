"""
FeatureFlag - 特性开关

提供特性开关的灵活控制，支持灰度发布和 A/B 测试。
"""

import hashlib
import logging
import random
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "FeatureFlag",
    "FeatureFlagType",
    "FeatureFlagManager",
]


class FeatureFlagType(Enum):
    """特性开关类型"""

    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_TARGET = "user_target"
    GRADUAL_ROLLOUT = "gradual_rollout"


@dataclass
class FeatureFlag:
    """特性开关"""

    name: str
    flag_type: FeatureFlagType
    enabled: bool
    description: str = ""
    default_value: Any = False

    # 百分比开关配置
    percentage: float = 100.0

    # 用户定向配置
    target_users: list[str] = field(default_factory=list)
    excluded_users: list[str] = field(default_factory=list)

    # 渐进式发布配置
    start_time: float = 0
    end_time: float = 0
    stages: list[dict] = field(default_factory=list)

    # 元数据
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class FeatureFlagManager:
    """
    特性开关管理器

    示例:
    ```python
    manager = FeatureFlagManager()

    # 创建特性开关
    manager.add_flag(FeatureFlag(
        name="new_ui",
        flag_type=FeatureFlagType.BOOLEAN,
        enabled=True,
    ))

    # 百分比开关
    manager.add_flag(FeatureFlag(
        name="new_algorithm",
        flag_type=FeatureFlagType.PERCENTAGE,
        percentage=10.0,  # 10% 用户
    ))

    # 检查开关
    if manager.is_enabled("new_ui"):
        show_new_ui()
    ```

    """

    def __init__(self):
        self._flags: dict[str, FeatureFlag] = {}
        self._lock = threading.RLock()
        self._evaluators: dict[str, Callable] = {}
        self._logger = logging.getLogger("FeatureFlagManager")

    def add_flag(self, flag: FeatureFlag) -> None:
        """添加特性开关"""
        with self._lock:
            self._flags[flag.name] = flag
            self._logger.info(f"添加特性开关: {flag.name}")

    def remove_flag(self, name: str) -> bool:
        """移除特性开关"""
        with self._lock:
            if name in self._flags:
                del self._flags[name]
                return True
            return False

    def get_flag(self, name: str) -> FeatureFlag | None:
        """获取特性开关"""
        with self._lock:
            return self._flags.get(name)

    def update_flag(self, name: str, **kwargs) -> bool:
        """更新特性开关"""
        with self._lock:
            flag = self._flags.get(name)
            if flag is None:
                return False

            for key, value in kwargs.items():
                if hasattr(flag, key):
                    setattr(flag, key, value)
            flag.updated_at = time.time()
            return True

    def is_enabled(
        self,
        name: str,
        user_id: str = None,
        context: dict = None,
    ) -> bool:
        """检查特性是否启用"""
        with self._lock:
            flag = self._flags.get(name)
            if flag is None:
                return False

            if not flag.enabled:
                return False

            return self._evaluate(flag, user_id, context)

    def get_value(
        self,
        name: str,
        default: Any = None,
        user_id: str = None,
        context: dict = None,
    ) -> Any:
        """获取特性值"""
        if not self.is_enabled(name, user_id, context):
            return default

        flag = self._flags.get(name)
        if flag:
            return flag.default_value
        return default

    def _evaluate(self, flag: FeatureFlag, user_id: str, context: dict) -> bool:
        """评估特性开关"""
        if flag.flag_type == FeatureFlagType.BOOLEAN:
            return flag.enabled

        elif flag.flag_type == FeatureFlagType.PERCENTAGE:
            return self._evaluate_percentage(flag, user_id)

        elif flag.flag_type == FeatureFlagType.USER_TARGET:
            return self._evaluate_user_target(flag, user_id)

        elif flag.flag_type == FeatureFlagType.GRADUAL_ROLLOUT:
            return self._evaluate_gradual(flag, user_id)

        return False

    def _evaluate_percentage(self, flag: FeatureFlag, user_id: str) -> bool:
        """评估百分比"""
        if not user_id:
            return random.random() * 100 < flag.percentage

        # 基于用户 ID 的一致性哈希
        hash_input = f"{flag.name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        percentage = (hash_value % 10000) / 100
        return percentage < flag.percentage

    def _evaluate_user_target(self, flag: FeatureFlag, user_id: str) -> bool:
        """评估用户定向"""
        if not user_id:
            return False

        if user_id in flag.excluded_users:
            return False

        if user_id in flag.target_users:
            return True

        return False

    def _evaluate_gradual(self, flag: FeatureFlag, user_id: str) -> bool:
        """评估渐进式发布"""
        now = time.time()

        # 检查时间范围
        if flag.start_time and now < flag.start_time:
            return False
        if flag.end_time and now > flag.end_time:
            return False

        # 使用百分比评估
        return self._evaluate_percentage(flag, user_id)

    def list_flags(self, enabled_only: bool = False) -> list[FeatureFlag]:
        """列出所有开关"""
        with self._lock:
            flags = list(self._flags.values())
            if enabled_only:
                flags = [f for f in flags if f.enabled]
            return flags

    def get_stats(self, name: str) -> dict:
        """获取开关统计"""
        with self._lock:
            flag = self._flags.get(name)
            if not flag:
                return {}

            return {
                "name": flag.name,
                "type": flag.flag_type.value,
                "enabled": flag.enabled,
                "percentage": flag.percentage,
                "target_users_count": len(flag.target_users),
                "created_at": flag.created_at,
                "updated_at": flag.updated_at,
            }

    def batch_check(
        self,
        names: list[str],
        user_id: str = None,
        context: dict = None,
    ) -> dict[str, bool]:
        """批量检查开关"""
        return {name: self.is_enabled(name, user_id, context) for name in names}


# 全局实例
_feature_flag_manager: FeatureFlagManager | None = None


def get_feature_flag_manager() -> FeatureFlagManager:
    """获取全局特性开关管理器"""
    global _feature_flag_manager
    if _feature_flag_manager is None:
        _feature_flag_manager = FeatureFlagManager()
    return _feature_flag_manager
