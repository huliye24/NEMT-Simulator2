#!/usr/bin/env python3
"""同步本地项目到云端"""

import paramiko
import os
import time
from pathlib import Path

# 配置
HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_PATH = r"E:\NEMT Simulator"
REMOTE_PATH = "/root/nemt-workspace"

# 排除的文件/文件夹
EXCLUDE = [
    ".git",
    "__pycache__",
    "node_modules",
    ".cursor",
    ".venv",
    "venv",
    "*.pyc",
    ".env",
    ".idea",
    "*.log",
    "dist",
    "build",
    ".gitignore",
]

def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    return client


def create_remote_dir(sftp, remote_path):
    """递归创建远程目录"""
    dirs_to_create = []
    current = remote_path
    
    while current and current != "/":
        try:
            sftp.stat(current)
            break
        except:
            dirs_to_create.insert(0, current)
            current = os.path.dirname(current)
    
    for d in dirs_to_create:
        try:
            sftp.mkdir(d)
            print(f"  创建目录: {d}")
        except:
            pass


def should_exclude(path):
    """检查是否应该排除"""
    name = os.path.basename(path)
    for ex in EXCLUDE:
        if ex.startswith("*"):
            if name.endswith(ex[1:]):
                return True
        elif name == ex or f"/{ex}" in path or f"\\{ex}" in path:
            return True
    return False


def sync_file(sftp, local_path, remote_path):
    """同步单个文件"""
    try:
        # 确保远程目录存在
        remote_dir = os.path.dirname(remote_path)
        create_remote_dir(sftp, remote_dir)
        
        # 上传文件
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"  错误: {e}")
        return False


def sync_folder(sftp, local_path, remote_path):
    """同步文件夹"""
    count = 0
    errors = []
    
    create_remote_dir(sftp, remote_path)
    
    for root, dirs, files in os.walk(local_path):
        # 检查是否应该排除这个目录
        if should_exclude(root):
            continue
        
        # 过滤子目录
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
        
        for file in files:
            local_file = os.path.join(root, file)
            
            if should_exclude(local_file):
                continue
            
            # 计算相对路径
            rel_path = os.path.relpath(local_file, local_path)
            remote_file = os.path.join(remote_path, rel_path).replace("\\", "/")
            
            try:
                sync_file(sftp, local_file, remote_file)
                count += 1
                if count % 50 == 0:
                    print(f"  已上传 {count} 个文件...")
            except Exception as e:
                errors.append((local_file, str(e)))
    
    return count, errors


def main():
    print("=" * 60)
    print("  同步本地项目到云端")
    print("=" * 60)
    print(f"\n源: {LOCAL_PATH}")
    print(f"目标: {REMOTE_PATH}")
    print()
    
    # 连接
    print("[1/3] 连接服务器...")
    client = ssh_connect()
    sftp = client.open_sftp()
    print("  已连接")
    
    # 创建远程目录
    print("\n[2/3] 创建远程目录...")
    create_remote_dir(sftp, REMOTE_PATH)
    
    # 同步文件
    print("\n[3/3] 同步文件...")
    start_time = time.time()
    count, errors = sync_folder(sftp, LOCAL_PATH, REMOTE_PATH)
    elapsed = time.time() - start_time
    
    print(f"\n{'=' * 60}")
    print(f"  同步完成!")
    print(f"  上传文件: {count}")
    print(f"  耗时: {elapsed:.1f}秒")
    print(f"  位置: {REMOTE_PATH}")
    
    if errors:
        print(f"\n  失败: {len(errors)}")
        for path, err in errors[:5]:
            print(f"    - {path}: {err}")
    else:
        print("  全部成功!")
    
    print("=" * 60)
    
    client.close()


if __name__ == "__main__":
    main()
