# Agent 协作系统 - 四角色职责与任务

> 基于 Notion "四角色职责与权限映射" 设计
> 维护者: Founder Agent

---

## 四角色概览

| 角色 | 职责 | 关键任务 |
|------|------|----------|
| **CEO/Founder** | 维护愿景、对齐检查、最终裁决 | 愿景演化、偏离检测、决策审批 |
| **CTO** | 技术架构、技术决策、代码审查 | 架构设计、技术选型、代码审查 |
| **PM** | 任务管理、流程协调、进度跟踪 | 任务分配、周会组织、里程碑管理 |
| **Tech Lead** | 具体实现、代码开发、测试验证 | 功能开发、代码实现、单元测试 |

---

## 核心文档

- [[Agent_Collaboration/Notion_权限映射]] - Notion数据库权限设计
- [[Agent_Collaboration/Task_Inbox]] - 任务收件箱设计
- [[Agent_Collaboration/Decision_Log]] - 决策记录设计
- [[Agent_Collaboration/Async_Workflow]] - 异步协作流程详解

---

## 异步协作核心逻辑

```
VISION.md (灯塔)
    ↓ 每次任务创建时对照
Task Inbox (收件箱与工作流)
    ↓ 产生偏离争议时
Decision Log (仲裁记录)
    ↓ 归档经验
Vision Milestones (航程校验)
    ↓ 定期审查
Weekly Vision Sync (纠偏会议)
```

---

*此文档由 Founder Agent 根据 Notion 页面自动生成*
