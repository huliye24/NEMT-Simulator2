"""
Core Adapters - 核心组件适配器

提供接口适配器，将原有实现适配到新接口。
"""

from nemt.core.adapters.config_center_adapter import ConfigCenterAdapter
from nemt.core.adapters.event_bus_adapter import EventBusAdapter
from nemt.core.adapters.storage_adapter import SQLiteStorageAdapter

__all__ = [
    "EventBusAdapter",
    "ConfigCenterAdapter",
    "SQLiteStorageAdapter",
]
