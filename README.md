<p align="center">
  <img src="web/public/nemt-logo.png" alt="NEMT Logo" width="200" />
</p>

# NEMT

**Non-Equilibrium Market Theory · 非平衡市场理论**

**AI 原生金融研究、市场模拟与移动交易基础设施**

Research · Experiments · Simulation · Risk-Controlled Trading

[快速开始](#快速开始) · [系统架构](#系统架构) · [开发状态](#开发状态) · [工程协议](#工程协议) · [项目路线](#项目路线)

---

## 项目简介

NEMT 是一个连接**市场理论研究、金融数据、计算实验、策略验证、模拟交易及移动终端**的开源工程项目。

我们采用循证、可复现的长期研发方法：

**理论假设 → 数据采集 → MATLAB / 云计算实验 → 策略验证 → Paper Trading → 交易应用**

研究层负责解释、检验和迭代假设；交易层负责在明确权限、风险限制和审计机制下执行操作。**研究结果和 AI 输出不能绕过风控直接发起真实交易。**

## 开发状态

NEMT App V0.1 已交付可演示的移动端 DEMO 基线，但**真实 Binance Spot Testnet 端到端验收尚未完成，LIVE 写入功能仍然禁用**。

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 手机端 Web / PWA | DEMO 已实现 | Next.js 16、React 19、TypeScript |
| 云端 API | 基线已实现 | FastAPI、登录、RBAC、CSRF、审计 |
| DEMO 模拟交易 | 已测试 | 订单预览、确认、模拟成交、撤单及余额更新 |
| 公共行情 | 基线已实现 | Binance 公共行情、数据新鲜度和异常提示 |
| Binance Spot Testnet | 待正式验收 | 需要服务端专用密钥及真实下单测试证据 |
| 订单数据流与恢复 | 待完善 | 部分成交、周期对账、断线重连和重启恢复 |
| LIVE 真实资金交易 | **禁用** | V0.1 不提供可执行的 LIVE 下单路径 |
| MATLAB / GPU 研究 | 持续建设 | 独立于交易执行，重视实验复现与参数记录 |

进度依据：[NEMT App EPIC #5](https://github.com/huliye24/NEMT-Simulator2/issues/5) · [Testnet 验收清单](docs/NEMT_APP_TESTNET_ACCEPTANCE.md)。

## 系统架构

```text
                NEMT Research & Experiments
         理论 · 数据集 · MATLAB · GPU · 模型验证
                            │
                     策略候选 / 证据
                            │
              回测 · 样本外评估 · Paper Trading
                            │
                       人工审核 / 风控
                            │
     ┌──────────────────────┴──────────────────────┐
     │             NEMT Mobile Web / PWA           │
     │       Next.js · 行情 · 账户 · 订单交互        │
     └──────────────────────┬──────────────────────┘
                            │ NEMT API
     ┌──────────────────────┴──────────────────────┐
     │               FastAPI Cloud API             │
     │       身份认证 · 权限 · 风控 · 审计 · 持久化    │
     └──────────────────────┬──────────────────────┘
                            │
                 DEMO / Binance Spot TESTNET
                 LIVE 写入默认禁止
```

**当前技术基线：** `web/` 已采用 Next.js，而不是部分历史文档中的 Vite 方案；技术决策见 [ADR-001](docs/ADR-001-nemt-app-baseline.md)。

| 目录 | 职责 |
| --- | --- |
| `web/` | 当前网站与手机端交易工作台 |
| `backend/trade_app/` | 独立 FastAPI 交易服务 |
| `backend/trade_main.py` | 云端 API 入口 |
| `backend/tests/` | DEMO 与服务端逻辑测试 |
| `quant-mvp/` | 行情采集与历史量化模块 |
| `matlab/` | 数学建模与实验研究 |
| `docs/` | 架构、实验、工程规范与运维手册 |
| `scripts/` | 工程与自动化检查工具 |

仓库部分历史组件仍在分阶段审查。清理工作见 [Issue #18](https://github.com/huliye24/NEMT-Simulator2/issues/18)。

## 快速开始

要求：**Python 3.11+、Node.js 22、npm**。以下过程默认在 **DEMO** 环境运行，不需要 Binance API Key。

### 1. 获取代码

```bash
git clone https://github.com/huliye24/NEMT-Simulator2.git
cd NEMT-Simulator2
```

### 2. 启动 FastAPI

```bash
python -m pip install -r backend/trade_requirements.txt
python backend/trade_main.py
```

建议在独立的 Python 虚拟环境中安装依赖。API 默认监听 `127.0.0.1:8000`，健康检查为 `/api/v1/health`。

### 3. 启动移动 Web 应用

在另一终端执行：

```bash
cd web
npm ci
npm run build
npm start
```

访问 **http://localhost:3000/trade**。DEMO 账户、Android 手机联调和启动排障见 [运行手册](docs/NEMT_APP_RUNBOOK.md)。

## 运行模式与安全边界

| 运行模式 | 用途 | 交易能力 |
| --- | --- | --- |
| `DEMO` | 本地模拟及界面验证 | 只操作模拟订单与模拟资金 |
| `TESTNET` | Binance Spot 测试网 | 必须在服务端显式配置测试网专用凭据 |
| `LIVE` | 真实资金环境 | **V0.1 不提供订单写入能力** |

- **Fail Closed：** 模式、权限、价格新鲜度或风控条件异常时拒绝订单。
- **密钥留在服务端：** 不将交易所凭据放入浏览器或客户端包。
- **先审查再交易：** 预览、确认、额度限制、幂等、审计在服务端执行。
- **研究与执行隔离：** AI 研究或回测结果不自动获得下单权限。
- **历史凭据风险：** 仓库曾记录需撤销或轮换的凭据信息；新源码 CI 通过不等于历史风险已经解决。详见 [安全清理方案](docs/SECURITY_CLEANUP_PLAN.md)。

实盘准入须单独审批，见 [Issue #15](https://github.com/huliye24/NEMT-Simulator2/issues/15)。

## 工程协议

NEMT 对人工与 AI 贡献者采用相同的工程纪律。开始修改前，须阅读：

- [AGENTS.md](AGENTS.md) 和 [Direction Lock](.cursor/rules/DIRECTION_LOCK.md)：允许范围、受保护目录与审批条件。
- [微任务协议](docs/MICRO_TASK_PROTOCOL.md) 和 [工程开发协议](docs/ENGINEERING_PROTOCOL.md)：任务以 **15–30 分钟**为计划单位；单一目标、明确测试和回滚。
- [科学实验协议](docs/SCIENTIFIC_EXPERIMENT_PROTOCOL.md)：数据版本、MATLAB/GPU 参数、实验记录及可复现性。
- [量化策略协议](docs/QUANT_STRATEGY_PROTOCOL.md)：从理论和实验到策略候选、验证、人工审核和 Paper Trading。

超过 Direction Lock 许可范围的操作必须获得维护者单独、明确的批准，不得以自动化或开发便利为由绕过。

## 测试

后端测试（需预先安装上述 Python 依赖）：

```bash
cd backend
python -m pytest
```

前端质量检查（在项目根目录运行）：

```bash
cd web
npm ci
npm run lint
npx tsc --noEmit
npm run build
```

仓库 CI 包括后端 DEMO 测试、前端 Lint/TypeScript/构建以及新应用源码的基本密钥守卫。**CI 通过不等于真实 Testnet 或生产环境通过验收。**

## 项目路线

| 阶段 | 核心目标 | 状态 |
| --- | --- | --- |
| Phase 1 | 手机端 DEMO、基础 API、模拟交易及风控 | 已有交付 |
| Phase 2 | Spot Testnet 下单、撤单、对账、异常恢复 | 开发及验收中 |
| Phase 3 | 云端实验、策略验证与 Paper Trading 闭环 | 长期研究 |
| Phase 4 | 安全、合规与受限实盘就绪评估 | 必须单独审批 |

## 理念

> **让市场研究能够被验证，让实验结果能够被复现，让交易执行始终受到约束。**

NEMT 的长期目标不是单一的交易页面，而是从可证伪的科学研究走向可审计金融软件的一套基础设施。

## License

开源许可以根目录 [LICENSE](LICENSE) 为准。使用第三方依赖和参考实现时须遵循各自的许可证。

---

*NEMT — Research First · Evidence Driven · Risk Controlled*
