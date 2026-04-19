import json

config = {
    "mcpServers": {
        "pycharm": {
            "command": "python",
            "args": ["pycharm_mcp_server.py"],
            "env": {"PYTHONPATH": "E:/NEMT Simulator"}
        },
        "matlab": {
            "command": "C:\\Program Files\\Python311\\python.exe",
            "args": ["matlab_mcp_server.py"],
            "env": {"PYTHONPATH": "E:/NEMT Simulator"}
        }
    }
}

with open("E:/NEMT Simulator/.cursor/mcp.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

print("MCP 配置已更新!")
