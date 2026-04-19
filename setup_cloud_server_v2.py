#!/usr/bin/env python3
"""
支线1补全：安装pip和依赖包
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
    client.connect(HOST, port=PORT, username=USERNAME, pkey=private_key, timeout=30)
    return client

def run_command(client, command):
    stdin, stdout, stderr = client.exec_command(command, timeout=300)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def main():
    print("等待apt锁释放...")
    
    try:
        client = create_ssh_client()
        print("连接成功!")
        
        # 等待apt锁
        print("检查apt锁...")
        for i in range(30):
            output, _ = run_command(client, "pgrep apt")
            if not output.strip():
                print("apt锁已释放")
                break
            print(f"  等待... ({i+1}/30)")
            time.sleep(2)
        
        # 1. 安装pip
        print("\n安装pip...")
        output, error = run_command(client, "apt-get update && apt-get install -y python3-pip")
        if error:
            print(f"  警告: {error[:200]}")
        
        # 2. 验证pip
        output, _ = run_command(client, "pip3 --version")
        print(f"  pip版本: {output.strip()}")
        
        # 3. 安装Python包
        print("\n安装Python依赖包...")
        packages = [
            "notion-client",
            "python-dotenv", 
            "paramiko",
            "psutil",
            "requests",
            "numpy",
            "pandas",
            "scipy",
            "matplotlib",
            "jupyter",
        ]
        
        for pkg in packages:
            print(f"  安装 {pkg}...")
            output, error = run_command(client, f"pip3 install {pkg}")
            if error and "already satisfied" not in error.lower():
                print(f"    警告: {error[:100]}")
        
        # 4. 安装Node.js
        print("\n安装Node.js...")
        output, error = run_command(client, "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -")
        if error and "curl" not in error.lower():
            print(f"  警告: {error[:100]}")
        
        output, error = run_command(client, "apt-get install -y nodejs")
        if error and "already" not in error.lower():
            print(f"  警告: {error[:100]}")
        
        # 5. 最终验证
        print("\n最终验证:")
        commands = [
            ("Python", "python3 --version"),
            ("pip", "pip3 --version"),
            ("Node.js", "node --version"),
            ("npm", "npm --version"),
            ("Git", "git --version"),
        ]
        
        for name, cmd in commands:
            output, _ = run_command(client, cmd)
            print(f"  {name}: {output.strip()}")
        
        # 6. 创建Python虚拟环境
        print("\n创建Python虚拟环境...")
        run_command(client, "cd /root && python3 -m venv nemt_env")
        print("  虚拟环境已创建: /root/nemt_env")
        
        # 7. 在虚拟环境中安装包
        print("\n在虚拟环境中安装数据科学包...")
        packages = ["numpy", "pandas", "scipy", "matplotlib", "jupyter", "notion-client", "requests"]
        for pkg in packages:
            print(f"  安装 {pkg}...")
            run_command(client, f"/root/nemt_env/bin/pip install {pkg}")
        
        # 8. 运行服务器基准测试
        print("\n在服务器上运行基准测试...")
        sftp = client.open_sftp()
        sftp.put("benchmark.py", "/root/nemt_workspace/code/benchmark.py")
        sftp.close()
        
        stdin, stdout, stderr = client.exec_command(
            "cd /root/nemt_workspace/code && python3 benchmark.py",
            timeout=300
        )
        
        while True:
            line = stdout.readline()
            if not line:
                break
            print(f"    {line}", end='')
        
        # 下载结果
        sftp = client.open_sftp()
        try:
            sftp.get("/root/benchmark_results.json", "benchmark_server_results.json")
            print("\n  服务器基准测试结果已下载!")
        except:
            print("\n  基准测试完成!")
        sftp.close()
        
        client.close()
        print("\n支线1：云服务器基础设施配置 - 完成!")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
