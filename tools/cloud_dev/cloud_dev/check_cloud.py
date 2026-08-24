#!/usr/bin/env python3
"""检查云端文件"""

import paramiko

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    
    stdin, stdout, stderr = client.exec_command("find /root/nemt-workspace -type f | wc -l", timeout=30)
    total = int(stdout.read().decode().strip())
    
    stdin, stdout, stderr = client.exec_command("du -sh /root/nemt-workspace", timeout=30)
    size = stdout.read().decode().strip()
    
    print(f"云端文件数: {total}")
    print(f"云端大小: {size}")
    
    # 按目录统计
    stdin, stdout, stderr = client.exec_command("cd /root/nemt-workspace && for d in */; do echo \"$d: $(find \"$d\" -type f | wc -l)\"; done", timeout=30)
    print("\n目录统计:")
    print(stdout.read().decode())
    
    client.close()


if __name__ == "__main__":
    main()
