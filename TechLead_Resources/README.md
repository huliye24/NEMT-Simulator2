# Tech Lead Resources

> Tech Lead Agent 的工作资源目录

## 目录结构

```
TechLead_Resources/
├── README.md                     # 本文件 - 目录索引
├── TASKS.md                     # 全局任务清单 (位于项目根目录)
├── SPRINT_GOALS.md              # 当前 Sprint 目标
├── CODE_STANDARDS.md            # 代码规范（细化版）
├── CODE_REVIEW_GUIDELINES.md   # 代码审查检查清单
├── CODE_REVIEW_LOG/             # 代码审查记录
├── MODULE_OWNERSHIP.md          # 模块所有权
├── BLOCKERS.md                  # 当前阻塞项
├── TECH_DEBT_ITEMS.md           # 技术债务清单
├── DEVELOPMENT_WORKFLOW.md      # 开发流程
├── GIT_GUIDELINES.md           # Git 规范
├── TESTING_REQUIREMENTS.md     # 测试要求
├── LOCAL_DEV_SETUP.md          # 本地开发环境
├── INTERFACE_CONTRACTS.md       # 接口契约
├── TECH_RISKS.md               # 技术风险
├── DEPENDENCY_MATRIX.md        # 依赖矩阵
├── COMMANDS.md                 # 常用命令
├── TASK_TEMPLATES/             # 任务模板
│   ├── BUG_FIX.md
│   ├── FEATURE.md
│   └── REFACTOR.md
├── SCRIPTS/                    # 工具脚本
│   ├── scan_tasks.py           # 扫描停滞任务
│   ├── fetch_prs.py           # 获取待审查 PR
│   └── generate_weekly_report.py # 生成周报
├── Obsidian_Template/           # Obsidian 模板 (用于复制到 Obsidian 库)
│   ├── README.md              # 使用说明
│   ├── TL_COCKPIT.md         # TL 驾驶舱
│   ├── 10_Inbox/
│   │   └── TL_INBOX.md        # TL 收件箱
│   ├── 20_Tasks/
│   │   └── TASK_TEMPLATE.md    # 任务模板 (含技术字段)
│   ├── 30_Decisions/
│   │   └── DECISION_TEMPLATE.md # 决策请求模板
│   ├── 60_Code_Reviews/
│   │   └── CR_TEMPLATE.md     # 代码审查模板
│   └── 70_Tech_Debt/
│       └── TD_TEMPLATE.md      # 技术债模板
├── Daily_Logs/                 # 每日日志
│   └── Daily_Dev_Log_2026-04-19.md
└── SPRINT_RETROSPECTIVE/       # Sprint 复盘
```

## 角色定位

- **角色名称**: Tech Lead（技术负责人）
- **核心职责**:
  - 将 CTO 的架构决策转化为具体模块、接口、任务
  - 拆解 PM 的实验需求为可执行的开发任务
  - 代码审查（Code Review），确保符合 `CODE_STANDARDS.md`
  - 管理日常开发进度，识别阻塞与技术风险
  - 维护 `TASKS.md`（任务清单）与 `SPRINT_GOALS.md`

## 成功指标

- [ ] 任务按时完成率 > 80%（按 Sprint 计划）
- [ ] PR 平均审查响应时间 < 4 小时
- [ ] 因任务拆解不清晰导致的返工 < 10% 的总工作量
- [ ] 技术债务新增速率低于偿还速率
- [ ] 阻塞项平均解决时间 < 2 天

---

*创建时间: 2026-04-19*
*最后更新: 2026-04-19*
