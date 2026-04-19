# 依赖矩阵
> 任务和模块之间的依赖关系

## 一、模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                     模块依赖图                              │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────┐
                    │  Market  │
                    │  (市场)  │
                    └────┬─────┘
                         │
                         ▼
                    ┌──────────┐
                    │  Model   │
                    │  (模型)  │
                    └────┬─────┘
                         │
                         ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│ Capital  │◀─────│ Strategy │─────▶│  Risk   │
│ (资金)  │      │ (策略)  │      │  (风控) │
└────┬─────┘      └──────────┘      └────┬─────┘
     │                                       │
     └───────────────┬───────────────────────┘
                     │
                     ▼
              ┌──────────┐
              │Execution │
              │  (执行)  │
              └──────────┘
```

## 二、模块依赖表

| 模块 | 依赖模块 | 依赖类型 | 原因 |
|------|----------|----------|------|
| Market | - | 无 | 底层模块 |
| Model | Market | 数据输入 | 需要市场数据 |
| Strategy | Model | 信号输入 | 需要模型信号 |
| Capital | Strategy | 订单输入 | 需要订单数据 |
| Risk | Strategy, Capital | 校验 | 需要订单和分配 |
| Execution | Risk | 风控校验 | 需要风控通过 |

## 三、节点开发依赖

| 节点 | 前置依赖 | 后置依赖 | 并行开发可能 |
|------|----------|----------|--------------|
| Market | 无 | Model, Strategy | ✅ 完全独立 |
| Model | Market | Strategy | ⚠️ 需 Mock Market |
| Strategy | Model | Capital, Risk | ⚠️ 需 Mock Model |
| Capital | Strategy | Risk, Execution | ⚠️ 需 Mock Strategy |
| Risk | Strategy, Capital | Execution | ⚠️ 需 Mock 两者 |
| Eviction | Strategy, Execution | 无 | ⚠️ 需 Mock 两者 |

## 四、任务依赖

### 4.1 Sprint 1 任务

| 任务 ID | 任务 | 依赖 | 优先级 | 状态 |
|---------|------|------|--------|------|
| TASK-001 | 创建 MarketNode 基类 | 无 | P1 | 🔜 待开发 |
| TASK-002 | 实现 MockMarketProvider | TASK-001 | P1 | 🔜 待开发 |
| TASK-003 | 创建 ModelNode 基类 | 无 | P1 | 🔜 待开发 |
| TASK-004 | 实现 NEMT Core | TASK-003 | P1 | 🔜 待开发 |
| TASK-005 | 创建 StrategyNode 基类 | TASK-003 | P1 | 🔜 待开发 |
| TASK-006 | 实现 CapitalNode | TASK-005 | P1 | ✅ 完成 |

### 4.2 Sprint 2 任务 (规划)

| 任务 ID | 任务 | 依赖 | 优先级 |
|---------|------|------|--------|
| TASK-007 | 实现 RiskNode | TASK-005, TASK-006 | P1 |
| TASK-008 | 实现 ExecutionNode | TASK-007 | P1 |
| TASK-009 | 实现 EvictionNode | TASK-008 | P2 |
| TASK-010 | 集成测试 | TASK-007, TASK-008 | P1 |

## 五、关键路径

```
关键路径 (Critical Path):

Market → Model → Strategy → Capital → Risk → Execution

预计时间: 6 周
```

## 六、阻塞风险

| 依赖 | 阻塞风险 | 影响 | 缓解方案 |
|------|----------|------|----------|
| Market → Model | Mock 数据质量差 | 模型输出不准确 | 准备多个 Mock 场景 |
| Model → Strategy | 信号格式变更 | 策略需重写 | 锁定接口契约 |
| Strategy → Risk | 订单格式变更 | 风控需重写 | 锁定接口契约 |

## 七、并行开发策略

### 7.1 可并行模块

- **第一层**: Market (独立)
- **第二层**: Model (独立，可 Mock Market)
- **第三层**: Strategy (独立，可 Mock Model)

### 7.2 顺序依赖

- **第四层**: Capital, Risk (需要 Strategy)
- **第五层**: Execution (需要 Risk)

### 7.3 推荐并行方式

```
并行组 1: Market 节点
并行组 2: Model 节点 (使用 Mock Market)
并行组 3: Strategy 节点 (使用 Mock Model)
并行组 4: Capital + Risk 节点 (使用 Mock Strategy)
并行组 5: Execution 节点 (需要 Risk 完成)
```

## 八、依赖更新规则

1. 接口变更需 Tech Lead 审批
2. 依赖链上游变更需通知下游负责人
3. 定期审查依赖合理性

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
