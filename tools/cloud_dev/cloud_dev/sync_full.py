#!/usr/bin/env python3
"""直接同步整个项目目录"""

import paramiko
from pathlib import Path
import os

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_DIR = r"E:\NEMT Simulator"
REMOTE_DIR = "/root/NEMT-Simulator2"


def main():
    print("=" * 70)
    print("  完整同步项目到云端")
    print("=" * 70)
    print(f"源: {LOCAL_DIR}")
    print(f"目标: root@42.51.42.123:{REMOTE_DIR}")
    print()
    
    # 连接
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=60)
    sftp = client.open_sftp()
    
    # 创建目标目录
    try:
        sftp.mkdir(REMOTE_DIR)
    except:
        pass
    
    def upload_tree(local_path, remote_path):
        """递归上传目录"""
        count = 0
        
        for item in sorted(os.listdir(local_path)):
            # 跳过这些
            if item in ['.git', '__pycache__', '.cursor', '.venv', 'venv', 
                       '.pytest_cache', '.ruff_cache', 'node_modules', '.idea',
                       'dist', 'build']:
                continue
            
            local_item = os.path.join(local_path, item)
            remote_item = f"{remote_path}/{item}"
            
            if os.path.isdir(local_item):
                try:
                    sftp.mkdir(remote_item)
                except:
                    pass
                count += upload_tree(local_item, remote_item)
            else:
                try:
                    sftp.put(local_item, remote_item)
                    count += 1
                    if count % 200 == 0:
                        print(f"  已上传 {count} 个文件...")
                except Exception as e:
                    print(f"  失败: {item} - {e}")
        
        return count
    
    print("开始上传...")
    count = upload_tree(LOCAL_DIR, REMOTE_DIR)
    
    print()
    print("=" * 70)
    print(f"  完成! 共上传 {count} 个文件")
    print(f"  位置: {REMOTE_DIR}")
    print("=" * 70)
    
    sftp.close()
    client.close()


if __name__ == "__main__":
    main()
