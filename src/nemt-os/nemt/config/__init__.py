"""
Config Module - 配置模块

提供配置管理和特性开关能力。
"""

from nemt.config.config_loader import (
    ConfigDict,
    ConfigEntry,
    ConfigLoader,
    ConfigSource,
    ConfigWatcher,
)
from nemt.config.feature_flag import (
    FeatureFlag,
    FeatureFlagManager,
    FeatureFlagType,
    get_feature_flag_manager,
)

__all__ = [
    "ConfigSource",
    "ConfigEntry",
    "ConfigLoader",
    "ConfigDict",
    "ConfigWatcher",
    "FeatureFlag",
    "FeatureFlagType",
    "FeatureFlagManager",
    "get_feature_flag_manager",
]
