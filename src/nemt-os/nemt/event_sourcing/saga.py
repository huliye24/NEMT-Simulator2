"""
Saga - Saga 模式

提供分布式事务的 Saga 模式实现:
- 编排式 Saga
- 补偿事务
- 错误恢复
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "Saga",
    "SagaStep",
    "SagaState",
    "SagaOrchestrator",
    "CompensableAction",
    "CompensationResult",
]


class SagaState(Enum):
    """Saga 状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"


@dataclass
class CompensationResult:
    """补偿结果"""

    success: bool
    error: str = ""
    data: Any = None


class CompensableAction:
    """
    可补偿动作

    定义 Saga 中的一个步骤及其补偿动作。
    """

    def __init__(
        self,
        name: str,
        execute: Callable,
        compensate: Callable,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        self.name = name
        self.execute = execute
        self.compensate = compensate
        self.retry_count = retry_count
        self.retry_delay = retry_delay


@dataclass
class SagaStepResult:
    """Saga 步骤结果"""

    step_name: str
    success: bool
    data: Any = None
    error: str = ""
    timestamp: float = field(default_factory=time.time)


class Saga:
    """
    Saga 定义

    定义一个分布式事务的步骤序列。

    示例:
    ```python
    class OrderSaga(Saga):
        def __init__(self):
            super().__init__("order_saga")

            self.add_step(CompensableAction(
                name="reserve_inventory",
                execute=self.reserve_inventory,
                compensate=self.release_inventory,
            ))

            self.add_step(CompensableAction(
                name="process_payment",
                execute=self.process_payment,
                compensate=self.refund_payment,
            ))

            self.add_step(CompensableAction(
                name="create_order",
                execute=self.create_order,
                compensate=self.cancel_order,
            ))
    ```
    """

    def __init__(self, saga_id: str = None):
        self.saga_id = saga_id or str(uuid.uuid4())
        self._steps: list[CompensableAction] = []
        self._results: list[SagaStepResult] = []
        self._state = SagaState.PENDING
        self._context: dict = {}

    @property
    def steps(self) -> list[CompensableAction]:
        return self._steps

    @property
    def state(self) -> SagaState:
        return self._state

    def add_step(self, action: CompensableAction) -> "Saga":
        """添加步骤"""
        self._steps.append(action)
        return self

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文"""
        return self._context.get(key, default)


class SagaOrchestrator:
    """
    Saga 编排器

    编排 Saga 的执行和补偿。

    示例:
    ```python
    orchestrator = SagaOrchestrator()

    # 执行 Saga
    saga = OrderSaga()
    result = await orchestrator.execute(saga)

    if not result.success:
        # 触发补偿
        await orchestrator.compensate(saga)
    ```
    """

    def __init__(self):
        self._sagas: dict[str, Saga] = {}
        self._logger = logging.getLogger("SagaOrchestrator")
        self._max_retries = 3

    def register(self, saga: Saga) -> None:
        """注册 Saga"""
        self._sagas[saga.saga_id] = saga

    def unregister(self, saga_id: str) -> bool:
        """注销 Saga"""
        if saga_id in self._sagas:
            del self._sagas[saga_id]
            return True
        return False

    def get(self, saga_id: str) -> Saga | None:
        """获取 Saga"""
        return self._sagas.get(saga_id)

    async def execute(self, saga: Saga, context: dict = None) -> SagaStepResult:
        """
        执行 Saga

        Args:
            saga: Saga 实例
            context: 执行上下文

        Returns:
            执行结果
        """
        self.register(saga)
        saga._state = SagaState.RUNNING

        if context:
            for key, value in context.items():
                saga.set_context(key, value)

        results = []

        try:
            # 执行每个步骤
            for step in saga.steps:
                self._logger.info(f"执行 Saga 步骤: {step.name}")

                result = await self._execute_step(step, saga)
                results.append(result)

                if not result.success:
                    self._logger.error(f"Saga 步骤失败: {step.name}")
                    saga._state = SagaState.FAILED
                    saga._results = results
                    return SagaStepResult(
                        step_name=step.name,
                        success=False,
                        error=f"Step failed: {result.error}",
                    )

                # 将结果存入上下文
                saga.set_context(step.name, result.data)

            saga._state = SagaState.COMPLETED
            saga._results = results

            return SagaStepResult(
                step_name="saga_complete",
                success=True,
                data={"saga_id": saga.saga_id, "steps": len(results)},
            )

        except Exception as e:
            self._logger.error(f"Saga 执行异常: {e}")
            saga._state = SagaState.FAILED
            return SagaStepResult(
                step_name="saga_error",
                success=False,
                error=str(e),
            )

    async def _execute_step(self, step: CompensableAction, saga: Saga) -> SagaStepResult:
        """执行单个步骤（带重试）"""
        last_error = None

        for attempt in range(step.retry_count):
            try:
                # 执行步骤
                if asyncio.iscoroutinefunction(step.execute):
                    data = await step.execute(saga._context)
                else:
                    data = step.execute(saga._context)

                return SagaStepResult(
                    step_name=step.name,
                    success=True,
                    data=data,
                )

            except Exception as e:
                last_error = e
                self._logger.warning(f"步骤 {step.name} 执行失败 (尝试 {attempt + 1}/{step.retry_count}): {e}")

                if attempt < step.retry_count - 1:
                    await asyncio.sleep(step.retry_delay * (attempt + 1))

        return SagaStepResult(
            step_name=step.name,
            success=False,
            error=str(last_error),
        )

    async def compensate(self, saga: Saga) -> bool:
        """
        补偿 Saga

        按反向顺序执行补偿操作。

        Args:
            saga: Saga 实例

        Returns:
            补偿是否成功
        """
        saga._state = SagaState.COMPENSATING
        self._logger.info(f"开始补偿 Saga: {saga.saga_id}")

        try:
            # 按反向顺序执行补偿
            for step in reversed(saga.steps[: len(saga._results)]):
                result = saga._results[len(saga._steps) - saga._steps.index(step) - 1]
                if not result.success:
                    continue

                self._logger.info(f"补偿 Saga 步骤: {step.name}")

                try:
                    if asyncio.iscoroutinefunction(step.compensate):
                        await step.compensate(saga._context, result.data)
                    else:
                        step.compensate(saga._context, result.data)

                except Exception as e:
                    self._logger.error(f"补偿步骤 {step.name} 失败: {e}")
                    saga._state = SagaState.FAILED
                    return False

            saga._state = SagaState.COMPENSATED
            self._logger.info(f"Saga 补偿完成: {saga.saga_id}")
            return True

        except Exception as e:
            self._logger.error(f"Saga 补偿异常: {e}")
            saga._state = SagaState.FAILED
            return False

    def get_status(self, saga_id: str) -> dict | None:
        """获取 Saga 状态"""
        saga = self._sagas.get(saga_id)
        if saga is None:
            return None

        return {
            "saga_id": saga.saga_id,
            "state": saga.state.value,
            "steps_count": len(saga.steps),
            "results": [
                {
                    "step_name": r.step_name,
                    "success": r.success,
                    "error": r.error,
                }
                for r in saga._results
            ],
        }

    def list_sagas(self, state: SagaState = None) -> list[dict]:
        """列出所有 Saga"""
        result = []
        for saga in self._sagas.values():
            if state is None or saga.state == state:
                result.append(self.get_status(saga.saga_id))
        return result


# 便捷装饰器
def saga_step(
    name: str,
    compensate: Callable = None,
    retry_count: int = 3,
    retry_delay: float = 1.0,
) -> Callable:
    """Saga 步骤装饰器"""

    def decorator(func: Callable) -> Callable:
        func._saga_step = CompensableAction(
            name=name,
            execute=func,
            compensate=compensate or (lambda ctx, data: None),
            retry_count=retry_count,
            retry_delay=retry_delay,
        )
        return func

    return decorator
