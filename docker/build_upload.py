#!/usr/bin/env python3
"""
Docker 镜像构建和上传脚本
1. 本地构建镜像
2. 保存为 tar 文件
3. 上传到云服务器
4. 云端加载镜像

使用方式:
    python docker/build_upload.py        # 完整流程
    python docker/build_upload.py build # 仅构建
    python docker/build_upload.py upload # 仅上传
    python docker/build_upload.py run    # 仅在云端运行
"""

import os
import sys
import subprocess
import time

# 配置
HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
IMAGE_NAME = "nemt-simulator"
IMAGE_TAG = "latest"
TAR_FILE = f"{IMAGE_NAME}.tar"
LOCAL_TAR = os.path.join(os.path.dirname(__file__), "..", TAR_FILE)
REMOTE_TAR = f"/root/{TAR_FILE}"
REMOTE_RUN_CMD = f"cd /root && docker load -i {TAR_FILE} && docker run -d --name nemt-app -p 3000:3000 -p 9222:9222 -p 8080:8080 {IMAGE_NAME}:{IMAGE_TAG}"


def run_cmd(cmd, desc="", timeout=600):
    """执行命令"""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}")
    print(f"CMD: {cmd}\n")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=False
    )

    if result.returncode != 0:
        print(f"\n[X] Failed: {desc}")
        sys.exit(1)

    print(f"[OK] Done: {desc}")
    return result


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "all"

    print("=" * 70)
    print("  NEMT Docker 镜像构建和上传")
    print("=" * 70)
    print(f"镜像: {IMAGE_NAME}:{IMAGE_TAG}")
    print(f"目标: root@{HOST}")
    print(f"操作: {action}")
    print()

    if action in ["build", "all"]:
        print("\n[1/4] 构建 Docker 镜像...")
        os.chdir(os.path.join(os.path.dirname(__file__), ".."))
        run_cmd(
            f"docker build -f docker/Dockerfile.app -t {IMAGE_NAME}:{IMAGE_TAG} .",
            "构建镜像",
            timeout=1800
        )

    if action in ["save", "all"]:
        print("\n[2/4] 保存镜像为 tar 文件...")
        if os.path.exists(LOCAL_TAR):
            print(f"  删除旧文件: {LOCAL_TAR}")
            os.remove(LOCAL_TAR)
        run_cmd(
            f"docker save {IMAGE_NAME}:{IMAGE_TAG} -o {LOCAL_TAR}",
            "保存镜像",
            timeout=600
        )
        size = os.path.getsize(LOCAL_TAR) / (1024*1024)
        print(f"  镜像大小: {size:.1f} MB")

    if action in ["upload", "all"]:
        print("\n[3/4] 上传到云服务器...")
        print(f"  本地: {LOCAL_TAR}")
        print(f"  云端: root@{HOST}:{REMOTE_TAR}")

        cmd = f'scp -P {PORT} -o StrictHostKeyChecking=no "{LOCAL_TAR}" {USERNAME}@{HOST}:{REMOTE_TAR}'
        run_cmd(cmd, "上传镜像", timeout=1800)

    if action in ["run", "all"]:
        print("\n[4/4] 在云端运行镜像...")
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=60)

        # 停止旧容器
        print("  停止旧容器...")
        stdin, stdout, stderr = client.exec_command("docker stop nemt-app 2>/dev/null || true")
        stdin, stdout, stderr = client.exec_command("docker rm nemt-app 2>/dev/null || true")

        # 加载镜像
        print("  加载镜像...")
        stdin, stdout, stderr = client.exec_command(f"docker load -i {REMOTE_TAR}")
        print(f"    {stdout.read().decode()}")

        # 运行容器
        print("  启动容器...")
        stdin, stdout, stderr = client.exec_command(
            f"docker run -d --name nemt-app -p 3000:3000 -p 9222:9222 -p 8080:8080 {IMAGE_NAME}:{IMAGE_TAG}"
        )
        result = stdout.read().decode()
        print(f"    容器ID: {result[:12]}...")

        # 检查状态
        time.sleep(3)
        stdin, stdout, stderr = client.exec_command("docker ps | grep nemt-app")
        status = stdout.read().decode()
        if "nemt-app" in status:
            print("  ✓ 容器运行中")
        else:
            print("  ⚠ 检查容器状态...")
            stdin, stdout, stderr = client.exec_command("docker logs nemt-app --tail 20")
            print(f"  日志:\n{stdout.read().decode()}")

        client.close()

    print("\n" + "=" * 70)
    print("  完成!")
    print("=" * 70)

    if action in ["run", "all"]:
        print(f"""
访问地址:
  - Web UI:  http://42.51.42.123:8080
  - Debug:   http://42.51.42.123:9222

管理命令:
  docker ps              # 查看容器
  docker logs -f nemt-app  # 查看日志
  docker stop nemt-app    # 停止
  docker start nemt-app   # 启动
""")

    if action == "all":
        print(f"""
后续修改代码后:
  1. 重新构建: python docker/build_upload.py build
  2. 重新上传: python docker/build_upload.py upload
  3. 重启容器: python docker/build_upload.py run

或使用 DockerHub (推荐):
  docker tag {IMAGE_NAME}:{IMAGE_TAG} yourdockerhub/{IMAGE_NAME}:{IMAGE_TAG}
  docker push yourdockerhub/{IMAGE_NAME}:{IMAGE_TAG}
""")


if __name__ == "__main__":
    main()
