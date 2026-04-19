# 🔧 Tech Lead 驾驶舱

> 刷新时间：`= date(now)`

---

## 📥 我的收件箱（待我处理的开发任务）

```dataview
TABLE WITHOUT ID
    file.link AS "任务",
    priority AS "优先级",
    type AS "类型",
    status AS "状态",
    deadline AS "截止"
FROM "10_Inbox"
WHERE contains(owner, "TL") AND status != "✅ Done" AND status != "❌ Cancelled"
SORT priority DESC
```

---

## 🔍 需要我审查的代码（状态为"需审核"且指派给我的）

```dataview
TABLE WITHOUT ID
    file.link AS "任务/PR",
    author AS "发起人",
    deadline AS "截止"
FROM "10_Inbox" OR "60_Code_Reviews"
WHERE contains(owner, "TL") AND status = "👀 需审核"
```

---

## 🧨 技术债雷达（未偿还的技术债）

```dataview
TABLE WITHOUT ID
    file.link AS "技术债条目",
    severity AS "严重程度",
    status AS "状态",
    created AS "发现日期"
FROM "70_Tech_Debt"
WHERE status != "✅ 已偿还"
SORT severity DESC
```

---

## 📤 我派出去的任务（等待其他人反馈）

```dataview
TABLE WITHOUT ID
    file.link AS "任务",
    owner AS "当前负责人",
    status AS "状态"
FROM "10_Inbox"
WHERE contains(author, "TL") AND status != "✅ Done"
SORT owner ASC
```

---

## 📋 最近的架构决策（必读）

```dataview
TABLE WITHOUT ID
    file.link AS "决策",
    decision_date AS "日期",
    decision_maker AS "决策者"
FROM "30_Decisions"
SORT decision_date DESC
LIMIT 5
```

---

## 📊 Sprint 进度

| 指标 | 数值 |
|------|------|
| 总任务数 | - |
| 已完成 | - |
| 进行中 | - |
| 待处理 | - |

---

## ⚡ 快捷操作

- [ ] [新建任务](../20_Tasks/TASK_TEMPLATE.md)
- [ ] [报告技术债](../70_Tech_Debt/TD_TEMPLATE.md)
- [ ] [创建代码审查](../60_Code_Reviews/CR_TEMPLATE.md)
- [ ] [请求 CTO 裁决](../30_Decisions/DECISION_TEMPLATE.md)

---

*最后更新: `= date(now)`*
