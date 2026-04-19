# 任务收件箱

```yaml
# 按协议格式，此文件记录所有待处理任务
# 状态流转: 📥 待认领 → 🚧 进行中 → ⏸️ 阻塞 → 👀 需审核 → ✅ 完成 / ❌ 取消
```

---

## 待处理任务

### T-001: 24/7 加密货币策略系统技术方案审批

```yaml
task_id: T-001
title: 审批 24/7 系统技术方案
author: CTO
owner: CEO
status: 📥 待认领
priority: P1
type: 决策请求
vision_check: true
created: 2026-04-19
deadline: 2026-04-20
related_decision: "[[2026-04-19_24x7系统技术方案]]"
```

**描述**：CTO 提交了 24/7 加密货币策略系统的技术方案，需要 CEO 审批。

**候选方案**：
- 方案 A：Freqtrade 路线
- 方案 B：NautilusTrader 路线
- 方案 C：自研 + CCXT（推荐）

**请 CEO 在评论区给出裁决意见。**

---

### T-002: CCXT 数据层 POC

```yaml
task_id: T-002
title: CCXT 数据层概念验证
author: CTO
owner: Tech Lead
status: 📥 待认领
priority: P1
type: 开发任务
vision_check: true
created: 2026-04-19
deadline: 2026-04-26
related_decision: "[[2026-04-19_24x7系统技术方案]]"
depends_on: [T-001]
```

**描述**：基于批准的方案 C，完成 CCXT 数据层 POC。

**技术要求**：
- 安装 CCXT
- 实现 Binance 历史 K线获取
- 实现 WebSocket 实时行情订阅
- 数据存入 SQLite/PostgreSQL

**预估工时**: 2 人天

**technical_notes**: 
```
1. pip install ccxt
2. 创建 nemt_data/fetcher.py
3. 创建 nemt_data/websocket.py
4. 测试 Binance API 连接
```

---

### T-003: 技术债务清理 - P0 级

```yaml
task_id: T-003
title: 清理 P0 级技术债务
author: CTO
owner: Tech Lead
status: 📥 待认领
priority: P0
type: 开发任务
vision_check: true
created: 2026-04-19
deadline: 2026-04-20
related_decision: "[[2026-04-19_技术债务清理计划]]"
```

**描述**：清理以下 P0 级技术债务：

**P0-001**: Notion API Token 硬编码
- 位置: `notion_theory_sync.py:21`
- 修复: 改用环境变量

**P0-002**: API Server 多版本并存
- 位置: `quant-sync-server/`
- 修复: 合并到一个版本

**预估工时**: 5h

---

### T-004: NEMT Core 集成到回测引擎

```yaml
task_id: T-004
title: NEMT Core 集成
author: CTO
owner: CTO
status: 📥 待认领
priority: P1
type: 开发任务
vision_check: true
created: 2026-04-19
deadline: 2026-05-03
depends_on: [T-002]
phase: Phase 3
```

**描述**：将 NEMT Core 集成到回测引擎。

**任务**：
1. 封装 NEMT Core 为可调用模块
2. 实现信号生成器接口
3. 连接回测引擎数据流

**预估工时**: 8h

---

## 已完成任务

| Task ID | 标题 | 完成日期 | 关联决策 |
|---------|------|----------|----------|
| - | - | - | - |

---

## 状态统计

| 状态 | 数量 |
|------|------|
| 📥 待认领 | 4 |
| 🚧 进行中 | 0 |
| ⏸️ 阻塞 | 0 |
| 👀 需审核 | 0 |
| ✅ 完成 | 0 |

---

*由 CTO Agent 维护*
*最后更新: 2026-04-19*
