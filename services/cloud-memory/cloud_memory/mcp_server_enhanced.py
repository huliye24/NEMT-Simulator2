#!/usr/bin/env python3
"""
NEMT Cloud MCP Server (增强版)
================================
支持 Cursor MCP SSE 连接，提供：
1. NEMT 计算工具（DCI、涡旋、共振等）
2. 文件操作工具（读写文件）
3. 记忆工具（已有）

运行方式:
    python3 mcp_server_enhanced.py

端口: 8766
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import queue
import subprocess
import hashlib
import re

# 添加 NEMT 路径
NEMT_PATH = "/root/NEMT-Simulator2"
sys.path.insert(0, NEMT_PATH)

# ============================================================================
# 日志配置
# ============================================================================

LOG_FILE = Path("/root/quant-sync-server/mcp_enhanced.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP-ENH] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("mcp_enhanced")

# ============================================================================
# MCP 工具注册表
# ============================================================================

TOOLS = {
    # ===== NEMT 计算工具 =====
    "nemt_compute_dci": {
        "description": "计算 NEMT DCI 指数（方向性变化指数）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {"type": "array", "items": {"type": "number"}, "description": "价格序列"},
                "window": {"type": "integer", "default": 14, "description": "计算窗口"},
            },
            "required": ["prices"],
        },
    },
    "nemt_compute_vortex": {
        "description": "计算 NEMT 涡旋指数（趋势强度）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "high": {"type": "array", "items": {"type": "number"}, "description": "最高价序列"},
                "low": {"type": "array", "items": {"type": "number"}, "description": "最低价序列"},
                "close": {"type": "array", "items": {"type": "number"}, "description": "收盘价序列"},
            },
            "required": ["high", "low", "close"],
        },
    },
    "nemt_compute_resonance": {
        "description": "计算市场共振状态",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {"type": "array", "items": {"type": "number"}, "description": "价格序列"},
                "threshold": {"type": "number", "default": 0.7, "description": "共振阈值"},
            },
            "required": ["prices"],
        },
    },
    "nemt_simulate": {
        "description": "运行 NEMT 模拟",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {"type": "array", "items": {"type": "number"}, "description": "价格序列"},
                "alpha": {"type": "number", "default": 0.1, "description": "扩散系数"},
                "beta": {"type": "number", "default": 1.0, "description": "非线性系数"},
                "noise_level": {"type": "number", "default": 0.2, "description": "噪声水平"},
            },
            "required": ["prices"],
        },
    },
    "nemt_get_signals": {
        "description": "获取完整 NEMT 信号（DCI、涡旋、共振等）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prices": {"type": "array", "items": {"type": "number"}, "description": "价格序列"},
                "high": {"type": "array", "items": {"type": "number"}, "description": "最高价序列"},
                "low": {"type": "array", "items": {"type": "number"}, "description": "最低价序列"},
            },
            "required": ["prices"],
        },
    },

    # ===== 文件操作工具 =====
    "file_read": {
        "description": "读取文件内容",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（绝对路径或相对于工作目录）"},
                "max_lines": {"type": "integer", "default": 500, "description": "最大行数"},
                "start_line": {"type": "integer", "default": 1, "description": "起始行号"},
            },
            "required": ["path"],
        },
    },
    "file_write": {
        "description": "写入文件内容",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件内容"},
                "append": {"type": "boolean", "default": False, "description": "是否追加模式"},
            },
            "required": ["path", "content"],
        },
    },
    "file_list": {
        "description": "列出目录文件",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": ".", "description": "目录路径"},
                "pattern": {"type": "string", "default": "*", "description": "文件匹配模式"},
                "recursive": {"type": "boolean", "default": False, "description": "递归列出"},
            },
        },
    },
    "file_search": {
        "description": "在文件中搜索文本",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "搜索路径"},
                "pattern": {"type": "string", "description": "搜索模式（支持正则）"},
                "case_sensitive": {"type": "boolean", "default": False},
                "file_pattern": {"type": "string", "default": "*.py", "description": "文件过滤"},
            },
            "required": ["path", "pattern"],
        },
    },
    "file_exists": {
        "description": "检查文件是否存在",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
            },
            "required": ["path"],
        },
    },
    "file_info": {
        "description": "获取文件信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
            },
            "required": ["path"],
        },
    },

    # ===== 记忆工具 =====
    "get_memory_context": {
        "description": "从云端 Obsidian 记忆库获取上下文",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "查询关键词"},
                "max_chars": {"type": "integer", "default": 8000},
                "days": {"type": "integer", "default": 7},
            },
        },
    },
    "search_memory": {
        "description": "在云端记忆库搜索",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string"},
            },
            "required": ["keyword"],
        },
    },
    "get_memory_summary": {
        "description": "获取记忆摘要",
        "inputSchema": {"type": "object", "properties": {}},
    },

    # ===== 系统工具 =====
    "system_info": {
        "description": "获取系统信息",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "run_command": {
        "description": "运行 Shell 命令",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "命令"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["command"],
        },
    },
}


# ============================================================================
# NEMT 计算函数
# ============================================================================

def compute_dci(prices: List[float], window: int = 14) -> dict:
    """计算 DCI 指数"""
    try:
        import numpy as np
        prices = np.array(prices)
        n = len(prices)
        if n < window:
            return {"error": f"数据不足，需要至少 {window} 个数据点"}

        dci_values = []
        for i in range(window, n):
            segment = prices[i-window:i]
            diff = np.diff(segment)
            sign_changes = np.sum(diff[:-1] * diff[1:] < 0)
            dci = sign_changes / (window - 1)
            dci_values.append(float(dci))

        # 当前值
        current_dci = dci_values[-1] if dci_values else 0
        avg_dci = np.mean(dci_values) if dci_values else 0

        return {
            "current_dci": round(current_dci, 4),
            "avg_dci": round(avg_dci, 4),
            "min_dci": round(min(dci_values), 4) if dci_values else 0,
            "max_dci": round(max(dci_values), 4) if dci_values else 0,
            "trend": "上升" if current_dci > avg_dci else "下降",
            "dci_series": [round(x, 4) for x in dci_values[-20:]],
        }
    except Exception as e:
        return {"error": str(e)}


def compute_vortex(high: List[float], low: List[float], close: List[float], window: int = 14) -> dict:
    """计算涡旋指数"""
    try:
        import numpy as np
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)

        n = len(close)
        if n < window + 1:
            return {"error": f"数据不足，需要至少 {window + 1} 个数据点"}

        # 计算真实波动
        tr1 = high - low
        tr2 = abs(high - np.roll(close, 1))
        tr3 = abs(low - np.roll(close, 1))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        tr[0] = tr1[0]

        # VM+ 和 VM-
        vm_plus = abs(high - np.roll(low, 1))
        vm_minus = abs(low - np.roll(high, 1))
        vm_plus[0] = high[0] - low[0]
        vm_minus[0] = high[0] - low[0]

        # 累加
        sum_vm_plus = np.array([np.sum(vm_plus[i-window+1:i+1]) for i in range(window-1, n)])
        sum_vm_minus = np.array([np.sum(vm_minus[i-window+1:i+1]) for i in range(window-1, n)])
        sum_tr = np.array([np.sum(tr[i-window+1:i+1]) for i in range(window-1, n)])

        # VI+ 和 VI-
        vi_plus = sum_vm_plus / (sum_tr + 1e-10)
        vi_minus = sum_vm_minus / (sum_tr + 1e-10)

        current_plus = float(vi_plus[-1])
        current_minus = float(vi_minus[-1])

        return {
            "vi_plus": round(current_plus, 4),
            "vi_minus": round(current_minus, 4),
            "vi_trend": round(current_plus - current_minus, 4),
            "signal": "看涨" if current_plus > current_minus else "看跌",
            "strength": "强" if abs(current_plus - current_minus) > 0.5 else "弱",
            "vi_plus_series": [round(x, 4) for x in vi_plus[-20:].tolist()],
            "vi_minus_series": [round(x, 4) for x in vi_minus[-20:].tolist()],
        }
    except Exception as e:
        return {"error": str(e)}


def compute_resonance(prices: List[float], threshold: float = 0.7) -> dict:
    """计算市场共振状态"""
    try:
        import numpy as np
        from scipy import signal

        prices = np.array(prices)
        n = len(prices)

        if n < 50:
            return {"error": "数据不足，至少需要50个数据点"}

        # 计算 FFT
        fft_vals = np.fft.fft(prices)
        fft_freq = np.fft.fftfreq(n)
        power = np.abs(fft_vals) ** 2

        # 找主周期
        positive_freq_idx = np.where(fft_freq > 0)[0]
        if len(positive_freq_idx) == 0:
            return {"error": "无法计算频率"}

        dominant_freq_idx = positive_freq_idx[np.argmax(power[positive_freq_idx])]
        dominant_freq = abs(fft_freq[dominant_freq_idx])
        dominant_period = 1 / dominant_freq if dominant_freq != 0 else 0

        # 计算谐波
        harmonics = []
        resonance_score = 0
        for i in range(1, 5):
            harmonic_freq = dominant_freq * i
            harmonic_idx = np.argmin(np.abs(fft_freq - harmonic_freq))
            if power[harmonic_idx] > threshold * power[dominant_freq_idx]:
                harmonics.append({
                    "harmonic": i,
                    "frequency": float(abs(fft_freq[harmonic_idx])),
                    "power": float(power[harmonic_idx]),
                })
                resonance_score += 0.25

        # 判断共振状态
        if resonance_score >= 0.75:
            state = "强共振"
            description = "市场处于高度协调状态，趋势可能持续"
        elif resonance_score >= 0.5:
            state = "中等共振"
            description = "市场存在一定协调性，关注方向选择"
        elif resonance_score >= 0.25:
            state = "弱共振"
            description = "市场协调性较差，可能震荡"
        else:
            state = "无共振"
            description = "市场完全无序，难以判断方向"

        return {
            "resonance_score": round(resonance_score, 4),
            "state": state,
            "description": description,
            "dominant_period": round(float(dominant_period), 2),
            "dominant_frequency": round(float(dominant_freq), 6),
            "harmonics": harmonics,
            "is_resonance": resonance_score >= threshold,
        }
    except Exception as e:
        return {"error": str(e)}


def nemt_simulate(prices: List[float], alpha: float = 0.1, beta: float = 1.0, noise_level: float = 0.2) -> dict:
    """运行 NEMT 模拟"""
    try:
        import numpy as np
        from dataclasses import dataclass

        prices = np.array(prices)

        @dataclass
        class NEMTParams:
            alpha: float = 0.1
            beta: float = 1.0
            noise_level: float = 0.2
            dt: float = 0.01

        params = NEMTParams(alpha=alpha, beta=beta, noise_level=noise_level)

        # 初始化状态
        normalized = (prices - np.mean(prices)) / (np.std(prices) + 1e-10)
        psi = normalized + 1j * np.zeros_like(normalized)

        # 简单模拟演化
        psi_evolution = [psi.copy()]
        for step in range(50):
            # 线性项
            laplacian = np.zeros_like(psi)
            laplacian[1:-1] = psi[:-2] - 2*psi[1:-1] + psi[2:]

            # 非线性项
            nonlinear = params.beta * np.abs(psi)**2 * psi

            # 噪声
            noise = params.noise_level * np.random.randn(len(psi)) * (1 + 1j*np.random.randn(len(psi))) / np.sqrt(2)

            # 演化
            dpsi = -1j * (params.alpha * laplacian + nonlinear) + noise
            psi = psi + params.dt * dpsi

            if step % 10 == 0:
                psi_evolution.append(psi.copy())

        # 计算最终状态
        final_psi = psi_evolution[-1]
        amplitude = np.abs(final_psi)
        phase = np.angle(final_psi)

        return {
            "evolution_steps": len(psi_evolution),
            "final_amplitude_mean": round(float(np.mean(amplitude)), 4),
            "final_amplitude_std": round(float(np.std(amplitude)), 4),
            "phase_coherence": round(float(np.mean(np.cos(phase))), 4),
            "energy": round(float(np.sum(np.abs(final_psi)**2)), 4),
            "stability": "稳定" if np.std(amplitude) < 0.5 else "不稳定",
            "params": {
                "alpha": params.alpha,
                "beta": params.beta,
                "noise_level": params.noise_level,
            }
        }
    except Exception as e:
        return {"error": str(e)}


def get_nemt_signals(prices: List[float], high: List[float] = None, low: List[float] = None) -> dict:
    """获取完整 NEMT 信号"""
    result = {}

    # DCI
    result["dci"] = compute_dci(prices)

    # Vortex
    if high and low and len(high) == len(prices) and len(low) == len(prices):
        result["vortex"] = compute_vortex(high, low, prices)

    # Resonance
    result["resonance"] = compute_resonance(prices)

    # 简单技术指标
    import numpy as np
    prices_arr = np.array(prices)
    result["technical"] = {
        "current_price": float(prices[-1]),
        "price_change_pct": round(float((prices[-1] - prices[0]) / prices[0] * 100), 2),
        "volatility": round(float(np.std(prices_arr) / np.mean(prices_arr)), 4),
        "momentum": round(float(prices[-1] / prices[-14] - 1) if len(prices) >= 14 else 0, 4),
    }

    # 综合信号
    dci_signal = result["dci"].get("trend", "")
    resonance_signal = result["resonance"].get("state", "")
    momentum = result["technical"].get("momentum", 0)

    if momentum > 0.05 and "共振" in resonance_signal:
        action = "买入"
    elif momentum < -0.05 and "共振" in resonance_signal:
        action = "卖出"
    else:
        action = "观望"

    result["action"] = action

    return result


# ============================================================================
# 文件操作函数
# ============================================================================

WORKSPACE = "/root/NEMT-Simulator2"

def file_read(path: str, max_lines: int = 500, start_line: int = 1) -> dict:
    """读取文件"""
    try:
        # 解析路径
        if not os.path.isabs(path):
            path = os.path.join(WORKSPACE, path)
        path = os.path.normpath(path)

        # 安全检查
        if not path.startswith(WORKSPACE):
            return {"error": "路径超出工作目录", "path": path}

        if not os.path.exists(path):
            return {"error": "文件不存在", "path": path}

        if not os.path.isfile(path):
            return {"error": "不是文件", "path": path}

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # 切片
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), start_idx + max_lines)
        content_lines = lines[start_idx:end_idx]

        return {
            "path": path,
            "lines": len(lines),
            "read_lines": len(content_lines),
            "start_line": start_line,
            "content": "".join(content_lines),
            "truncated": len(lines) > end_idx,
        }
    except Exception as e:
        return {"error": str(e)}


def file_write(path: str, content: str, append: bool = False) -> dict:
    """写入文件"""
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORKSPACE, path)
        path = os.path.normpath(path)

        if not path.startswith(WORKSPACE):
            return {"error": "路径超出工作目录"}

        # 确保目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)

        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "path": path,
            "bytes": len(content.encode("utf-8")),
            "mode": "append" if append else "write",
        }
    except Exception as e:
        return {"error": str(e)}


def file_list(path: str = ".", pattern: str = "*", recursive: bool = False) -> dict:
    """列出目录"""
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORKSPACE, path)
        path = os.path.normpath(path)

        if not path.startswith(WORKSPACE):
            return {"error": "路径超出工作目录"}

        if not os.path.exists(path):
            return {"error": "目录不存在"}

        files = []
        if recursive:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    if Path(filename).match(pattern):
                        full_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(full_path, path)
                        stat = os.stat(full_path)
                        files.append({
                            "name": filename,
                            "path": rel_path,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        })
        else:
            for entry in os.scandir(path):
                if entry.is_file() and Path(entry.name).match(pattern):
                    stat = entry.stat()
                    files.append({
                        "name": entry.name,
                        "path": entry.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })

        return {
            "path": path,
            "count": len(files),
            "files": sorted(files, key=lambda x: x["name"]),
        }
    except Exception as e:
        return {"error": str(e)}


def file_search(path: str, pattern: str, case_sensitive: bool = False, file_pattern: str = "*.py") -> dict:
    """搜索文件内容"""
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORKSPACE, path)
        path = os.path.normpath(path)

        if not path.startswith(WORKSPACE):
            return {"error": "路径超出工作目录"}

        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matches = []
        for root, dirs, files in os.walk(path):
            for filename in files:
                if not Path(filename).match(file_pattern):
                    continue
                full_path = os.path.join(root, filename)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                rel_path = os.path.relpath(full_path, path)
                                matches.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "content": line.rstrip(),
                                })
                                if len(matches) >= 100:
                                    break
                except Exception:
                    continue
                if len(matches) >= 100:
                    break
            if len(matches) >= 100:
                break

        return {
            "path": path,
            "pattern": pattern,
            "count": len(matches),
            "matches": matches[:50],  # 限制返回数量
        }
    except Exception as e:
        return {"error": str(e)}


def file_exists(path: str) -> dict:
    """检查文件是否存在"""
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORKSPACE, path)
        path = os.path.normpath(path)

        return {
            "path": path,
            "exists": os.path.exists(path),
            "is_file": os.path.isfile(path) if os.path.exists(path) else None,
            "is_dir": os.path.isdir(path) if os.path.exists(path) else None,
        }
    except Exception as e:
        return {"error": str(e)}


def file_info(path: str) -> dict:
    """获取文件信息"""
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORKSPACE, path)
        path = os.path.normpath(path)

        if not os.path.exists(path):
            return {"error": "文件不存在"}

        stat = os.path.stat(path)
        return {
            "path": path,
            "size": stat.st_size,
            "size_human": f"{stat.st_size / 1024:.1f} KB" if stat.st_size > 1024 else f"{stat.st_size} B",
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# 记忆函数
# ============================================================================

def get_memory_context(query: str = "", max_chars: int = 8000, days: int = 7) -> dict:
    """获取记忆上下文"""
    try:
        sys.path.insert(0, "/root/quant-sync-server/cloud_memory")
        from cloud_memory_reader import ObsidianReader, MemoryConfig

        VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", "/root/obsidian_vault/NEMT_Notion")
        config = MemoryConfig(vault_path=VAULT_PATH, time_window_days=days, max_chars=max_chars)
        reader = ObsidianReader(config)
        items = reader.scan_vault(query=query)
        context = reader.build_context(items, query=query, max_chars=max_chars)

        header = (
            f"=== NEMT 记忆上下文 ===\n"
            f"时间窗口: 最近 {days} 天\n"
            f"记忆条目: {len(items)} 个\n"
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"========================\n\n"
        )

        return {"content": header + context}
    except Exception as e:
        return {"error": str(e)}


def search_memory(keyword: str) -> dict:
    """搜索记忆"""
    try:
        sys.path.insert(0, "/root/quant-sync-server/cloud_memory")
        from cloud_memory_reader import ObsidianReader, MemoryConfig

        VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", "/root/obsidian_vault/NEMT_Notion")
        config = MemoryConfig(vault_path=VAULT_PATH, time_window_days=30)
        reader = ObsidianReader(config)
        items = reader.scan_vault(query=keyword)

        return {
            "count": len(items),
            "results": [
                {"title": i.title, "path": i.path, "priority": i.priority}
                for i in sorted(items, key=lambda x: -x.relevance_score)
            ]
        }
    except Exception as e:
        return {"error": str(e)}


def get_memory_summary() -> dict:
    """获取记忆摘要"""
    try:
        sys.path.insert(0, "/root/quant-sync-server/cloud_memory")
        from cloud_memory_reader import get_memory_summary
        return get_memory_summary()
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# 系统函数
# ============================================================================

def get_system_info() -> dict:
    """获取系统信息"""
    try:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "hostname": os.uname().nodename,
            "uptime": datetime.now().isoformat(),
        }
    except ImportError:
        return {
            "hostname": os.uname().nodename,
            "uptime": datetime.now().isoformat(),
            "note": "psutil not available",
        }
    except Exception as e:
        return {"error": str(e)}


def run_command(command: str, timeout: int = 30) -> dict:
    """运行 Shell 命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timeout", "command": command, "timeout": timeout}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# 工具调用处理
# ============================================================================

def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """处理工具调用"""
    log.info(f"Tool call: {tool_name}")

    try:
        # NEMT 计算工具
        if tool_name == "nemt_compute_dci":
            result = compute_dci(
                arguments.get("prices", []),
                arguments.get("window", 14)
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "nemt_compute_vortex":
            result = compute_vortex(
                arguments.get("high", []),
                arguments.get("low", []),
                arguments.get("close", []),
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "nemt_compute_resonance":
            result = compute_resonance(
                arguments.get("prices", []),
                arguments.get("threshold", 0.7)
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "nemt_simulate":
            result = nemt_simulate(
                arguments.get("prices", []),
                arguments.get("alpha", 0.1),
                arguments.get("beta", 1.0),
                arguments.get("noise_level", 0.2)
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "nemt_get_signals":
            result = get_nemt_signals(
                arguments.get("prices", []),
                arguments.get("high"),
                arguments.get("low")
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        # 文件操作工具
        elif tool_name == "file_read":
            result = file_read(
                arguments.get("path", ""),
                arguments.get("max_lines", 500),
                arguments.get("start_line", 1)
            )
            content = result.pop("content", "")
            text = json.dumps(result, ensure_ascii=False, indent=2)
            if content:
                text += f"\n\n--- 文件内容 ---\n{content}"
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "file_write":
            result = file_write(
                arguments.get("path", ""),
                arguments.get("content", ""),
                arguments.get("append", False)
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "file_list":
            result = file_list(
                arguments.get("path", "."),
                arguments.get("pattern", "*"),
                arguments.get("recursive", False)
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "file_search":
            result = file_search(
                arguments.get("path", "."),
                arguments.get("pattern", ""),
                arguments.get("case_sensitive", False),
                arguments.get("file_pattern", "*.py")
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "file_exists":
            result = file_exists(arguments.get("path", ""))
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "file_info":
            result = file_info(arguments.get("path", ""))
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        # 记忆工具
        elif tool_name == "get_memory_context":
            result = get_memory_context(
                arguments.get("query", ""),
                arguments.get("max_chars", 8000),
                arguments.get("days", 7)
            )
            return {"content": [{"type": "text", "text": result.get("content", str(result))}]}

        elif tool_name == "search_memory":
            result = search_memory(arguments.get("keyword", ""))
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "get_memory_summary":
            result = get_memory_summary()
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        # 系统工具
        elif tool_name == "system_info":
            result = get_system_info()
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        elif tool_name == "run_command":
            result = run_command(
                arguments.get("command", ""),
                arguments.get("timeout", 30)
            )
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

        else:
            return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

    except Exception as e:
        log.error(f"Tool error: {e}", exc_info=True)
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}


# ============================================================================
# HTTP Handler (复用之前的 SSE Handler)
# ============================================================================

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class MCPHandler(BaseHTTPRequestHandler):
    """MCP HTTP 处理器"""

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _send_sse(self, event: str, data: Any, event_id: str = None):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        message = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        try:
            self.wfile.write(message.encode("utf-8"))
            self.wfile.flush()
        except Exception as e:
            log.error(f"SSE send error: {e}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parsed.query

        if path == "/health":
            self._send_json({"status": "ok", "timestamp": datetime.now().isoformat(), "tools": len(TOOLS)})

        elif path == "/sse":
            # SSE 连接端点
            global client_counter
            with client_lock:
                client_id = str(client_counter)
                client_counter += 1
                output_queue = queue.Queue()
                client = SSEClient(client_id, output_queue)
                clients[client_id] = client

            log.info(f"New SSE client: {client_id}")

            self._send_sse("connected", {
                "client_id": client_id,
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "nemt-cloud-mcp-enhanced", "version": "2.0.0"},
                "capabilities": {"tools": {"listChanged": True}},
                "tools": [
                    {"name": name, "description": info["description"], "inputSchema": info["inputSchema"]}
                    for name, info in TOOLS.items()
                ]
            })

            try:
                while True:
                    try:
                        event_data = output_queue.get(timeout=30)
                        self._send_sse(event_data["event"], event_data["data"])
                    except queue.Empty:
                        self._send_sse("ping", {"timestamp": datetime.now().isoformat()})
            except Exception as e:
                log.info(f"SSE client {client_id} disconnected: {e}")
            finally:
                with client_lock:
                    clients.pop(client_id, None)

        elif path == "/tools/list":
            self._send_json({
                "tools": [
                    {"name": name, "description": info["description"], "inputSchema": info["inputSchema"]}
                    for name, info in TOOLS.items()
                ]
            })

        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="replace")

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, status=400)
            return

        if path == "/tools/call":
            tool_name = request.get("name", "")
            arguments = request.get("arguments", {})
            result = handle_tool_call(tool_name, arguments)
            self._send_json({"result": result})

            with client_lock:
                for client in clients.values():
                    client.send_event("tool_response", {"tool": tool_name, "result": result})
        else:
            self._send_json({"error": "Not found"}, status=404)

    def log_message(self, format, *args):
        log.info(format % args)


# ============================================================================
# SSE 连接管理
# ============================================================================

class SSEClient:
    def __init__(self, client_id: str, output_queue: queue.Queue):
        self.client_id = client_id
        self.output_queue = output_queue
        self.subscribed_events = set()

    def send_event(self, event: str, data: Any):
        self.output_queue.put({"event": event, "data": data})

clients: Dict[str, SSEClient] = {}
client_counter = 0
client_lock = threading.Lock()


# ============================================================================
# 启动
# ============================================================================

PORT = int(os.environ.get("MCP_SSE_PORT", "8766"))
HOST = "0.0.0.0"

def run_server():
    server = HTTPServer((HOST, PORT), MCPHandler)
    log.info(f"MCP Enhanced Server started: http://{HOST}:{PORT}")
    log.info(f"SSE endpoint: http://42.51.42.123:{PORT}/sse")
    log.info(f"Tools: {list(TOOLS.keys())}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Server shutdown")
        server.shutdown()

if __name__ == "__main__":
    run_server()
