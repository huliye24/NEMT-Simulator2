# 📋 TL 任务模板（扩展版）

> 用于开发任务的卡片模板，包含技术验收字段

---

```yaml
---
task_id: T000
title: 任务标题
author: PM          # 发件人
owner: TL            # 收件人
status: 📥 待认领
priority: P1
type: 开发任务
vision_check: true
deadline: 2026-04-25
created: 2026-04-19
tags: [task, development]
related_decision:
related_milestone: "里程碑名称"
review_status: 未开始
---

# {{title}}

## 📋 需求描述

（PM 填写）

## 🛠️ 技术方案（TL 填写）

### 涉及模块
-

### 预计改动文件
-

### 关键设计决策
-

### 愿景对齐检查
- [ ] 是否引入 VISION.md 边界外的功能？
- [ ] 新增依赖是否符合架构原则？
- [ ] 代码是否增加了不必要的复杂度？

## ✅ 验收标准

### 功能验收（PM 提供）
- [ ]

### 技术验收（TL 自定）
- [ ] 单元测试覆盖率 > 80%
- [ ] 通过 Lint 检查
- [ ] 通过类型检查

### 架构合规检查
- [ ] 符合 [[VISION.md]] 或架构原则

## 📊 进度记录

| 日期 | 状态 | 进展 | 负责人 |
|------|------|------|--------|
| YYYY-MM-DD | 🚧 进行中 | 初始 | TL |

## 💬 讨论区

<!-- @ 相关人员协作 -->

## 📎 关联

- 关联决策: [[]]
- 关联技术债: [[]]
- Commit 记录: `commit-hash`
```

---

## 使用说明

1. 复制此模板到 `20_Tasks/` 目录
2. 填写 `task_id`（递增编号）
3. 填写需求描述（PM 提供）
4. TL 填写技术方案
5. 设置状态并开始开发

---

*模板来源: TechLead_Resources/Obsidian_Template/20_Tasks/TASK_TEMPLATE.md*
