#!/usr/bin/env python3
"""
精简同步 - 只上传核心程序代码，跳过辅助/脚手架
"""

import paramiko
import os

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_DIR = r"E:\NEMT Simulator"
REMOTE_DIR = "/root/NEMT-Simulator2"

# 核心代码目录
CORE_DIRS = [
    "electron",
    "web",
    "nemt_os",
    "nemt_go",
    "backtest",
    "docker",
    "k8s",
]

# 跳过的目录
SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    ".pytest_cache", ".ruff_cache", ".idea", ".vscode",
    "dist", "build", "release",
    "Lean", "Data", "freqtrade", "vnpy", "examples",
    "docs", "build_helpers", "scripts", "cloud_dev",
    ".cursor", ".claude", "*.log", "*.pyc",
}

# 跳过的大文件扩展名
SKIP_EXT = {".zip", ".rar", ".tar", ".gz", ".mp4", ".mp3", ".exe", ".dll"}


def should_skip(path):
    """检查是否应该跳过"""
    name = os.path.basename(path)
    if name in SKIP_DIRS or name.startswith("."):
        return True
    if name.startswith("node_modules"):
        return True
    _, ext = os.path.splitext(name)
    if ext.lower() in SKIP_EXT:
        return True
    return False


def sync_dir(sftp, local_path, remote_path, total_files):
    """同步单个目录"""
    count = 0
    errors = []

    for root, dirs, files in os.walk(local_path):
        # 过滤目录
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(root, d))]

        rel_path = os.path.relpath(root, local_path)
        remote_dir = f"{remote_path}/{rel_path}" if rel_path != "." else remote_path

        try:
            sftp.stat(remote_dir)
        except:
            try:
                sftp.mkdir(remote_dir)
            except:
                pass

        for f in files:
            local_file = os.path.join(root, f)
            if should_skip(local_file):
                continue

            remote_file = f"{remote_dir}/{f}"
            try:
                sftp.put(local_file, remote_file)
                count += 1
                if count % 50 == 0:
                    print(f"  已同步 {count}/{total_files} 个文件...")
            except Exception as e:
                errors.append((local_file, str(e)))

    return count, errors


def main():
    print("=" * 70)
    print("  精简同步 - 只上传核心程序代码")
    print("=" * 70)
    print(f"源: {LOCAL_DIR}")
    print(f"目标: root@{HOST}:{REMOTE_DIR}")
    print(f"\n核心目录: {', '.join(CORE_DIRS)}")
    print()

    # 连接
    print("[1/4] 连接云服务器...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=60)
    sftp = client.open_sftp()
    print("  ✓ 连接成功")

    # 创建目标目录
    print("[2/4] 创建目录结构...")
    try:
        sftp.mkdir(REMOTE_DIR)
    except:
        pass

    for d in CORE_DIRS:
        try:
            sftp.mkdir(f"{REMOTE_DIR}/{d}")
        except:
            pass
    print("  ✓ 目录就绪")

    # 统计文件数
    print("[3/4] 扫描文件...")
    total = 0
    for d in CORE_DIRS:
        local_d = os.path.join(LOCAL_DIR, d)
        if os.path.exists(local_d):
            for root, _, files in os.walk(local_d):
                total += len([f for f in files if not should_skip(os.path.join(root, f))])
    print(f"  ✓ 共 {total} 个文件待同步")

    # 同步
    print("[4/4] 开始同步...")
    print("-" * 70)
    total_synced = 0
    all_errors = []

    for d in CORE_DIRS:
        local_d = os.path.join(LOCAL_DIR, d)
        if not os.path.exists(local_d):
            print(f"  ⚠ 跳过 {d}/ (目录不存在)")
            continue

        print(f"  → 同步 {d}/ ...")
        synced, errors = sync_dir(sftp, local_d, f"{REMOTE_DIR}/{d}", total)
        total_synced += synced
        all_errors.extend(errors)
        print(f"    ✓ {synced} 个文件")

    print("-" * 70)

    # 总结
    print(f"\n{'='*70}")
    print(f"  同步完成!")
    print(f"{'='*70}")
    print(f"  成功: {total_synced} 个文件")

    if all_errors:
        print(f"  失败: {len(all_errors)} 个文件")
        for path, err in all_errors[:5]:
            print(f"    - {path}: {err}")
    else:
        print(f"  失败: 0 个文件")

    # 下一步
    print(f"\n{'='*70}")
    print("  下一步 (在云端执行):")
    print(f"{'='*70}")
    print(f"""
  cd {REMOTE_DIR}
  cd electron && npm install && npm run dev:electron
""")

    sftp.close()
    client.close()


if __name__ == "__main__":
    main()
