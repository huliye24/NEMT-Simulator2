"""
Strategy Isolation - 策略隔离框架

提供策略执行的隔离和资源管理:
- 策略上下文隔离
- 资源配额
- 策略生命周期管理
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "StrategyContext",
    "StrategyIsolation",
    "StrategyQuota",
    "StrategyLifecycle",
]


class StrategyState(Enum):
    """策略状态"""

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class StrategyQuota:
    """策略资源配额"""

    strategy_id: str
    # CPU 配额
    max_cpu_percent: float = 50.0
    # 内存配额
    max_memory_mb: int = 512
    # 网络配额
    max_network_requests: int = 1000
    # 执行配额
    max_execution_time_seconds: float = 3600.0
    max_iterations: int = 100000
    # 数据配额
    max_data_size_mb: int = 100
    # 费用配额
    max_cost: float = 100.0


@dataclass
class StrategyUsage:
    """策略资源使用"""

    strategy_id: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    network_requests: int = 0
    execution_time_seconds: float = 0.0
    iterations: int = 0
    data_size_mb: float = 0.0
    cost: float = 0.0
    last_updated: float = field(default_factory=time.time)


@dataclass
class StrategyContext:
    """策略上下文"""

    context_id: str
    strategy_id: str
    name: str
    quota: StrategyQuota
    namespace: str  # 隔离命名空间
    created_at: float
    state: StrategyState = StrategyState.CREATED
    metadata: dict[str, Any] = field(default_factory=dict)
    usage: StrategyUsage = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = StrategyUsage(strategy_id=self.strategy_id)


class StrategyIsolation:
    """
    策略隔离器

    管理策略的隔离执行环境。

    示例:
    ```python
    isolation = StrategyIsolation()

    # 创建策略上下文
    context = isolation.create_context(
        strategy_id="strategy_001",
        name="我的策略",
        quota=StrategyQuota(strategy_id="strategy_001"),
    )

    # 执行策略
    result = isolation.execute(context, strategy_code, data)
    ```
    """

    def __init__(self):
        self._contexts: dict[str, StrategyContext] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger("StrategyIsolation")

    def create_context(
        self,
        strategy_id: str,
        name: str,
        quota: StrategyQuota = None,
        namespace: str = None,
        metadata: dict[str, Any] = None,
    ) -> StrategyContext:
        """
        创建策略上下文

        Args:
            strategy_id: 策略 ID
            name: 策略名称
            quota: 资源配额
            namespace: 隔离命名空间
            metadata: 元数据

        Returns:
            策略上下文
        """
        if quota is None:
            quota = StrategyQuota(strategy_id=strategy_id)

        if namespace is None:
            namespace = f"strategy_{strategy_id}"

        context = StrategyContext(
            context_id=str(uuid.uuid4())[:8],
            strategy_id=strategy_id,
            name=name,
            quota=quota,
            namespace=namespace,
            created_at=time.time(),
            metadata=metadata or {},
        )

        with self._lock:
            self._contexts[context.context_id] = context

        self._logger.info(f"创建策略上下文: {context.context_id} ({strategy_id})")
        return context

    def get_context(self, context_id: str) -> StrategyContext | None:
        """获取策略上下文"""
        with self._lock:
            return self._contexts.get(context_id)

    def get_context_by_strategy(self, strategy_id: str) -> StrategyContext | None:
        """根据策略 ID 获取上下文"""
        with self._lock:
            for ctx in self._contexts.values():
                if ctx.strategy_id == strategy_id:
                    return ctx
        return None

    def destroy_context(self, context_id: str) -> bool:
        """销毁策略上下文"""
        with self._lock:
            if context_id in self._contexts:
                del self._contexts[context_id]
                return True
        return False

    def update_quota(self, context_id: str, quota: StrategyQuota) -> bool:
        """更新配额"""
        with self._lock:
            if context_id in self._contexts:
                self._contexts[context_id].quota = quota
                return True
        return False

    def check_quota(self, context_id: str) -> dict[str, Any]:
        """
        检查配额使用情况

        Returns:
            配额检查结果
        """
        ctx = self.get_context(context_id)
        if ctx is None:
            return {"valid": False, "reason": "context not found"}

        quota = ctx.quota
        usage = ctx.usage

        checks = {
            "cpu": usage.cpu_percent <= quota.max_cpu_percent,
            "memory": usage.memory_mb <= quota.max_memory_mb,
            "network": usage.network_requests <= quota.max_network_requests,
            "execution_time": usage.execution_time_seconds <= quota.max_execution_time_seconds,
            "iterations": usage.iterations <= quota.max_iterations,
            "data_size": usage.data_size_mb <= quota.max_data_size_mb,
            "cost": usage.cost <= quota.max_cost,
        }

        all_valid = all(checks.values())

        return {
            "valid": all_valid,
            "checks": checks,
            "quota": {
                "max_cpu_percent": quota.max_cpu_percent,
                "max_memory_mb": quota.max_memory_mb,
                "max_execution_time_seconds": quota.max_execution_time_seconds,
            },
            "usage": {
                "cpu_percent": usage.cpu_percent,
                "memory_mb": usage.memory_mb,
                "execution_time_seconds": usage.execution_time_seconds,
                "iterations": usage.iterations,
            },
        }

    def update_usage(self, context_id: str, **kwargs) -> bool:
        """更新资源使用"""
        with self._lock:
            ctx = self._contexts.get(context_id)
            if ctx is None:
                return False

            usage = ctx.usage
            for key, value in kwargs.items():
                if hasattr(usage, key):
                    setattr(usage, key, value)
            usage.last_updated = time.time()
            return True

    def execute(
        self,
        context: StrategyContext,
        code: str,
        data: dict[str, Any],
        timeout: float = None,
    ) -> dict[str, Any]:
        """
        在隔离环境中执行策略

        Args:
            context: 策略上下文
            code: 策略代码
            data: 输入数据
            timeout: 超时时间

        Returns:
            执行结果
        """
        from nemt.sandbox import ResourceLimits, Sandbox, SandboxConfig

        # 检查配额
        quota_check = self.check_quota(context.context_id)
        if not quota_check["valid"]:
            return {
                "success": False,
                "error": "quota exceeded",
                "quota_check": quota_check,
            }

        # 设置沙箱配置
        limits = ResourceLimits(
            max_memory_mb=context.quota.max_memory_mb,
            max_execution_seconds=timeout or context.quota.max_execution_time_seconds,
        )

        config = SandboxConfig(
            name=context.strategy_id,
            limits=limits,
        )

        sandbox = Sandbox(config)

        # 执行
        result = sandbox.execute(code, {"data": data})

        # 更新使用情况
        self.update_usage(
            context.context_id,
            execution_time_seconds=result.execution_time,
            memory_mb=result.memory_used_mb,
            iterations=context.usage.iterations + 1,
        )

        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time,
            "memory_used_mb": result.memory_used_mb,
            "state": result.state.value,
        }

    def list_contexts(self) -> list[StrategyContext]:
        """列出所有上下文"""
        with self._lock:
            return list(self._contexts.values())


class StrategyLifecycle:
    """
    策略生命周期管理器

    管理策略的初始化、运行、暂停、停止等生命周期。
    """

    def __init__(self, isolation: StrategyIsolation = None):
        self._isolation = isolation or StrategyIsolation()
        self._logger = logging.getLogger("StrategyLifecycle")

    def initialize(self, context_id: str) -> bool:
        """初始化策略"""
        ctx = self._isolation.get_context(context_id)
        if ctx is None:
            return False

        ctx.state = StrategyState.INITIALIZING
        self._logger.info(f"初始化策略: {ctx.strategy_id}")

        # TODO: 执行初始化逻辑
        ctx.state = StrategyState.RUNNING
        return True

    def pause(self, context_id: str) -> bool:
        """暂停策略"""
        ctx = self._isolation.get_context(context_id)
        if ctx is None or ctx.state != StrategyState.RUNNING:
            return False

        ctx.state = StrategyState.PAUSED
        self._logger.info(f"暂停策略: {ctx.strategy_id}")
        return True

    def resume(self, context_id: str) -> bool:
        """恢复策略"""
        ctx = self._isolation.get_context(context_id)
        if ctx is None or ctx.state != StrategyState.PAUSED:
            return False

        ctx.state = StrategyState.RUNNING
        self._logger.info(f"恢复策略: {ctx.strategy_id}")
        return True

    def stop(self, context_id: str) -> bool:
        """停止策略"""
        ctx = self._isolation.get_context(context_id)
        if ctx is None:
            return False

        ctx.state = StrategyState.STOPPING
        self._logger.info(f"停止策略: {ctx.strategy_id}")

        # TODO: 执行清理逻辑
        ctx.state = StrategyState.STOPPED
        return True


# 全局实例
_strategy_isolation: StrategyIsolation | None = None


def get_strategy_isolation() -> StrategyIsolation:
    """获取策略隔离器"""
    global _strategy_isolation
    if _strategy_isolation is None:
        _strategy_isolation = StrategyIsolation()
    return _strategy_isolation
