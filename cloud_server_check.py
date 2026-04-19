#!/usr/bin/env python3
"""
云服务器状态检查和修复
"""

import paramiko
import os
import time

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
KEY_PATH = os.path.join(os.path.dirname(__file__), "ssh_key_nemt")

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client.connect(HOST, port=PORT, username=USERNAME, pkey=private_key, timeout=60)
    return client

def run_command(client, command, timeout=120):
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def main():
    print("="*60)
    print("云服务器状态检查")
    print("="*60)
    
    try:
        client = create_ssh_client()
        print("SSH连接成功!")
        
        # 1. 杀掉apt进程
        print("\n1. 清理apt进程...")
        run_command(client, "pkill -9 apt; pkill -9 dpkg; rm -f /var/lib/dpkg/lock-frontend /var/lib/apt/lists/lock /var/cache/apt/archives/lock; dpkg --configure -a")
        
        # 等待一下
        time.sleep(2)
        
        # 2. 更新apt
        print("\n2. 更新apt...")
        output, error = run_command(client, "apt-get update", timeout=180)
        if error:
            print(f"  错误: {error[:200]}")
        else:
            print("  apt更新完成")
        
        # 3. 安装pip
        print("\n3. 安装pip...")
        output, error = run_command(client, "apt-get install -y python3-pip", timeout=180)
        if error:
            print(f"  错误: {error[:200]}")
        else:
            print("  pip安装完成")
        
        # 4. 检查pip
        output, _ = run_command(client, "pip3 --version")
        print(f"  pip版本: {output.strip()}")
        
        # 5. 安装必要包
        print("\n4. 安装Python基础包...")
        packages = ["notion-client", "requests", "psutil"]
        for pkg in packages:
            output, error = run_command(client, f"pip3 install {pkg}", timeout=120)
            if error and "already" not in error.lower():
                print(f"    {pkg}: 警告 - {error[:50]}")
            else:
                print(f"    {pkg}: OK")
        
        # 6. 安装数据科学包
        print("\n5. 安装数据科学包...")
        science_packages = ["numpy", "pandas", "scipy", "matplotlib"]
        for pkg in science_packages:
            print(f"    安装 {pkg}...")
            output, error = run_command(client, f"pip3 install {pkg}", timeout=300)
        
        # 7. 安装Node.js
        print("\n6. 安装Node.js...")
        output, error = run_command(client, "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -", timeout=120)
        output, error = run_command(client, "apt-get install -y nodejs", timeout=180)
        
        # 8. 最终验证
        print("\n" + "="*60)
        print("最终环境状态:")
        print("="*60)
        
        checks = [
            ("系统", "uname -a"),
            ("CPU", "nproc"),
            ("内存", "free -h"),
            ("Python", "python3 --version"),
            ("pip", "pip3 --version"),
            ("Node.js", "node --version"),
            ("npm", "npm --version"),
            ("Git", "git --version"),
        ]
        
        for name, cmd in checks:
            output, _ = run_command(client, cmd)
            print(f"  {name}: {output.strip()}")
        
        # 9. 创建工作目录
        print("\n7. 创建工作目录...")
        run_command(client, "mkdir -p /root/nemt_workspace/{code,data,logs,backups}")
        run_command(client, "mkdir -p /root/obsidian_vault/{Decision_Records,Strategy_Notes}")
        print("  工作目录创建完成")
        
        # 10. 检查numpy
        print("\n8. 检查NumPy...")
        output, _ = run_command(client, "python3 -c 'import numpy; print(numpy.__version__)'")
        print(f"  NumPy版本: {output.strip()}")
        
        client.close()
        print("\n" + "="*60)
        print("状态检查完成!")
        print("="*60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
