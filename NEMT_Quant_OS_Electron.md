# NEMT Quant OS Electron - 架构优先开发

> **版本**: v0.1 | **更新**: 2026-04-19 | **状态**: 🏗️ 厨房阶段进行中

---

## 一、厨房理论核心理念

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ❶ 先搭厨房，再请厨师                                            │
│     → 系统必须先能编译/运行，再谈业务逻辑                         │
│                                                                  │
│  ❷ 厨房阶段禁止深度业务逻辑                                     │
│     → 只有框架、接口、模拟数据                                   │
│                                                                  │
│  ❸ 厨师阶段只填充实现，不改厨房结构                              │
│     → 接口契约神圣不可侵犯                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、整体开发阶段

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEMT Quant OS Electron 开发阶段                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: 厨房阶段 (Architecture Kitchen)                          │ Week 1  │
│  ──────────────────────────────────────                                   │
│  • 项目结构搭建                                                         │
│  • Electron 主进程骨架                                                   │
│  • React 前端骨架                                                        │
│  • IPC 通信协议定义                                                      │
│  • Python 服务骨架                                                       │
│  • Mock 数据层                                                            │
│  • 日志/配置/错误处理                                                    │
│  • 验收: 能运行，显示 "Kitchen Ready"                                 │
│                                                                              │
│  Phase 2: 厨房阶段 - 数据层 (Data Kitchen)                     │  Week 2  │
│  ──────────────────────────────────────                                   │
│  • 市场数据抽象层                                                        │
│  • K线数据结构                                                           │
│  • 数据存储层 (SQLite)                                                   │
│  • Redis 事件总线                                                       │
│  • Notion 适配器骨架                                                     │
│  • 验收: 能显示模拟市场数据                                              │
│                                                                              │
│  Phase 3: 厨师阶段 - NEMT Core (Chef: NEMT)                    │  Week 3  │
│  ──────────────────────────────────────                                   │
│  • NLS 方程实现                                                          │
│  • 四相位检测                                                            │
│  • 谱分析                                                                │
│  • 信号生成                                                              │
│  • 验收: NEMT Core 能输出有效信号                                       │
│                                                                              │
│  Phase 4: 厨师阶段 - 策略层 (Chef: Strategy)                  │  Week 4  │
│  ──────────────────────────────────────                                   │
│  • 策略工厂                                                              │
│  • 策略模板                                                              │
│  • 回测引擎                                                              │
│  • 评分系统                                                              │
│  • 验收: 能生成、测试、评分策略                                          │
│                                                                              │
│  Phase 5: 厨师阶段 - 风险/大脑层                           │  Week 5  │
│  ──────────────────────────────────────                                   │
│  • 风控规则                                                              │
│  • 权重分配                                                              │
│  • 大脑决策                                                              │
│  • 进化系统                                                              │
│  • 验收: 系统能自动管理策略组合                                           │
│                                                                              │
│  Phase 6: 生产化 (Production)                                │  Week 6  │
│  ──────────────────────────────────────                                   │
│  • 打包 Electron                                                          │
│  • 性能优化                                                              │
│  • 完整测试                                                              │
│  • 文档完善                                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、多节点系统架构

> **核心理念**: 厨房（架构）已就绪 → 多个独立节点（模块）并行开发 → 每个节点有自己的输入/输出/验收标准

### 3.1 系统节点总览

```
┌─────────────────────────────────────────────────────────────┐
│                      多节点量化系统                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  市场层      │───→│  模型层      │───→│  策略层      │  │
│  │ Market Node  │    │ Model Node   │    │ Strategy Node│  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                   │         │
│                                                   ↓         │
│                              ┌──────────────┐    ┌──────────────┐
│                              │ 资金管理层   │←───│ 策略淘汰模块 │
│                              │ Capital Node │    │ Eviction    │
│                              └──────────────┘    └──────────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**节点通信协议（所有节点遵循）：**
- **输入**: 标准化的 `MarketDataFrame`（时间戳、OHLCV、成交量）
- **输出**: 标准化的 `Signal` / `Position` / `Allocation` 对象
- **接口**: 所有节点必须实现 `run(input) -> output` 方法

### 3.2 节点定义

| 节点 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **市场层** | 获取市场数据、清洗、对齐 | - | MarketData |
| **模型层** | 计算特征、预测信号 | MarketData | ModelSignal |
| **策略层** | 组合信号、生成订单 | ModelSignal[] | Order |
| **资金管理层** | 分配资金、风控 | Order[] | FinalOrder |
| **淘汰模块** | 评估、淘汰差策略 | Order[] | EvictionLog |

### 3.3 节点详细设计

#### 节点 ① 市场层 (Market Node)

```python
class BaseMarketProvider(ABC):
    """市场数据抽象基类"""
    @abstractmethod
    def get_latest(self, symbol: str, interval: str) -> MarketData:
        """获取最新市场数据"""
        pass

    @abstractmethod
    def get_history(self, symbol: str, start: datetime, end: datetime) -> List[MarketData]:
        """获取历史数据"""
        pass

# Mock 实现（厨房阶段）
class MockMarketProvider(BaseMarketProvider):
    def get_latest(self, symbol: str, interval: str) -> MarketData:
        return MarketData(
            timestamp=datetime.now(),
            open=67000, high=67500, low=66800, close=67200,
            volume=12345
        )
```

#### 节点 ② 模型层 (Model Node)

```python
class BaseModel(ABC):
    """模型抽象基类"""
    @abstractmethod
    def predict(self, data: MarketData) -> ModelSignal:
        """预测信号"""
        pass

    def get_confidence(self) -> float:
        """置信度"""
        return 0.5

# Mock 实现（厨房阶段）
class MockModel(BaseModel):
    def predict(self, data: MarketData) -> ModelSignal:
        directions = [-1, 0, 1]
        return ModelSignal(
            direction=random.choice(directions),
            confidence=random.uniform(0.3, 0.9),
            strength=random.uniform(0.1, 1.0)
        )
```

#### 节点 ③ 策略层 (Strategy Node)

```python
class BaseStrategy(ABC):
    """策略抽象基类"""
    @abstractmethod
    def generate_signal(self, model_outputs: List[ModelSignal]) -> Order:
        """生成订单"""
        pass

# 策略状态
class StrategyState(Enum):
    ALIVE = "alive"      # 活跃
    TESTING = "testing"  # 测试中
    DORMANT = "dormant"  # 休眠
    DEAD = "dead"        # 已淘汰
```

#### 节点 ④ 资金管理层 (Capital Node)

```python
class BaseCapitalManager(ABC):
    """资金管理抽象基类"""
    @abstractmethod
    def allocate(self, orders: List[Order]) -> List[FinalOrder]:
        """分配资金"""
        pass

# Mock 实现（等权重分配）
class EqualWeightCapitalManager(BaseCapitalManager):
    def allocate(self, orders: List[Order]) -> List[FinalOrder]:
        total = len(orders)
        if total == 0:
            return []
        weight = 1.0 / total
        return [order.to_final(weight) for order in orders]
```

### 3.4 策略淘汰闭环 (Eviction Loop)

**触发条件（每周评估一次）：**
- 策略连续 5 个交易日亏损 > 5%
- 策略夏普比率 < 0（近20日）
- 策略最大回撤超过历史均值的 2 倍
- 策略信号与其他策略平均相关性 > 0.9（冗余淘汰）

**淘汰流程：**

```
┌─────────────┐    ┌────────────────┐    ┌─────────────────┐
│ 策略表现监控 │───→│ 触发淘汰条件?  │───→│ 标记为淘汰候选  │
└─────────────┘    └────────────────┘    └────────┬────────┘
                           │                      │
                           ↓                      ↓
                  ┌────────────────┐    ┌─────────────────┐
                  │      否        │    │  资金权重归零    │
                  └────────────────┘    └────────┬────────┘
                                                   │
                                                   ↓
                                          ┌─────────────────┐
                                          │ 移至休眠区      │
                                          └────────┬────────┘
                                                   │
                                                   ↓
                                          ┌─────────────────┐
                                          │ 通知开发人员    │
                                          └─────────────────┘
```

### 3.5 完整数据流示例

```python
# 伪代码：一个完整循环
market_data = MarketNode.get_latest()           # 市场层
model_signals = ModelNode.predict(market_data)  # 模型层
strategy_orders = StrategyNode.run(model_signals) # 策略层
final_orders = CapitalNode.allocate(strategy_orders) # 资金管理层
executor.execute(final_orders)                  # 执行
EvictionNode.evaluate(strategy_orders)         # 淘汰检查
```

---

## 四、厨房阶段清单 (Phase 1)

### 3.1 项目目录结构

```
NEMT-Quant-OS-Electron/
├── electron/                      # Electron 主进程
│   ├── main.ts                   # 入口 (能打印 "Kitchen Ready")
│   ├── preload.ts               # contextBridge 骨架
│   ├── services/
│   │   └── serviceManager.ts    # 服务管理器 (骨架)
│   ├── ipc/
│   │   ├── handlers.ts          # IPC 处理器注册
│   │   └── types.ts             # IPC 类型定义
│   └── menu.ts                  # 原生菜单 (骨架)
│
├── web/                          # React 前端
│   ├── src/
│   │   ├── App.tsx              # 主组件 (骨架)
│   │   ├── main.tsx
│   │   ├── electron/
│   │   │   └── api.ts          # Electron API 封装 (骨架)
│   │   ├── pages/
│   │   │   └── Dashboard.tsx    # 仪表盘 (骨架)
│   │   ├── components/
│   │   │   ├── Layout.tsx       # 布局组件
│   │   │   └── StatusBar.tsx   # 状态栏
│   │   ├── stores/
│   │   │   └── appStore.ts     # 状态管理 (骨架)
│   │   └── types/
│   │       └── index.ts        # 类型定义
│   └── package.json
│
├── quant-sync-server/            # Python 服务
│   ├── main.py                  # 入口 (能打印 "Kitchen Ready")
│   ├── config.py                # 配置管理
│   ├── api/
│   │   ├── routes.py            # API 路由 (骨架)
│   │   └── schemas.py           # Pydantic 模型
│   ├── adapters/                # 适配器 (骨架)
│   ├── services/                # 服务层 (骨架)
│   └── requirements.txt
│
├── shared/                       # 共享代码
│   └── types/                   # 共享类型定义
│       ├── strategy.ts
│       ├── market.ts
│       └── backtest.ts
│
├── tests/                       # 测试骨架
│   ├── electron/
│   ├── web/
│   └── python/
│
├── package.json                 # 根 package.json
├── tsconfig.json
├── vite.config.ts
├── electron-builder.yml
└── README.md
```

### 3.2 Electron 主进程 (厨房)

**目标**: 能启动，显示 "Kitchen Ready"，日志正常

```
electron/main.ts
```

```typescript
import { app, BrowserWindow, ipcMain } from 'electron';
import { setupLogger } from './services/logger';
import { setupIpcHandlers } from './ipc/handlers';
import { ServiceManager } from './services/serviceManager';

const logger = setupLogger();

async function createWindow() {
  logger.info('Creating main window...');
  
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    title: 'NEMT Quant OS'
  });

  await win.loadURL('http://localhost:5173');
  logger.info('Window created successfully');
}

async function startServices() {
  logger.info('Starting services...');
  const serviceManager = new ServiceManager();
  await serviceManager.startAll();
  logger.info('All services started');
}

app.whenReady().then(async () => {
  logger.info('='.repeat(50));
  logger.info('NEMT Quant OS Electron - Kitchen Ready');
  logger.info('='.repeat(50));
  
  await startServices();
  await createWindow();
  setupIpcHandlers();
  
  logger.info('Kitchen initialization complete');
});

app.on('window-all-closed', () => {
  logger.info('All windows closed, quitting...');
  app.quit();
});
```

**验收标准**:
- [ ] `npm run dev` 能启动 Electron
- [ ] 控制台输出 "Kitchen Ready"
- [ ] 无红色错误
- [ ] 窗口正常显示

### 3.3 React 前端 (厨房)

**目标**: 基础布局，能连接 Electron，显示状态

```
web/src/App.tsx
```

```typescript
import { useEffect, useState } from 'react';
import { Layout } from './components/Layout';
import { StatusBar } from './components/StatusBar';
import { Dashboard } from './pages/Dashboard';
import { useAppStore } from './stores/appStore';

function App() {
  const { status, connect, systemStatus } = useAppStore();
  const [kitchenReady, setKitchenReady] = useState(false);

  useEffect(() => {
    // 连接 Electron
    connect();
    setKitchenReady(true);
    
    // 获取系统状态
    systemStatus();
  }, []);

  if (!kitchenReady) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">🔧</div>
          <div>Initializing Kitchen...</div>
        </div>
      </div>
    );
  }

  return (
    <Layout>
      <StatusBar status={status} />
      <Dashboard />
    </Layout>
  );
}

export default App;
```

**验收标准**:
- [ ] 页面正常加载
- [ ] 显示 "Kitchen Ready" 状态
- [ ] 无 TypeScript 编译错误

### 3.4 Python 服务 (厨房)

**目标**: FastAPI 能启动，基础 API 可调用

```
quant-sync-server/main.py
```

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config import settings
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="NEMT Quant Sync Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("NEMT Quant Sync Server - Kitchen Ready")
    logger.info("=" * 50)
    logger.info(f"Notion: {'Configured' if settings.notion_token else 'Not Configured'}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "kitchen": "ready"}
```

**验收标准**:
- [ ] `uvicorn main:app` 能启动
- [ ] `/health` 返回 `{"status": "ok"}`
- [ ] 控制台输出 "Kitchen Ready"

### 3.5 IPC 通信协议 (厨房)

**定义所有接口契约，但不实现业务逻辑**

```
electron/ipc/types.ts
```

```typescript
// ============================================================
// NEMT Quant OS - IPC Type Definitions (Kitchen Version)
// 所有接口在这里定义，具体实现后面填充
// ============================================================

// 策略相关
export interface Strategy {
  id: string;
  name: string;
  type: StrategyType;
  status: StrategyStatus;
  params: Record<string, number>;
  performance?: PerformanceMetrics;
  createdAt: string;
}

export type StrategyType = 'nemt-dci' | 'trend' | 'mean-rev' | 'momentum';
export type StrategyStatus = 'alive' | 'testing' | 'dormant' | 'dead';

export interface PerformanceMetrics {
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  totalPnL: number;
  score: number;
}

// 市场数据
export interface MarketData {
  symbol: string;
  price: number;
  timestamp: number;
  volume: number;
}

export interface KLine {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: number;
}

// 回测相关
export interface BacktestConfig {
  strategyId: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
}

export interface BacktestResult {
  id: string;
  status: 'running' | 'completed' | 'failed';
  progress: number;
  metrics?: BacktestMetrics;
}

export interface BacktestMetrics {
  totalTrades: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  profitFactor: number;
}

// 系统状态
export interface SystemStatus {
  pythonServer: 'running' | 'stopped';
  marketData: 'connected' | 'disconnected';
  activeStrategies: number;
  systemMode: 'normal' | 'caution' | 'defense';
}

// IPC API 接口 (所有接口定义在这里)
export interface ElectronAPI {
  // 策略管理
  strategy: {
    generate(params: Partial<Strategy>): Promise<Strategy>;
    list(): Promise<Strategy[]>;
    get(id: string): Promise<Strategy | null>;
    update(id: string, data: Partial<Strategy>): Promise<Strategy>;
    delete(id: string): Promise<void>;
  };

  // 回测
  backtest: {
    run(config: BacktestConfig): Promise<string>; // job ID
    getResult(jobId: string): Promise<BacktestResult>;
    cancel(jobId: string): Promise<void>;
    onProgress(callback: (progress: number) => void): () => void;
  };

  // 市场数据
  market: {
    getPrice(symbol: string): Promise<number>;
    getKlines(symbol: string, interval: string, limit: number): Promise<KLine[]>;
    onTick(callback: (tick: MarketData) => void): () => void;
  };

  // Notion 同步
  notion: {
    syncStrategies(): Promise<SyncResult>;
    syncBacktests(): Promise<SyncResult>;
  };

  // 系统
  system: {
    getStatus(): Promise<SystemStatus>;
    restartPython(): Promise<void>;
    quit(): Promise<void>;
  };
}

export interface SyncResult {
  success: boolean;
  count: number;
  errors?: string[];
}
```

**验收标准**:
- [ ] 所有接口类型已定义
- [ ] TypeScript 编译通过
- [ ] 文档已生成

### 3.6 Mock 数据层 (厨房)

**提供模拟数据，让 UI 能正常显示**

```
electron/services/mockData.ts
```

```typescript
import { Strategy, MarketData, BacktestResult, SystemStatus } from '../ipc/types';

// Mock 策略
export function getMockStrategies(): Strategy[] {
  return [
    {
      id: 'strat-001',
      name: 'NEMT-DCI 策略 A',
      type: 'nemt-dci',
      status: 'alive',
      params: { alpha: 0.5, beta: 0.3, noise: 0.1 },
      performance: {
        sharpeRatio: 1.8,
        maxDrawdown: 0.12,
        winRate: 0.62,
        totalPnL: 24500,
        score: 85
      },
      createdAt: '2026-04-01T10:00:00Z'
    },
    {
      id: 'strat-002',
      name: '趋势跟踪 B',
      type: 'trend',
      status: 'testing',
      params: { maPeriod: 20, threshold: 0.02 },
      performance: {
        sharpeRatio: 1.2,
        maxDrawdown: 0.08,
        winRate: 0.55,
        totalPnL: 12800,
        score: 72
      },
      createdAt: '2026-04-10T14:30:00Z'
    },
    {
      id: 'strat-003',
      name: '均值回归 C',
      type: 'mean-rev',
      status: 'dormant',
      params: { bbPeriod: 20, stdDev: 2 },
      createdAt: '2026-03-20T09:00:00Z'
    }
  ];
}

// Mock 市场数据
export function getMockMarketData(): MarketData {
  return {
    symbol: 'BTC/USDT',
    price: 67432.50 + (Math.random() - 0.5) * 100,
    timestamp: Date.now(),
    volume: 12345678.90
  };
}

// Mock 回测结果
export function getMockBacktestResult(jobId: string): BacktestResult {
  return {
    id: jobId,
    status: 'completed',
    progress: 100,
    metrics: {
      totalTrades: 156,
      winRate: 0.63,
      sharpeRatio: 1.95,
      maxDrawdown: 0.11,
      profitFactor: 2.1
    }
  };
}

// Mock 系统状态
export function getMockSystemStatus(): SystemStatus {
  return {
    pythonServer: 'running',
    marketData: 'connected',
    activeStrategies: 3,
    systemMode: 'normal'
  };
}
```

**验收标准**:
- [ ] Mock 数据返回正常
- [ ] UI 能正常显示模拟数据
- [ ] 可切换 Mock/真实数据源

---

## 四、厨房验收检查表 (Phase 1)

### 4.1 必须项检查

```
项目结构
├── electron/          ✅ 目录存在
├── web/               ✅ 目录存在
├── quant-sync-server/ ✅ 目录存在
└── package.json       ✅ 存在

配置文件
├── .env               ✅ 存在
├── tsconfig.json      ✅ 存在
└── vite.config.ts     ✅ 存在

依赖锁定
├── requirements.txt   ✅ 存在
└── package.json       ✅ 依赖已锁定

运行入口
├── electron/main.ts   ✅ 能打印 "Kitchen Ready"
└── quant-sync-server/main.py  ✅ 能打印 "Kitchen Ready"

日志系统
└── 每个模块都有 logger ✅

错误处理
└── 全局异常捕获 ✅

Mock 数据
└── 能返回模拟数据 ✅

单元测试骨架
└── tests/ 目录 ✅
```

### 4.2 功能检查

```
✅ Electron 能启动
✅ React 页面能加载
✅ Python API 能访问
✅ IPC 通信正常
✅ Mock 数据能显示
✅ 日志正常输出
```

### 4.3 禁止项检查 (厨房阶段禁止)

```
❌ 真实算法 (RSI, MA 等) - 禁止
❌ 真实 API 调用 - 禁止
❌ 超过 10 行业务逻辑 - 禁止
❌ 硬编码业务常量 - 禁止
```

---

## 五、厨师阶段预告 (Phase 3+)

> 厨房完成后，进入厨师阶段，依次实现:

### Phase 3: NEMT Core 厨师

```
模块: NEMT Core
厨房状态: ✅ 就绪
厨师任务:
  ├── 实现 NLS 方程
  ├── 实现四相位检测
  ├── 实现谱分析
  └── 实现信号生成

验收标准:
  1. NEMT Core 能处理 K线数据
  2. 输出有效相位判断
  3. 生成有效信号
  4. 与 Mock 层对接正常
```

### Phase 4: 策略层 厨师

```
模块: 策略工厂
厨房状态: ✅ 就绪
厨师任务:
  ├── 实现策略模板
  ├── 实现参数校验
  ├── 实现回测引擎
  └── 实现评分系统

验收标准:
  1. 能生成策略
  2. 能运行回测
  3. 能计算评分
  4. 能激活/淘汰策略
```

### Phase 5: 风险/大脑层 厨师

```
模块: Brain Layer
厨房状态: ✅ 就绪
厨师任务:
  ├── 实现权重分配
  ├── 实现资金调度
  ├── 实现风控规则
  └── 实现进化机制

验收标准:
  1. 能根据相位调整权重
  2. 能控制仓位
  3. 能自动淘汰差策略
  4. 能生成新策略
```

---

## 六、相关文档

- [NEMT_Quant_OS_Electron.md](./NEMT_Quant_OS_Electron.md) - 最终方案参考
- [PRD.md](./PRD.md) - 产品需求文档
- [SPEC.md](./SPEC.md) - 技术规格说明
- [TASKS.md](./TASKS.md) - 开发任务清单

---

## 一句话总结

> **厨房理论 = 先让系统空转起来，再让业务跑起来。**

*文档版本: 0.1 (厨房优先版)*
*创建日期: 2026-04-19*
