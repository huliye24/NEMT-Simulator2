# Obsidian 模板文件夹

> 这是 Tech Lead 在 Obsidian 中的标准目录结构，可直接复制到 Obsidian 库中使用。

## 目录结构

```
Obsidian_Template/
├── TL_COCKPIT.md              # TL 驾驶舱（每日必看）
├── TL_INBOX.md               # TL 收件箱
├── README.md                  # 本文件
│
├── 00_Vision/                # 灯塔（只读）
│   └── VISION_EXCERPT.md     # 愿景摘要（关键条款）
│
├── 10_Inbox/                 # 任务收件箱
│   └── TASK_INBOX_TEMPLATE.md
│
├── 20_Tasks/                 # 详细任务卡片
│   ├── TASK_TEMPLATE.md      # 任务模板（含技术字段）
│   └── EXAMPLE_TASK.md       # 示例任务
│
├── 30_Decisions/            # 技术决策记录
│   ├── DECISION_TEMPLATE.md
│   └── EXAMPLE_DECISION.md
│
├── 60_Code_Reviews/         # 代码审查记录
│   ├── CR_TEMPLATE.md
│   └── EXAMPLE_CR.md
│
└── 70_Tech_Debt/           # 技术债跟踪
    ├── TD_TEMPLATE.md
    └── EXAMPLE_TD.md
```

## 使用方法

### 方法一：复制整个文件夹

1. 将 `Obsidian_Template` 整个复制到你的 Obsidian 库根目录
2. 重命名为你想要的名称（如 `TechLead/`）

### 方法二：按需复制

只复制你需要的部分到 Obsidian 库中

## 核心文件说明

### TL_COCKPIT.md
每天打开 Obsidian 首先看的控制台，包含：
- 我的收件箱
- 待审查代码
- 技术债雷达
- 我派出去的任务
- 最新架构决策

### TASK_TEMPLATE.md
任务卡片模板，扩展了技术字段：
- `technical_notes`: 技术实现要点
- `review_status`: 审查状态
- `vision_check`: 愿景对齐检查

## Obsidian 推荐插件

| 插件 | 用途 |
|------|------|
| Dataview | 生成驾驶舱中的查询表格 |
| Tasks | 任务状态管理 |
| Templater | 快速生成模板 |
| Advanced Tables | 表格编辑 |
| Obsidian Git | Git 同步 |

## Dataview 查询说明

这些 Dataview 查询需要在 Obsidian 中安装 Dataview 插件才能正常工作。

### 查询任务

```dataview
TABLE ...
FROM "10_Inbox"
WHERE ...
```

### 自定义查询

如果你的任务存储在其他位置，修改 `FROM` 路径即可。

## 状态符号约定

| 符号 | 含义 |
|------|------|
| 📥 | 待认领 |
| 🚧 | 进行中 |
| 👀 | 需审核 |
| ✅ | 已完成 |
| ❌ | 已取消 |
| 🕒 | 待排期 |

## 优先级约定

| 优先级 | 含义 |
|--------|------|
| P0 | 最高优先级，阻塞其他工作 |
| P1 | 高优先级，本周内完成 |
| P2 | 中优先级，本 Sprint 完成 |
| P3 | 低优先级，下个 Sprint |

---

*创建时间: 2026-04-19*
*基于: Tech Lead 生产关系操作手册*
