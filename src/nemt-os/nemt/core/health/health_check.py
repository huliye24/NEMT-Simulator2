"""
HealthCheck - 健康检查系统

提供系统健康检查功能，支持:
- 健康检查接口
- 预置检查器
- 健康状态聚合
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from nemt.core.interfaces import HealthStatus

__all__ = ["HealthCheck", "HealthCheckResult", "HealthCheckerRegistry", "CompositeHealthCheck"]


class CheckStatus(Enum):
    """检查状态"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    name: str
    status: CheckStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


class HealthCheck:
    """
    健康检查基类

    示例:
    ```python
    class MyCheck(HealthCheck):
        def __init__(self):
            super().__init__("my_check", "我的检查")

        def check(self) -> HealthCheckResult:
            # 执行检查
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.HEALTHY,
                message="一切正常"
            )
    ```
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    def check(self) -> HealthCheckResult:
        """
        执行检查

        Returns:
            检查结果
        """
        raise NotImplementedError()

    def __call__(self) -> HealthCheckResult:
        return self.check()


class LambdaHealthCheck(HealthCheck):
    """Lambda 健康检查 - 使用 lambda 函数"""

    def __init__(self, name: str, checker: Callable[[], HealthCheckResult], description: str = ""):
        super().__init__(name, description)
        self._checker = checker

    def check(self) -> HealthCheckResult:
        return self._checker()


class EventBusHealthCheck(HealthCheck):
    """EventBus 健康检查"""

    def __init__(self, event_bus):
        super().__init__("event_bus", "事件总线健康检查")
        self._event_bus = event_bus

    def check(self) -> HealthCheckResult:
        try:
            stats = self._event_bus.get_stats()
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.HEALTHY,
                message="EventBus 运行正常",
                details={
                    "handler_count": stats.get("handler_count", 0),
                    "event_count": stats.get("event_count", 0),
                    "error_count": stats.get("error_count", 0),
                },
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.UNHEALTHY,
                message=f"EventBus 检查失败: {e}",
            )


class StorageHealthCheck(HealthCheck):
    """Storage 健康检查"""

    def __init__(self, storage):
        super().__init__("storage", "存储健康检查")
        self._storage = storage

    def check(self) -> HealthCheckResult:
        try:
            # 简单检查：尝试获取配置
            self._storage.get_config("health_check_test", "ok")
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.HEALTHY,
                message="Storage 运行正常",
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.UNHEALTHY,
                message=f"Storage 检查失败: {e}",
            )


class CapsuleHealthCheck(HealthCheck):
    """Capsule 健康检查"""

    def __init__(self, capsule):
        super().__init__(f"capsule_{capsule.capsule_id}", f"胶囊 {capsule.capsule_id} 健康检查")
        self._capsule = capsule

    def check(self) -> HealthCheckResult:
        try:
            health = self._capsule.get_health()
            metrics = self._capsule.get_metrics()
            details = self._capsule.get_health_details() if hasattr(self._capsule, "get_health_details") else {}

            status_map = {
                HealthStatus.HEALTHY: CheckStatus.HEALTHY,
                HealthStatus.DEGRADED: CheckStatus.DEGRADED,
                HealthStatus.UNHEALTHY: CheckStatus.UNHEALTHY,
                HealthStatus.UNKNOWN: CheckStatus.UNKNOWN,
            }

            return HealthCheckResult(
                name=self.name,
                status=status_map.get(health, CheckStatus.UNKNOWN),
                message=f"Capsule {self._capsule.capsule_id} 健康",
                details={
                    "health": health.value,
                    "state": details.get("state", "unknown"),
                    "metrics": metrics,
                },
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.UNHEALTHY,
                message=f"Capsule 检查失败: {e}",
            )


class HealthCheckerRegistry:
    """健康检查器注册表"""

    def __init__(self):
        self._checkers: dict[str, HealthCheck] = {}

    def register(self, checker: HealthCheck) -> "HealthCheckerRegistry":
        """注册检查器"""
        self._checkers[checker.name] = checker
        return self

    def unregister(self, name: str) -> bool:
        """注销检查器"""
        if name in self._checkers:
            del self._checkers[name]
            return True
        return False

    def get(self, name: str) -> HealthCheck | None:
        """获取检查器"""
        return self._checkers.get(name)

    def list_checkers(self) -> list[str]:
        """列出所有检查器"""
        return list(self._checkers.keys())

    def run_all(self) -> list[HealthCheckResult]:
        """运行所有检查"""
        results = []
        for checker in self._checkers.values():
            start = time.time()
            try:
                result = checker.check()
                result.duration_ms = (time.time() - start) * 1000
            except Exception as e:
                result = HealthCheckResult(
                    name=checker.name,
                    status=CheckStatus.UNHEALTHY,
                    message=f"检查异常: {e}",
                    duration_ms=(time.time() - start) * 1000,
                )
            results.append(result)
        return results


class CompositeHealthCheck(HealthCheck):
    """组合健康检查"""

    def __init__(self, name: str, checks: list[HealthCheck], strategy: str = "all"):
        """
        Args:
            name: 检查名称
            checks: 子检查列表
            strategy: 聚合策略 ("all", "any", "majority")
        """
        super().__init__(name, "组合健康检查")
        self.checks = checks
        self.strategy = strategy

    def check(self) -> HealthCheckResult:
        """执行组合检查"""
        start = time.time()
        results = []

        for check in self.checks:
            try:
                result = check.check()
                results.append(result)
            except Exception as e:
                results.append(
                    HealthCheckResult(
                        name=check.name,
                        status=CheckStatus.UNHEALTHY,
                        message=f"检查异常: {e}",
                    )
                )

        # 聚合结果
        if self.strategy == "all":
            # 全部通过才算通过
            statuses = [r.status for r in results]
            if CheckStatus.UNHEALTHY in statuses:
                overall = CheckStatus.UNHEALTHY
            elif CheckStatus.DEGRADED in statuses:
                overall = CheckStatus.DEGRADED
            elif CheckStatus.UNKNOWN in statuses:
                overall = CheckStatus.UNKNOWN
            else:
                overall = CheckStatus.HEALTHY
        elif self.strategy == "any":
            # 任意一个通过即通过
            statuses = [r.status for r in results]
            if CheckStatus.HEALTHY in statuses:
                overall = CheckStatus.HEALTHY
            elif CheckStatus.DEGRADED in statuses:
                overall = CheckStatus.DEGRADED
            else:
                overall = CheckStatus.UNHEALTHY
        else:
            overall = CheckStatus.UNKNOWN

        return HealthCheckResult(
            name=self.name,
            status=overall,
            message=f"{len(results)} 项检查",
            details={"results": [r.to_dict() for r in results]},
            duration_ms=(time.time() - start) * 1000,
        )


def create_system_health_check(
    event_bus=None,
    storage=None,
    capsules: list = None,
) -> CompositeHealthCheck:
    """
    创建系统健康检查

    Args:
        event_bus: EventBus 实例
        storage: Storage 实例
        capsules: Capsule 实例列表

    Returns:
        组合健康检查
    """
    checks = []

    if event_bus:
        checks.append(EventBusHealthCheck(event_bus))

    if storage:
        checks.append(StorageHealthCheck(storage))

    if capsules:
        for capsule in capsules:
            checks.append(CapsuleHealthCheck(capsule))

    return CompositeHealthCheck("system", checks, strategy="all")
