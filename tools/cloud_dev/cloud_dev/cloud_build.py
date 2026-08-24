#!/usr/bin/env python3
"""
云端构建 Docker 镜像脚本
用法：
  1. 先同步代码到云端
  2. 在云端执行此脚本（通过 SSH）
"""

import paramiko
import sys

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"

REMOTE_DIR = "/root/NEMT-Simulator2"
IMAGE_NAME = "nemt-simulator"
IMAGE_TAG = "latest"

DOCKERFILE_CONTENT = '''
FROM node:20-slim

RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    git \\
    libgtk-3-0 \\
    libnotify4 \\
    libnss3 \\
    libxss1 \\
    libxtst6 \\
    xdg-utils \\
    libatspi2.0-0 \\
    libdrm2 \\
    libgbm1 \\
    libasound2 \\
    wget \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制 package.json
COPY package.json ./

# 安装 Node 依赖
RUN npm install

# 安装 Python 依赖
RUN pip3 install --no-cache-dir fastapi uvicorn websockets aiohttp pandas numpy

# 复制源码
COPY nemt_os/ ./nemt_os/
COPY web/ ./web/
COPY backtest/ ./backtest/

# 复制 electron
COPY electron/ ./electron/
WORKDIR /app/electron

# 安装 Electron 依赖
RUN npm install

# 返回 app 目录
WORKDIR /app

# 暴露端口
EXPOSE 3000 9222 8080

# 启动命令
CMD ["python3", "-m", "uvicorn", "nemt_os.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
'''


def run_ssh_command(client, cmd):
    """执行 SSH 命令"""
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode()
    error = stderr.read().decode()
    if error:
        print(f"  Error: {error}")
    return output


def main():
    print("=" * 70)
    print("  Cloud Build - Build Docker Image on Server")
    print("=" * 70)
    print(f"Server: {HOST}")
    print(f"Image: {IMAGE_NAME}:{IMAGE_TAG}")
    print()

    # 连接
    print("[1/6] Connecting to server...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=60)
    print("  [OK] Connected")

    # 创建 Dockerfile
    print("[2/6] Creating Dockerfile...")
    dockerfile_path = f"{REMOTE_DIR}/Dockerfile"
    cmd = f'cat > {dockerfile_path} << "EOF"\n{DOCKERFILE_CONTENT}\nEOF'
    run_ssh_command(client, cmd)
    print("  [OK] Dockerfile created")

    # 创建 package.json 软链接
    print("[3/6] Setting up package.json...")
    run_ssh_command(client, f"cd {REMOTE_DIR} && ln -sf electron/package.json package.json 2>/dev/null || cp electron/package.json package.json")
    print("  [OK] package.json ready")

    # 构建镜像
    print("[4/6] Building Docker image...")
    print("  This may take 10-20 minutes...")
    print("-" * 70)

    cmd = f"cd {REMOTE_DIR} && docker build -t {IMAGE_NAME}:{IMAGE_TAG} . 2>&1"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

    # 实时输出
    for line in iter(lambda: stdout.readline(), ""):
        if line.strip():
            print(f"  {line.strip()}")

    print("-" * 70)

    # 检查镜像
    print("[5/6] Checking image...")
    output = run_ssh_command(client, f"docker images {IMAGE_NAME}")
    if IMAGE_NAME in output:
        print("  [OK] Image built successfully!")
    else:
        print("  [X] Build may have failed, check logs above")
        client.close()
        return

    # 运行容器
    print("[6/6] Starting container...")
    run_ssh_command(client, "docker stop nemt-app 2>/dev/null || true")
    run_ssh_command(client, "docker rm nemt-app 2>/dev/null || true")

    result = run_ssh_command(client,
        f"docker run -d --name nemt-app -p 3000:3000 -p 9222:9222 -p 8080:8080 {IMAGE_NAME}:{IMAGE_TAG}"
    )
    container_id = result.strip()[:12] if result.strip() else "unknown"
    print(f"  Container ID: {container_id}")

    # 等待启动
    import time
    time.sleep(3)

    # 检查状态
    status = run_ssh_command(client, "docker ps | grep nemt-app")
    if "nemt-app" in status:
        print("  [OK] Container is running!")
    else:
        print("  [!] Checking logs...")
        logs = run_ssh_command(client, "docker logs nemt-app --tail 10")
        print(logs)

    client.close()

    print()
    print("=" * 70)
    print("  Done!")
    print("=" * 70)
    print(f"""
Access:
  Web UI:  http://42.51.42.123:8080
  Debug:   http://42.51.42.123:9222

Commands:
  docker ps              - View containers
  docker logs -f nemt-app - View logs
  docker stop nemt-app    - Stop
  docker start nemt-app   - Start
""")


if __name__ == "__main__":
    main()
