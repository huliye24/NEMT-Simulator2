#!/usr/bin/env python3
"""
Notion 同步服务的 Git 自动备份
================================
定期将 Obsidian 内容自动提交到 Git

使用方法:
    python git_backup.py --backup          # 立即备份
    python git_backup.py --setup          # 初始化 Git 并配置 cron
    python git_backup.py --status         # 查看备份状态
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# 配置
OBSIDIAN_ROOT = "/root/obsidian_vault"
GIT_DIR = "/root/obsidian_vault/.git"
STATE_FILE = "/root/quant-sync-server/backup_state.json"
REMOTE_URL = ""  # 可选: 设置你的 Git 远程仓库

BACKUP_CONFIG = {
    "auto_backup": True,
    "backup_interval_hours": 6,
    "commit_prefix": "📝 Sync",
    "ignore_patterns": [
        ".obsidian/plugins",
        ".obsidian/workspace",
        "__pycache__",
        "*.pyc",
        ".DS_Store",
        "node_modules",
    ]
}

def run_cmd(cmd: list) -> tuple:
    """执行命令"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=OBSIDIAN_ROOT,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"last_backup": None, "backup_count": 0, "commits": []}

def save_state(state: dict):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def check_git() -> bool:
    """检查是否为 Git 仓库"""
    return os.path.exists(GIT_DIR)

def init_git():
    """初始化 Git 仓库"""
    if check_git():
        print("Git 仓库已存在")
        return True
    
    print("初始化 Git 仓库...")
    
    # 创建 .gitignore
    gitignore_path = os.path.join(OBSIDIAN_ROOT, ".gitignore")
    with open(gitignore_path, 'w') as f:
        f.write("# Obsidian\n")
        f.write(".obsidian/plugins/*\n")
        f.write("!.obsidian/plugins/community-plugins.json\n")
        f.write(".obsidian/workspace.json\n")
        f.write(".obsidian/workspace-mobile.json\n")
        f.write("\n# Python\n")
        f.write("__pycache__\n")
        f.write("*.pyc\n")
        f.write("\n# System\n")
        f.write(".DS_Store\n")
        f.write("Thumbs.db\n")
        f.write("\n# IDE\n")
        f.write(".idea/\n")
        f.write("*.swp\n")
        f.write("\n# Node\n")
        f.write("node_modules/\n")
    
    # 初始化
    code, out, err = run_cmd(["git", "init"])
    if code != 0:
        print(f"git init 失败: {err}")
        return False
    
    # 配置
    run_cmd(["git", "config", "user.email", "noreply@nemt.local"])
    run_cmd(["git", "config", "user.name", "NEMT Sync Bot"])
    
    print("Git 仓库初始化完成")
    return True

def get_changes() -> list:
    """获取变更文件"""
    code, out, err = run_cmd(["git", "status", "--porcelain"])
    if code != 0:
        return []
    
    changes = []
    for line in out.strip().split("\n"):
        if line:
            # 格式: XY filename
            status = line[:2].strip()
            filename = line[3:].strip()
            changes.append({"status": status, "file": filename})
    return changes

def backup() -> dict:
    """执行备份"""
    state = load_state()
    result = {
        "success": False,
        "changes": 0,
        "message": ""
    }
    
    if not check_git():
        if not init_git():
            result["message"] = "Git 初始化失败"
            return result
    
    # 添加所有变更
    code, out, err = run_cmd(["git", "add", "-A"])
    if code != 0:
        result["message"] = f"git add 失败: {err}"
        return result
    
    # 检查变更
    changes = get_changes()
    result["changes"] = len(changes)
    
    if len(changes) == 0:
        result["success"] = True
        result["message"] = "无变更，跳过"
        return result
    
    # 提交
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"📝 Sync {timestamp}\n\n"
    commit_msg += f"变更文件 ({len(changes)}):\n"
    for c in changes[:10]:
        commit_msg += f"- [{c['status']}] {c['file']}\n"
    if len(changes) > 10:
        commit_msg += f"- ... 还有 {len(changes) - 10} 个文件\n"
    
    code, out, err = run_cmd(["git", "commit", "-m", commit_msg])
    if code != 0:
        result["message"] = f"git commit 失败: {err}"
        return result
    
    # 更新状态
    state["last_backup"] = datetime.now().isoformat()
    state["backup_count"] += 1
    state["commits"].append({
        "time": state["last_backup"],
        "changes": len(changes)
    })
    # 只保留最近 100 条记录
    state["commits"] = state["commits"][-100:]
    save_state(state)
    
    result["success"] = True
    result["message"] = f"已提交 {len(changes)} 个变更"
    return result

def push(remote: str = "origin", branch: str = "main"):
    """推送到远程"""
    if not REMOTE_URL and not remote:
        print("未配置远程仓库")
        return
    
    if REMOTE_URL:
        # 检查 remote 是否已添加
        code, out, err = run_cmd(["git", "remote", "get-url", remote])
        if code != 0:
            run_cmd(["git", "remote", "add", remote, REMOTE_URL])
            print(f"已添加远程: {remote} -> {REMOTE_URL}")
    
    code, out, err = run_cmd(["git", "push", remote, branch, "--force"])
    if code == 0:
        print(f"已推送到 {remote}/{branch}")
    else:
        print(f"推送失败: {err}")

def setup_cron():
    """配置 cron 自动备份"""
    cron_entry = f"0 */{BACKUP_CONFIG['backup_interval_hours']} * * * cd {OBSIDIAN_ROOT} && /usr/bin/python3 /root/quant-sync-server/git_backup.py --backup >> /root/quant-sync-server/backup_cron.log 2>&1\n"
    
    # 读取现有 crontab
    code, out, err = run_cmd(["crontab", "-l"])
    existing = out if code == 0 else ""
    
    # 检查是否已存在
    if "git_backup.py" in existing:
        print("Cron 任务已配置")
        return
    
    # 添加新任务
    new_crontab = existing + "\n" + cron_entry
    
    proc = subprocess.Popen(
        ["crontab", "-"],
        stdin=subprocess.PIPE,
        text=True
    )
    proc.communicate(input=new_crontab)
    
    print(f"Cron 任务已配置: 每 {BACKUP_CONFIG['backup_interval_hours']} 小时自动备份")

def status():
    """查看备份状态"""
    state = load_state()
    
    print(f"\n{'='*60}")
    print(f"Git 备份状态")
    print(f"{'='*60}")
    print(f"仓库: {OBSIDIAN_ROOT}")
    print(f"Git: {'已初始化' if check_git() else '未初始化'}")
    
    if state.get("last_backup"):
        print(f"最后备份: {state['last_backup']}")
    print(f"备份次数: {state.get('backup_count', 0)}")
    
    changes = get_changes()
    print(f"待提交变更: {len(changes)} 个文件")
    
    for c in changes[:5]:
        print(f"  [{c['status']}] {c['file']}")
    if len(changes) > 5:
        print(f"  ... 还有 {len(changes) - 5} 个")
    
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description="Git 自动备份")
    parser.add_argument("--backup", action="store_true", help="立即备份")
    parser.add_argument("--push", action="store_true", help="推送到远程")
    parser.add_argument("--setup", action="store_true", help="初始化并配置 cron")
    parser.add_argument("--status", action="store_true", help="查看状态")
    
    args = parser.parse_args()
    
    if args.setup:
        init_git()
        setup_cron()
        status()
    elif args.backup:
        result = backup()
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    elif args.push:
        push()
    elif args.status:
        status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
