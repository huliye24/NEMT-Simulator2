#!/usr/bin/env python3
"""检查AI工具安装状态"""

import paramiko

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"


def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    return client


def run_command(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='ignore')


def main():
    client = ssh_connect()
    print("检查AI工具安装状态...")
    print("=" * 50)

    # 检查文件
    files = ["/root/ai.py", "/root/code.py"]
    for f in files:
        result = run_command(client, f"ls -la {f} 2>/dev/null")
        if result:
            print(f"[OK] {f} 已安装")
        else:
            print(f"[X] {f} 未安装")

    # 检查快捷命令
    result = run_command(client, "grep -c 'nemt-help' /root/.bashrc")
    if result.strip() == "1":
        print("[OK] 快捷命令已配置")

    # Python版本
    result = run_command(client, "python3 --version")
    print(f"\nPython: {result.strip()}")

    # requests库
    result = run_command(client, "python3 -c 'import requests; print(requests.__version__)'")
    print(f"requests: {result.strip()}")

    print("=" * 50)
    client.close()

if __name__ == "__main__":
    main()
