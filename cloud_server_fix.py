#!/usr/bin/env python3
"""
完成云服务器pip和包安装
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
    print("等待apt锁释放...")
    
    try:
        client = create_ssh_client()
        print("SSH连接成功!")
        
        # 等待apt锁释放
        for i in range(60):
            output, _ = run_command(client, "pgrep -x apt || pgrep -x dpkg || echo 'none'")
            if 'none' in output or not output.strip():
                print(f"锁已释放 (等待 {i+1} 秒)")
                break
            print(f"等待apt锁释放... ({i+1}/60)")
            time.sleep(2)
        
        # 强制清理锁
        run_command(client, "rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock 2>/dev/null")
        run_command(client, "dpkg --configure -a 2>/dev/null")
        time.sleep(2)
        
        # 安装pip
        print("\n安装pip...")
        output, error = run_command(client, "DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip", timeout=300)
        if "already" in output.lower() or error and "already" in error.lower():
            print("pip已安装")
        elif error and "Unable" in error:
            print(f"安装失败: {error[:100]}")
            # 尝试直接使用pip
            output, _ = run_command(client, "which pip3 || which pip")
            print(f"pip路径: {output.strip()}")
        else:
            print("pip安装完成")
        
        # 验证pip
        output, _ = run_command(client, "/usr/bin/pip3 --version || pip3 --version || /usr/local/bin/pip3 --version")
        print(f"pip版本: {output.strip()}")
        
        # 如果pip不可用，尝试安装get-pip.py
        if not output.strip() or "not found" in output.lower():
            print("\n尝试通过get-pip.py安装...")
            run_command(client, "curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py", timeout=60)
            output, error = run_command(client, "python3 /tmp/get-pip.py", timeout=180)
            if error:
                print(f"错误: {error[:100]}")
        
        # 验证pip3
        output, _ = run_command(client, "pip3 --version")
        print(f"pip3版本: {output.strip()}")
        
        # 安装基础包
        print("\n安装Python包...")
        packages = ["requests", "psutil", "notion-client", "python-dotenv"]
        for pkg in packages:
            print(f"  安装 {pkg}...")
            run_command(client, f"pip3 install {pkg}", timeout=120)
        
        # 安装数据科学包
        print("\n安装数据科学包...")
        science = ["numpy", "pandas", "scipy", "matplotlib"]
        for pkg in science:
            print(f"  安装 {pkg}...")
            run_command(client, f"pip3 install {pkg}", timeout=300)
        
        # 最终验证
        print("\n" + "="*60)
        print("最终环境验证:")
        print("="*60)
        
        checks = [
            ("Python", "python3 --version"),
            ("pip3", "pip3 --version"),
            ("Node.js", "node --version"),
            ("NumPy", "python3 -c 'import numpy; print(numpy.__version__)'"),
            ("Pandas", "python3 -c 'import pandas; print(pandas.__version__)'"),
        ]
        
        for name, cmd in checks:
            output, _ = run_command(client, cmd)
            print(f"  {name}: {output.strip()}")
        
        # 运行基准测试
        print("\n运行服务器基准测试...")
        sftp = client.open_sftp()
        sftp.put("benchmark.py", "/root/nemt_workspace/code/benchmark.py")
        sftp.close()
        
        stdin, stdout, stderr = client.exec_command(
            "cd /root/nemt_workspace/code && python3 benchmark.py 2>&1",
            timeout=300
        )
        
        while True:
            line = stdout.readline()
            if not line:
                break
            print(f"    {line}", end='')
        
        # 下载结果
        try:
            sftp = client.open_sftp()
            sftp.get("/root/benchmark_results.json", "benchmark_server_results.json")
            print("\n基准测试结果已保存!")
            sftp.close()
        except:
            pass
        
        client.close()
        print("\n支线1：云服务器基础设施配置 - 完成!")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
