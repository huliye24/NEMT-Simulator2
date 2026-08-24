#!/usr/bin/env python3
"""
NEMT Cloud MCP Server (SSE版本)
================================
支持 Cursor MCP SSE 连接的云端 MCP 服务器

运行方式:
    python3 mcp_server_sse.py

端口: 8766
SSE 端点: http://42.51.42.123:8766/sse
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Any, Optional, Dict, Set
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import queue

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from cloud_memory_reader import ObsidianReader, MemoryConfig, get_memory_context, get_memory_summary

# ============================================================================
# 日志配置
# ============================================================================

LOG_FILE = Path("/root/quant-sync-server/mcp_sse.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP-SSE] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("mcp_sse")

# ============================================================================
# MCP 工具注册表
# ============================================================================

TOOLS = {
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
                "keyword": {"type": "string", "description": "搜索关键词"},
            },
            "required": ["keyword"],
        },
    },
    "get_memory_summary": {
        "description": "获取记忆摘要",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "list_memory_files": {
        "description": "列出所有记忆文件",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "read_memory_file": {
        "description": "读取指定记忆文件",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
            },
            "required": ["path"],
        },
    },
    "get_recent_tasks": {
        "description": "获取最近任务和决策",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 5},
            },
        },
    },
}

# ============================================================================
# SSE 连接管理
# ============================================================================

class SSEClient:
    """SSE 客户端连接"""
    def __init__(self, client_id: str, output_queue: queue.Queue):
        self.client_id = client_id
        self.output_queue = output_queue
        self.subscribed_events = set()

    def send_event(self, event: str, data: Any):
        """发送 SSE 事件"""
        self.output_queue.put({
            "event": event,
            "data": data
        })

clients: Dict[str, SSEClient] = {}
client_counter = 0
client_lock = threading.Lock()


def get_memory_context(query: str = "", max_chars: int = 8000, days: int = 7) -> str:
    """获取记忆上下文"""
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
    return header + context


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """处理工具调用"""
    log.info(f"Tool call: {tool_name} args={arguments}")

    try:
        if tool_name == "get_memory_context":
            content = get_memory_context(
                query=arguments.get("query", ""),
                max_chars=arguments.get("max_chars", 8000),
                days=arguments.get("days", 7)
            )
            return {"content": [{"type": "text", "text": content}]}

        elif tool_name == "search_memory":
            VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", "/root/obsidian_vault/NEMT_Notion")
            config = MemoryConfig(vault_path=VAULT_PATH, time_window_days=30)
            reader = ObsidianReader(config)
            items = reader.scan_vault(query=arguments.get("keyword", ""))
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "count": len(items),
                        "results": [
                            {"title": i.title, "path": i.path, "priority": i.priority}
                            for i in sorted(items, key=lambda x: -x.relevance_score)
                        ]
                    }, ensure_ascii=False, indent=2)
                }]
            }

        elif tool_name == "get_memory_summary":
            summary = get_memory_summary()
            return {"content": [{"type": "text", "text": json.dumps(summary, ensure_ascii=False, indent=2)}]}

        elif tool_name == "list_memory_files":
            VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", "/root/obsidian_vault/NEMT_Notion")
            config = MemoryConfig(vault_path=VAULT_PATH)
            reader = ObsidianReader(config)
            items = reader.scan_vault()
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "count": len(items),
                        "files": [
                            {"title": i.title, "path": i.path, "priority": i.priority}
                            for i in sorted(items, key=lambda x: x.priority_key)
                        ]
                    }, ensure_ascii=False, indent=2)
                }]
            }

        elif tool_name == "read_memory_file":
            VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", "/root/obsidian_vault/NEMT_Notion")
            file_path = arguments.get("path", "")
            vault = Path(VAULT_PATH).resolve()
            target = (vault / file_path).resolve()
            if not str(target).startswith(str(vault)):
                return {"content": [{"type": "text", "text": "Path outside vault"}], "isError": True}
            if not target.exists():
                return {"content": [{"type": "text", "text": "File not found"}], "isError": True}
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {"content": [{"type": "text", "text": content}]}

        elif tool_name == "get_recent_tasks":
            content = get_memory_context(days=arguments.get("count", 7))
            lines = content.split("\n")
            decision_lines = []
            in_decision = False
            for line in lines:
                if "决策" in line or "Decision" in line or "任务" in line:
                    in_decision = True
                if in_decision:
                    decision_lines.append(line)
                    if len(decision_lines) > 50:
                        break
            filtered = "\n".join(decision_lines) if decision_lines else content[:2000]
            return {"content": [{"type": "text", "text": filtered}]}

        else:
            return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

    except Exception as e:
        log.error(f"Tool error: {e}", exc_info=True)
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}


# ============================================================================
# HTTP Handler
# ============================================================================

class MCPHandler(BaseHTTPRequestHandler):
    """MCP SSE HTTP 处理器"""

    def _send_json(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _send_sse(self, event: str, data: Any, event_id: str = None):
        """发送 SSE 事件"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        if event_id:
            self.send_header("X-Event-ID", str(event_id))
        self.end_headers()

        message = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        try:
            self.wfile.write(message.encode("utf-8"))
            self.wfile.flush()
        except Exception as e:
            log.error(f"SSE send error: {e}")

    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parsed.query

        log.info(f"GET {path}")

        if path == "/health":
            self._send_json({"status": "ok", "timestamp": datetime.now().isoformat()})

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

            # 发送初始连接事件
            self._send_sse("connected", {
                "client_id": client_id,
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "nemt-cloud-mcp", "version": "1.0.0"},
                "capabilities": {"tools": {"listChanged": True}},
                "tools": [
                    {"name": name, "description": info["description"], "inputSchema": info["inputSchema"]}
                    for name, info in TOOLS.items()
                ]
            })

            # 保持连接并发送事件
            try:
                while True:
                    try:
                        event_data = output_queue.get(timeout=30)
                        self._send_sse(event_data["event"], event_data["data"])
                    except queue.Empty:
                        # 发送心跳
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

        elif path == "/memory":
            params = parse_qs(query)
            content = get_memory_context(
                query=params.get("q", [""])[0],
                max_chars=int(params.get("max_chars", ["8000"])[0]),
                days=int(params.get("days", ["7"])[0])
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))

        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        """处理 POST 请求"""
        parsed = urlparse(self.path)
        path = parsed.path

        log.info(f"POST {path}")

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

            # 广播到所有 SSE 客户端
            with client_lock:
                for client in clients.values():
                    client.send_event("tool_response", {
                        "tool": tool_name,
                        "result": result
                    })

        else:
            self._send_json({"error": "Not found"}, status=404)

    def log_message(self, format, *args):
        log.info(format % args)


# ============================================================================
# 启动
# ============================================================================

PORT = int(os.environ.get("MCP_SSE_PORT", "8766"))
HOST = "0.0.0.0"

def run_server():
    server = HTTPServer((HOST, PORT), MCPHandler)
    log.info(f"MCP SSE Server started: http://{HOST}:{PORT}")
    log.info(f"SSE endpoint: http://42.51.42.123:{PORT}/sse")
    log.info(f"Tools: {list(TOOLS.keys())}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Server shutdown")
        server.shutdown()

if __name__ == "__main__":
    run_server()
