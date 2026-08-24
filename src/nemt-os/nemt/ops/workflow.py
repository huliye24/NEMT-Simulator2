"""
WorkflowEngine - 工作流引擎

提供可视化编排、任务调度能力。
"""

import logging
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "TaskStatus",
    "TaskType",
    "Task",
    "Workflow",
    "WorkflowEngine",
]


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskType(Enum):
    """任务类型"""

    ACTION = "action"  # 执行动作
    CONDITION = "condition"  # 条件判断
    PARALLEL = "parallel"  # 并行执行
    LOOP = "loop"  # 循环
    WAIT = "wait"  # 等待
    NOTIFY = "notify"  # 通知


@dataclass
class Task:
    """工作流任务"""

    task_id: str
    name: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    handler: Callable = None
    params: dict = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 60
    depends_on: list[str] = field(default_factory=list)
    result: Any = None
    error: str = ""
    start_time: float = 0
    end_time: float = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class Workflow:
    """工作流定义"""

    workflow_id: str
    name: str
    description: str = ""
    tasks: list[Task] = field(default_factory=list)
    entry_task: str = ""
    timeout: float = 3600
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    completed_at: float = 0


class WorkflowEngine:
    """
    工作流引擎

    示例:
    ```python
    engine = WorkflowEngine()

    # 定义工作流
    workflow = Workflow(
        workflow_id="daily_report",
        name="Daily Report",
    )

    # 添加任务
    workflow.tasks = [
        Task(task_id="fetch", name="Fetch Data", task_type=TaskType.ACTION),
        Task(task_id="process", name="Process", task_type=TaskType.ACTION, depends_on=["fetch"]),
        Task(task_id="notify", name="Notify", task_type=TaskType.NOTIFY, depends_on=["process"]),
    ]
    workflow.entry_task = "fetch"

    # 注册工作流
    engine.register(workflow)

    # 执行
    run_id = await engine.execute("daily_report")

    # 查询状态
    status = engine.get_status(run_id)
    ```
    """

    def __init__(self):
        self._workflows: dict[str, Workflow] = {}
        self._runs: dict[str, dict] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("WorkflowEngine")
        self._executors: dict[TaskType, Callable] = {}

        # 注册默认执行器
        self._register_default_executors()

    def _register_default_executors(self) -> None:
        """注册默认执行器"""

        async def execute_action(task: Task) -> Any:
            """执行动作任务"""
            if task.handler:
                if callable(task.handler):
                    result = task.handler(task.params)
                    if callable(result.__await__):
                        result = await result
                else:
                    result = task.handler
            else:
                result = f"Executed: {task.name}"
            return result

        async def execute_condition(task: Task) -> bool:
            """执行条件任务"""
            if task.handler:
                result = task.handler(task.params)
                if callable(result.__await__):
                    result = await result
                return bool(result)
            return True

        self._executors[TaskType.ACTION] = execute_action
        self._executors[TaskType.CONDITION] = execute_condition

    def register(self, workflow: Workflow) -> None:
        """注册工作流"""
        with self._lock:
            self._workflows[workflow.workflow_id] = workflow

    def unregister(self, workflow_id: str) -> bool:
        """注销工作流"""
        with self._lock:
            if workflow_id in self._workflows:
                del self._workflows[workflow_id]
                return True
            return False

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        """获取工作流"""
        return self._workflows.get(workflow_id)

    async def execute(
        self,
        workflow_id: str,
        params: dict = None,
        context: dict = None,
    ) -> str:
        """执行工作流"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        run_id = str(uuid.uuid4())
        params = params or {}
        context = context or {}

        run = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": TaskStatus.RUNNING,
            "params": params,
            "context": context,
            "task_results": {},
            "started_at": time.time(),
        }

        with self._lock:
            self._runs[run_id] = run

        workflow.status = TaskStatus.RUNNING
        workflow.started_at = time.time()

        try:
            # 拓扑排序执行任务
            await self._execute_tasks(workflow, run)

            # 判断结果
            failed_tasks = [tid for tid, result in run["task_results"].items() if result["status"] == TaskStatus.FAILED]

            if failed_tasks:
                workflow.status = TaskStatus.FAILED
                run["status"] = TaskStatus.FAILED
            else:
                workflow.status = TaskStatus.SUCCESS
                run["status"] = TaskStatus.SUCCESS

        except Exception as e:
            workflow.status = TaskStatus.FAILED
            run["status"] = TaskStatus.FAILED
            run["error"] = str(e)
            self._logger.error(f"工作流执行失败: {workflow_id}: {e}")

        workflow.completed_at = time.time()
        run["completed_at"] = time.time()

        return run_id

    async def _execute_tasks(self, workflow: Workflow, run: dict) -> None:
        """执行任务"""
        task_map = {t.task_id: t for t in workflow.tasks}
        completed = set()
        pending = {t.task_id for t in workflow.tasks}

        while pending:
            # 找出可执行的任务（依赖已完成的）
            ready = []
            for task_id in pending:
                task = task_map[task_id]
                if all(dep in completed for dep in task.depends_on):
                    ready.append(task)

            if not ready:
                # 检查是否有循环依赖
                if pending:
                    failed_id = next(iter(pending))
                    run["task_results"][failed_id] = {
                        "status": TaskStatus.FAILED,
                        "error": "Circular dependency detected",
                    }
                    completed.add(failed_id)
                    pending.remove(failed_id)
                continue

            # 执行就绪任务
            for task in ready:
                try:
                    result = await self._execute_task(task, run)
                    run["task_results"][task.task_id] = result
                except Exception as e:
                    run["task_results"][task.task_id] = {
                        "status": TaskStatus.FAILED,
                        "error": str(e),
                    }

                completed.add(task.task_id)
                pending.remove(task.task_id)

    async def _execute_task(self, task: Task, run: dict) -> dict:
        """执行单个任务"""
        task.status = TaskStatus.RUNNING
        task.start_time = time.time()

        result = {"status": TaskStatus.SUCCESS, "output": None}

        try:
            # 获取执行器
            executor = self._executors.get(task.task_type)
            if executor:
                output = await executor(task)
                result["output"] = output
            else:
                result["output"] = f"Executed: {task.name}"

            task.status = TaskStatus.SUCCESS
            task.result = result["output"]

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            result["status"] = TaskStatus.FAILED
            result["error"] = str(e)

            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                self._logger.warning(f"任务重试: {task.name} ({task.retry_count}/{task.max_retries})")

        task.end_time = time.time()
        return result

    def get_status(self, run_id: str) -> dict | None:
        """获取运行状态"""
        return self._runs.get(run_id)

    def cancel(self, run_id: str) -> bool:
        """取消运行"""
        with self._lock:
            if run_id in self._runs:
                self._runs[run_id]["status"] = TaskStatus.CANCELLED
                return True
        return False

    def list_runs(
        self,
        workflow_id: str = None,
        status: TaskStatus = None,
        limit: int = 100,
    ) -> list[dict]:
        """列出运行记录"""
        with self._lock:
            runs = list(self._runs.values())

        if workflow_id:
            runs = [r for r in runs if r["workflow_id"] == workflow_id]
        if status:
            runs = [r for r in runs if r["status"] == status]

        runs.sort(key=lambda r: r["started_at"], reverse=True)
        return runs[:limit]
