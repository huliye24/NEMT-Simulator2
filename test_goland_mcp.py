#!/usr/bin/env python3
"""
测试 GoLand MCP Server
"""
import subprocess
import json
import sys

# MCP 服务器路径
SERVER = "E:/NEMT Simulator/goland_mcp_server.exe"

def send_request(req):
    """发送 MCP 请求并返回响应"""
    proc = subprocess.Popen(
        [SERVER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=json.dumps(req) + "\n", timeout=30)
    if stderr:
        print(f"Server: {stderr.strip()}")
    return json.loads(stdout.strip())

# 测试 1: initialize
print("=== Test 1: initialize ===")
resp = send_request({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
})
print(f"Result: {resp}")

# 测试 2: tools/list
print("\n=== Test 2: tools/list ===")
resp = send_request({
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
})
print(f"Tool count: {len(resp['result']['tools'])}")
for tool in resp['result']['tools']:
    print(f"  - {tool['name']}: {tool['description']}")

# 测试 3: go_info
print("\n=== Test 3: go_info ===")
resp = send_request({
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {"name": "go_info", "arguments": {}}
})
print(resp['result']['content'][0]['text'])

# 测试 4: go_version
print("\n=== Test 4: go_version ===")
resp = send_request({
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {"name": "go_version", "arguments": {}}
})
print(resp['result']['content'][0]['text'])

# 测试 5: go_env_var (GOROOT)
print("\n=== Test 5: go_env_var(GOROOT) ===")
resp = send_request({
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {"name": "go_env_var", "arguments": {"name": "GOROOT"}}
})
print(resp['result']['content'][0]['text'])

print("\nAll tests completed!")
