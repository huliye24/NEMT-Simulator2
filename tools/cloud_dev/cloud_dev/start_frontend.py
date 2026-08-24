#!/usr/bin/env python3
"""
启动云端前端服务

这个脚本会将前端代码同步到云服务器并启动开发服务器
"""

import sys
import paramiko
import time
import os
import shutil

# 服务器配置
HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
REMOTE_DIR = "/root/nemt-web"


def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    return client


def run_command(client, cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='ignore')


def main():
    print("=" * 60)
    print("  启动云端前端服务")
    print("=" * 60)

    try:
        client = ssh_connect()
        print("\n已连接到服务器")

        # 1. 创建远程目录
        print("\n[1/6] 创建远程目录...")
        run_command(client, f"mkdir -p {REMOTE_DIR}")
        print(f"  目录: {REMOTE_DIR}")

        # 2. 同步代码（使用SFTP）
        print("\n[2/6] 同步前端代码...")
        print("  使用SFTP上传...")

        local_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        web_dir = os.path.join(local_dir, "web")

        if not os.path.exists(web_dir):
            print(f"  错误: 本地目录不存在: {web_dir}")
            return

        sftp = client.open_sftp()

        # 上传函数
        def upload_dir(local_path, remote_path):
            os.chdir(local_path)
            for item in os.listdir(local_path):
                if item.startswith('.') or item in ['node_modules', 'dist', 'build', 'target']:
                    continue
                local_item = os.path.join(local_path, item)
                remote_item = os.path.join(remote_path, item)
                if os.path.isdir(local_item):
                    try:
                        sftp.stat(remote_item)
                    except:
                        sftp.mkdir(remote_item)
                    upload_dir(local_item, remote_item)
                else:
                    sftp.put(local_item, remote_item)

        # 清除旧文件
        run_command(client, f"rm -rf {REMOTE_DIR}/*")

        upload_dir(web_dir, REMOTE_DIR)
        sftp.close()
        print("  同步完成!")

        # 3. 安装依赖
        print("\n[3/6] 安装npm依赖...")
        print("  设置npm镜像...")

        # 使用国内镜像加速
        run_command(client, "npm config set registry https://registry.npmmirror.com")

        # 后台安装依赖
        run_command(client, f"cd {REMOTE_DIR} && nohup npm install > /tmp/npm_frontend.log 2>&1 &")
        print("  npm install 已在后台运行...")

        # 等待安装
        for i in range(30):
            time.sleep(5)
            output = run_command(client, "ls -la /root/nemt-web/node_modules 2>/dev/null | wc -l")
            try:
                count = int(output.strip())
                if count > 10:
                    print(f"  依赖安装完成 ({i*5}秒)")
                    break
            except:
                pass
            print(f"  等待安装... {i*5}秒")

        # 4. 启动开发服务器
        print("\n[4/6] 启动开发服务器...")

        # 停止旧的node进程
        run_command(client, "pkill -f 'vite' 2>/dev/null")

        # 后台启动
        run_command(client, f"cd {REMOTE_DIR} && nohup npm run dev > /tmp/vite.log 2>&1 &")
        print("  启动中...")

        # 等待启动
        for i in range(20):
            time.sleep(2)
            output = run_command(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:5173 --max-time 2 || echo '000'")
            if output.strip() == "200":
                print(f"  前端服务已启动! ({i*2}秒)")
                break
            print(f"  等待... {i*2}秒")

        # 5. 检查状态
        print("\n[5/6] 检查服务状态...")
        output = run_command(client, "ps aux | grep vite | grep -v grep")
        print(f"  进程: {'运行中' if output.strip() else '未运行'}")

        # 6. 配置防火墙
        print("\n[6/6] 配置防火墙...")
        run_command(client, "ufw allow 5173/tcp comment 'vite-dev-server'")
        print("  防火墙端口已开放")

        # 输出结果
        print("\n" + "=" * 60)
        print("  前端服务已启动!")
        print("=" * 60)
        print(f"\n  访问地址: http://{HOST}:5173")
        print(f"  注意: 如果无法访问，等待1-2分钟让Vite编译完成")
        print("\n  本地访问: http://localhost:5173")
        print("=" * 60)

        client.close()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
