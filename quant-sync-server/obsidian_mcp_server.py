#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian MCP Server
===================
通过 Local REST API 与 Obsidian 交互的 MCP 服务器

安装依赖:
    pip install requests

使用前:
1. 在 Obsidian 中安装 "Local REST API" 插件
2. 启用插件并获取 API Key
3. 设置环境变量 OBSIDIAN_API_KEY

运行方式:
    python obsidian_mcp_server.py

然后在 Cursor 中配置 MCP 使用这个服务器
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

# MCP Protocol imports
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============ 配置 ============
OBSIDIAN_API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")
OBSIDIAN_HOST = os.environ.get("OBSIDIAN_HOST", "127.0.0.1")
OBSIDIAN_PORT = os.environ.get("OBSIDIAN_PORT", "27124")

BASE_URL = f"https://{OBSIDIAN_HOST}:{OBSIDIAN_PORT}"


def get_headers():
    return {
        'Authorization': f'Bearer {OBSIDIAN_API_KEY}',
        'Content-Type': 'application/json',
    }


def check_connection() -> Dict[str, Any]:
    """检查 Obsidian API 连接状态"""
    try:
        response = requests.get(
            f"{BASE_URL}/vault/",
            headers=get_headers(),
            verify=False,
            timeout=5
        )
        if response.status_code == 200:
            return {"status": "connected", "data": response.json()}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============ MCP 工具定义 ============

TOOLS = [
    {
        "name": "obsidian_create_note",
        "description": "创建或更新 Obsidian 笔记",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "笔记路径 (如: 'Projects/NEMT/overview')"},
                "content": {"type": "string", "description": "笔记内容 (Markdown)"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "obsidian_read_note",
        "description": "读取 Obsidian 笔记内容",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "笔记路径"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "obsidian_search",
        "description": "搜索 Obsidian 笔记",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "obsidian_list_notes",
        "description": "列出 vault 中的所有笔记",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "文件夹路径 (可选)"}
            }
        }
    },
    {
        "name": "obsidian_get_status",
        "description": "获取 Obsidian 连接状态",
        "input_schema": {"type": "object", "properties": {}}
    }
]


# ============ MCP 处理函数 ============

def handle_create_note(path: str, content: str) -> Dict[str, Any]:
    """创建或更新笔记"""
    try:
        response = requests.put(
            f"{BASE_URL}/vault/{path}",
            headers=get_headers(),
            data=content.encode('utf-8'),
            verify=False
        )
        
        if response.status_code in [200, 201]:
            return {"success": True, "path": path}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_read_note(path: str) -> Dict[str, Any]:
    """读取笔记"""
    try:
        response = requests.get(
            f"{BASE_URL}/vault/{path}",
            headers=get_headers(),
            verify=False
        )
        
        if response.status_code == 200:
            return {"success": True, "content": response.text, "path": path}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_search(query: str) -> Dict[str, Any]:
    """搜索笔记"""
    try:
        response = requests.get(
            f"{BASE_URL}/search/",
            headers=get_headers(),
            params={"query": query},
            verify=False
        )
        
        if response.status_code == 200:
            return {"success": True, "results": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_list_notes(folder: str = "") -> Dict[str, Any]:
    """列出笔记"""
    try:
        url = f"{BASE_URL}/vault/"
        if folder:
            url += f"{folder}/"
        
        response = requests.get(url, headers=get_headers(), verify=False)
        
        if response.status_code == 200:
            return {"success": True, "files": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_get_status() -> Dict[str, Any]:
    """获取连接状态"""
    status = check_connection()
    return {
        "success": True,
        "status": status.get("status"),
        "message": "Obsidian MCP Server ready" if status.get("status") == "connected" else status.get("message", "Unknown error")
    }


# ============ MCP STDIO 服务器 ============

def run_stdio_server():
    """以 STDIO 模式运行 MCP 服务器 (用于 Cursor)"""
    print("[INFO] Obsidian MCP Server starting (stdio mode)...", file=sys.stderr)
    
    # 读取初始化请求
    init_request = json.loads(sys.stdin.readline())
    
    # 发送初始化响应
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": init_request.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "obsidian-mcp-server",
                "version": "1.0.0"
            }
        }
    }), file=sys.stdout)
    sys.stdout.flush()
    
    # 处理请求循环
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            request_id = request.get("id")
            
            if method == "tools/list":
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": TOOLS}
                }), file=sys.stdout)
            
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name == "obsidian_create_note":
                    result = handle_create_note(**tool_args)
                elif tool_name == "obsidian_read_note":
                    result = handle_read_note(**tool_args)
                elif tool_name == "obsidian_search":
                    result = handle_search(**tool_args)
                elif tool_name == "obsidian_list_notes":
                    result = handle_list_notes(**tool_args)
                elif tool_name == "obsidian_get_status":
                    result = handle_get_status()
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                    }
                }), file=sys.stdout)
            
            sys.stdout.flush()
            
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)


# ============ HTTP 服务器 (可选) ============

def run_http_server(host: str = "0.0.0.0", port: int = 8080):
    """以 HTTP 模式运行服务器"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route('/note/<path:path>', methods=['GET', 'PUT', 'POST', 'DELETE'])
    def handle_note(path):
        if request.method == 'GET':
            result = handle_read_note(path)
        elif request.method in ['PUT', 'POST']:
            content = request.data.decode('utf-8')
            result = handle_create_note(path, content)
        elif request.method == 'DELETE':
            result = {"success": False, "message": "Delete not implemented"}
        else:
            result = {"success": False, "message": "Method not allowed"}
        
        return jsonify(result)
    
    @app.route('/search')
    def search():
        query = request.args.get('q', '')
        return jsonify(handle_search(query))
    
    @app.route('/status')
    def status():
        return jsonify(handle_get_status())
    
    print(f"[INFO] Obsidian MCP Server running on http://{host}:{port}")
    app.run(host=host, port=port)


# ============ 主入口 ============

def main():
    print("=" * 60)
    print("Obsidian MCP Server")
    print("=" * 60)
    
    if not OBSIDIAN_API_KEY:
        print("\n[ERROR] OBSIDIAN_API_KEY not set!")
        print("")
        print("设置方法:")
        print("  Windows: set OBSIDIAN_API_KEY=your-api-key")
        print("  或在 .env 文件中设置")
        print("")
        print("获取 API Key:")
        print("  1. 打开 Obsidian")
        print("  2. 设置 → Local REST API")
        print("  3. 复制 API Key")
        return
    
    # Check connection
    status = check_connection()
    if status.get("status") == "connected":
        print("\n[OK] Connected to Obsidian")
    else:
        print(f"\n[WARN] Connection failed: {status.get('message')}")
        print("Please check:")
        print("  1. Obsidian is running")
        print("  2. Local REST API plugin is enabled")
        print("  3. API Key is correct")
    
    # Run mode
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8080
        run_http_server(host, port)
    else:
        run_stdio_server()


if __name__ == "__main__":
    main()
