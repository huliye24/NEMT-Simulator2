#!/usr/bin/env python3
"""
支线1：云服务器基础设施配置
执行所有云服务器环境设置任务
"""

import paramiko
import os
import time
import json

# 云服务器配置
HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
KEY_PATH = os.path.join(os.path.dirname(__file__), "ssh_key_nemt")

def create_ssh_client():
    """创建SSH客户端"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client.connect(HOST, port=PORT, username=USERNAME, pkey=private_key, timeout=30)
    return client

def run_command(client, command, sudo=False):
    """执行远程命令"""
    if sudo:
        command = f"sudo {command}"
    stdin, stdout, stderr = client.exec_command(command, timeout=300)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def task_1_1_check_env(client):
    """1.1 检查当前环境"""
    print("\n" + "="*60)
    print("1.1 检查当前环境")
    print("="*60)
    
    commands = [
        ("系统信息", "uname -a"),
        ("CPU信息", "cat /proc/cpuinfo | grep 'model name' | head -1"),
        ("CPU核心数", "nproc"),
        ("内存信息", "free -h"),
        ("磁盘信息", "df -h"),
        ("操作系统版本", "cat /etc/os-release | grep PRETTY_NAME"),
        ("Python版本", "python3 --version 2>/dev/null || python --version"),
        ("pip版本", "pip3 --version 2>/dev/null || pip --version"),
        ("Node.js版本", "node --version 2>/dev/null || echo 'not installed'"),
        ("npm版本", "npm --version 2>/dev/null || echo 'not installed'"),
        ("Git版本", "git --version 2>/dev/null || echo 'not installed'"),
        ("Docker版本", "docker --version 2>/dev/null || echo 'not installed'"),
    ]
    
    results = {}
    for name, cmd in commands:
        output, _ = run_command(client, cmd)
        results[name] = output.strip()
        print(f"  {name}: {output.strip()[:80]}")
    
    return results

def task_1_2_install_base_tools(client):
    """1.2 安装基础工具"""
    print("\n" + "="*60)
    print("1.2 安装基础工具")
    print("="*60)
    
    commands = [
        "apt-get update",
        "apt-get install -y wget curl git build-essential software-properties-common",
    ]
    
    for cmd in commands:
        print(f"  执行: {cmd[:50]}...")
        _, error = run_command(client, cmd)
        if error and "apt-get" not in cmd:
            print(f"    警告: {error[:100]}")

def task_1_3_install_python(client):
    """1.3 安装/升级Python"""
    print("\n" + "="*60)
    print("1.3 安装/升级Python环境")
    print("="*60)
    
    # 检查Python版本
    output, _ = run_command(client, "python3 --version")
    print(f"  当前Python版本: {output.strip()}")
    
    # 安装Python 3.11和pip
    commands = [
        "apt-get install -y python3.11 python3.11-venv python3-pip",
        "ln -sf /usr/bin/python3.11 /usr/bin/python3",
        "ln -sf /usr/bin/python3 /usr/bin/python",
        "pip3 install --upgrade pip",
    ]
    
    for cmd in commands:
        print(f"  执行: {cmd[:50]}...")
        _, error = run_command(client, cmd)
        if error and "ln -sf" not in cmd:
            print(f"    警告: {error[:100]}")
    
    # 验证
    output, _ = run_command(client, "python3 --version")
    print(f"  Python版本: {output.strip()}")

def task_1_4_install_nodejs(client):
    """1.4 安装Node.js"""
    print("\n" + "="*60)
    print("1.4 安装Node.js")
    print("="*60)
    
    # 检查是否已安装
    output, _ = run_command(client, "node --version")
    if output.strip() and not output.strip().startswith("not"):
        print(f"  Node.js已安装: {output.strip()}")
        return
    
    commands = [
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
    ]
    
    for cmd in commands:
        print(f"  执行: {cmd[:50]}...")
        _, error = run_command(client, cmd)
        if error and "curl" not in cmd:
            print(f"    警告: {error[:100]}")
    
    # 验证
    output, _ = run_command(client, "node --version")
    print(f"  Node.js版本: {output.strip()}")
    
    output, _ = run_command(client, "npm --version")
    print(f"  npm版本: {output.strip()}")

def task_1_5_create_dirs(client):
    """1.5 创建工作目录结构"""
    print("\n" + "="*60)
    print("1.5 创建工作目录结构")
    print("="*60)
    
    dirs = [
        "/root/nemt_workspace",
        "/root/nemt_workspace/code",
        "/root/nemt_workspace/data",
        "/root/nemt_workspace/logs",
        "/root/nemt_workspace/backups",
        "/root/obsidian_vault",
        "/root/obsidian_vault/Decision_Records",
        "/root/obsidian_vault/Strategy_Notes",
    ]
    
    for d in dirs:
        print(f"  创建目录: {d}")
        run_command(client, f"mkdir -p {d}")

def task_1_6_sync_code(client):
    """1.6 同步代码到服务器"""
    print("\n" + "="*60)
    print("1.6 同步本地代码到服务器")
    print("="*60)
    
    # 使用SFTP上传关键文件
    sftp = client.open_sftp()
    
    # 本地要同步的文件/目录
    files_to_sync = [
        ("benchmark.py", "/root/nemt_workspace/code/"),
        ("benchmark_results.json", "/root/nemt_workspace/data/"),
        ("benchmark_cloud_results.json", "/root/nemt_workspace/data/"),
        ("cloud_server_report.md", "/root/nemt_workspace/"),
    ]
    
    for local_path, remote_path in files_to_sync:
        if os.path.exists(local_path):
            remote_file = remote_path + os.path.basename(local_path)
            print(f"  上传: {local_path} -> {remote_file}")
            sftp.put(local_path, remote_file)
    
    sftp.close()
    print("  代码同步完成!")

def task_1_7_install_python_packages(client):
    """1.7 安装Python依赖包"""
    print("\n" + "="*60)
    print("1.7 安装Python依赖包")
    print("="*60)
    
    packages = [
        "notion-client",
        "python-dotenv",
        "paramiko",
        "psutil",
        "requests",
    ]
    
    for pkg in packages:
        print(f"  安装: {pkg}")
        _, error = run_command(client, f"pip3 install {pkg}")
        if error and "already satisfied" not in error.lower():
            print(f"    警告: {error[:100]}")

def task_1_8_install_data_science(client):
    """1.8 安装数据科学库"""
    print("\n" + "="*60)
    print("1.8 安装NumPy/pandas等数据科学库")
    print("="*60)
    
    packages = [
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "jupyter",
    ]
    
    for pkg in packages:
        print(f"  安装: {pkg}")
        _, error = run_command(client, f"pip3 install {pkg}")
        if error and "already satisfied" not in error.lower():
            print(f"    警告: {error[:100]}")

def run_benchmark_on_server(client):
    """在服务器上运行基准测试"""
    print("\n" + "="*60)
    print("在服务器上运行基准测试")
    print("="*60)
    
    # 上传基准测试脚本
    sftp = client.open_sftp()
    sftp.put("benchmark.py", "/root/nemt_workspace/code/benchmark.py")
    sftp.close()
    
    print("  运行基准测试...")
    
    # 运行测试
    stdin, stdout, stderr = client.exec_command(
        "cd /root/nemt_workspace/code && python3 benchmark.py",
        timeout=300
    )
    
    # 流式输出
    while True:
        line = stdout.readline()
        if not line:
            break
        print(f"    {line}", end='')
    
    # 下载结果
    sftp = client.open_sftp()
    sftp.get("/root/benchmark_results.json", "benchmark_server_results.json")
    sftp.close()
    
    print("\n  服务器基准测试完成!")

def main():
    """主函数"""
    print("="*60)
    print("支线1：云服务器基础设施配置")
    print("="*60)
    print(f"目标服务器: {HOST}")
    
    try:
        # 连接服务器
        print("\n正在连接服务器...")
        client = create_ssh_client()
        print("连接成功!")
        
        # 执行任务
        env_info = task_1_1_check_env(client)
        task_1_2_install_base_tools(client)
        task_1_3_install_python(client)
        task_1_4_install_nodejs(client)
        task_1_5_create_dirs(client)
        task_1_6_sync_code(client)
        task_1_7_install_python_packages(client)
        task_1_8_install_data_science(client)
        
        # 运行服务器基准测试
        run_benchmark_on_server(client)
        
        # 最终状态
        print("\n" + "="*60)
        print("支线1完成! 最终环境状态:")
        print("="*60)
        task_1_1_check_env(client)
        
        client.close()
        print("\n支线1：云服务器基础设施配置 - 完成!")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
