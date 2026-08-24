#!/usr/bin/env python3
"""同步到 NEMT003 (空白项目)"""

import paramiko
import os

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_DIR = r"E:\NEMT Simulator"
REMOTE_DIR = "/root/NEMT003"

CORE_DIRS = ["electron", "web", "nemt_os", "nemt_go", "backtest", "docker", "k8s"]

SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    ".pytest_cache", ".ruff_cache", ".idea", ".vscode",
    "dist", "build", "release",
    "Lean", "Data", "freqtrade", "vnpy", "examples",
    "docs", "build_helpers", "scripts", "cloud_dev",
    ".cursor", ".claude", "*.log", "*.pyc",
}


def should_skip(path):
    name = os.path.basename(path)
    if name in SKIP_DIRS or name.startswith("."):
        return True
    if name.startswith("node_modules"):
        return True
    _, ext = os.path.splitext(name)
    if ext.lower() in {".zip", ".rar", ".tar", ".gz", ".mp4", ".mp3", ".exe", ".dll"}:
        return True
    return False


def main():
    print("=" * 70)
    print("  Sync to NEMT003")
    print("=" * 70)
    print(f"Local:  {LOCAL_DIR}")
    print(f"Remote: root@{HOST}:{REMOTE_DIR}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=60)
    sftp = client.open_sftp()

    # 创建目录
    for d in CORE_DIRS:
        try:
            sftp.mkdir(f"{REMOTE_DIR}/{d}")
        except:
            pass

    # 同步
    total_synced = 0
    for d in CORE_DIRS:
        local_d = os.path.join(LOCAL_DIR, d)
        if not os.path.exists(local_d):
            print(f"  [SKIP] {d}/ (not found)")
            continue

        count = 0
        for root, dirs, files in os.walk(local_d):
            dirs[:] = [dd for dd in dirs if not should_skip(os.path.join(root, dd))]
            rel_path = os.path.relpath(root, local_d)
            remote_dir = f"{REMOTE_DIR}/{d}/{rel_path}" if rel_path != "." else f"{REMOTE_DIR}/{d}"

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
                try:
                    remote_file = f"{remote_dir}/{f}"
                    sftp.put(local_file, remote_file)
                    count += 1
                except:
                    pass

        print(f"  [OK] {d}/ - {count} files")
        total_synced += count

    print(f"\nTotal: {total_synced} files synced")

    sftp.close()
    client.close()


if __name__ == "__main__":
    main()
