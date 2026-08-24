# NEMT Memory System (Plan B)
> Agent-Driven Active Memory System for Cursor
> 解决 Cursor AI 记忆问题的方案 B：Agent 驱动主动记忆

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     Cursor Agent Session                      │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │ READ Phase  │ → │   Working   │ → │ CHECKPOINT Phase│   │
│  │             │   │   Phase     │   │                 │   │
│  │ Context     │   │             │   │ Checkpoint      │   │
│  │ Injector    │   │ Memory      │   │ Generator       │   │
│  │ (R1-R4)     │   │ Writer      │   │                 │   │
│  │             │   │ (T1-T5)     │   │ Active          │   │
│  │             │   │             │   │ Retriever       │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
│        ↑                ↓                    ↑               │
└────────┼────────────────┼────────────────────┼───────────────┘
         │                ↓                    │
         │         ┌──────────────┐           │
         │         │  Notion API  │           │
         │         │  (优先)      │           │
         │         └──────┬───────┘           │
         │                ↓                   │
         │         ┌──────────────┐           │
         │         │ 本地回退     │           │
         │         │ (Markdown)   │           │
         │         └──────────────┘           │
         │                                              │
         └────── Notion Database ──────────────────────┘
```

## 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 配置系统 | `nemt_sync_config.py` | 跨平台配置、路径解析、Token 加载 |
| 本地回退 | `local_fallback.py` | Markdown 本地存储、降级写入、同步日志 |
| Notion 查询 | `notion_query.py` | Notion 数据库只读查询、降级逻辑 |
| 上下文注入器 | `context_injector.py` | 会话启动时检索记忆 (READ Phase) |
| 记忆写入器 | `memory_writer.py` | T1-T5 触发器、自动沉淀 |
| 主动检索器 | `active_retriever.py` | R1-R4 主动检索、Checkpoint 生成 |

## 文件结构

```
notion_sync/
├── nemt_sync_config.py       # 跨平台配置（核心）
├── local_fallback.py         # 本地回退存储
├── notion_query.py           # Notion 查询客户端
├── context_injector.py       # Context Injector (READ Phase)
├── memory_writer.py          # Memory Writer (T1-T5 triggers)
├── active_retriever.py       # Active Retriever + Checkpoint
├── extended_schemas.py       # 扩展的 Notion Schema
├── setup_databases.py        # 数据库创建脚本
├── e2e_test.py              # 端到端测试
├── .env.example              # 环境变量模板
├── database_config.json      # 数据库配置（创建后生成）
└── local_fallback/          # 本地回退目录
    ├── decisions/
    ├── experiences/
    ├── failures/
    └── sync_log.json
```

## 快速开始

### 1. 配置 Notion Token

```bash
# 复制模板
copy notion_sync\.env.example notion_sync\.env

# 编辑 .env，填入你的 Notion Integration Token
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxx
```

获取 Token: https://www.notion.so/my-integrations

### 2. 创建数据库

```bash
cd notion_sync
python setup_databases.py --extended
```

这会在 Notion 中创建 4 个数据库：
- Decisions (决策记录) - 扩展版
- Experiences (经验沉淀) - 新建
- Failures (失败记录) - 新建
- Tasks (任务) - 扩展版

### 3. 测试系统

```bash
python e2e_test.py
```

### 4. 在 Cursor Agent 中使用

```python
# 在 Agent 启动时
from notion_sync.context_injector import get_context_injector

injector = get_context_injector()
bundle = injector.inject_from_session_context()
context_text = bundle.to_context_prompt()
# 将 context_text 追加到 Agent 系统提示

# 在 Agent 每次响应后
from notion_sync.memory_writer import get_memory_writer

writer = get_memory_writer()
writer.auto_write(user_message=msg, agent_response=response)

# 在会话结束时
from notion_sync.active_retriever import CheckpointGenerator

checkpoint = CheckpointGenerator()
session = checkpoint.create_session(session_id="xxx")
checkpoint_output = checkpoint.generate(session)
# 输出 checkpoint 或追加到日志
```

## 触发器详解

| 触发器 | 类型 | 说明 | 阈值 |
|--------|------|------|------|
| T1 | 显式 | 用户说"记录"、"memori"、"写下来" | 0.95 |
| T2 | 隐式 | 检测到技术决策（方案选择、架构决策） | 0.70 |
| T3 | 隐式 | 检测到成功经验（✅ 修复了、解决了） | 0.65 |
| T4 | 隐式 | 检测到错误（SyntaxError、RuntimeError 等） | 0.90 |
| T5 | 定时 | 会话结束检查（总结性记录） | 0.50 |

## 检索策略详解

| 策略 | 类型 | 说明 | 权重 |
|------|------|------|------|
| R1 | 标签匹配 | 基于项目标签精确匹配 | 高 |
| R2 | 时间衰减 | 最近 14 天半衰期 | 中 |
| R3 | 失败优先 | 活跃失败记录权重最高 | 极高 |
| R4 | 关联决策 | 关联已有决策的经验权重更高 | 高 |

## Notion Schema 扩展

### Decisions (扩展)

新增字段：
- `结论`: 一句话结论 [必须]
- `理由`: 决策理由 [必须]
- `质量评分`: high/medium/low
- `需回顾`: checkbox，勾选后会在 Checkpoint 中提醒
- `对齐原则`: multi_select（策略即有机体、Kitchen Theory 等）
- `违反边界`: multi_select（禁止实盘、禁止前端等）

### Experiences (新建)

- `类型`: solution/mistake/diagnostic/decision/observation
- `摘要`: 一句话总结 [Agent 生成]
- `详细`: 详细记录
- `有用度`: 1-5 分，人类评分
- `已验证`: checkbox
- `已过时`: checkbox

### Failures (新建)

- `类别`: validation/integration/logic/data/boundary
- `状态`: 活跃/调查中/已解决
- `症状`: 问题表现
- `根因`: 根因分析
- `解决方案`: 解决方向或已执行的方案

## 本地回退机制

当 Notion API 不可用时：

1. **自动降级**: 写入操作自动切换到本地 Markdown
2. **[PENDING] 标记**: 文件名前缀标记待同步状态
3. **同步日志**: `sync_log.json` 记录同步历史
4. **自动恢复**: Notion 恢复后可手动触发同步

```
decisions/
├── [PENDING]_2026-04-21_123456_验证层集成.md   ← 待同步
└── 2026-04-21_123000_Phase检测优化.md          ← 已同步
```

## 降级场景处理

| 场景 | 行为 | 用户感知 |
|------|------|----------|
| Token 未配置 | 静默降级到本地 | 无感知，文件写入本地 |
| Rate Limit (429) | 等待后重试 1 次 | 首次可能延迟 |
| 网络错误 | 降级到本地 | 无感知 |
| DB 不存在 | 降级到本地 | 无感知（仅 log 警告） |
| 字段不匹配 | 写入已知字段，跳过未知 | 字段可能缺失 |

## 与 Cursor 的集成方式

### 方式 1: Cursor Rule (推荐)

创建 `.cursor/rules/memory_system.md`:

```markdown
# NEMT Memory System

## 会话启动 (READ)
每次会话开始时，执行：
1. 从 notion_sync/context_injector.py 加载 ContextInjector
2. 调用 injector.inject_from_session_context()
3. 将返回的 bundle.to_context_prompt() 追加到系统提示

## 会话进行中
每次 Agent 响应后，执行：
1. 从 notion_sync/memory_writer.py 加载 MemoryWriter
2. 调用 writer.auto_write(user_message, agent_response)
3. 自动捕获 T1-T5 触发器

## 会话结束 (CHECKPOINT)
会话结束时，执行：
1. 从 notion_sync/active_retriever.py 加载 CheckpointGenerator
2. 调用 checkpoint.generate(session)
3. 输出或保存 Checkpoint 报告
```

### 方式 2: MCP Server

将 memory system 作为 MCP Server 暴露：

```python
# notion_sync/mcp_server.py
# 暴露工具：retrieve_memories, write_decision, write_experience, generate_checkpoint
```

### 方式 3: 直接调用

在 Cursor Agent 的 Python 工具中直接调用。

## 下一步

1. [ ] 在 Cursor 中配置 Rule，启用 Memory System
2. [ ] 配置 Notion Token，开始实际使用
3. [ ] 根据使用反馈，调整 T1-T5 触发阈值
4. [ ] 补充更多触发器模式（覆盖你的常见工作流）
5. [ ] 添加 Obsidian → Notion 反向同步（当前是 stub）
