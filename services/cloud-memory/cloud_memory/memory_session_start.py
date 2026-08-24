#!/usr/bin/env python3
"""
NEMT Memory Session Start Hook
==============================
在 Cursor 会话启动时自动从云端获取记忆上下文，注入到系统提示中。

功能（S11 Hook 触发 + S4 Obsidian 直读）：
1. 读取云端记忆服务 API
2. 可选：通过 GitHub API 获取远程记忆
3. 本地缓存：避免重复请求
4. 输出记忆上下文片段供 Agent 使用

部署：
- Windows: 复制到 .cursor/hooks/nemt_memory/memory_session_start.py
- 云服务器: 作为 systemd 服务运行 memory_server.py
"""

import os
import sys
import json
import re
import hashlib
import urllib.request
import urllib.error
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# 配置
# ============================================================================

CLOUD_SERVER_URL = os.environ.get(
    "NEMT_MEMORY_SERVER",
    "http://42.51.42.123:8765"
)

TIMEOUT_SECONDS = 10
CACHE_DIR = Path.home() / ".cursor" / "nemt_memory_cache"
CACHE_FILE = CACHE_DIR / "session_memory.json"

# 日志
LOG_FILE = Path.home() / ".cursor" / "nemt_memory.log"


# ============================================================================
# 日志
# ============================================================================

def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} [{level}] {msg}"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    if level == "ERROR":
        print(line, file=sys.stderr)
    else:
        print(line)


# ============================================================================
# HTTP 客户端
# ============================================================================

def fetch_cloud_memory(query: str = "", max_chars: int = 8000, days: int = 7) -> Optional[str]:
    """
    从云端记忆服务获取上下文
    """
    params = f"?q={urllib.parse.quote(query)}&max_chars={max_chars}&days={days}"
    url = f"{CLOUD_SERVER_URL}/memory{params}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "NEMT-Memory-Hook/1.0",
                "Accept": "text/plain; charset=utf-8",
            }
        )
        log(f"Fetching memory from cloud: {url}")
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        log(f"HTTP Error {e.code}: {e.reason}", "ERROR")
        return None
    except urllib.error.URLError as e:
        log(f"URL Error: {e.reason}", "ERROR")
        return None
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        return None


def fetch_local_fallback(query: str = "") -> Optional[str]:
    """
    本地备选：从本地 Obsidian Vault 直接读取（当云端不可用时）
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))
        from cloud_memory_reader import get_memory_context
        return get_memory_context(query=query, max_chars=8000)
    except ImportError:
        log("cloud_memory_reader not found, skipping local fallback", "WARN")
        return None


def load_cache() -> dict:
    """加载本地缓存"""
    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(data: dict):
    """保存本地缓存"""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def is_cache_valid(cache: dict, max_age_hours: int = 1) -> bool:
    """检查缓存是否有效"""
    if not cache or "timestamp" not in cache:
        return False

    try:
        cached_time = datetime.fromisoformat(cache["timestamp"])
        age = (datetime.now() - cached_time).total_seconds() / 3600
        return age < max_age_hours
    except Exception:
        return False


# ============================================================================
# 上下文组装
# ============================================================================

def extract_current_task() -> str:
    """
    从当前工作目录和 git 状态提取当前任务线索
    """
    clues = []

    # 从 git 分支名提取
    try:
        result = os.popen("git branch --show-current 2>nul").read().strip()
        if result:
            clues.append(result)
    except Exception:
        pass

    # 从当前目录名提取
    cwd = os.getcwd()
    if cwd:
        parts = Path(cwd).parts
        if len(parts) > 0:
            clues.append(parts[-1])

    return " ".join(clues)


def build_injection_message(memory_context: str) -> str:
    """
    将记忆上下文格式化为注入消息
    """
    lines = [
        "",
        "=" * 60,
        "【NEMT 云端记忆上下文】",
        "=" * 60,
        "",
        memory_context,
        "",
        "=" * 60,
        "【记忆上下文结束】",
        "=" * 60,
        "",
    ]
    return "\n".join(lines)


def build_system_prompt_override(current_context: str, current_task: str) -> str:
    """
    构建 system prompt 覆盖片段
    可注入到 Cursor 的 system prompt 中
    """
    sections = [
        "## 当前会话上下文",
        "",
        f"**会话时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**当前任务**: {current_task if current_task else '(未检测到)'}",
        "",
        "## 项目知识库摘要",
        "(来自云端 Obsidian 记忆库)",
        "",
    ]

    if current_context and len(current_context) > 100:
        sections.append(current_context)
    else:
        sections.append("*(记忆上下文加载中或为空)*")

    sections.extend([
        "",
        "## 使用指南",
        "- 如果你参考了以上知识库内容，请在回答开始时说明",
        "- 如果知识库内容与当前问题相关，请优先使用",
        "- 如有疑问，可通过查阅上述文件获取更多信息",
    ])

    return "\n".join(sections)


# ============================================================================
# 主函数
# ============================================================================

def main():
    """
    Hook 主函数：
    1. 读取会话状态（用户消息等）
    2. 获取当前任务线索
    3. 尝试从云端获取记忆上下文
    4. 尝试本地备选
    5. 输出记忆注入内容
    """
    log("=== NEMT Memory Session Start Hook ===")

    # 解析参数（Cursor hook 会通过 stdin 传递上下文）
    input_data = {}
    try:
        stdin_data = sys.stdin.read()
        if stdin_data.strip():
            input_data = json.loads(stdin_data)
    except Exception:
        pass

    # 提取当前任务线索
    current_task = extract_current_task()
    user_message = input_data.get("message", input_data.get("query", ""))
    git_branch = input_data.get("git_branch", "")

    if git_branch:
        current_task = f"{git_branch} {current_task}".strip()

    log(f"Current task: {current_task}")
    log(f"User message: {user_message[:100] if user_message else '(empty)'}")

    # 构建查询
    query = f"{current_task} {user_message}".strip()
    if not query:
        query = ""

    # 尝试从云端获取记忆
    memory_context = None
    source = "none"

    cache = load_cache()
    cache_key = hashlib.md5(query.encode()).hexdigest()

    if is_cache_valid(cache):
        log("Using cached memory")
        memory_context = cache.get("context", "")
        source = "cache"
    else:
        # 云端获取
        memory_context = fetch_cloud_memory(query=query)
        if memory_context:
            source = "cloud"
            log(f"Got {len(memory_context)} chars from cloud")

            # 存入缓存
            save_cache({
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "context": memory_context,
            })
        else:
            # 本地备选
            memory_context = fetch_local_fallback(query=query)
            if memory_context:
                source = "local"
                log(f"Got {len(memory_context)} chars from local")
            else:
                log("No memory source available", "WARN")

    # 输出结果
    if memory_context and len(memory_context) > 100:
        injection = build_injection_message(memory_context)
        system_prompt = build_system_prompt_override(memory_context, current_task)

        output = {
            "source": source,
            "injection": injection,
            "system_prompt_override": system_prompt,
            "task": current_task,
            "char_count": len(memory_context),
            "timestamp": datetime.now().isoformat(),
        }

        # 输出 JSON 给 Cursor
        print(json.dumps(output, ensure_ascii=False))
        log(f"Memory injected successfully ({len(memory_context)} chars, source={source})")
    else:
        # 无记忆时输出空
        output = {
            "source": source,
            "injection": "",
            "system_prompt_override": "",
            "task": current_task,
            "char_count": 0,
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(output, ensure_ascii=False))
        log("No memory to inject")


if __name__ == "__main__":
    # Python 重新配置输出编码
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    main()
