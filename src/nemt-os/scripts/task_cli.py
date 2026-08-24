#!/usr/bin/env python
"""
任务状态机 CLI 工具

用法:
    python task_cli.py status          # 查看状态
    python task_cli.py add <id> <name> [desc]  # 添加任务
    python task_cli.py start <id>     # 开始任务
    python task_cli.py complete <id>   # 完成任务
    python task_cli.py fail <id>       # 标记失败
    python task_cli.py pause <id>      # 暂停任务
    python task_cli.py list            # 列出所有任务
    python task_cli.py current         # 显示当前任务
    python task_cli.py reset           # 重置状态
"""

import sys
from pathlib import Path

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nemt_os.scripts.task_state_machine import (
    Task,
    TaskPriority,
    TaskStateManager,
    TaskStatus,
    print_current_task,
)


def cmd_status():
    """显示状态"""
    print(print_current_task())


def cmd_add(task_id: str, name: str, desc: str = ""):
    """添加任务"""
    manager = TaskStateManager()
    manager.load()

    task = Task(
        id=task_id,
        name=name,
        description=desc,
        status=TaskStatus.PENDING,
        priority=TaskPriority.P2,
    )

    manager.add_task(task)
    print(f"[OK] Task added: {task_id} - {name}")


def cmd_start(task_id: str):
    """开始任务"""
    manager = TaskStateManager()
    success, msg = manager.start_task(task_id)
    if success:
        print(f"[START] {msg}")
        # 显示当前任务详情
        state = manager.load()
        current = state.get_current_task()
        if current:
            print(f"\n[INFO] Description: {current.description}")
            if current.depends_on:
                print(f"[INFO] Dependencies: {', '.join(current.depends_on)}")
    else:
        print(f"[FAIL] Cannot start: {msg}")


def cmd_complete(task_id: str):
    """完成任务"""
    manager = TaskStateManager()
    manager.complete_task(task_id)
    print(f"[OK] Task {task_id} completed!")

    # 自动显示下一个任务
    summary = manager.get_summary()
    if summary["can_continue"]:
        print(f"\n[>>] Next task: {summary['current_task']}")


def cmd_fail(task_id: str, error: str = ""):
    """标记失败"""
    manager = TaskStateManager()
    manager.fail_task(task_id, error)
    print(f"[FAIL] Task {task_id} marked as failed")


def cmd_pause(task_id: str):
    """暂停任务"""
    manager = TaskStateManager()
    manager.pause_task(task_id)
    print(f"[PAUSE] Task {task_id} paused")


def cmd_list():
    """列出所有任务"""
    manager = TaskStateManager()
    state = manager.load()

    print("\n" + "=" * 60)
    print("ALL TASKS")
    print("=" * 60)

    status_symbols = {
        TaskStatus.PENDING: ("[ ]", "pending"),
        TaskStatus.IN_PROGRESS: ("[*]", "in_progress"),
        TaskStatus.COMPLETED: ("[OK]", "completed"),
        TaskStatus.FAILED: ("[X]", "failed"),
        TaskStatus.PAUSED: ("[-]", "paused"),
    }

    for i, task in enumerate(state.task_list, 1):
        status = task.status
        if isinstance(status, str):
            status = TaskStatus(status)
        symbol, status_text = status_symbols.get(status, ("[?]", "unknown"))

        current_marker = ">> " if task.id == state.current_task else "   "

        print(f"{current_marker}{i}. [{status_text}] {task.name} ({task.id})")
        if task.description:
            print(f"      {task.description}")

    print("=" * 60)
    print(f"Total: {state.total_tasks} | Done: {len(state.completed_tasks)} | Failed: {len(state.failed_tasks)}")


def cmd_current():
    """显示当前任务"""
    manager = TaskStateManager()
    state = manager.load()
    current = state.get_current_task()

    if current:
        print("\n" + "=" * 50)
        print("CURRENT TASK")
        print("=" * 50)
        print(f"ID: {current.id}")
        print(f"Name: {current.name}")
        print(f"Description: {current.description or 'N/A'}")
        print(f"Status: {current.status.value if hasattr(current.status, 'value') else current.status}")
        print(f"Priority: {current.priority.value if hasattr(current.priority, 'value') else current.priority}")
        if current.depends_on:
            print(f"Dependencies: {', '.join(current.depends_on)}")
        print("=" * 50)
    else:
        print("[INFO] No current task")


def cmd_reset():
    """重置状态"""
    confirm = input("WARNING: Reset task state? (yes/no): ")
    if confirm.lower() == "yes":
        state_file = Path(__file__).parent.parent / "task_state.json"
        if state_file.exists():
            # 备份
            backup_file = state_file.with_suffix(".json.bak")
            state_file.rename(backup_file)
            print(f"[OK] Backup created: {backup_file}")

        # 创建新状态
        manager = TaskStateManager()
        manager.save()
        print("[OK] Task state reset")


def cmd_init(project_name: str, tasks: list):
    """初始化任务列表"""
    manager = TaskStateManager()
    state = manager.load()

    for task_data in tasks:
        task = Task(
            id=task_data["id"],
            name=task_data["name"],
            description=task_data.get("description", ""),
            priority=TaskPriority(task_data.get("priority", "P2")),
            depends_on=task_data.get("depends_on", []),
        )
        manager.add_task(task)

    # 设置第一个任务为当前
    if tasks:
        manager.start_task(tasks[0]["id"])

    print(f"[OK] Initialized {len(tasks)} tasks")
    manager.print_status()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "status":
        cmd_status()
    elif cmd == "add" and len(sys.argv) >= 4:
        cmd_add(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "start" and len(sys.argv) >= 3:
        cmd_start(sys.argv[2])
    elif cmd == "complete" and len(sys.argv) >= 3:
        cmd_complete(sys.argv[2])
    elif cmd == "fail" and len(sys.argv) >= 3:
        cmd_fail(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "pause" and len(sys.argv) >= 3:
        cmd_pause(sys.argv[2])
    elif cmd == "list":
        cmd_list()
    elif cmd == "current":
        cmd_current()
    elif cmd == "reset":
        cmd_reset()
    elif cmd == "init" and len(sys.argv) >= 3:
        # 初始化示例任务
        sample_tasks = [
            {"id": "fix_imports", "name": "修复 Python 导入路径", "priority": "P0"},
            {"id": "verify_build", "name": "验证前端构建", "priority": "P0", "depends_on": ["fix_imports"]},
            {"id": "run_tests", "name": "运行测试套件", "priority": "P1", "depends_on": ["verify_build"]},
            {"id": "update_docs", "name": "更新文档", "priority": "P2", "depends_on": ["run_tests"]},
        ]
        cmd_init(sys.argv[2], sample_tasks)
    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
