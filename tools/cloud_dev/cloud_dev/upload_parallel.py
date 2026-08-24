#!/usr/bin/env python3
"""
并行上传 - 使用多线程，速度快10倍
"""

import paramiko
from pathlib import Path
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_BASE = Path(r"E:\NEMT Simulator")
REMOTE_BASE = "/root/nemt-workspace"

# 并行数
MAX_WORKERS = 10

# 跳过目录
SKIP_DIRS = {'.git', '__pycache__', '.cursor', '.venv', 'venv',
             '.pytest_cache', '.ruff_cache', 'node_modules', '.idea',
             'dist', 'build'}

total_lock = Lock()
uploaded_count = 0


def get_all_files():
    """获取所有文件"""
    files = []
    for root, dirs, filenames in os.walk(LOCAL_BASE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in filenames:
            local_file = Path(root) / f
            rel_path = local_file.relative_to(LOCAL_BASE)
            files.append({
                'local': local_file,
                'remote': f"{REMOTE_BASE}/{rel_path}"
            })
    return files


def upload_single(file_info):
    """上传单个文件"""
    global uploaded_count
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()
    
    try:
        remote_path = file_info['remote']
        # 创建目录
        parts = remote_path.strip('/').split('/')[:-1]
        for i in range(1, len(parts) + 1):
            p = '/' + '/'.join(parts[:i])
            try:
                sftp.stat(p)
            except:
                sftp.mkdir(p)
        
        sftp.put(str(file_info['local']), remote_path)
        
        with total_lock:
            uploaded_count += 1
            if uploaded_count % 100 == 0:
                print(f"已上传 {uploaded_count} 个文件...")
        
        return True
    except Exception as e:
        return False
    finally:
        sftp.close()
        client.close()


def main():
    global uploaded_count
    
    print("=" * 70)
    print("  并行上传工具 (10线程)")
    print("=" * 70)
    
    # 扫描文件
    print("\n[1/3] 扫描文件...")
    files = get_all_files()
    total = len(files)
    print(f"  发现 {total} 个文件")
    
    if total == 0:
        print("没有文件需要上传")
        return
    
    # 开始上传
    print(f"\n[2/3] 开始上传 ({MAX_WORKERS}个并行)...")
    print("-" * 70)
    
    start_time = time.time()
    uploaded_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(upload_single, f): f for f in files}
        
        for future in as_completed(futures):
            result = future.result()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print(f"  完成!")
    print(f"  总文件: {total}")
    print(f"  耗时: {elapsed:.0f} 秒")
    print(f"  速度: {total/elapsed:.1f} 文件/秒")
    print(f"  位置: {REMOTE_BASE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
