# NEMT Simulator - Codex AI Context

> **重要**: AI 每次对话开始时，请先阅读此文件和 `.cursor/rules/DIRECTION_LOCK.md`


## 强制微任务协议（NEMT Micro-Task Protocol）

**所有 Codex、Claude Code 和其他开发 Agent 必须先阅读 [docs/MICRO_TASK_PROTOCOL.md](docs/MICRO_TASK_PROTOCOL.md)。**

- 单个任务目标耗时 **15–30 分钟**，每次只完成一个可验收的小目标。
- 一次任务、一个目标、一个验证结果、一个 Git Commit。
- 预估超过 30 分钟要先拆分；执行时超出范围应停止并报告，不擅自追加功能。
- 必须明确允许/禁止修改范围、测试、验收标准和停止条件。
- 完成后提交简短结果并停止；**未经审核不得自动执行下一任务**。
- 原有方向锁、交易风控、密钥与生产环境限制继续有效，不得因微任务协议而放宽。

## 方向锁 (Direction Lock)

**重要**: 在开始任何修改之前，必须先读取 `.cursor/rules/DIRECTION_LOCK.md` 了解当前 AI 工作范围限制。

```
✅ 允许修改: /web/src/components, /web/src/stores, /web/src/pages, /nemt_os/services, /docs
🚫 禁止修改: /core, /database, /auth, /.git
```

> **提示**: 使用 `direction_lock.bat` 管理方向锁配置

## 核心模型

```
状态 + 规则 + 任务 → AI → 输出 → 更新状态

三层架构:
① AI 层 (无记忆执行器)
② 状态层 (Node / State) ← 系统连续性在此保证
③ 约束层 (Rules / Interface)
```

## 快速接入

```
project/
├── CORE_MODEL.md              ← 第一性原理 (必读)
├── docs/
│   ├── ENTRY.md               ← 快速接入指南
│   ├── ARCHITECTURE.md        ← 系统架构
│   ├── RULES.md               ← 开发规则
│   └── STATE.md               ← 当前状态
├── nodes/                     ← 节点契约 (约束层)
│   └── *.yaml
└── engine/                    ← 执行引擎
    ├── state_manager.py       ← 状态层实现
    └── node_executor.py       ← 执行器实现
```

NEMT Simulator (Non-Equilibrium Market Theory Simulator) is a quantitative trading simulation system that models cryptocurrency market dynamics using the nonlinear Schrodinger (NLS) equation.

**Frontend**: React 18 + TypeScript + Vite + Zustand + Chart.js
**Backend**: Python 3.11 + Capsule Pattern + Event Bus
**API Server**: Python FastAPI (quant-sync-server)

## Project Structure

```
nemt-simulator/
├── web/                         # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── App.tsx              # Main app (~1460 lines) - needs refactoring
│   │   ├── main.tsx             # React entry point
│   │   ├── components/           # React components
│   │   │   ├── Charts.tsx       # Spectrum/Evolution/Noise charts
│   │   │   ├── Controls.tsx     # Parameter sliders, presets, buttons
│   │   │   ├── KanbanBoard.tsx  # Task board
│   │   │   ├── TheoryTab.tsx    # NEMT theory documentation tab
│   │   │   ├── TheoryDashboard.tsx
│   │   │   ├── OnChainDashboard.tsx
│   │   │   ├── NotionBoard.tsx
│   │   │   ├── ExecutionCard.tsx
│   │   │   ├── NEMTDashboard.tsx
│   │   │   ├── MarketPanel.tsx
│   │   │   └── strategy/        # Strategy panel components
│   │   ├── hooks/
│   │   │   └── useElectron.ts   # React hooks for Electron IPC
│   │   ├── services/            # API and business logic services
│   │   │   ├── nemtPipeline.ts  # Core pipeline (~655 lines) - needs refactoring
│   │   │   ├── executionService.ts
│   │   │   ├── strategyService.ts
│   │   │   ├── notionService.ts
│   │   │   └── marketService.ts
│   │   ├── stores/              # Zustand state management
│   │   │   └── strategyStore.ts
│   │   ├── types/               # TypeScript type definitions
│   │   │   ├── nemt.ts         # Core types (~666 lines) - needs refactoring
│   │   │   ├── strategy.ts
│   │   │   └── execution.ts
│   │   └── utils/               # Utility functions
│   │       ├── nemtCore.ts      # NLS equation simulator (~568 lines)
│   │       ├── nemtSignals.ts
│   │       └── nemtValidator.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── electron/                      # Electron Desktop Container
│   ├── src/
│   │   ├── main.ts              # Electron main process (Python subprocess, IPC)
│   │   ├── preload.ts           # Secure IPC bridge (contextBridge)
│   │   └── types/
│   │       └── electron.d.ts    # Type definitions
│   ├── build/                    # App icons and resources
│   ├── dist-electron/            # Compiled TypeScript output
│   ├── package.json             # Electron dependencies
│   ├── tsconfig.json            # TypeScript config for Electron
│   └── README.md
│
├── nemt_os/                      # Backend (Python)
│   ├── nemt/
│   │   ├── core/                 # Core capsule modules
│   │   │   ├── nemt_engine.py   # Main orchestrator (~304 lines)
│   │   │   ├── event_bus.py      # Pub/sub event system (~460 lines)
│   │   │   ├── capsule.py        # Base capsule class (~227 lines)
│   │   │   ├── capsule_manager.py
│   │   │   ├── config_center.py
│   │   │   └── *.capsule.py      # Specialized capsules
│   │   ├── market_providers/     # Data source adapters
│   │   ├── nEMT_core/            # NLS equation core
│   │   │   ├── nls_solver.py
│   │   │   └── pipeline.py
│   │   └── adapters/
│   ├── tests/                    # Python tests
│   └── requirements.txt
│
├── quant-sync-server/             # Python API server (FastAPI)
│
├── tests/                         # Root-level tests
│
├── docs/                         # Documentation
│
└── scripts/                      # Dev helper scripts
    └── dev.py                    # Unified dev commands (test, lint, format, etc.)
```

## Architecture Patterns

### Capsule Pattern (Python Backend)

The backend uses a Capsule pattern where each module (`market_capsule.py`, `signal_capsule.py`, etc.) is a self-contained capsule with:
- `setup()`: Initialization
- `execute()`: Main logic
- `cleanup()`: Resource release
- Event-driven communication via `EventBus`

### Pipeline Pattern (Frontend)

Frontend follows a pipeline: Notion read → NEMT analysis → Signal generation → Result display. The `nemtPipeline.ts` service orchestrates this flow in both local (TypeScript) and remote (Python API) modes.

### Zustand State Management

Frontend uses Zustand for global state. Key stores: `strategyStore.ts`, with plans for `nemtStore.ts` and `pipelineStore.ts`.

### Strategy + Trader Module (freqtrade + Lean + vnpy + nautilus_AItrader)

The `web/src/strategy/`, `web/src/trader/`, and `web/src/ai/` modules combine best practices from multiple projects:

**strategy/**: freqtrade + QuantConnect Lean inspired
- **IStrategy Interface**: Standard strategy interface with `populateIndicators`, `populateEntryTrend`, `populateExitTrend`
- **QCAlgorithm**: Event-driven algorithm base class with `Initialize()`, `OnData()`, `OnEndOfDay()`
- **BacktestEngine**: Historical backtesting with performance metrics (supports Binance/CSV/mock data, 5 strategies: MA/R SI/BB/MACD/Combo)
- **BacktestView**: Full UI with config/results/trades/settings tabs, equity curve chart, trade table
- **DataLoader**: Binance API loader, CSV parser, mock data generator, data validation
- **Optimizer**: Grid and random search parameter optimization
- **Technical Indicators**: Full TA-Lib implementation (RSI, MACD, ADX, Bollinger, etc.)
- **BinanceAdapter**: Exchange adapter for market data and trading
- **StrategyConfig**: Configuration system with presets (conservative, balanced, aggressive)
- **NEMTCalculator**: NEMT state calculation (psi, phi, entropy, phase)
- **Store Bridge**: Integration with NEMT Zustand stores

**trader/**: vnpy inspired
- **EventEngine**: Event-driven engine with event type registry
- **BaseGateway**: Exchange adapter base class (BinanceGateway)
- **MainEngine**: Core engine managing Gateway, Engine, App
- **DataEngine**: Market data caching and retrieval
- **TradeEngine**: Order management and execution
- **SignalEngine**: Trading signal processing
- **alpha/**: AI quantitative module
  - **Alpha158**: Factor engineering (Qlib-inspired)
  - **Models**: ML models (LinearRegression, Ridge, RandomForest, MLP)
  - **AlphaStrategy**: ML-based trading signals

**ai/**: nautilus_AItrader inspired
- **DeepSeekAnalyzer**: AI-powered market analysis and signal generation
- **SentimentDataFetcher**: Fear & Greed index and market sentiment
- **DeepSeekAIStrategy**: Full AI trading strategy with technical analysis
- **RiskManager**: Advanced risk management (SL/TP, trailing stop, partial TP, OCO orders)

---

## 策略开发工作流 (NEMT Plugins)

NEMT Simulator 使用基于 spec-kit-cn、pm-skills 和 freqtrade 的策略开发工作流。所有技能位于 `.cursor/rules/nemplugs/`。

### 完整工作流

```
/discover              ← 发现策略机会 (数据分析、市场研究、假设识别)
/write-strategy        ← 创建策略规范 (入场/出场规则、NEMT 整合、风险管理)
/plan-strategy         ← 技术实施计划 (架构设计、参数配置、回测计划)
/backtest              ← 历史回测 (双缓冲系统验证、NEMT 指标)
/live-trade            ← 实时交易 (信号监控、订单执行、风险控制)
/monitor               ← 策略监控 (回测 vs 实战对比、North Star 指标)
```

### 技能文件

| 技能 | 路径 | 用途 |
|------|------|------|
| Constitution | `nemt-plugins/constitution/SKILL.md` | 项目原则和治理 |
| Discover | `nemt-plugins/discover/SKILL.md` | 策略发现 |
| Write Strategy | `nemt-plugins/write-strategy/SKILL.md` | 策略规范 |
| Plan Strategy | `nemt-plugins/plan-strategy/SKILL.md` | 技术计划 |
| Backtest | `nemt-plugins/backtest/SKILL.md` | 回测执行 |
| Live Trade | `nemt-plugins/live-trade/SKILL.md` | 实时交易 |
| Monitor | `nemt-plugins/monitor/SKILL.md` | 策略监控 |
| NEMT Concepts | `nemt-plugins/shared/nemt-concepts.md` | 核心概念 |
| Templates | `nemt-plugins/templates/` | 规范和计划模板 |

### 策略评估标准 (Constitution)

| 指标 | 通过标准 | 目标标准 |
|------|----------|----------|
| 胜率 | >= 50% | >= 55% |
| 夏普比率 | >= 1.5 | >= 2.0 |
| 最大回撤 | <= 20% | <= 15% |
| 盈亏比 | >= 1.2 | >= 1.5 |

### NEMT 状态机

```
┌─────────────┐
│   stable    │  ψ 适中, S低
└──────┬──────┘
       │
┌──────┴──────┐
▼             ▼
critical_up  critical_dn
→ BUY        → SELL
└──────┬──────┘
       ▼
    decay
```

详细 NEMT 概念见 `.cursor/rules/nemt-plugins/shared/nemt-concepts.md`

## Key Conventions

### TypeScript
- Use strict TypeScript mode (strict: true in tsconfig)
- All async functions must handle errors with try/catch
- Use explicit return types for public functions
- Prefer `interface` over `type` for object shapes
- Use named exports, avoid default exports for utilities

### Python
- Type hints required for all public function signatures
- Use `Optional[T]` instead of `T | None`
- Docstrings for all public classes and functions
- Capsule methods: `setup()`, `execute()`, `cleanup()`
- Events: `event_bus.publish(event_type, data)` and `event_bus.subscribe(event_type, handler)`

### Testing
- Frontend: Vitest for component/integration tests
- Backend: pytest with markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
- Coverage minimum: 50% for backend, 30% for frontend

### Git Workflow
- Branch naming: `feature/`, `fix/`, `refactor/`, `docs/`
- Commit messages: Conventional Commits (feat, fix, docs, refactor, test)
- PR requires: passing CI, at least 1 review

## Running the Project

```bash
# Frontend
cd web && npm install && npm run dev

# Backend
cd nemt_os && pip install -r requirements.txt && python run_demo.py

# Both
cd scripts && python dev.py test
```

## Electron Desktop Container

The project includes an Electron-based desktop container that wraps the web app and Python backend into a native desktop application.

### Architecture
- **Electron Main Process**: Manages Python subprocess, IPC, system tray, menus
- **Electron Renderer**: React frontend (same as web/)
- **Python Subprocess**: NEMT Core Engine via JSON-RPC over stdin/stdout

### Running Electron
```bash
cd electron
npm install
npm run dev:electron
```

### Key Files
- `electron/src/main.ts`: Main process with Python IPC
- `electron/src/preload.ts`: Secure context bridge
- `web/src/hooks/useElectron.ts`: React hooks for Electron APIs

## 工程状态层 (重要)

AI 每次对话都应从这里开始：

```
project/docs/           ← 工程状态层 (AI 外部大脑)
├── ENTRY.md        ← 快速接入指南 (必读)
├── ARCHITECTURE.md ← 系统架构图、模块职责
├── RULES.md        ← 编码规范、命名、测试
└── STATE.md        ← 真实状态、待办、问题
```

详细说明见 `project/docs/ENTRY.md`

---

## 架构守卫 (Architecture Guard)

在修改代码前，架构守卫会自动扫描检测违规。

### 禁止的模式

| 规则 | 违规行为 |
|------|----------|
| F001 | 组件直接调用数据库 |
| F002 | 组件直接调用服务层 |
| F003 | Store 调用组件 |
| F004 | Store 循环依赖 |

### 允许的依赖关系

```
pages → components → hooks → stores → services → core
```

### 使用方法

```bash
# 运行架构守卫
architecture_guard.bat
```

---

## 方向锁 (Direction Lock)

在开始任何修改之前，**必须**先读取 `.cursor/rules/DIRECTION_LOCK.md` 了解当前 AI 工作范围限制。

### 当前限制

**✅ 允许修改**:
- `/web/src/components` - React 组件
- `/web/src/stores` - 状态管理
- `/web/src/pages` - 页面组件
- `/web/src/hooks` - 自定义 Hooks
- `/web/src/utils` - 工具函数
- `/nemt_os/services` - 服务层代码
- `/docs` - 文档文件

**🚫 禁止修改**:
- `/core` - 核心系统
- `/database` - 数据库层
- `/auth` - 认证模块
- `/.git` - Git 仓库

### 管理工具

使用 `direction_lock.bat` 管理方向锁：
- 启用/禁用方向锁
- 添加/移除允许目录
- 添加/移除禁止目录
- 导出配置

---

## Important Notes

1. **App.tsx is too large** (~1460 lines) and needs to be split into tab components
2. **nemtPipeline.ts is too large** (~655 lines) and needs modularization
3. **types/nemt.ts has enums scattered** - refactor to separate files under `types/`
4. **Python uses CRLF-safe setup** - .gitattributes enforces LF line endings
5. **Windows compatibility** - All scripts use `python`, not `python3`
