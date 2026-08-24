#!/usr/bin/env python3
"""
Cloud Dev Environment - 云端开发环境管理脚本

用法:
    python cloud_dev.py status     - 查看服务状态
    python cloud_dev.py start      - 启动wede服务
    python cloud_dev.py stop       - 停止wede服务
    python cloud_dev.py restart    - 重启wede服务
    python cloud_dev.py logs       - 查看日志
    python cloud_dev.py setup      - 初始化配置
"""

import sys
import paramiko
import time
import os

# 服务器配置
HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
SERVICE_NAME = "wede"
PORT_WEB = 3000
DEFAULT_PASSWORD = "NEMT2026"


def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    return client


def run_command(client, cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='ignore')


def cmd_status(client):
    """查看服务状态"""
    print(f"\n{'='*60}")
    print(f"  {SERVICE_NAME} 服务状态")
    print(f"{'='*60}\n")

    # 服务状态
    status = run_command(client, f"systemctl is-active {SERVICE_NAME}")
    status_icon = "[OK]" if status.strip() == "active" else "[X]"
    print(f"  服务状态: {status_icon} {'running' if status.strip() == 'active' else 'stopped'}")

    # 端口
    port_info = run_command(client, f"ss -tlnp | grep {PORT_WEB}")
    port_icon = "[OK]" if str(PORT_WEB) in port_info else "[X]"
    print(f"  Web端口: {port_icon} {'listening' if str(PORT_WEB) in port_info else 'not listening'}")

    # HTTP测试
    http_code = run_command(client, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{PORT_WEB} --max-time 5")
    print(f"  HTTP响应: {http_code.strip()}")

    # 进程
    proc = run_command(client, f"ps aux | grep {SERVICE_NAME} | grep -v grep | wc -l")
    print(f"  进程数: {proc.strip()}")

    # 资源使用
    if status.strip() == "active":
        mem = run_command(client, f"ps aux | grep {SERVICE_NAME} | grep -v grep | awk '{{print $6}}'")
        try:
            mem_mb = int(mem.strip()) / 1024
            print(f"  内存占用: {mem_mb:.1f} MB")
        except:
            pass

    print(f"\n{'='*60}")
    if status.strip() == "active":
        print(f"\n  [URL] http://{HOST}:{PORT_WEB}")
        print(f"  [PASS] {DEFAULT_PASSWORD}")
    print(f"{'='*60}\n")


def cmd_start(client):
    """启动服务"""
    print(f"\n启动 {SERVICE_NAME} 服务...")

    # 检查是否已在运行
    status = run_command(client, f"systemctl is-active {SERVICE_NAME}")
    if status.strip() == "active":
        print("  服务已在运行中")
        return

    run_command(client, f"systemctl start {SERVICE_NAME}")
    time.sleep(3)

    status = run_command(client, f"systemctl is-active {SERVICE_NAME}")
    if status.strip() == "active":
        print("  [OK] Service started!")
        print(f"\n  [URL] http://{HOST}:{PORT_WEB}")
        print(f"  [PASS] {DEFAULT_PASSWORD}")
    else:
        print("  [X] Service start failed")
        logs = run_command(client, f"journalctl -u {SERVICE_NAME} --no-pager -n 5")
        print(f"  Logs:\n{logs}")


def cmd_stop(client):
    """停止服务"""
    print(f"\n停止 {SERVICE_NAME} 服务...")
    run_command(client, f"systemctl stop {SERVICE_NAME}")
    time.sleep(2)

    status = run_command(client, f"systemctl is-active {SERVICE_NAME}")
    if status.strip() != "active":
        print("  [OK] Service stopped")
    else:
        print("  ❌ 停止失败")


def cmd_restart(client):
    """重启服务"""
    print(f"\n重启 {SERVICE_NAME} 服务...")
    run_command(client, f"systemctl restart {SERVICE_NAME}")
    time.sleep(3)

    status = run_command(client, f"systemctl is-active {SERVICE_NAME}")
    if status.strip() == "active":
        print("  [OK] Service restarted!")
        print(f"\n  [URL] http://{HOST}:{PORT_WEB}")
    else:
        print("  [X] Restart failed")


def cmd_logs(client, lines=20):
    """查看日志"""
    print(f"\n最近 {lines} 行日志:")
    print("-" * 60)
    logs = run_command(client, f"journalctl -u {SERVICE_NAME} --no-pager -n {lines}")
    print(logs if logs else "无日志")


def cmd_setup(client):
    """初始化配置"""
    print("\n初始化配置...")

    # 确保配置目录存在
    run_command(client, "mkdir -p ~/.config/wede")

    # 创建配置文件 (正确格式)
    config = f'{{"port": "3000", "host": "0.0.0.0", "password": "{DEFAULT_PASSWORD}"}}'
    run_command(client, f'cat > /root/.config/wede/wede.config.json << EOF\n{config}\nEOF')
    print("  ✅ 配置文件已创建")

    # 创建systemd服务
    service = f"""[Unit]
Description=wede - Lightweight Web IDE
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/local/bin/wede serve -p {PORT_WEB}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    run_command(client, f'cat > /etc/systemd/system/{SERVICE_NAME}.service << EOF\n{service}EOF')
    print("  ✅ systemd服务已配置")

    # 重载systemd
    run_command(client, "systemctl daemon-reload")
    print("  ✅ systemd已重载")

    # 防火墙
    run_command(client, f"ufw allow {PORT_WEB}/tcp comment '{SERVICE_NAME}-web-ide'")
    print(f"  ✅ 防火墙端口 {PORT_WEB} 已开放")

    # 启动服务
    run_command(client, f"systemctl enable {SERVICE_NAME}")
    run_command(client, f"systemctl start {SERVICE_NAME}")
    time.sleep(3)

    status = run_command(client, f"systemctl is-active {SERVICE_NAME}")
    if status.strip() == "active":
        print("  [OK] Setup complete!")
        print(f"\n  [URL] http://{HOST}:{PORT_WEB}")
        print(f"  [PASS] {DEFAULT_PASSWORD}")
    else:
        print("  [X] Setup failed, check logs")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n快速使用:")
        print("  python cloud_dev.py           # 查看状态")
        print("  python cloud_dev.py status    # 查看状态")
        print("  python cloud_dev.py start    # 启动服务")
        print("  python cloud_dev.py stop      # 停止服务")
        print("  python cloud_dev.py restart   # 重启服务")
        print("  python cloud_dev.py logs      # 查看日志")
        print("  python cloud_dev.py setup     # 初始化配置")
        return

    try:
        client = ssh_connect()
        print(f"\n已连接到 {HOST}\n")

        cmd = sys.argv[1].lower()

        if cmd == "status":
            cmd_status(client)
        elif cmd == "start":
            cmd_start(client)
        elif cmd == "stop":
            cmd_stop(client)
        elif cmd == "restart":
            cmd_restart(client)
        elif cmd == "logs":
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            cmd_logs(client, lines)
        elif cmd == "setup":
            cmd_setup(client)
        else:
            print(f"未知命令: {cmd}")
            print("可用命令: status, start, stop, restart, logs, setup")

        client.close()

    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
