# 📥 TL 收件箱

> Tech Lead 的任务收件箱，聚合所有指派给 TL 的任务

## 📋 待处理任务

```dataview
TABLE WITHOUT ID
    file.link AS "任务",
    priority AS "优先级",
    type AS "类型",
    status AS "状态",
    deadline AS "截止"
FROM "10_Inbox"
WHERE contains(owner, "TL")
SORT priority ASC, deadline ASC
```

## 🚧 进行中

```dataview
TABLE WITHOUT ID
    file.link AS "任务",
    priority AS "优先级",
    deadline AS "截止",
    review_status AS "审查状态"
FROM "10_Inbox"
WHERE contains(owner, "TL") AND status = "🚧 进行中"
SORT priority ASC
```

## 👀 待审核

```dataview
TABLE WITHOUT ID
    file.link AS "任务",
    author AS "作者",
    created AS "创建时间"
FROM "10_Inbox"
WHERE status = "👀 需审核"
SORT created DESC
```

## 📋 按类型分类

### 开发任务

```dataview
TABLE WITHOUT ID
    file.link AS "任务",
    priority AS "优先级",
    status AS "状态"
FROM "10_Inbox"
WHERE type = "开发任务" AND status != "✅ Done"
SORT priority ASC
```

### 决策请求

```dataview
TABLE WITHOUT ID
    file.link AS "决策",
    priority AS "优先级",
    status AS "状态",
    owner AS "裁决人"
FROM "10_Inbox"
WHERE type = "决策请求" AND status != "✅ Done"
SORT priority ASC
```

## ⚡ 快捷操作

- [新建开发任务](../20_Tasks/TASK_TEMPLATE.md)
- [新建决策请求](../30_Decisions/DECISION_TEMPLATE.md)
- [报告技术债](../70_Tech_Debt/TD_TEMPLATE.md)

---

*最后更新: `= date(now)`*
