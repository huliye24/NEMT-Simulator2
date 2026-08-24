#!/usr/bin/env python3
"""上传大目录"""

import paramiko
from pathlib import Path
import os

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_BASE = Path(r"E:\NEMT Simulator")
REMOTE_BASE = "/root/nemt-workspace"

# 要上传的目录
DIRS = [
    "nemt_os",
    "electron",
    "docker",
    "k8s",
    "nemt-go",
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


def upload_dir(sftp, local_dir, max_files=500):
    rel = local_dir.relative_to(LOCAL_BASE)
    remote_dir = f"{REMOTE_BASE}/{rel}"
    
    print(f"\n{'='*60}")
    print(f"目录: {rel}")
    print(f"{'='*60}")
    
    success = 0
    failed = 0
    
    for root, dirs, files in os.walk(local_dir):
        # 创建目录结构
        for d in dirs:
            local_path = Path(root) / d
            rel_path = local_path.relative_to(LOCAL_BASE)
            remote_path = f"{REMOTE_BASE}/{rel_path}"
            create_dir(sftp, remote_path)
        
        # 上传文件
        for f in files:
            local_file = Path(root) / f
            rel_path = local_file.relative_to(LOCAL_BASE)
            remote_path = f"{REMOTE_BASE}/{rel_path}"
            
            try:
                sftp.put(str(local_file), remote_path)
                success += 1
                if success % 50 == 0:
                    print(f"  已上传 {success} 个文件...")
                
                if success >= max_files:
                    print(f"  达到上限 {max_files}，停止")
                    return success, failed
                    
            except Exception as e:
                print(f"[失败] {rel_path}: {e}")
                failed += 1
    
    print(f"  小计: {success} 成功, {failed} 失败")
    return success, failed


def main():
    sftp = connect()
    print("=" * 60)
    print("  上传大型目录")
    print("=" * 60)
    
    total_success = 0
    total_failed = 0
    
    for dir_name in DIRS:
        local_dir = LOCAL_BASE / dir_name
        if not local_dir.exists():
            print(f"\n[跳过] {dir_name} (不存在)")
            continue
        
        s, f = upload_dir(sftp, local_dir)
        total_success += s
        total_failed += f
    
    print("\n" + "=" * 60)
    print(f"  总计: {total_success} 成功, {total_failed} 失败")
    print("=" * 60)
    
    sftp.close()


if __name__ == "__main__":
    main()
