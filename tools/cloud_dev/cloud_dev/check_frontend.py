#!/usr/bin/env python3
"""检查前端项目"""

import sys
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


def run_command(client, cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='ignore')


def main():
    try:
        client = ssh_connect()

        print("检查前端项目...")
        print("=" * 60)

        # 查找前端项目目录
        dirs = [
            "/root", "/opt", "/home", "/workspace", "/home/nemt",
            "/root/dev", "/root/projects", "/root/app"
        ]

        for d in dirs:
            output = run_command(client, f"ls -la {d} 2>/dev/null | head -20")
            if output and len(output) > 50:
                print(f"\n{d}:")
                print(output[:500])

        # 查找package.json
        print("\n" + "=" * 60)
        print("查找 package.json...")
        output = run_command(client, "find / -name 'package.json' -type f 2>/dev/null | head -20")
        print(output if output else "未找到")

        # 检查npm/node
        print("\n" + "=" * 60)
        print("Node.js环境:")
        output = run_command(client, "node --version && npm --version")
        print(output)

        # 检查正在运行的Node进程
        print("\n正在运行的Node进程:")
        output = run_command(client, "ps aux | grep -E 'node|npm' | grep -v grep")
        print(output if output else "无")

        client.close()

    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
