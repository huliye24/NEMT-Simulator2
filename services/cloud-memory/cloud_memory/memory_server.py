#!/usr/bin/env python3
"""
NEMT Cloud Memory Server
========================
云端 REST API 服务，供本地 Cursor Hook 调用获取记忆上下文。

端点:
  GET /memory          - 获取完整记忆上下文
  GET /memory?q=...    - 获取与查询相关的记忆上下文
  GET /memory/summary  - 获取记忆摘要
  GET /health          - 健康检查

运行方式:
  python3 memory_server.py

或使用 systemd 服务运行（见 notion-sync.service）
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from threading import Thread

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from cloud_memory_reader import ObsidianReader, MemoryConfig, get_memory_context, get_memory_summary

# ============================================================================
# 日志配置
# ============================================================================

LOG_DIR = Path("/root/quant-sync-server")
LOG_FILE = LOG_DIR / "memory_server.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("memory_server")

# ============================================================================
# 配置
# ============================================================================

VAULT_PATH = os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    "/root/obsidian_vault/NEMT_Notion"
)

PORT = int(os.environ.get("MEMORY_SERVER_PORT", "8765"))
HOST = os.environ.get("MEMORY_SERVER_HOST", "0.0.0.0")

# 缓存配置
CACHE_TTL_SECONDS = 60  # 60秒缓存
_cache = {"data": "", "timestamp": 0, "query": ""}


# ============================================================================
# 缓存
# ============================================================================

def get_cached(query: str = "") -> str | None:
    """获取缓存的记忆上下文"""
    now = datetime.now().timestamp()
    if (
        query == _cache.get("query", "")
        and now - _cache.get("timestamp", 0) < CACHE_TTL_SECONDS
    ):
        log.debug(f"Cache hit for query: {query[:50]}")
        return _cache.get("data")
    return None


def set_cache(query: str, data: str):
    """设置缓存"""
    _cache["query"] = query
    _cache["data"] = data
    _cache["timestamp"] = datetime.now().timestamp()


# ============================================================================
# HTTP Handler
# ============================================================================

class MemoryHandler(BaseHTTPRequestHandler):
    """记忆服务 HTTP 处理器"""

    def _send_json(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Memory-Version", "1.0")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _send_text(self, text: str, status: int = 200):
        """发送纯文本响应"""
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parsed.query
        params = parse_qs(query)

        log.info(f"GET {path} | query={query[:80] if query else ''}")

        try:
            if path == "/health":
                self._send_json({"status": "ok", "timestamp": datetime.now().isoformat()})

            elif path == "/memory":
                # 获取记忆上下文
                q = params.get("q", [params.get("query", [""])[0]])[0]
                max_chars = int(params.get("max_chars", ["8000"])[0])
                time_window = int(params.get("days", ["7"])[0])

                # 检查缓存
                cached = get_cached(q)
                if cached:
                    self._send_text(cached)
                    return

                # 获取记忆
                config = MemoryConfig(
                    vault_path=VAULT_PATH,
                    time_window_days=time_window,
                    max_chars=max_chars,
                )
                reader = ObsidianReader(config)
                items = reader.scan_vault(query=q)
                context = reader.build_context(items, query=q, max_chars=max_chars)

                # 格式化输出
                header = (
                    f"=== NEMT 记忆上下文 ===\n"
                    f"时间窗口: 最近 {time_window} 天\n"
                    f"记忆条目: {len(items)} 个\n"
                    f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"========================\n\n"
                )
                full_context = header + context + "\n\n========================\n=== 记忆上下文结束 ==="

                # 缓存
                set_cache(q, full_context)

                self._send_text(full_context)

            elif path == "/memory/summary":
                # 获取记忆摘要
                summary = get_memory_summary()
                self._send_json(summary)

            elif path == "/memory/list":
                # 列出所有可用记忆文件
                config = MemoryConfig(vault_path=VAULT_PATH)
                reader = ObsidianReader(config)
                items = reader.scan_vault()
                files = [
                    {
                        "title": i.title,
                        "path": i.path,
                        "priority": i.priority,
                        "modified": i.modified_time.isoformat(),
                        "category": i.category,
                    }
                    for i in sorted(items, key=lambda x: x.priority_key)
                ]
                self._send_json({"count": len(files), "files": files})

            elif path == "/memory/file":
                # 读取指定文件
                file_path = params.get("path", [""])[0]
                if not file_path:
                    self._send_json({"error": "missing path parameter"}, status=400)
                    return

                # 安全检查：防止路径遍历
                vault = Path(VAULT_PATH).resolve()
                target = Path(file_path).resolve()
                if not str(target).startswith(str(vault)):
                    self._send_json({"error": "path outside vault"}, status=403)
                    return

                if not target.exists():
                    self._send_json({"error": "file not found"}, status=404)
                    return

                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                self._send_json({
                    "path": str(target),
                    "content": content,
                    "size": len(content),
                })

            elif path == "/memory/search":
                # 简单关键词搜索
                q = params.get("q", [""])[0]
                if not q:
                    self._send_json({"error": "missing q parameter"}, status=400)
                    return

                config = MemoryConfig(vault_path=VAULT_PATH, time_window_days=30)
                reader = ObsidianReader(config)
                items = reader.scan_vault(query=q)

                self._send_json({
                    "query": q,
                    "count": len(items),
                    "results": [
                        {
                            "title": i.title,
                            "path": i.path,
                            "priority": i.priority,
                            "modified": i.modified_time.isoformat(),
                            "relevance": round(i.relevance_score, 2),
                        }
                        for i in sorted(items, key=lambda x: -x.relevance_score)
                    ]
                })

            else:
                self._send_json(
                    {
                        "error": "Not found",
                        "endpoints": [
                            "GET /health",
                            "GET /memory",
                            "GET /memory?q=query",
                            "GET /memory/summary",
                            "GET /memory/list",
                            "GET /memory/file?path=...",
                            "GET /memory/search?q=keyword",
                        ]
                    },
                    status=404
                )

        except Exception as e:
            log.error(f"Error handling {path}: {e}", exc_info=True)
            self._send_json({"error": str(e)}, status=500)

    def log_message(self, format, *args):
        """自定义日志格式"""
        log.info(format % args)


# ============================================================================
# 启动
# ============================================================================

def run_server(port: int = PORT, host: str = HOST):
    """启动服务器"""
    server = HTTPServer((host, port), MemoryHandler)
    log.info(f"记忆服务启动: http://{host}:{port}")
    log.info(f"Vault: {VAULT_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("服务器关闭")
        server.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port=port)
