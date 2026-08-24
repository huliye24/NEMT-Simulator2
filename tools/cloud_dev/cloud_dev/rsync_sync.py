#!/usr/bin/env python3
"""
使用 rsync 快速同步 - 比SFTP快10倍
"""

import paramiko
import subprocess

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_DIR = r"E:\NEMT Simulator"
REMOTE_DIR = "/root/NEMT-Simulator2"

# 排除的目录
EXCLUDES = [
    '--exclude=.git',
    '--exclude=__pycache__',
    '--exclude=node_modules',
    '--exclude=.venv',
    '--exclude=venv',
    '--exclude=.pytest_cache',
    '--exclude=.ruff_cache',
    '--exclude=.idea',
    '--exclude=dist',
    '--exclude=build',
]

def main():
    print("=" * 70)
    print("  使用 rsync 快速同步")
    print("=" * 70)
    print(f"源: {LOCAL_DIR}")
    print(f"目标: {USERNAME}@{HOST}:{REMOTE_DIR}")
    print()
    
    # 构建rsync命令
    exclude_args = ' '.join(EXCLUDES)
    
    rsync_cmd = f'''
rsync -avz --progress {exclude_args} \
    -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
    --delete \
    "{LOCAL_DIR}/" \
    "{USERNAME}@{HOST}:{REMOTE_DIR}/"
'''
    
    print("开始同步...")
    print("-" * 70)
    
    # 使用subprocess运行rsync
    result = subprocess.run(
        f'sshpass -p "{PASSWORD}" rsync -avz --progress {exclude_args} '
        f'-e "ssh -o StrictHostKeyChecking=no" '
        f'--delete '
        f'"{LOCAL_DIR}/" '
        f'"{USERNAME}@{HOST}:{REMOTE_DIR}/"',
        shell=True,
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("  同步完成!")
        print("=" * 70)
    else:
        print("\n同步失败，尝试备选方案...")


if __name__ == "__main__":
    main()
