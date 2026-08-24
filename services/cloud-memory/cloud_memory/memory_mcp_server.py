#!/usr/bin/env python3
"""
NEMT Cloud Memory MCP Server
============================
MCP (Model Context Protocol) 服务器，为 Cursor IDE 提供云端记忆上下文。

使用方式：
  1. 配置 Cursor MCP settings
  2. Cursor 会话启动时自动通过 MCP 调用

MCP 工具：
  nemt_memory.get_context(query)  - 获取记忆上下文
  nemt_memory.search(keyword)    - 搜索记忆
  nemt_memory.summary()          - 获取记忆摘要
  nemt_memory.list_files()       - 列出可用记忆文件
  nemt_memory.read_file(path)     - 读取指定记忆文件
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Optional
from http.client import HTTPConnection
from urllib.parse import urlencode

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP] %(levelname)s: %(message)s",
)
log = logging.getLogger("mcp_memory")


# ============================================================================
# MCP 配置
# ============================================================================

CLOUD_SERVER = os.environ.get("NEMT_MEMORY_SERVER", "42.51.42.123:8765")
TIMEOUT = 10


# ============================================================================
# MCP 协议
# ============================================================================

def mcp_request(method: str, path: str, params: dict = None) -> dict:
    """通过 HTTP 向云端记忆服务发送 MCP 请求"""
    try:
        conn = HTTPConnection(CLOUD_SERVER, timeout=TIMEOUT)
        if params:
            query = urlencode(params)
            full_path = f"{path}?{query}"
        else:
            full_path = path

        headers = {
            "User-Agent": "NEMT-MCP/1.0",
            "Accept": "application/json, text/plain",
        }

        conn.request("GET", full_path, headers=headers)
        resp = conn.getresponse()

        data = resp.read().decode("utf-8", errors="replace")

        if resp.status == 200:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {"content": data, "_raw": True}
        else:
            return {"error": f"HTTP {resp.status}", "body": data}

    except Exception as e:
        log.error(f"MCP request failed: {e}")
        return {"error": str(e)}


# ============================================================================
# MCP 工具注册表
# ============================================================================

TOOLS = {
    "get_memory_context": {
        "description": "从云端 Obsidian 记忆库获取上下文，可按查询关键词过滤",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "当前任务/问题的关键词，用于相关性过滤",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "最大字符数",
                    "default": 8000,
                },
                "days": {
                    "type": "integer",
                    "description": "时间窗口（天）",
                    "default": 7,
                },
            },
        },
    },
    "search_memory": {
        "description": "在云端记忆库中搜索关键词",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词",
                },
            },
            "required": ["keyword"],
        },
    },
    "get_memory_summary": {
        "description": "获取记忆库摘要：条目数量、最近修改等",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "list_memory_files": {
        "description": "列出所有可用的记忆文件",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "read_memory_file": {
        "description": "读取指定记忆文件的内容",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径（相对路径或绝对路径）",
                },
            },
            "required": ["path"],
        },
    },
    "get_recent_tasks": {
        "description": "获取最近的任务记录和决策",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "返回数量",
                    "default": 5,
                },
            },
        },
    },
}


# ============================================================================
# MCP 协议处理器
# ============================================================================

def handle_initialize(params: dict) -> dict:
    """MCP initialize 请求"""
    log.info(f"Initialize: {params}")
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {
                "listChanged": True,
            }
        },
        "serverInfo": {
            "name": "nemt-memory",
            "version": "1.0.0",
        },
    }


def handle_list_tools(params: dict) -> dict:
    """MCP list_tools 请求"""
    return {
        "tools": [
            {
                "name": name,
                "description": info["description"],
                "inputSchema": info["inputSchema"],
            }
            for name, info in TOOLS.items()
        ]
    }


def handle_call_tool(name: str, params: dict) -> dict:
    """MCP call_tool 请求"""
    log.info(f"Call tool: {name} params={params}")

    try:
        if name == "get_memory_context":
            result = mcp_request(
                "GET",
                "/memory",
                {
                    "q": params.get("query", ""),
                    "max_chars": params.get("max_chars", 8000),
                    "days": params.get("days", 7),
                }
            )
            content = result.get("content", result.get("text", str(result)))
            return {
                "content": [
                    {
                        "type": "text",
                        "text": content,
                    }
                ]
            }

        elif name == "search_memory":
            result = mcp_request("GET", "/memory/search", {"q": params.get("keyword", "")})
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2),
                    }
                ]
            }

        elif name == "get_memory_summary":
            result = mcp_request("GET", "/memory/summary")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2),
                    }
                ]
            }

        elif name == "list_memory_files":
            result = mcp_request("GET", "/memory/list")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2),
                    }
                ]
            }

        elif name == "read_memory_file":
            result = mcp_request("GET", "/memory/file", {"path": params.get("path", "")})
            content = result.get("content", str(result))
            return {
                "content": [
                    {
                        "type": "text",
                        "text": content,
                    }
                ]
            }

        elif name == "get_recent_tasks":
            # 获取最近的决策和任务
            result = mcp_request("GET", "/memory", {"days": params.get("days", 7)})
            content = result.get("content", str(result))

            # 简单过滤：提取最近的决策
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
            return {
                "content": [
                    {
                        "type": "text",
                        "text": filtered or content[:2000],
                    }
                ]
            }

        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                "isError": True,
            }

    except Exception as e:
        log.error(f"Tool call failed: {e}")
        return {
            "content": [{"type": "text", "text": f"Error: {e}"}],
            "isError": True,
        }


# ============================================================================
# MCP JSON-RPC 处理
# ============================================================================

def handle_request(data: dict) -> Any:
    """处理单个 JSON-RPC 请求"""
    method = data.get("method", "")
    params = data.get("params", {})
    msg_id = data.get("id")

    result = None
    error = None

    if method == "initialize":
        result = handle_initialize(params)
    elif method == "tools/list":
        result = handle_list_tools(params)
    elif method == "tools/call":
        result = handle_call_tool(params.get("name", ""), params.get("arguments", {}))
    elif method == "ping":
        result = {"pong": True}
    else:
        error = {"code": -32601, "message": f"Method not found: {method}"}

    response = {"jsonrpc": "2.0", "id": msg_id}
    if error:
        response["error"] = error
    else:
        response["result"] = result

    return response


# ============================================================================
# 主循环
# ============================================================================

def main():
    """主循环：读取 stdin JSON-RPC 请求，输出响应"""
    log.info("NEMT Cloud Memory MCP Server started")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            request_data = json.loads(line)
            response = handle_request(request_data)

            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON: {e}")
            error_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }
            print(json.dumps(error_resp))
            sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            error_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {e}"},
            }
            print(json.dumps(error_resp))
            sys.stdout.flush()

    log.info("NEMT Cloud Memory MCP Server stopped")


if __name__ == "__main__":
    main()
