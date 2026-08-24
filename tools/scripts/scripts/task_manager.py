#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务状态更新工具
用于更新 tasks/星座A_回测引擎_tasks.json 中的任务状态
"""
import json
import sys
from pathlib import Path

TASKS_FILE = Path(__file__).parent.parent / "tasks" / "星座A_回测引擎_tasks.json"
BOARD_FILE = Path(__file__).parent.parent / "tasks" / "星座A_回测引擎_任务看板.md"


def load_tasks():
    """加载任务"""
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_tasks(data):
    """保存任务"""
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_task_status(task_id: int, new_status: str):
    """更新单个任务状态"""
    data = load_tasks()
    
    for phase in data['phases']:
        for task in phase['tasks']:
            if task['id'] == task_id:
                task['status'] = new_status
                save_tasks(data)
                print(f"Task {task_id} updated to: {new_status}")
                return True
    
    print(f"Task {task_id} not found")
    return False


def mark_done(task_id: int):
    """标记任务为已完成"""
    return update_task_status(task_id, "DONE")


def mark_todo(task_id: int):
    """标记任务为待做"""
    return update_task_status(task_id, "TODO")


def mark_wip(task_id: int):
    """标记任务为进行中"""
    return update_task_status(task_id, "WIP")


def mark_blocked(task_id: int):
    """标记任务为阻塞"""
    return update_task_status(task_id, "BLOCKED")


def mark_skip(task_id: int):
    """标记任务为跳过"""
    return update_task_status(task_id, "SKIP")


def show_progress():
    """显示进度"""
    data = load_tasks()
    
    total = data['total_tasks']
    completed = 0
    
    print()
    print("=" * 60)
    print("   星座 A: 可运行的多策略回测引擎 - 进度")
    print("=" * 60)
    print()
    
    for phase in data['phases']:
        phase_total = len(phase['tasks'])
        phase_done = sum(1 for t in phase['tasks'] if t['status'] == 'DONE')
        completed += phase_done
        
        pct = (phase_done / phase_total * 100) if phase_total > 0 else 0
        bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
        
        print(f"{phase['name']}:")
        print(f"  [{bar}] {phase_done}/{phase_total} ({pct:.0f}%)")
        print()
    
    total_pct = (completed / total * 100) if total > 0 else 0
    total_bar = "#" * int(total_pct / 5) + "-" * (20 - int(total_pct / 5))
    
    print("-" * 60)
    print(f"总计: [{total_bar}] {completed}/{total} ({total_pct:.1f}%)")
    print("=" * 60)
    
    return completed, total


def show_pending():
    """显示待做任务"""
    data = load_tasks()
    
    print()
    print("待做任务:")
    print("-" * 40)
    
    for phase in data['phases']:
        pending = [t for t in phase['tasks'] if t['status'] == 'TODO' and not t.get('milestone')]
        if pending:
            print(f"\n{phase['name']}:")
            for t in pending[:5]:
                print(f"  #{t['id']:3d}: {t['title']}")
            if len(pending) > 5:
                print(f"  ... 还有 {len(pending) - 5} 个")


def show_all():
    """显示所有任务"""
    data = load_tasks()
    
    for phase in data['phases']:
        print()
        print(f"=== {phase['name']} ===")
        for t in phase['tasks']:
            status_icon = {
                "TODO": "[ ]",
                "WIP": "[>]",
                "DONE": "[V]",
                "PARTIAL": "[~]",
                "BLOCKED": "[X]",
                "SKIP": "[o]"
            }.get(t['status'], "[?]")
            
            milestone_marker = " ***" if t.get('milestone') else ""
            print(f"{status_icon} #{t['id']:3d}: {t['title']}{milestone_marker}")


def batch_update(start: int, end: int, new_status: str):
    """批量更新任务状态"""
    data = load_tasks()
    updated = 0
    
    for phase in data['phases']:
        for task in phase['tasks']:
            if start <= task['id'] <= end:
                task['status'] = new_status
                updated += 1
    
    save_tasks(data)
    print(f"Updated {updated} tasks ({start}-{end}) to: {new_status}")


def main():
    if len(sys.argv) < 2:
        show_progress()
        print()
        print("用法:")
        print("  python task_manager.py progress    - 显示进度")
        print("  python task_manager.py pending     - 显示待做任务")
        print("  python task_manager.py all        - 显示所有任务")
        print("  python task_manager.py done <id>  - 标记完成")
        print("  python task_manager.py todo <id>  - 标记待做")
        print("  python task_manager.py wip <id>    - 标记进行中")
        print("  python task_manager.py batch <start> <end> <status> - 批量更新")
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "progress":
        show_progress()
    elif cmd == "pending":
        show_pending()
    elif cmd == "all":
        show_all()
    elif cmd == "done" and len(sys.argv) >= 3:
        mark_done(int(sys.argv[2]))
        show_progress()
    elif cmd == "todo" and len(sys.argv) >= 3:
        mark_todo(int(sys.argv[2]))
    elif cmd == "wip" and len(sys.argv) >= 3:
        mark_wip(int(sys.argv[2]))
    elif cmd == "blocked" and len(sys.argv) >= 3:
        mark_blocked(int(sys.argv[2]))
    elif cmd == "skip" and len(sys.argv) >= 3:
        mark_skip(int(sys.argv[2]))
    elif cmd == "batch" and len(sys.argv) >= 5:
        batch_update(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4].upper())
        show_progress()
    else:
        print("Unknown command or missing arguments")


if __name__ == "__main__":
    main()
