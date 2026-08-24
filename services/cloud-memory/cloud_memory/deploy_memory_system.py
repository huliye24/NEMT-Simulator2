#!/usr/bin/env python3
"""
NEMT Cloud Memory System - 一键部署脚本
=======================================
将云端记忆系统部署到云服务器，并配置本地 Cursor。

使用方法:
  python3 deploy_memory_system.py [--local-only] [--cloud-only] [--test]
"""

import os
import sys
import json
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# ============================================================================
# 配置
# ============================================================================

SERVER = "42.51.42.123"
PORT = 22
USERNAME = "root"
KEY_PATH = "e:/NEMT Simulator/ssh_key_nemt"

LOCAL_DIR = Path("e:/NEMT Simulator/cloud_memory")
SERVER_DIR = "/root/quant-sync-server"
SERVER_CLOUD_DIR = f"{SERVER_DIR}/cloud_memory"

# 云端记忆服务端口
MEMORY_PORT = 8765

# 本地 Cursor MCP 配置
CURSOR_MCP_CONFIG = Path.home() / ".cursor" / "mcp.json"

# 日志
LOG_FILE = Path(__file__).parent / "deploy_memory.log"


# ============================================================================
# 工具函数
# ============================================================================

def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def run_ssh(cmd: str, timeout: int = 60) -> tuple:
    """在云服务器上执行命令"""
    key_arg = f'-i "{KEY_PATH}"' if KEY_PATH else ''
    full_cmd = f'ssh {key_arg} -o StrictHostKeyChecking=no -o ConnectTimeout=10 {USERNAME}@{SERVER} "{cmd}"'
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1


def run_scp(local_path: str, remote_path: str) -> bool:
    """上传文件到云服务器"""
    key_arg = f'-i "{KEY_PATH}"' if KEY_PATH else ''
    cmd = f'scp -r {key_arg} -o StrictHostKeyChecking=no -o ConnectTimeout=30 "{local_path}" {USERNAME}@{SERVER}:"{remote_path}"'
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode == 0
    except Exception as e:
        log(f"SCP failed: {e}", "ERROR")
        return False


# ============================================================================
# 步骤 1: 上传代码到云服务器
# ============================================================================

def deploy_cloud():
    """部署云端组件"""
    log("=" * 60)
    log("Step 1: 部署云端组件")
    log("=" * 60)

    # 创建云端目录
    stdout, stderr, code = run_ssh(f"mkdir -p {SERVER_CLOUD_DIR}")
    if code != 0:
        log(f"创建目录失败: {stderr}", "ERROR")
        return False

    # 上传所有文件
    files_to_upload = [
        "cloud_memory_reader.py",
        "memory_server.py",
        "memory_mcp_server.py",
        "nemt-memory.service",
    ]

    for f in files_to_upload:
        local = LOCAL_DIR / f
        remote = f"{SERVER_CLOUD_DIR}/{f}"
        log(f"上传 {f}...")
        if not run_scp(str(local), remote):
            log(f"上传 {f} 失败", "ERROR")
            return False
        log(f"  {f} 上传成功")

    # 上传 __init__.py
    init_file = LOCAL_DIR / "__init__.py"
    with open(init_file, "w", encoding="utf-8") as f:
        f.write("# NEMT Cloud Memory System\n")
    run_scp(str(init_file), f"{SERVER_CLOUD_DIR}/__init__.py")

    log("云端代码部署完成")
    return True


# ============================================================================
# 步骤 2: 配置 systemd 服务
# ============================================================================

def setup_systemd():
    """配置 systemd 服务"""
    log("=" * 60)
    log("Step 2: 配置 systemd 服务")
    log("=" * 60)

    # 上传 systemd service 文件
    service_file = LOCAL_DIR / "nemt-memory.service"
    run_scp(str(service_file), "/etc/systemd/system/nemt-memory.service")

    # 重新加载 systemd
    stdout, stderr, code = run_ssh("systemctl daemon-reload")
    if code != 0:
        log(f"daemon-reload 失败: {stderr}", "ERROR")

    # 启用并启动服务
    stdout, stderr, code = run_ssh("systemctl enable nemt-memory.service")
    if code != 0:
        log(f"enable 失败: {stderr}", "WARN")

    stdout, stderr, code = run_ssh("systemctl restart nemt-memory.service")
    if code != 0:
        log(f"restart 失败: {stderr}", "ERROR")
        return False

    log("systemd 服务已重启")

    # 等待服务启动
    time.sleep(3)

    # 检查服务状态
    stdout, stderr, code = run_ssh("systemctl status nemt-memory.service")
    log(f"服务状态:\n{stdout}")

    return True


# ============================================================================
# 步骤 3: 测试云端服务
# ============================================================================

def test_cloud():
    """测试云端服务"""
    log("=" * 60)
    log("Step 3: 测试云端服务")
    log("=" * 60)

    # 测试健康检查
    stdout, stderr, code = run_ssh(
        f'curl -s http://localhost:{MEMORY_PORT}/health'
    )
    if code == 0 and stdout.strip():
        try:
            health = json.loads(stdout)
            log(f"健康检查: {health}")
        except Exception:
            log(f"健康检查响应: {stdout[:200]}")
    else:
        log(f"健康检查失败: {stderr or stdout}", "WARN")

    # 测试记忆摘要
    stdout, stderr, code = run_ssh(
        f'curl -s http://localhost:{MEMORY_PORT}/memory/summary'
    )
    if code == 0 and stdout.strip():
        try:
            summary = json.loads(stdout)
            log(f"记忆摘要: 共 {summary.get('total', 0)} 个条目")
        except Exception:
            log(f"摘要响应: {stdout[:200]}", "WARN")

    # 测试记忆上下文
    stdout, stderr, code = run_ssh(
        f'curl -s http://localhost:{MEMORY_PORT}/memory?days=7'[:200]
    )
    # 分开执行
    cmd = f'curl -s "http://localhost:{MEMORY_PORT}/memory?days=7" | head -c 500'
    stdout, stderr, code = run_ssh(cmd, timeout=30)
    if code == 0:
        log(f"记忆上下文测试 (前500字符):\n{stdout}")

    return True


# ============================================================================
# 步骤 4: 配置本地 Cursor MCP
# ============================================================================

def setup_local_mcp():
    """配置本地 Cursor MCP"""
    log("=" * 60)
    log("Step 4: 配置本地 Cursor MCP")
    log("=" * 60)

    # 读取现有 MCP 配置
    mcp_config = {"mcpServers": {}}

    if CURSOR_MCP_CONFIG.exists():
        try:
            with open(CURSOR_MCP_CONFIG, "r", encoding="utf-8") as f:
                mcp_config = json.load(f)
        except Exception:
            pass

    # 添加 NEMT Memory MCP 服务
    nemt_memory_config = {
        "command": "python3",
        "args": [
            str(LOCAL_DIR / "memory_mcp_server.py"),
        ],
        "env": {
            "NEMT_MEMORY_SERVER": f"{SERVER}:{MEMORY_PORT}",
            "OBSIDIAN_VAULT_PATH": "e:/NEMT Simulator/obsidian_vault/NEMT_Notion",
        },
    }

    mcp_config["mcpServers"]["nemt-memory"] = nemt_memory_config

    # 也添加一个 HTTP 版本（备选）
    mcp_config["mcpServers"]["nemt-memory-http"] = {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-http",
            f"http://{SERVER}:{MEMORY_PORT}",
        ],
    }

    # 写入配置
    CURSOR_MCP_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(CURSOR_MCP_CONFIG, "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, ensure_ascii=False, indent=2)

    log(f"MCP 配置已写入: {CURSOR_MCP_CONFIG}")
    log(f"需要重启 Cursor 使配置生效")

    return True


# ============================================================================
# 步骤 5: 配置 Cursor Hook（备选本地方案）
# ============================================================================

def setup_local_hook():
    """配置本地 Cursor Hook 脚本"""
    log("=" * 60)
    log("Step 5: 配置本地 Cursor Hook (备选方案)")
    log("=" * 60)

    hook_dir = Path("e:/NEMT Simulator/.cursor/hooks/nemt_memory_cloud")
    hook_dir.mkdir(parents=True, exist_ok=True)

    # 复制记忆读取器
    shutil.copy(LOCAL_DIR / "cloud_memory_reader.py", hook_dir / "cloud_memory_reader.py")

    # 复制 session start hook
    shutil.copy(LOCAL_DIR / "memory_session_start.py", hook_dir / "memory_session_start.py")

    log(f"Hook 脚本已部署到: {hook_dir}")
    log("注意: 需要配置 .cursor/hooks.json 启用此 hook")

    return True


# ============================================================================
# 主函数
# ============================================================================

def main():
    log("=" * 60)
    log("NEMT Cloud Memory System - 部署开始")
    log("=" * 60)
    log(f"目标服务器: {SERVER}:{PORT}")
    log(f"本地代码目录: {LOCAL_DIR}")
    log(f"云端部署目录: {SERVER_CLOUD_DIR}")

    mode = "full"
    if len(sys.argv) > 1:
        if sys.argv[1] == "--local-only":
            mode = "local"
        elif sys.argv[1] == "--cloud-only":
            mode = "cloud"
        elif sys.argv[1] == "--test":
            mode = "test"

    if mode in ("cloud", "full"):
        if not deploy_cloud():
            log("云端部署失败", "ERROR")
            return

    if mode in ("cloud", "full"):
        if not setup_systemd():
            log("systemd 配置失败", "ERROR")
            return

    if mode in ("test", "cloud", "full"):
        if not test_cloud():
            log("云端测试失败", "ERROR")
            return

    if mode in ("local", "full"):
        if not setup_local_mcp():
            log("本地 MCP 配置失败", "ERROR")
            return

    if mode in ("local", "full"):
        setup_local_hook()

    log("=" * 60)
    log("部署完成!")
    log("=" * 60)
    log("")
    log("后续步骤:")
    log("1. 重启 Cursor IDE 使 MCP 配置生效")
    log("2. 检查 MCP 服务器列表中是否出现 nemt-memory")
    log("3. 在 Cursor 中测试: 打开新会话，观察是否有记忆上下文注入")
    log("")
    log(f"云端记忆服务: http://{SERVER}:{MEMORY_PORT}")
    log(f"MCP 端点: nemt-memory (HTTP)")


if __name__ == "__main__":
    main()
