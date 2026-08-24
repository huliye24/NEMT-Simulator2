#!/usr/bin/env python3
"""带进度条的批量上传工具"""

import paramiko
from pathlib import Path
import os
import time

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


def upload_file(sftp, local_file, remote_path):
    """上传单个文件"""
    try:
        create_dir(sftp, os.path.dirname(remote_path))
        sftp.put(str(local_file), remote_path)
        return True
    except Exception as e:
        return str(e)


def get_all_files():
    """获取所有文件列表"""
    all_files = []
    
    for root, dirs, files in os.walk(LOCAL_BASE):
        # 跳过目录
        dirs[:] = [d for d in dirs if d not in [
            '.git', '__pycache__', '.cursor', '.venv', 'venv',
            '.pytest_cache', '.ruff_cache', 'node_modules', '.idea',
            'dist', 'build', '.gitignore'
        ]]
        
        for f in files:
            local_file = Path(root) / f
            rel_path = local_file.relative_to(LOCAL_BASE)
            all_files.append({
                'local': local_file,
                'remote': f"{REMOTE_BASE}/{rel_path}",
                'size': local_file.stat().st_size
            })
    
    return all_files


def upload_batch(files, start_idx, batch_size):
    """上传一批文件"""
    sftp = connect()
    
    success = 0
    failed = 0
    total_size = 0
    
    for i in range(start_idx, min(start_idx + batch_size, len(files))):
        file_info = files[i]
        result = upload_file(sftp, file_info['local'], file_info['remote'])
        
        if result is True:
            success += 1
            total_size += file_info['size']
        else:
            failed += 1
    
    sftp.close()
    return success, failed, total_size


def show_progress_bar(current, total, bar_width=40):
    """显示进度条"""
    progress = current / total if total > 0 else 0
    filled = int(bar_width * progress)
    bar = '#' * filled + '-' * (bar_width - filled)
    
    pct = progress * 100
    return f"[{bar}] {pct:.1f}% ({current}/{total})"


def main():
    print("=" * 70)
    print("  完整上传工具 - 带进度显示")
    print("=" * 70)
    
    # 先获取所有文件
    print("\n[1/3] 扫描文件...")
    all_files = get_all_files()
    total_files = len(all_files)
    total_size = sum(f['size'] for f in all_files)
    
    print(f"  发现 {total_files} 个文件")
    print(f"  总大小: {total_size / 1024 / 1024:.1f} MB")
    
    # 确认
    print("\n[2/3] 开始上传...")
    print("=" * 70)
    
    BATCH_SIZE = 50  # 每批50个
    start_time = time.time()
    uploaded = 0
    
    while uploaded < total_files:
        remaining = total_files - uploaded
        batch = min(BATCH_SIZE, remaining)
        
        # 上传这批
        success, failed, size = upload_batch(all_files, uploaded, batch)
        
        uploaded += success
        elapsed = time.time() - start_time
        speed = uploaded / elapsed if elapsed > 0 else 0
        eta = (remaining / speed) if speed > 0 else 0
        
        # 显示进度
        bar = show_progress_bar(uploaded, total_files)
        print(f"\r{bar} | 速度: {speed:.1f}/s | 剩余: {eta:.0f}s    ", end='', flush=True)
        
        if failed > 0:
            print(f"\n  失败: {failed} 个")
    
    elapsed = time.time() - start_time
    print(f"\n\n" + "=" * 70)
    print(f"  上传完成!")
    print(f"  总文件: {total_files}")
    print(f"  总大小: {total_size / 1024 / 1024:.1f} MB")
    print(f"  耗时: {elapsed:.0f} 秒")
    print(f"  速度: {total_files / elapsed:.1f} 文件/秒")
    print(f"  位置: {REMOTE_BASE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
