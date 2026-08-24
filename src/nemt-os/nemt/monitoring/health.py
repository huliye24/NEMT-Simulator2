"""
HealthCheck - 健康检查系统

提供健康检查、就绪检查和存活检查能力。
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "HealthStatus",
    "HealthCheckResult",
    "HealthCheck",
    "HealthCheckRegistry",
    "LivenessProbe",
    "ReadinessProbe",
]


class HealthStatus(Enum):
    """健康状态"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    name: str
    status: HealthStatus
    message: str = ""
    duration_ms: float = 0
    timestamp: float = field(default_factory=time.time)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class HealthCheck:
    """
    健康检查基类

    示例:
    ```python
    class DatabaseHealthCheck(HealthCheck):
        def __init__(self, db):
            super().__init__("database")
            self.db = db

        async def check(self) -> HealthCheckResult:
            try:
                await self.db.ping()
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="Database is healthy"
                )
            except Exception as e:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e)
                )
    ```
    """

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout

    async def check(self) -> HealthCheckResult:
        """执行健康检查"""
        raise NotImplementedError

    async def check_sync(self) -> HealthCheckResult:
        """同步健康检查"""
        start = time.time()
        try:
            return await self.check()
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )


class LambdaHealthCheck(HealthCheck):
    """Lambda 健康检查"""

    def __init__(
        self,
        name: str,
        checker: Callable[[], bool],
        timeout: float = 5.0,
    ):
        super().__init__(name, timeout)
        self.checker = checker

    async def check(self) -> HealthCheckResult:
        start = time.time()
        try:
            result = self.checker()
            status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
            message = f"{self.name} is {'healthy' if result else 'unhealthy'}"
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = str(e)

        return HealthCheckResult(
            name=self.name,
            status=status,
            message=message,
            duration_ms=(time.time() - start) * 1000,
        )


class HealthCheckRegistry:
    """
    健康检查注册表

    示例:
    ```python
    registry = HealthCheckRegistry()

    # 注册健康检查
    registry.register(DatabaseHealthCheck(db))
    registry.register(LambdaHealthCheck("redis", lambda: redis.ping()))

    # 执行所有检查
    results = await registry.check_all()

    # 获取汇总状态
    overall = registry.get_overall_status(results)
    ```
    """

    def __init__(self):
        self._checks: dict[str, HealthCheck] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("HealthCheckRegistry")

    def register(self, check: HealthCheck) -> None:
        """注册健康检查"""
        with self._lock:
            self._checks[check.name] = check
            self._logger.info(f"注册健康检查: {check.name}")

    def unregister(self, name: str) -> bool:
        """注销健康检查"""
        with self._lock:
            if name in self._checks:
                del self._checks[name]
                return True
            return False

    def get(self, name: str) -> HealthCheck | None:
        """获取健康检查"""
        with self._lock:
            return self._checks.get(name)

    def list_checks(self) -> list[str]:
        """列出所有健康检查"""
        with self._lock:
            return list(self._checks.keys())

    async def check_all(self) -> list[HealthCheckResult]:
        """执行所有健康检查"""
        tasks = []
        for check in self._checks.values():
            tasks.append(self._run_check(check))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        check_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                check_name = list(self._checks.keys())[i]
                check_results.append(
                    HealthCheckResult(
                        name=check_name,
                        status=HealthStatus.UNHEALTHY,
                        message=str(result),
                    )
                )
            else:
                check_results.append(result)

        return check_results

    async def _run_check(self, check: HealthCheck) -> HealthCheckResult:
        """运行单个检查"""
        start = time.time()
        try:
            if asyncio.iscoroutinefunction(check.check):
                result = await asyncio.wait_for(check.check(), timeout=check.timeout)
            else:
                result = check.check_sync()
            return result
        except TimeoutError:
            return HealthCheckResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check timed out after {check.timeout}s",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return HealthCheckResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def get_overall_status(self, results: list[HealthCheckResult]) -> HealthStatus:
        """获取总体健康状态"""
        if not results:
            return HealthStatus.UNKNOWN

        statuses = [r.status for r in results]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY

        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED

        return HealthStatus.UNKNOWN

    def to_dict(self, results: list[HealthCheckResult] = None) -> dict:
        """导出为字典"""
        if results is None:
            return {"status": HealthStatus.UNKNOWN.value, "checks": []}

        return {
            "status": self.get_overall_status(results).value,
            "checks": [r.to_dict() for r in results],
        }


class LivenessProbe(HealthCheck):
    """存活探针"""

    def __init__(self, checks: list[HealthCheck]):
        super().__init__("liveness")
        self.checks = checks

    async def check(self) -> HealthCheckResult:
        registry = HealthCheckRegistry()
        for check in self.checks:
            registry.register(check)

        results = await registry.check_all()
        overall = registry.get_overall_status(results)

        return HealthCheckResult(
            name=self.name,
            status=overall,
            message="Liveness probe " + ("passed" if overall == HealthStatus.HEALTHY else "failed"),
            details={"checks": [r.to_dict() for r in results]},
        )


class ReadinessProbe(HealthCheck):
    """就绪探针"""

    def __init__(self, checks: list[HealthCheck]):
        super().__init__("readiness")
        self.checks = checks

    async def check(self) -> HealthCheckResult:
        registry = HealthCheckRegistry()
        for check in self.checks:
            registry.register(check)

        results = await registry.check_all()
        overall = registry.get_overall_status(results)

        return HealthCheckResult(
            name=self.name,
            status=overall,
            message="Readiness probe " + ("passed" if overall == HealthStatus.HEALTHY else "failed"),
            details={"checks": [r.to_dict() for r in results]},
        )


# 全局实例
_health_registry: HealthCheckRegistry | None = None


def get_health_registry() -> HealthCheckRegistry:
    """获取全局健康检查注册表"""
    global _health_registry
    if _health_registry is None:
        _health_registry = HealthCheckRegistry()
    return _health_registry
