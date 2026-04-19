#!/usr/bin/env python3
"""
扫描 TASKS.md 中的任务状态
识别停滞任务并发送提醒
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path


def parse_tasks(tasks_file: str) -> list:
    """解析 TASKS.md 中的任务"""
    tasks = []
    
    if not os.path.exists(tasks_file):
        print(f"文件不存在: {tasks_file}")
        return tasks
    
    with open(tasks_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取任务列表
    task_pattern = r'\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|'
    matches = re.findall(task_pattern, content)
    
    for match in matches:
        task_id, status, last_update = match
        task_id = task_id.strip()
        status = status.strip()
        
        if task_id.startswith('TASK-') or task_id.startswith('- ['):
            tasks.append({
                'id': task_id,
                'status': status,
                'last_update': last_update.strip()
            })
    
    return tasks


def check_stalled_tasks(tasks: list, threshold_days: int = 2) -> list:
    """检查停滞任务"""
    stalled = []
    today = datetime.now()
    
    for task in tasks:
        status = task['status']
        
        # 检查进行中的任务
        if '进行中' in status or 'in_progress' in status.lower():
            # 尝试解析日期
            last_update = task['last_update']
            try:
                # 简单日期解析 (格式: YYYY-MM-DD)
                if len(last_update) >= 10:
                    update_date = datetime.strptime(last_update[:10], '%Y-%m-%d')
                    days_ago = (today - update_date).days
                    
                    if days_ago >= threshold_days:
                        stalled.append({
                            'id': task['id'],
                            'days_ago': days_ago,
                            'status': status
                        })
            except ValueError:
                pass
    
    return stalled


def generate_report(stalled_tasks: list) -> str:
    """生成报告"""
    if not stalled_tasks:
        return "✅ 没有停滞任务"
    
    report = f"⚠️ 停滞任务 ({len(stalled_tasks)} 个):\n\n"
    
    for task in stalled_tasks:
        report += f"- {task['id']}: {task['days_ago']} 天未更新\n"
    
    return report


def main():
    # 查找 TASKS.md
    possible_paths = [
        'TechLead_Resources/TASKS.md',
        'TASKS.md',
        '../TASKS.md'
    ]
    
    tasks_file = None
    for path in possible_paths:
        if os.path.exists(path):
            tasks_file = path
            break
    
    if not tasks_file:
        print("❌ 找不到 TASKS.md")
        return
    
    print(f"📋 扫描任务: {tasks_file}")
    
    # 解析任务
    tasks = parse_tasks(tasks_file)
    print(f"   找到 {len(tasks)} 个任务")
    
    # 检查停滞
    stalled = check_stalled_tasks(tasks)
    
    # 生成报告
    report = generate_report(stalled)
    print(f"\n{report}")
    
    return stalled


if __name__ == "__main__":
    main()
