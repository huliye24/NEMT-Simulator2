#!/usr/bin/env python3
"""完整上传所有文件 - 不遗漏"""

import paramiko
from pathlib import Path
import os

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_BASE = Path(r"E:\NEMT Simulator")
REMOTE_BASE = "/root/nemt-workspace"

# 所有要上传的目录和文件
DIRS_TO_UPLOAD = [
    "Lean",
    "freqtrade",
    "TradingAgents",
    "nautilus_AItrader",
    "spec-kit-cn",
    "pm-skills",
    "vnpy",
    "web",
    "NEMT-Simulator2",
    "quant-sync-server",
    "notion_sync",
    "direction_4_verification",
    "project",
    "scripts",
    "tasks",
    "NEMT_Agent_System",
    "NEMT_Notion",
    "NEMT_Vision",
    "tests",
    "cloud_memory",
    "AI-Product-Development-Toolkit",
    "matlab",
    "11_SWITCHBOARD_LEARNING",
    "NEMT-Simulator2.zip",
    "examples",
    "website",
    "nemt-core",
    "NEMT_Notion",
    "scripts",
]


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    return client.open_sftp()


def create_dir(sftp, path):
    parts = path.strip('/').split('/')
    for i in range(1, len(parts) + 1):
        p = '/' + '/'.join(parts[:i])
        try:
            sftp.stat(p)
        except:
            sftp.mkdir(p)


def upload_all_dirs():
    sftp = connect()
    
    print("=" * 70)
    print("  完整上传所有目录")
    print("=" * 70)
    
    total_files = 0
    total_size = 0
    
    for dir_name in DIRS_TO_UPLOAD:
        local_dir = LOCAL_BASE / dir_name
        
        if not local_dir.exists():
            # 尝试查找可能的变体
            found = False
            for item in LOCAL_BASE.iterdir():
                if item.is_dir() and (dir_name.lower() in item.name.lower() or item.name.lower() in dir_name.lower()):
                    local_dir = item
                    dir_name = item.name
                    found = True
                    break
            if not found:
                print(f"[跳过] {dir_name} (不存在)")
                continue
        
        print(f"\n{'='*70}")
        print(f"上传: {dir_name}")
        print(f"{'='*70}")
        
        success = 0
        skipped = 0
        
        for root, dirs, files in os.walk(local_dir):
            # 创建所有子目录
            for d in dirs:
                local_path = Path(root) / d
                rel_path = local_path.relative_to(LOCAL_BASE)
                remote_path = f"{REMOTE_BASE}/{rel_path}"
                create_dir(sftp, remote_path)
            
            # 上传所有文件
            for f in files:
                local_file = Path(root) / f
                rel_path = local_file.relative_to(LOCAL_BASE)
                remote_path = f"{REMOTE_BASE}/{rel_path}"
                
                # 获取文件大小
                size = local_file.stat().st_size
                total_size += size
                
                try:
                    sftp.put(str(local_file), remote_path)
                    success += 1
                    total_files += 1
                    
                    if success % 100 == 0:
                        print(f"  已上传 {success} 个文件 ({total_size//1024//1024}MB)...")
                        
                except Exception as e:
                    print(f"  [失败] {rel_path}: {e}")
        
        print(f"  完成: {success} 个文件")
    
    # 上传根目录所有剩余文件
    print(f"\n{'='*70}")
    print("上传根目录剩余文件")
    print(f"{'='*70}")
    
    for item in LOCAL_BASE.iterdir():
        if item.is_file():
            rel_path = item.name
            remote_path = f"{REMOTE_BASE}/{rel_path}"
            
            try:
                sftp.put(str(item), remote_path)
                total_files += 1
                print(f"[OK] {rel_path}")
            except Exception as e:
                print(f"[失败] {rel_path}: {e}")
    
    print(f"\n{'='*70}")
    print(f"  上传完成!")
    print(f"  总文件数: {total_files}")
    print(f"  总大小: {total_size//1024//1024}MB")
    print(f"  位置: {REMOTE_BASE}")
    print(f"{'='*70}")
    
    sftp.close()


if __name__ == "__main__":
    upload_all_dirs()
