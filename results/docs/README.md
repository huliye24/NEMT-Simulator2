# PM Resources 索引

> NEMT量化操作系统 - 结果管理文档

## 核心文档

| 文档 | 说明 |
|------|------|
| [VISION.md](./VISION.md) | 系统愿景与北极星指标 |
| [RESULTS.md](./RESULTS.md) | 系统整体结果指标 |
| [METRICS_DEFINITIONS.md](./METRICS_DEFINITIONS.md) | 所有指标的计算公式 |
| [STRATEGY_POOL.md](./STRATEGY_POOL.md) | 策略池清单 |
| [EVOLUTION_RULES.md](./EVOLUTION_RULES.md) | 策略淘汰/引入规则 |
| [EXPERIMENTS.md](./EXPERIMENTS.md) | 实验记录 |
| [RESOURCE_ALLOCATION.md](./RESOURCE_ALLOCATION.md) | 计算资源分配 |

## 报告文档

| 文档 | 说明 |
|------|------|
| [WEEKLY_RESULTS_REPORT_2026_W17.md](./WEEKLY_RESULTS_REPORT_2026_W17.md) | 本周结果报告 |
| [Daily_Results_Log_2026-04-19.md](./Daily_Results_Log_2026-04-19.md) | 今日日志 |
| [ALERTS.md](./ALERTS.md) | 告警记录 |

---

## PM工作流程

### 每日任务（约20分钟）

1. **早晨**: 运行 `pm_daily_workflow.py` 检查结果指标
2. **中午**: 检查策略池健康状态
3. **傍晚**: 更新实验进度

### 每周任务（周一上午）

1. 生成 `WEEKLY_RESULTS_REPORT_*.md`
2. 策略演化会议
3. 调整资源分配

---

## PM成功指标

- [ ] 系统夏普逐月提升
- [ ] 策略池平均寿命 > 60天
- [ ] 淘汰率稳定在 10-20%/月
- [ ] 实验采纳率 > 30%
- [ ] 回撤事件 < 1次/季度

---

*最后更新: 2026-04-19*
