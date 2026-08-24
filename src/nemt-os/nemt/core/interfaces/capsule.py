"""
ICapsule - 胶囊接口定义

定义所有胶囊必须实现的接口。
"""

from enum import Enum
from typing import Any, Protocol, runtime_checkable


class CapsuleState(Enum):
    """胶囊状态"""

    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class HealthStatus(Enum):
    """健康状态"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@runtime_checkable
class ICapsule(Protocol):
    """
    胶囊接口

    所有胶囊必须实现此接口。
    """

    @property
    def capsule_id(self) -> str:
        """胶囊唯一标识"""
        ...

    @property
    def state(self) -> CapsuleState:
        """当前状态"""
        ...

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        ...

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        ...

    def init(self) -> None:
        """
        初始化胶囊

        在此方法中:
        - 订阅事件
        - 初始化内部状态
        - 设置默认配置

        Raises:
            Exception: 初始化失败时抛出异常
        """
        ...

    def start(self) -> None:
        """
        启动胶囊

        开始执行主要逻辑。
        """
        ...

    def exec(self) -> dict[str, Any]:
        """
        执行主要逻辑

        Returns:
            执行结果字典
        """
        ...

    def shutdown(self) -> None:
        """
        关闭胶囊

        在此方法中:
        - 取消事件订阅
        - 清理资源
        - 保存状态
        """
        ...

    def get_health(self) -> HealthStatus:
        """
        获取健康状态

        Returns:
            健康状态枚举
        """
        ...

    def get_metrics(self) -> dict[str, Any]:
        """
        获取指标数据

        Returns:
            指标字典
        """
        ...


class IInitializable(Protocol):
    """可初始化接口"""

    def initialize(self) -> None:
        """初始化"""
        ...

    def is_initialized(self) -> bool:
        """是否已初始化"""
        ...


class IStartable(Protocol):
    """可启动接口"""

    def start(self) -> None:
        """启动"""
        ...

    def stop(self) -> None:
        """停止"""
        ...

    def is_running(self) -> bool:
        """是否正在运行"""
        ...


class IHealthCheckable(Protocol):
    """可健康检查接口"""

    def get_health(self) -> HealthStatus:
        """获取健康状态"""
        ...

    def get_health_details(self) -> dict[str, Any]:
        """获取健康详情"""
        ...


class IMetricsCollector(Protocol):
    """指标采集接口"""

    def get_metrics(self) -> dict[str, Any]:
        """获取指标"""
        ...

    def reset_metrics(self) -> None:
        """重置指标"""
        ...
