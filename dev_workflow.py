#!/usr/bin/env python3
"""
NEMT 开发工作流 - 本地开发，云端测试
用法:
    python dev_workflow.py sync      # 同步代码到云端
    python dev_workflow.py test      # 在云端安装依赖并启动
    python dev_workflow.py logs      # 查看云端日志
    python dev_workflow.py stop       # 停止云端服务
    python dev_workflow.py full      # 同步+测试
    python dev_workflow.py cos       # 上传到 COS
"""

import sys
import paramiko
import subprocess
import os

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
REMOTE_DIR = "/root/NEMT003"


def run_local(cmd, desc=""):
    """运行本地命令"""
    print(f"\n>>> {desc}")
    print(f"CMD: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=r"E:\NEMT Simulator")
    return result.returncode == 0


def run_ssh(cmd, desc="", timeout=30):
    """运行 SSH 命令"""
    print(f"\n>>> {desc}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=timeout)
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    output = stdout.read().decode()
    error = stderr.read().decode()
    client.close()
    if error:
        print(f"Error: {error[:200]}")
    print(output[:500] if len(output) > 500 else output)
    return output


def sync():
    """同步代码到云端"""
    print("=" * 60)
    print("  [1] Sync to Cloud")
    print("=" * 60)

    sync_script = r"E:\NEMT Simulator\cloud_dev\sync_nemt003.py"
    run_local(f'python -X utf8 "{sync_script}"', "Syncing code...")

    print("\n[OK] Code synced to /root/NEMT003")


def install():
    """在云端安装依赖"""
    print("=" * 60)
    print("  [2] Install Dependencies on Cloud")
    print("=" * 60)

    run_ssh(f"cd {REMOTE_DIR}/electron && npm install", "Installing electron deps...", timeout=120)
    run_ssh(f"cd {REMOTE_DIR}/web && npm install", "Installing web deps...", timeout=120)


def test():
    """启动云端测试"""
    print("=" * 60)
    print("  [3] Start Cloud Test")
    print("=" * 60)

    # 停止旧进程
    run_ssh("pkill -f 'npm run dev' 2>/dev/null || true")
    run_ssh("pkill -f 'vite' 2>/dev/null || true")

    # 启动 web 服务
    print("\nStarting web dev server...")
    run_ssh(
        f"cd {REMOTE_DIR}/web && nohup npm run dev > /tmp/nemt-web.log 2>&1 &",
        "Starting web..."
    )

    # 检查启动
    import time
    time.sleep(5)
    result = run_ssh("curl -s http://localhost:5173 | head -c 100", "Checking web server...")

    print(f"""
[OK] Cloud test started!

Access:
  Web:    http://42.51.42.123:5173
  SSH:    root@{HOST}

Check logs:
  ssh root@{HOST} "tail -f /tmp/nemt-web.log"
""")


def logs():
    """查看云端日志"""
    print("=" * 60)
    print("  Cloud Logs")
    print("=" * 60)
    run_ssh("tail -50 /tmp/nemt-web.log 2>/dev/null || echo 'No logs yet'")


def stop():
    """停止云端服务"""
    print("=" * 60)
    print("  Stop Cloud Services")
    print("=" * 60)
    run_ssh("pkill -f 'npm run dev' 2>/dev/null || true")
    run_ssh("pkill -f 'vite' 2>/dev/null || true")
    run_ssh("pkill -f 'node' 2>/dev/null || true")
    print("[OK] Services stopped")


def cos():
    """上传到 COS"""
    print("=" * 60)
    print("  [4] Upload to COS")
    print("=" * 60)
    cos_script = r"E:\NEMT Simulator\cos_sync.py"
    run_local(f'python "{cos_script}"', "Uploading to COS...")


def full():
    """完整流程：同步+测试"""
    sync()
    install()
    test()
    print("=" * 60)
    print("  [OK] Ready for testing!")
    print("=" * 60)
    print(f"  http://42.51.42.123:5173")


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "help"

    print("=" * 60)
    print("  NEMT Dev Workflow - Local Dev, Cloud Test")
    print("=" * 60)
    print(f"Local:   E:\\NEMT Simulator")
    print(f"Cloud:   root@{HOST}:{REMOTE_DIR}")
    print(f"Action:  {action}")
    print()

    if action == "sync":
        sync()
    elif action == "install":
        install()
    elif action == "test":
        test()
    elif action == "logs":
        logs()
    elif action == "stop":
        stop()
    elif action == "cos":
        cos()
    elif action == "full":
        full()
    else:
        print("""
Commands:
  sync    - Sync code to cloud
  install - Install dependencies on cloud
  test    - Start cloud test server
  logs    - View cloud logs
  stop    - Stop cloud services
  cos     - Upload to COS backup
  full    - Sync + Install + Test (full workflow)
        """)


if __name__ == "__main__":
    main()
