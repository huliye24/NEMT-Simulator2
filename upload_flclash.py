#!/usr/bin/env python3
"""
上传 FlClash Linux 源码到云端并编译
"""
import os
import paramiko
import zipfile
import io

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
REMOTE_DIR = "/root/FlClash"

def upload_flclash():
    local_flclash = r"E:\NEMT Simulator\FlClash"
    
    print("=== Upload FlClash to Cloud ===")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    except Exception as e:
        print(f"SSH Error: {e}")
        return
    
    sftp = client.open_sftp()
    
    # 只上传 linux 相关文件夹
    linux_folders = ["linux", "core", "lib", "services", "assets", "arb", "snapshots"]
    
    # 创建远程目录
    print(f"Creating {REMOTE_DIR}...")
    try:
        sftp.mkdir(REMOTE_DIR)
    except:
        pass
    
    for folder in linux_folders:
        local_path = os.path.join(local_flclash, folder)
        if os.path.exists(local_path):
            remote_path = f"{REMOTE_DIR}/{folder}"
            print(f"Uploading {folder}/...")
            
            # 删除旧目录
            try:
                sftp.stat(remote_path)
                sftp.rmdir(remote_path)
            except:
                pass
            
            # 上传目录内容
            upload_dir(sftp, local_path, remote_path)
    
    # 上传必要文件
    essential_files = ["pubspec.yaml", "pubspec.lock", "README_zh_CN.md"]
    for f in essential_files:
        local_f = os.path.join(local_flclash, f)
        if os.path.exists(local_f):
            print(f"Uploading {f}...")
            sftp.put(local_f, f"{REMOTE_DIR}/{f}")
    
    sftp.close()
    client.close()
    
    print("\n[OK] FlClash uploaded!")
    print(f"Location: {REMOTE_DIR}")

def upload_dir(sftp, local_dir, remote_dir):
    """递归上传目录"""
    try:
        sftp.mkdir(remote_dir)
    except:
        pass
    
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"
        
        if os.path.isdir(local_path):
            try:
                sftp.mkdir(remote_path)
            except:
                pass
            upload_dir(sftp, local_path, remote_path)
        else:
            sftp.put(local_path, remote_path)

if __name__ == "__main__":
    upload_flclash()
