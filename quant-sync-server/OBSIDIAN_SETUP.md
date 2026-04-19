# Obsidian MCP Server 配置指南

## 快速开始

### 1. 安装 Obsidian 插件

1. 打开 Obsidian
2. 设置 → 第三方插件 → 社区插件市场
3. 搜索 "Local REST API"
4. 安装并启用插件
5. 设置 → Local REST API → 复制 API Key

### 2. 配置 API Key

创建 `quant-sync-server/obsidian.env` 文件:

```bash
OBSIDIAN_API_KEY=你的API密钥
OBSIDIAN_HOST=127.0.0.1
OBSIDIAN_PORT=27124
OBSIDIAN_VAULT=NEMT-Simulator
```

### 3. 测试连接

```bash
cd quant-sync-server
python sync_to_obsidian.py
```

如果连接成功，将自动同步以下内容到 Obsidian:
- 00-项目总览.md
- TechTree/科技树.md
- WorkLog/工作日志.md
- NodeTasks/节点任务.md
- DesignSchemes/设计方案.md

---

## MCP Server 使用

### 在 Cursor 中配置 MCP

1. 编辑 `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["quant-sync-server/obsidian_mcp_server.py"],
      "env": {
        "OBSIDIAN_API_KEY": "你的API密钥"
      }
    }
  }
}
```

2. 重启 Cursor

### MCP 工具列表

| 工具名称 | 功能 |
|---------|------|
| `obsidian_create_note` | 创建或更新笔记 |
| `obsidian_read_note` | 读取笔记内容 |
| `obsidian_search` | 搜索笔记 |
| `obsidian_list_notes` | 列出所有笔记 |
| `obsidian_get_status` | 检查连接状态 |

---

## 同步的数据

### 从 Notion 同步

| Notion 数据库 | Obsidian 笔记 |
|--------------|--------------|
| TechTree | TechTree/科技树.md |
| NEMT_WorkLog | WorkLog/工作日志.md |
| Node开发任务 | NodeTasks/节点任务.md |
| DesignSchemes | DesignSchemes/设计方案.md |

---

## 常见问题

### Q: 连接失败?

1. 确认 Obsidian 正在运行
2. 确认 Local REST API 插件已启用
3. 确认 API Key 正确
4. 检查防火墙设置

### Q: 如何手动触发同步?

```bash
cd quant-sync-server
python sync_to_obsidian.py
```

### Q: 如何在代码中使用 Obsidian?

```python
from obsidian_mcp_server import handle_create_note

result = handle_create_note(
    path="Projects/NEMT/new-note",
    content="# New Note\n\nContent here..."
)
```

---

## 文件列表

```
quant-sync-server/
├── obsidian_mcp_server.py   # MCP 服务器
├── sync_to_obsidian.py      # 同步脚本
└── obsidian.env.example     # 配置示例
```
