import subprocess
import json
import sys

# 设置 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# MCP 服务器路径
SERVER = "E:/NEMT Simulator/goland_mcp_server.exe"

def send_request(req):
    """发送 MCP 请求并返回响应"""
    proc = subprocess.Popen(
        [SERVER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate(input=(json.dumps(req) + "\n").encode(), timeout=30)
    if stderr:
        print(f"Server: {stderr.decode()}")
    return json.loads(stdout.decode().strip())

# 测试 1: initialize
print("=== Test 1: initialize ===")
resp = send_request({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
})
print(resp)

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

# 测试 5: go_env_var
print("\n=== Test 5: go_env_var ===")
resp = send_request({
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {"name": "go_env_var", "arguments": {"name": "GOROOT"}}
})
print(resp['result']['content'][0]['text'])

print("\nAll tests completed!")
