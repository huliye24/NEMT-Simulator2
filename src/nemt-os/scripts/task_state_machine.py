"""
任务状态机 - Task State Machine

核心理念：
👉 先读状态 → 再行动

每次 Cursor Agent 行动前必须：
1. 读取 task_state.json 了解当前任务
2. 检查已完成任务列表避免重复
3. 按任务优先级和依赖关系执行
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 待执行
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    PAUSED = "paused"  # 暂停
    CANCELLED = "cancelled"  # 取消


class TaskPriority(str, Enum):
    """任务优先级"""

    P0 = "P0"  # 必须完成
    P1 = "P1"  # 重要
    P2 = "P2"  # 一般
    P3 = "P3"  # 可选


@dataclass
class Task:
    """单个任务"""

    id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.P2
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    failed_at: str | None = None
    depends_on: list = field(default_factory=list)
    subtasks: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    result: dict | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", "P2")),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            failed_at=data.get("failed_at"),
            depends_on=data.get("depends_on", []),
            subtasks=data.get("subtasks", []),
            notes=data.get("notes", []),
            result=data.get("result"),
        )


@dataclass
class TaskStateMachine:
    """任务状态机"""

    current_task: str = "init"
    status: TaskStatus = TaskStatus.PENDING
    task_list: list = field(default_factory=list)
    completed_tasks: list = field(default_factory=list)
    failed_tasks: list = field(default_factory=list)
    paused_tasks: list = field(default_factory=list)
    total_tasks: int = 0
    metadata: dict = field(default_factory=dict)

    def get_current_task(self) -> Task | None:
        """获取当前任务"""
        for task in self.task_list:
            if task.id == self.current_task:
                return task
        return None

    def is_task_completed(self, task_id: str) -> bool:
        """检查任务是否已完成"""
        return task_id in self.completed_tasks

    def can_start_task(self, task_id: str) -> tuple[bool, str]:
        """检查任务是否可以开始（依赖是否满足）"""
        task = self._find_task(task_id)
        if task is None:
            return False, f"任务 {task_id} 不存在"

        if task.status == TaskStatus.COMPLETED:
            return False, f"任务 {task_id} 已完成"

        if task.status == TaskStatus.IN_PROGRESS:
            return False, f"任务 {task_id} 正在执行中"

        for dep_id in task.depends_on:
            if not self.is_task_completed(dep_id):
                dep_task = self._find_task(dep_id)
                dep_name = dep_task.name if dep_task else dep_id
                return False, f"依赖任务 '{dep_name}' 未完成"

        return True, "可以开始"

    def _find_task(self, task_id: str) -> Task | None:
        """查找任务"""
        for task in self.task_list:
            if task.id == task_id:
                return task
        return None

    def to_dict(self) -> dict:
        result = asdict(self)
        result["task_list"] = [t.to_dict() if isinstance(t, Task) else t for t in self.task_list]
        result["status"] = self.status.value if isinstance(self.status, TaskStatus) else self.status
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "TaskStateMachine":
        tasks = [Task.from_dict(t) if isinstance(t, dict) else t for t in data.get("task_list", [])]
        status = TaskStatus(data.get("status", "pending"))
        return cls(
            current_task=data.get("current_task", "init"),
            status=status,
            task_list=tasks,
            completed_tasks=data.get("completed_tasks", []),
            failed_tasks=data.get("failed_tasks", []),
            paused_tasks=data.get("paused_tasks", []),
            total_tasks=data.get("total_tasks", 0),
            metadata=data.get("metadata", {}),
        )


class TaskStateManager:
    """任务状态管理器"""

    def __init__(self, state_file: str = None):
        if state_file is None:
            # 默认在项目根目录
            project_root = Path(__file__).parent.parent.parent
            state_file = project_root / "task_state.json"
        self.state_file = Path(state_file)
        self._state: TaskStateMachine | None = None

    def load(self) -> TaskStateMachine:
        """加载状态"""
        if self._state is None:
            if self.state_file.exists():
                with open(self.state_file, encoding="utf-8") as f:
                    data = json.load(f)
                self._state = TaskStateMachine.from_dict(data)
            else:
                self._state = TaskStateMachine()
        return self._state

    def save(self) -> None:
        """保存状态"""
        if self._state is not None:
            self._state.metadata["updated_at"] = datetime.now().isoformat()
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._state.to_dict(), f, ensure_ascii=False, indent=2)

    def add_task(self, task: Task) -> None:
        """添加任务"""
        state = self.load()
        # 检查是否已存在
        if not any(t.id == task.id for t in state.task_list):
            state.task_list.append(task)
            state.total_tasks = len(state.task_list)
            self.save()

    def start_task(self, task_id: str) -> tuple[bool, str]:
        """开始任务"""
        state = self.load()
        can_start, msg = state.can_start_task(task_id)

        if not can_start:
            return False, msg

        task = state._find_task(task_id)
        if task:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now().isoformat()
            state.current_task = task_id
            state.status = TaskStatus.IN_PROGRESS
            self.save()

        return True, f"任务 '{task.name}' 已开始"

    def complete_task(self, task_id: str, result: dict = None) -> None:
        """完成任务"""
        state = self.load()
        task = state._find_task(task_id)

        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            task.result = result

            if task_id not in state.completed_tasks:
                state.completed_tasks.append(task_id)

            if task_id in state.failed_tasks:
                state.failed_tasks.remove(task_id)
            if task_id in state.paused_tasks:
                state.paused_tasks.remove(task_id)

            # 找到下一个待执行任务
            self._move_to_next_task()
            self.save()

    def fail_task(self, task_id: str, error: str = "") -> None:
        """标记任务失败"""
        state = self.load()
        task = state._find_task(task_id)

        if task:
            task.status = TaskStatus.FAILED
            task.failed_at = datetime.now().isoformat()
            task.notes.append(error)

            if task_id not in state.failed_tasks:
                state.failed_tasks.append(task_id)

            state.status = TaskStatus.FAILED
            self.save()

    def pause_task(self, task_id: str) -> None:
        """暂停任务"""
        state = self.load()
        task = state._find_task(task_id)

        if task:
            task.status = TaskStatus.PAUSED
            if task_id not in state.paused_tasks:
                state.paused_tasks.append(task_id)
            self.save()

    def get_summary(self) -> dict:
        """获取状态摘要"""
        state = self.load()
        current = state.get_current_task()

        return {
            "current_task": state.current_task,
            "current_task_name": current.name if current else "N/A",
            "status": state.status.value if isinstance(state.status, TaskStatus) else state.status,
            "total_tasks": state.total_tasks,
            "completed": len(state.completed_tasks),
            "failed": len(state.failed_tasks),
            "pending": state.total_tasks - len(state.completed_tasks) - len(state.failed_tasks),
            "completed_list": state.completed_tasks,
            "failed_list": state.failed_tasks,
            "can_continue": len(state.failed_tasks) == 0 and len(state.completed_tasks) < state.total_tasks,
        }

    def _move_to_next_task(self) -> None:
        """移动到下一个待执行任务"""
        state = self.load()

        for task in state.task_list:
            if task.status == TaskStatus.PENDING:
                state.current_task = task.id
                state.status = TaskStatus.PENDING
                return

        # 所有任务完成
        state.status = TaskStatus.COMPLETED

    def print_status(self) -> str:
        """打印状态摘要"""
        summary = self.get_summary()

        lines = [
            "=" * 50,
            "[TASK STATE MACHINE]",
            "=" * 50,
            f"Current Task: {summary['current_task_name']} ({summary['current_task']})",
            f"Status: {summary['status']}",
            f"Progress: {summary['completed']}/{summary['total_tasks']}",
            "-" * 50,
            f"[OK] Completed ({len(summary['completed_list'])}): {summary['completed_list']}",
            f"[FAIL] Failed ({len(summary['failed_list'])}): {summary['failed_list']}",
            "=" * 50,
        ]

        return "\n".join(lines)


# 全局单例
_manager: TaskStateManager | None = None


def get_task_manager() -> TaskStateManager:
    """获取全局任务管理器"""
    global _manager
    if _manager is None:
        _manager = TaskStateManager()
    return _manager


def print_current_task() -> str:
    """打印当前任务（供 Cursor Agent 调用）"""
    manager = get_task_manager()
    return manager.print_status()


def must_read_state(func):
    """装饰器：强制在执行前读取状态"""

    def wrapper(*args, **kwargs):
        manager = get_task_manager()
        summary = manager.get_summary()
        print(f"\n{'='*50}")
        print("🔔 任务状态提醒 (Task State Machine)")
        print(f"{'='*50}")
        print(f"当前任务: {summary['current_task_name']} ({summary['current_task']})")
        print(f"状态: {summary['status']}")
        print(f"进度: {summary['completed']}/{summary['total_tasks']} 任务")
        if summary["completed_list"]:
            print(f"✅ 已完成: {', '.join(summary['completed_list'])}")
        if summary["failed_list"]:
            print(f"❌ 失败: {', '.join(summary['failed_list'])}")
        print(f"{'='*50}\n")
        return func(*args, **kwargs)

    return wrapper
