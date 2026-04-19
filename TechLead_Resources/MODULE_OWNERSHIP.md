# 模块所有权

> 各模块负责人分配表

## 模块所有权表

| 模块 | 路径 | 负责人 | 状态 | 备注 |
|------|------|--------|------|------|
| **市场层** | `quant-sync-server/services/market_node.py` | 待分配 | 🔜 待开发 | |
| **模型层** | `quant-sync-server/services/model_node.py` | 待分配 | 🔜 待开发 | NEMT Core |
| **策略层** | `quant-sync-server/services/strategy_node.py` | 待分配 | 🔜 待开发 | |
| **资金管理层** | `quant-sync-server/services/capital_node.py` | Tech Lead | ✅ 完成 | Brain Layer |
| **淘汰模块** | `quant-sync-server/services/eviction_node.py` | 待分配 | 🔜 待开发 | Evolution |
| **Brain Layer** | `brain_layer.py` | Tech Lead | ✅ 完成 | |
| **风控模块** | `nemt_risk.py` | 待分配 | ✅ 基础完成 | |
| **信号模块** | `nemt_signals.py` | 待分配 | ✅ 基础完成 | |
| **Web 前端** | `web/src/` | 待分配 | 🔄 进行中 | |
| **Electron** | `electron/` | 待分配 | 🔜 待开发 | |
| **Notion 同步** | `quant-sync-server/` | 待分配 | 🔄 进行中 | |

## 职责定义

### 负责人职责

1. **维护**: 负责模块的日常维护和 bug 修复
2. **审查**: 对该模块的 PR 有最终审查权
3. **文档**: 维护模块的技术文档
4. **升级**: 规划模块的技术升级路线

### 所有权变更流程

1. 当前负责人提名接替者
2. Tech Lead 审批
3. 文档更新
4. 交接期（2 周）

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
