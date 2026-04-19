# NEMT Quant OS - Electron 应用架构设计

> **基于"厨房理论"的架构优先开发模型**
> 先搭厨房（架构），再请厨师（策略）

---

## 目录

1. [设计理念](#1-设计理念)
2. [技术架构总览](#2-技术架构总览)
3. [目录结构](#3-目录结构)
4. [核心模块设计](#4-核心模块设计)
5. [IPC通信设计](#5-ipc通信设计)
6. [Electron主进程](#6-electron主进程)
7. [渲染进程](#7-渲染进程)
8. [Python子进程](#8-python子进程)
9. [厨房验收标准](#9-厨房验收标准)
10. [开发任务清单](#10-开发任务清单)
11. [技术选型](#11-技术选型)

---

## 1. 设计理念

### 1.1 厨房理论核心

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           厨房理论开发模型                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  阶段一：厨房搭建（架构）                                                    │
│  ├── 项目结构、配置管理、日志系统                                           │
│  ├── IPC通信协议、模块间接口定义                                            │
│  ├── Python子进程管理、数据抽象层                                          │
│  ├── 验收标准：能启动、能跑Mock数据                                        │
│                                                                             │
│  阶段二：厨师填充（业务）                                                  │
│  ├── NEMT核心算法集成                                                      │
│  ├── 策略模块实现                                                          │
│  ├── 回测引擎集成                                                          │
│  ├── 验收标准：功能完整、可运行回测                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 与现有代码的关系

| 现有代码 | 迁移方式 | 目标位置 |
|---------|---------|---------|
| `nemt_core.py` | 直接复用 | `python/nemt/core.py` |
| `quant-mvp/calculator/` | 改造后复用 | `python/nemt/strategies/` |
| `nemtPipeline.ts` | 改造为IPC调用 | `src/services/` |
| `executionFramework.ts` | 改造为IPC调用 | `src/services/` |
| `App.tsx` + 组件 | 直接迁移 | `src/renderer/` |
| `quant-sync-server/` | 简化为本地服务 | `python/services/` |

---

## 2. 技术架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NEMT Quant OS 架构图                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      Electron 主进程 (Main Process)                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │   Window    │  │   IPC        │  │   Python     │              │  │
│  │  │   Manager   │  │   Handler    │  │   Process    │              │  │
│  │  │             │  │              │  │   Manager    │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                          IPC Bridge (Electron IPC)                          │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    渲染进程 (Renderer Process)                         │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │                        React 应用                              │   │  │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │  │
│  │  │  │  模拟器    │  │  Dashboard │  │   策略     │            │   │  │
│  │  │  │  页面      │  │   页面     │  │   管理     │            │   │  │
│  │  │  └────────────┘  └────────────┘  └────────────┘            │   │  │
│  │  │                                                             │   │  │
│  │  │  ┌─────────────────────────────────────────────────────┐   │   │  │
│  │  │  │              Services (TypeScript)                   │   │   │  │
│  │  │  │  pipelineService | executionService | riskService   │   │   │  │
│  │  │  └─────────────────────────────────────────────────────┘   │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    Python 子进程 (Child Process)                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │   NEMT      │  │   Strategy   │  │   Backtest   │            │  │
│  │  │   Core      │  │   Engine     │  │   Engine     │            │  │
│  │  │   (NLS)     │  │              │  │              │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │   Signal    │  │   Risk       │  │   Data       │            │  │
│  │  │   Generator │  │   Controller  │  │   Provider   │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        本地数据存储                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │   SQLite     │  │   CSV/JSON   │  │   Logs       │            │  │
│  │  │   Database   │  │   Files      │  │   Directory  │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈总结

| 层次 | 技术 | 用途 |
|------|------|------|
| 桌面框架 | Electron 28+ | 跨平台桌面应用 |
| 前端框架 | React 18 + TypeScript | UI渲染 |
| UI组件 | TailwindCSS + Lucide | 样式和图标 |
| Python运行时 | 内置Python子进程 | 量化计算 |
| 数据存储 | SQLite + 文件系统 | 本地持久化 |
| IPC通信 | Electron IPC + JSON-RPC | 进程间通信 |
| 构建工具 | electron-builder | 打包发布 |

---

## 3. 目录结构

```
nemt-quant-os/
├── electron/
│   ├── main.ts                 # Electron主进程入口
│   ├── preload.ts              # 预加载脚本
│   ├── ipc/
│   │   ├── handlers.ts         # IPC处理器注册
│   │   └── channels.ts         # IPC通道定义
│   ├── services/
│   │   ├── windowManager.ts    # 窗口管理
│   │   ├── pythonProcess.ts    # Python进程管理
│   │   └── logger.ts           # 日志服务
│   └── utils/
│       └── config.ts           # 配置加载
│
├── python/
│   ├── __init__.py
│   ├── nemt/
│   │   ├── __init__.py
│   │   ├── core.py             # NEMT核心（NLS方程）
│   │   ├── simulator.py         # 模拟器封装
│   │   └── types.py            # 类型定义
│   │
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py             # 策略基类
│   │   ├── trend.py            # 趋势策略
│   │   ├── mean_rev.py          # 均值回归
│   │   └── momentum.py         # 动量策略
│   │
│   ├── signals/
│   │   ├── __init__.py
│   │   ├── generator.py         # 信号生成器
│   │   └── indicators/          # 技术指标
│   │       ├── rsi.py
│   │       ├── macd.py
│   │       ├── bollinger.py
│   │       └── ma.py
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── executor.py          # 执行引擎
│   │   ├── risk.py             # 风控
│   │   └── orders.py           # 订单管理
│   │
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py            # 回测引擎
│   │   └── metrics.py          # 性能指标
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rpc_server.py       # JSON-RPC服务器
│   │   └── data_provider.py    # 数据提供者
│   │
│   └── data/
│       ├── __init__.py
│       └── storage.py          # 数据存储
│
├── src/                        # React前端
│   ├── main.tsx                # React入口
│   ├── App.tsx                 # 主应用（迁移现有代码）
│   ├── components/              # UI组件
│   │   ├── Charts.tsx
│   │   ├── Controls.tsx
│   │   ├── ExecutionCard.tsx
│   │   └── ...
│   ├── services/               # 前端服务（改造后）
│   │   ├── nemtPipeline.ts     # 改造为IPC调用
│   │   ├── executionService.ts
│   │   └── ipcClient.ts        # IPC客户端封装
│   ├── hooks/                  # React hooks
│   ├── types/                  # TypeScript类型
│   ├── utils/                  # 工具函数
│   └── styles/                 # 样式文件
│
├── resources/                  # 静态资源
│   └── icons/                  # 应用图标
│
├── config/
│   └── settings.yaml           # 应用配置
│
├── data/                       # 数据目录
│   ├── market/                 # 市场数据
│   └── results/                # 回测结果
│
├── logs/                       # 日志目录
│
├── package.json
├── tsconfig.json
├── vite.config.ts              # Vite配置
├── electron-builder.yml        # 打包配置
├── requirements.txt             # Python依赖
├── SPEC.md                     # 本文档
└── README.md
```

---

## 4. 核心模块设计

### 4.1 模块分层

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           模块分层架构                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    Presentation Layer (UI层)                        │  │
│  │   React Components → Hooks → IPC Client → Electron IPC              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                      ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    Service Layer (服务层)                              │  │
│  │   PipelineService | ExecutionService | RiskService | DataService    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                      ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    Domain Layer (领域层)                              │  │
│  │   NEMT Core | Strategies | Signals | Risk | Backtest               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                      ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    Infrastructure Layer (基础设施层)                   │  │
│  │   Python Process | SQLite | File System | Logging                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 各模块职责

| 模块 | 职责 | 对应现有代码 |
|------|------|------------|
| `nemt/core.py` | NLS方程模拟、谱分析 | `nemt_core.py` |
| `nemt/simulator.py` | 模拟器封装，提供Python API | 新增 |
| `strategies/base.py` | 策略基类接口 | `quant-mvp/` |
| `strategies/*` | 具体策略实现 | 新增 |
| `signals/generator.py` | 信号生成与聚合 | `nemtPipeline.ts` |
| `execution/executor.py` | 订单执行模拟 | `executionFramework.ts` |
| `execution/risk.py` | 风控规则引擎 | `nemt_risk.py` |
| `backtest/engine.py` | 回测循环引擎 | `quant-mvp/calculator/` |
| `services/rpc_server.py` | JSON-RPC服务 | `quant-sync-server/api_server.py` 简化版 |

---

## 5. IPC通信设计

### 5.1 IPC通道定义

```typescript
// electron/ipc/channels.ts

export const IPC_CHANNELS = {
  // Python进程管理
  PYTHON_START: 'python:start',
  PYTHON_STOP: 'python:stop',
  PYTHON_STATUS: 'python:status',

  // NEMT核心
  NEMT_RUN: 'nemt:run',
  NEMT_NOISE_SCAN: 'nemt:noise-scan',
  NEMT_NONLINEAR_SCAN: 'nemt:nonlinear-scan',

  // 策略操作
  STRATEGY_LIST: 'strategy:list',
  STRATEGY_GET: 'strategy:get',
  STRATEGY_CREATE: 'strategy:create',
  STRATEGY_UPDATE: 'strategy:update',
  STRATEGY_DELETE: 'strategy:delete',
  STRATEGY_RUN: 'strategy:run',

  // 回测操作
  BACKTEST_RUN: 'backtest:run',
  BACKTEST_STATUS: 'backtest:status',
  BACKTEST_CANCEL: 'backtest:cancel',
  BACKTEST_RESULTS: 'backtest:results',

  // 风控操作
  RISK_CHECK: 'risk:check',
  RISK_STATUS: 'risk:status',

  // 数据操作
  DATA_LOAD: 'data:load',
  DATA_SAVE: 'data:save',

  // 系统操作
  SYSTEM_STATUS: 'system:status',
  SYSTEM_LOGS: 'system:logs',
} as const;
```

### 5.2 IPC请求/响应格式

```typescript
// 请求格式
interface IPCRequest {
  id: string;           // 请求唯一ID
  channel: string;      // 通道名
  method: string;       // 方法名
  params?: any;         // 参数
  timestamp: number;    // 时间戳
}

// 响应格式
interface IPCResponse {
  id: string;           // 对应请求ID
  success: boolean;      // 是否成功
  result?: any;         // 结果数据
  error?: {
    code: string;
    message: string;
  };
  timestamp: number;    // 时间戳
}

// 进度事件（用于长时间运行的任务）
interface IPCProgress {
  id: string;
  channel: string;
  progress: number;      // 0-100
  message: string;
  data?: any;
}
```

### 5.3 TypeScript IPC客户端

```typescript
// src/services/ipcClient.ts

class IPCClient {
  private invoke<T>(channel: string, ...args: any[]): Promise<T>;
  private on(channel: string, callback: (data: any) => void): void;
  private off(channel: string): void;
}

// 具体服务封装
class NEMTService {
  constructor(private ipc: IPCClient) {}

  async runSimulation(params: NEMTParams): Promise<SimulationResult> {
    return this.ipc.invoke(IPC_CHANNELS.NEMT_RUN, params);
  }

  async runNoiseScan(params: NEMTParams): Promise<NoiseScanResult> {
    return this.ipc.invoke(IPC_CHANNELS.NEMT_NOISE_SCAN, params);
  }
}

class StrategyService {
  constructor(private ipc: IPCClient) {}

  async listStrategies(): Promise<Strategy[]> {
    return this.ipc.invoke(IPC_CHANNELS.STRATEGY_LIST);
  }

  async runStrategy(id: string, data: number[]): Promise<StrategyResult> {
    return this.ipc.invoke(IPC_CHANNELS.STRATEGY_RUN, { id, data });
  }
}

class BacktestService {
  constructor(private ipc: IPCClient) {}

  async run(config: BacktestConfig): Promise<void> {
    // 使用进度回调
    this.ipc.on('backtest:progress', (progress) => {
      console.log(`Backtest progress: ${progress}%`);
    });
    return this.ipc.invoke(IPC_CHANNELS.BACKTEST_RUN, config);
  }
}
```

---

## 6. Electron主进程

### 6.1 主进程入口

```typescript
// electron/main.ts

import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'path';
import { WindowManager } from './services/windowManager';
import { PythonProcessManager } from './services/pythonProcess';
import { setupIpcHandlers } from './ipc/handlers';
import { Logger } from './services/logger';

class NEMTApp {
  private windowManager: WindowManager;
  private pythonManager: PythonProcessManager;
  private logger: Logger;

  constructor() {
    this.logger = new Logger();
    this.windowManager = new WindowManager(this.logger);
    this.pythonManager = new PythonProcessManager(this.logger);
  }

  async initialize(): Promise<void> {
    // 1. 初始化日志
    await this.logger.initialize();
    this.logger.info('NEMT App initializing...');

    // 2. 初始化Python子进程
    await this.pythonManager.initialize();
    this.logger.info('Python process started');

    // 3. 设置IPC处理器
    setupIpcHandlers(this.pythonManager, this.logger);
    this.logger.info('IPC handlers registered');

    // 4. 创建主窗口
    await this.windowManager.createMainWindow();
    this.logger.info('Main window created');
  }

  async shutdown(): Promise<void> {
    this.logger.info('NEMT App shutting down...');
    await this.pythonManager.stop();
    await this.windowManager.closeAll();
    await this.logger.shutdown();
  }
}

// 应用入口
const nemtApp = new NEMTApp();

app.whenReady().then(async () => {
  try {
    await nemtApp.initialize();
  } catch (error) {
    console.error('Failed to initialize:', error);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  nemtApp.shutdown().then(() => app.quit());
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  nemtApp.shutdown().then(() => process.exit(1));
});
```

### 6.2 Python进程管理

```typescript
// electron/services/pythonProcess.ts

import { spawn, ChildProcess } from 'child_process';
import { join } from 'path';
import { EventEmitter } from 'events';

export class PythonProcessManager extends EventEmitter {
  private process: ChildProcess | null = null;
  private pythonPath: string;
  private rpcPort: number = 9555;

  constructor(private logger: Logger) {
    super();
  }

  async initialize(): Promise<void> {
    const scriptPath = join(__dirname, '../../python/services/rpc_server.py');

    this.process = spawn(this.pythonPath, [scriptPath, '--port', this.rpcPort.toString()], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PYTHONPATH: join(__dirname, '../../python'),
      },
    });

    this.process.stdout?.on('data', (data) => {
      this.logger.debug('Python:', data.toString());
    });

    this.process.stderr?.on('data', (data) => {
      this.logger.error('Python Error:', data.toString());
    });

    this.process.on('exit', (code) => {
      this.logger.warn(`Python process exited with code ${code}`);
      this.emit('exit', code);
    });

    // 等待Python服务就绪
    await this.waitForReady();
  }

  async stop(): Promise<void> {
    if (this.process) {
      this.process.kill('SIGTERM');
      this.process = null;
    }
  }

  isRunning(): boolean {
    return this.process !== null && !this.process.killed;
  }

  // 转发RPC调用到Python进程
  async call(method: string, params: any): Promise<any> {
    // 实现JSON-RPC调用逻辑
  }
}
```

---

## 7. 渲染进程

### 7.1 预加载脚本

```typescript
// electron/preload.ts

import { contextBridge, ipcRenderer } from 'electron';
import { IPC_CHANNELS } from './ipc/channels';

// 暴露安全的API到渲染进程
contextBridge.exposeInMainWorld('nemt', {
  // NEMT核心
  nemt: {
    run: (params: any) => ipcRenderer.invoke(IPC_CHANNELS.NEMT_RUN, params),
    noiseScan: (params: any) => ipcRenderer.invoke(IPC_CHANNELS.NEMT_NOISE_SCAN, params),
    nonlinearScan: (params: any) => ipcRenderer.invoke(IPC_CHANNELS.NEMT_NONLINEAR_SCAN, params),
  },

  // 策略
  strategy: {
    list: () => ipcRenderer.invoke(IPC_CHANNELS.STRATEGY_LIST),
    get: (id: string) => ipcRenderer.invoke(IPC_CHANNELS.STRATEGY_GET, id),
    create: (config: any) => ipcRenderer.invoke(IPC_CHANNELS.STRATEGY_CREATE, config),
    update: (id: string, config: any) => ipcRenderer.invoke(IPC_CHANNELS.STRATEGY_UPDATE, id, config),
    delete: (id: string) => ipcRenderer.invoke(IPC_CHANNELS.STRATEGY_DELETE, id),
    run: (id: string, data: number[]) => ipcRenderer.invoke(IPC_CHANNELS.STRATEGY_RUN, id, data),
  },

  // 回测
  backtest: {
    run: (config: any) => ipcRenderer.invoke(IPC_CHANNELS.BACKTEST_RUN, config),
    status: () => ipcRenderer.invoke(IPC_CHANNELS.BACKTEST_STATUS),
    cancel: () => ipcRenderer.invoke(IPC_CHANNELS.BACKTEST_CANCEL),
    results: () => ipcRenderer.invoke(IPC_CHANNELS.BACKTEST_RESULTS),
    onProgress: (callback: (progress: any) => void) => {
      ipcRenderer.on('backtest:progress', (_, data) => callback(data));
    },
  },

  // 风控
  risk: {
    check: (order: any) => ipcRenderer.invoke(IPC_CHANNELS.RISK_CHECK, order),
    status: () => ipcRenderer.invoke(IPC_CHANNELS.RISK_STATUS),
  },

  // 系统
  system: {
    status: () => ipcRenderer.invoke(IPC_CHANNELS.SYSTEM_STATUS),
    logs: () => ipcRenderer.invoke(IPC_CHANNELS.SYSTEM_LOGS),
  },
});

// 类型声明
declare global {
  interface Window {
    nemt: {
      nemt: any;
      strategy: any;
      backtest: any;
      risk: any;
      system: any;
    };
  }
}
```

### 7.2 React中的IPC调用

```typescript
// src/services/ipcClient.ts

class NEMTService {
  async runSimulation(params: any): Promise<any> {
    return window.nemt.nemt.run(params);
  }

  async runNoiseScan(params: any): Promise<any> {
    return window.nemt.nemt.noiseScan(params);
  }
}

// 使用示例
const nemtService = new NEMTService();

// 在React组件中
const result = await nemtService.runSimulation({
  alpha: 0.1,
  beta: 1.0,
  noiseLevel: 0.2,
  steps: 200,
  n: 1000,
});
```

---

## 8. Python子进程

### 8.1 RPC服务器

```python
# python/services/rpc_server.py

"""
NEMT JSON-RPC 服务器
基于标准库的简单JSON-RPC实现
"""

import json
import sys
import traceback
from typing import Any, Callable, Dict
from jsonrpc import JSONRPCResponseManager, dispatcher

# 添加项目路径
sys.path.insert(0, '../..')

from nemt.core import NEMTSimulator, NEMTParams
from strategies.base import StrategyBase
from backtest.engine import BacktestEngine


class NEMTRPCServer:
    def __init__(self):
        self.simulator = NEMTSimulator()
        self.backtest_engine = BacktestEngine()
        self._register_methods()

    def _register_methods(self):
        """注册所有RPC方法"""
        dispatcher['nemt.run'] = self._nemt_run
        dispatcher['nemt.noise_scan'] = self._nemt_noise_scan
        dispatcher['strategy.list'] = self._strategy_list
        dispatcher['strategy.run'] = self._strategy_run
        dispatcher['backtest.run'] = self._backtest_run
        dispatcher['backtest.status'] = self._backtest_status
        dispatcher['risk.check'] = self._risk_check

    def _nemt_run(self, params: Dict) -> Dict:
        """运行NEMT模拟"""
        try:
            nemt_params = NEMTParams(**params)
            self.simulator = NEMTSimulator(nemt_params)
            psi = self.simulator.initialize_state(params['data'])
            psi = self.simulator.evolve(psi)
            freqs, spectrum = self.simulator.spectral_analysis()
            spectral_width = self.simulator.compute_spectral_width()
            resonance = self.simulator.detect_resonance()

            return {
                'success': True,
                'data': {
                    'spectralWidth': spectral_width,
                    'meanFrequency': self.simulator.mean_frequency,
                    'spectrum': spectrum.tolist(),
                    'freqs': freqs.tolist(),
                    'resonance': resonance,
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _nemt_noise_scan(self, params: Dict) -> Dict:
        """噪声扫描"""
        # 实现噪声扫描逻辑
        pass

    def _strategy_list(self) -> Dict:
        """获取策略列表"""
        return {
            'success': True,
            'data': [
                {'id': 'trend_001', 'name': '趋势策略', 'type': 'trend', 'status': 'active'},
                {'id': 'mean_rev_001', 'name': '均值回归', 'type': 'mean_rev', 'status': 'active'},
                {'id': 'momentum_001', 'name': '动量策略', 'type': 'momentum', 'status': 'active'},
            ]
        }

    def _strategy_run(self, strategy_id: str, data: list) -> Dict:
        """运行策略"""
        # 实现策略运行逻辑
        pass

    def _backtest_run(self, config: Dict) -> Dict:
        """运行回测"""
        # 实现回测逻辑
        pass

    def _backtest_status(self) -> Dict:
        """获取回测状态"""
        return {
            'success': True,
            'data': {
                'running': self.backtest_engine.is_running,
                'progress': self.backtest_engine.progress,
            }
        }

    def _risk_check(self, order: Dict) -> Dict:
        """风控检查"""
        # 实现风控逻辑
        pass

    def handle_request(self, request: str) -> str:
        """处理JSON-RPC请求"""
        response = JSONRPCResponseManager.handle(request, dispatcher)
        return json.dumps(response.data)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9555)
    args = parser.parse_args()

    server = NEMTRPCServer()
    print(f"NEMT RPC Server ready on port {args.port}", file=sys.stderr)

    # 简单交互循环
    while True:
        try:
            request = sys.stdin.readline()
            if not request:
                break
            response = server.handle_request(request.strip())
            print(response)
            sys.stdout.flush()
        except Exception as e:
            error_response = json.dumps({
                'jsonrpc': '2.0',
                'error': {'code': -32603, 'message': str(e)},
                'id': None
            })
            print(error_response)
            sys.stdout.flush()


if __name__ == '__main__':
    main()
```

### 8.2 NEMT核心迁移

```python
# python/nemt/core.py
# 直接复用现有 nemt_core.py 的代码

import numpy as np
from scipy.fft import fft, ifft, fftfreq
from dataclasses import dataclass, asdict
from typing import Optional, Tuple, Dict, Any
import warnings


@dataclass
class NEMTParams:
    """NEMT模型参数"""
    alpha: float = 0.1       # 扩散系数
    beta: float = 1.0       # 非线性强度
    noise_level: float = 0.2  # 噪声水平
    dt: float = 0.01        # 时间步长
    dx: float = 1.0         # 空间步长
    steps: int = 200         # 演化步数
    n: int = 1000           # 数据点数量

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NEMTParams':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class NEMTSimulator:
    """非平衡市场理论模拟器"""

    def __init__(self, params: Optional[NEMTParams] = None):
        self.params = params or NEMTParams()
        self.psi_history = []
        self.spectrum = None
        self.spectral_width = None
        self.psi = None
        self.N = None

    def initialize_state(self, price_data: np.ndarray) -> np.ndarray:
        """初始化市场状态"""
        normalized = (price_data - np.mean(price_data)) / np.std(price_data)
        psi = normalized + 1j * np.zeros_like(normalized)
        self.psi = psi
        self.N = len(psi)
        return psi

    def evolve(self, psi: np.ndarray, steps: Optional[int] = None) -> np.ndarray:
        """时间演化"""
        psi = psi.copy()
        steps = steps or self.params.steps
        self.psi_history = [np.abs(psi)]

        alpha = self.params.alpha
        beta = self.params.beta
        dt = self.params.dt

        for t in range(steps):
            laplacian = self._compute_laplacian(psi)
            psi_abs = np.abs(psi)
            psi_abs = np.clip(psi_abs, 0, 10)
            nonlinear = beta * (psi_abs ** 2) * psi
            dpsi = 1j * (alpha * laplacian + nonlinear)
            noise = self._generate_noise(len(psi))
            psi = psi + dt * (dpsi + noise)
            self.psi_history.append(np.abs(psi))

        self.psi_final = psi
        self.psi_evolution = np.array(self.psi_history).T
        return psi

    def _compute_laplacian(self, psi: np.ndarray) -> np.ndarray:
        """计算拉普拉斯算子"""
        laplacian = np.zeros_like(psi, dtype=complex)
        laplacian[1:-1] = psi[:-2] - 2*psi[1:-1] + psi[2:]
        laplacian[0] = psi[1] - 2*psi[0]
        laplacian[-1] = psi[-2] - 2*psi[-1]
        return laplacian / (self.params.dx ** 2)

    def _generate_noise(self, size: int) -> np.ndarray:
        """生成高斯噪声"""
        return self.params.noise_level * np.random.randn(size) * \
               (1 + 1j * np.random.randn(size)) / np.sqrt(2)

    def spectral_analysis(self, psi: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """频谱分析"""
        psi_to_use = psi if psi is not None else self.psi_final
        spectrum = fft(psi_to_use)
        N = len(psi_to_use)
        freqs = fftfreq(N, self.params.dx)
        positive_mask = freqs >= 0
        freqs_positive = freqs[positive_mask]
        spectrum_positive = np.abs(spectrum[positive_mask])
        self.spectrum = spectrum_positive
        self.freqs = freqs_positive
        return freqs_positive, spectrum_positive

    def compute_spectral_width(self) -> float:
        """计算谱宽"""
        if self.spectrum is None:
            self.spectral_analysis()
        spectrum_power = np.abs(self.spectrum) ** 2
        freqs = self.freqs
        total_power = np.sum(spectrum_power)
        if total_power < 1e-10:
            warnings.warn("谱功率过低")
            return 0.0
        mean_freq = np.sum(freqs * spectrum_power) / total_power
        variance = np.sum((freqs - mean_freq) ** 2 * spectrum_power) / total_power
        spectral_width = np.sqrt(variance)
        self.spectral_width = spectral_width
        self.mean_frequency = mean_freq
        return spectral_width

    def detect_resonance(self) -> Dict:
        """检测共振峰"""
        if self.spectrum is None:
            self.spectral_analysis()
        spectrum_power = np.abs(self.spectrum) ** 2
        peak_indices = []
        for i in range(1, len(spectrum_power) - 1):
            if spectrum_power[i] > spectrum_power[i-1] and \
               spectrum_power[i] > spectrum_power[i+1]:
                if spectrum_power[i] > np.mean(spectrum_power) * 2:
                    peak_indices.append(i)
        return {
            'peak_frequencies': self.freqs[peak_indices].tolist(),
            'peak_amplitudes': np.abs(self.spectrum[peak_indices]).tolist(),
            'num_peaks': len(peak_indices)
        }

    def run_experiment(self, price_data: np.ndarray) -> Dict[str, Any]:
        """运行完整实验"""
        psi = self.initialize_state(price_data)
        psi = self.evolve(psi)
        freqs, spectrum = self.spectral_analysis()
        spectral_width = self.compute_spectral_width()
        resonance = self.detect_resonance()

        return {
            'spectralWidth': spectral_width,
            'meanFrequency': self.mean_frequency,
            'spectrum': spectrum.tolist(),
            'freqs': freqs.tolist(),
            'resonance': resonance,
            'evolution': np.array(self.psi_history).tolist() if self.psi_history else [],
            'params': self.params.to_dict(),
        }
```

---

## 9. 厨房验收标准

### 9.1 基础验收（Kitchen Ready）

| 验收项 | 验证方法 | 预期结果 |
|-------|---------|---------|
| 项目启动 | `npm run dev` | 无报错，主窗口显示 |
| Python就绪 | 查看日志 | "Python RPC Server ready" |
| IPC连接 | 前端控制台 | 无连接错误 |
| 日志系统 | 查看logs目录 | 日志文件正常写入 |
| 配置加载 | 修改settings.yaml | 配置变更生效 |

### 9.2 Mock数据验收（Kitchen with Mock）

| 验收项 | 验证方法 | 预期结果 |
|-------|---------|---------|
| NEMT模拟 | 点击"运行" | 返回谱宽数值 |
| 策略列表 | 查看策略面板 | 显示Mock策略 |
| 回测运行 | 运行回测 | 返回模拟结果 |
| 风控检查 | 提交订单 | 风控通过/拒绝 |

### 9.3 真实数据验收（Chef Phase 1）

| 验收项 | 验证方法 | 预期结果 |
|-------|---------|---------|
| 数据加载 | 加载CSV | 数据正常解析 |
| NEMT真实计算 | 运行模拟 | 正确计算谱宽 |
| 策略信号生成 | 运行策略 | 生成交易信号 |
| 回测执行 | 运行完整回测 | 产出性能指标 |

---

## 10. 开发任务清单

### 阶段一：厨房搭建（Kitchen）

#### K1 - 项目初始化
- [ ] 初始化Electron + React + Vite项目
- [ ] 配置TypeScript
- [ ] 配置TailwindCSS
- [ ] 配置electron-builder
- [ ] 验证项目能启动

#### K2 - Electron主进程
- [ ] 实现主进程入口（main.ts）
- [ ] 实现预加载脚本（preload.ts）
- [ ] 实现窗口管理器
- [ ] 实现日志服务

#### K3 - IPC通信层
- [ ] 定义IPC通道常量
- [ ] 实现IPC处理器注册
- [ ] 实现Python进程管理器
- [ ] 验证IPC通信正常

#### K4 - Python RPC服务器
- [ ] 实现JSON-RPC服务器骨架
- [ ] 注册基础方法
- [ ] 实现错误处理
- [ ] 验证Python进程启动

#### K5 - 基础UI
- [ ] 迁移现有App.tsx组件
- [ ] 适配IPC调用
- [ ] 实现加载状态
- [ ] 实现错误提示

### 阶段二：厨师填充（Chef）

#### C1 - NEMT核心集成
- [ ] 迁移nemt_core.py到python/nemt/
- [ ] 实现Python RPC方法
- [ ] 前端对接NEMT服务
- [ ] 验证谱宽计算正确

#### C2 - 策略模块
- [ ] 定义策略基类
- [ ] 实现趋势策略
- [ ] 实现均值回归策略
- [ ] 实现动量策略
- [ ] 策略列表API

#### C3 - 信号模块
- [ ] 实现信号生成器
- [ ] 实现技术指标（RSI, MACD, MA, BB）
- [ ] 信号聚合逻辑

#### C4 - 回测引擎
- [ ] 实现回测循环
- [ ] 实现性能指标计算
- [ ] 实现结果存储
- [ ] 前端回测界面

#### C5 - 风控模块
- [ ] 实现风控规则引擎
- [ ] 实现仓位检查
- [ ] 实现回撤限制
- [ ] 前端风控状态显示

### 阶段三：完善（Polish）

#### P1 - 数据持久化
- [ ] SQLite数据库集成
- [ ] 回测结果存储
- [ ] 策略配置持久化

#### P2 - 界面优化
- [ ] 图表优化
- [ ] 响应式布局
- [ ] 主题切换

#### P3 - 打包发布
- [ ] 配置打包脚本
- [ ] 生成安装包
- [ ] 验证Windows/Mac运行

---

## 11. 技术选型

### 11.1 依赖版本

| 包 | 版本 | 说明 |
|---|------|------|
| electron | ^28.0.0 | 桌面框架 |
| react | ^18.2.0 | UI库 |
| typescript | ^5.3.0 | 类型系统 |
| vite | ^5.0.0 | 构建工具 |
| @electron-toolkit | ^2.0.0 | Electron工具包 |
| tailwindcss | ^3.4.0 | 样式框架 |
| lucide-react | ^0.300.0 | 图标库 |
| better-sqlite3 | ^9.2.0 | SQLite绑定 |
| numpy | ^1.26.0 | Python数值计算 |
| scipy | ^1.11.0 | Python科学计算 |

### 11.2 package.json关键脚本

```json
{
  "scripts": {
    "dev": "concurrently \"npm run dev:renderer\" \"npm run dev:electron\"",
    "dev:renderer": "vite",
    "dev:electron": "wait-on http://localhost:5173 && electron .",
    "build": "npm run build:renderer && npm run build:electron",
    "build:renderer": "vite build",
    "build:electron": "tsc -p tsconfig.electron.json",
    "pack": "npm run build && electron-builder --dir",
    "dist": "npm run build && electron-builder",
    "postinstall": "electron-builder install-app-deps"
  }
}
```

---

## 附录：现有代码迁移映射

| 现有文件 | 目标位置 | 迁移方式 |
|---------|---------|---------|
| `nemt_core.py` | `python/nemt/core.py` | 直接复制 |
| `nemtPipeline.ts` | `src/services/nemtPipeline.ts` | 改造IPC调用 |
| `executionFramework.ts` | `src/services/executionService.ts` | 改造IPC调用 |
| `App.tsx` | `src/App.tsx` | 直接迁移 |
| `components/*` | `src/components/*` | 直接迁移 |
| `quant-mvp/calculator/` | `python/strategies/` | 参考实现 |

---

*文档版本：1.0*
*创建日期：2026-04-18*
*设计理念：厨房理论 - 架构优先开发模型*
