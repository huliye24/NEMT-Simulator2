#!/usr/bin/env python3
"""
方法1: 压缩后上传 (推荐 - 最快)
1. 本地压缩成zip
2. 上传zip
3. 云端解压
"""

import paramiko
from pathlib import Path
import zipfile
import os
import time

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_BASE = Path(r"E:\NEMT Simulator")
REMOTE_BASE = "/root/nemt-workspace"
ZIP_FILE = r"E:\NEMT_Simulator_Full.zip"

# 跳过目录
SKIP_DIRS = {'.git', '__pycache__', '.cursor', '.venv', 'venv',
             '.pytest_cache', '.ruff_cache', 'node_modules', '.idea',
             'dist', 'build'}


def create_zip():
    """创建zip文件"""
    print("=" * 70)
    print("  步骤1: 创建压缩包")
    print("=" * 70)
    
    # 删除旧zip
    if Path(ZIP_FILE).exists():
        os.remove(ZIP_FILE)
        print("删除旧文件...")
    
    count = 0
    total_size = 0
    
    with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(LOCAL_BASE):
            # 过滤目录
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            for f in files:
                local_file = Path(root) / f
                rel_path = local_file.relative_to(LOCAL_BASE)
                
                zf.write(local_file, rel_path)
                count += 1
                total_size += local_file.stat().st_size
                
                if count % 500 == 0:
                    print(f"  已添加 {count} 个文件...")
    
    zip_size = Path(ZIP_FILE).stat().st_size
    print(f"\n压缩完成: {count} 个文件")
    print(f"压缩后大小: {zip_size / 1024 / 1024:.1f} MB")
    print(f"原始大小: {total_size / 1024 / 1024:.1f} MB")
    print(f"压缩率: {100 - zip_size * 100 / total_size:.1f}%")
    
    return ZIP_FILE


def upload_zip(zip_path):
    """上传zip文件"""
    print("\n" + "=" * 70)
    print("  步骤2: 上传压缩包")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=120)
    sftp = client.open_sftp()
    
    remote_zip = f"{REMOTE_BASE}/NEMT_Simulator_Full.zip"
    
    print(f"上传: {zip_path}")
    print("预计时间: 3-5分钟")
    
    start = time.time()
    sftp.put(zip_path, remote_zip)
    elapsed = time.time() - start
    
    sftp.close()
    client.close()
    
    print(f"上传完成! 耗时: {elapsed:.0f} 秒")
    return remote_zip


def extract_zip(remote_zip):
    """云端解压"""
    print("\n" + "=" * 70)
    print("  步骤3: 云端解压")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=120)
    
    # 解压命令
    cmd = f'cd {REMOTE_BASE} && unzip -o NEMT_Simulator_Full.zip'
    print(f"执行: {cmd}")
    
    stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if error:
        print(f"错误: {error[:500]}")
    
    print(f"解压完成!")
    
    # 验证
    stdin, stdout, stderr = client.exec_command(f'find {REMOTE_BASE} -type f | wc -l', timeout=30)
    count = int(stdout.read().decode().strip())
    print(f"云端文件总数: {count}")
    
    # 删除zip节省空间
    client.exec_command(f'rm {REMOTE_BASE}/NEMT_Simulator_Full.zip')
    
    client.close()


def main():
    start = time.time()
    
    # 1. 压缩
    zip_path = create_zip()
    
    # 2. 上传
    remote_zip = upload_zip(zip_path)
    
    # 3. 解压
    extract_zip(remote_zip)
    
    elapsed = time.time() - start
    
    print("\n" + "=" * 70)
    print("  全部完成!")
    print(f"  总耗时: {elapsed / 60:.1f} 分钟")
    print(f"  位置: {REMOTE_BASE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
