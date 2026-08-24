#!/usr/bin/env python3
"""继续上传剩余文件"""

import paramiko
from pathlib import Path
import os

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_BASE = Path(r"E:\NEMT Simulator")
REMOTE_BASE = "/root/nemt-workspace"


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


def upload_dir(sftp, local_dir, offset=0, limit=500):
    rel = local_dir.relative_to(LOCAL_BASE)
    
    print(f"\n{'='*60}")
    print(f"目录: {rel} (跳过前{offset}, 最多{limit})")
    print(f"{'='*60}")
    
    success = 0
    skipped = 0
    
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
            
            skipped += 1
            if skipped <= offset:
                continue
            
            if success >= limit:
                print(f"  达到限制 {limit}，停止")
                return success
            
            try:
                sftp.put(str(local_file), remote_path)
                success += 1
                if success % 50 == 0:
                    print(f"  已上传 {success} 个文件...")
            except Exception as e:
                print(f"[失败] {rel_path}: {e}")
    
    print(f"  完成: {success} 个文件")
    return success


def main():
    sftp = connect()
    
    # 继续上传 nemt_os 和 electron
    print("继续上传剩余文件...")
    
    # nemt_os 从501开始
    sftp.put
    
    for name, offset in [("nemt_os", 500), ("electron", 500)]:
        local_dir = LOCAL_BASE / name
        if local_dir.exists():
            uploaded = upload_dir(sftp, local_dir, offset=offset)
            print(f"  {name}: +{uploaded}")
    
    sftp.close()


if __name__ == "__main__":
    main()
