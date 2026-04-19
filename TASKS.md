# NEMT量化系统 · 开发任务清单 (TASKS)

> 版本: v0.3 | 更新: 2026-04-19 | 状态: 🏗️ 厨房阶段进行中
>
> **开发理念**: 厨房理论 - 先搭厨房，再请厨师
>
> **架构**: 多节点系统 - 市场层→模型层→策略层→资金管理层→淘汰模块

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
│  ❸ 厨师阶段只填充实现，不改厨房结构                             │
│     → 接口契约神圣不可侵犯                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、多节点系统架构

> **核心理念**: 厨房（架构）已就绪 → 多个独立节点（模块）并行开发 → 每个节点有自己的输入/输出/验收标准

### 2.1 系统节点总览

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
│                              │ 资金管理层   │←───│ 淘汰模块    │
│                              │ Capital Node │    │ Eviction    │
│                              └──────────────┘    └──────────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 节点定义

| 节点 | 职责 | 输入 | 输出 | 基类 |
|------|------|------|------|------|
| **市场层** | 获取市场数据、清洗、对齐 | - | MarketData | BaseMarketProvider |
| **模型层** | 计算特征、预测信号 | MarketData | ModelSignal | BaseModel |
| **策略层** | 组合信号、生成订单 | ModelSignal[] | Order | BaseStrategy |
| **资金管理层** | 分配资金、风控 | Order[] | FinalOrder | BaseCapitalManager |
| **淘汰模块** | 评估、淘汰差策略 | Order[] | EvictionLog | BaseEvictionManager |

### 2.3 节点状态追踪

| 节点 | 厨房状态 | 厨师状态 | 备注 |
|------|----------|----------|------|
| 市场层 | 🔄 进行中 | 🔜 待开始 | |
| 模型层 | 🔄 进行中 | 🔜 待开始 | NEMT Core 在此层 |
| 策略层 | 🔄 进行中 | 🔜 待开始 | |
| **资金管理层** | ✅ **已完成** | 🔜 待开始 | Brain Layer 在此层 |
| 淘汰模块 | 🔄 进行中 | 🔜 待开始 | Evolution 在此层 |

**资金管理层已完成功能:**
- [x] `quant-sync-server/services/capital_node.py` - 基础框架
- [x] `BaseCapitalManager` 抽象基类
- [x] `EqualWeightCapitalManager` 等权重分配器
- [x] `PhaseDrivenCapitalManager` 相位驱动分配器
- [x] `RiskAdjustedCapitalManager` 风险调整分配器
- [x] 单元测试通过 (19/19)

---

## 三、开发阶段

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEMT Quant OS Electron 开发阶段                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  M1: 厨房搭建 (v0.1-kitchen)                                    │ Week 1   │
│  ──────────────────────────────────────                                   │
│  • 项目结构搭建                                                         │
│  • 所有节点基类定义                                                    │
│  • Mock 实现                                                           │
│  • 验收: 能运行，显示 "Kitchen Ready"                                 │
│                                                                              │
│  M2: 市场层厨师 (v0.2-chef)                                    │ Week 2   │
│  ──────────────────────────────────────                                   │
│  • 真实数据源接入                                                      │
│  • 数据清洗/对齐                                                       │
│  • 验收: 能获取实时市场数据                                            │
│                                                                              │
│  M3: 模型层厨师 (v0.3-chef)                                    │ Week 3   │
│  ──────────────────────────────────────                                   │
│  • NLS 方程实现                                                        │
│  • 四相位检测                                                          │
│  • 谱分析/信号生成                                                     │
│  • 验收: NEMT Core 能输出有效信号                                      │
│                                                                              │
│  M4: 策略层厨师 (v0.4-chef)                                    │ Week 4   │
│  ──────────────────────────────────────                                   │
│  • 策略工厂                                                            │
│  • 策略模板                                                            │
│  • 回测引擎                                                            │
│  • 评分系统                                                            │
│  • 验收: 能生成、测试、评分策略                                         │
│                                                                              │
│  M5: 资金/淘汰层厨师 (v0.5-chef)                               │ Week 5   │
│  ──────────────────────────────────────                                   │
│  • 权重分配                                                            │
│  • 风控规则                                                            │
│  • 淘汰机制                                                            │
│  • 进化系统                                                            │
│  • 验收: 系统能自动管理策略组合                                         │
│                                                                              │
│  M6: 生产化 (v1.0)                                               │ Week 6   │
│  ──────────────────────────────────────                                   │
│  • Electron 打包                                                        │
│  • 性能优化                                                            │
│  • 完整测试                                                            │
│  • 文档完善                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、厨房阶段清单 (M1)

> **目标**: 先让系统空转起来，所有节点都有 Mock 实现

### 4.1 项目目录结构

```
NEMT-Quant-OS-Electron/
├── electron/                      # Electron 主进程
│   ├── main.ts                   # 入口 (打印 "Kitchen Ready")
│   ├── preload.ts               # contextBridge
│   ├── services/
│   │   ├── logger.ts           # 日志服务
│   │   ├── config.ts           # 配置管理
│   │   └── serviceManager.ts   # 服务管理器
│   ├── ipc/
│   │   ├── handlers.ts         # IPC 处理器
│   │   └── types.ts            # IPC 类型定义
│   └── menu.ts                 # 原生菜单
│
├── web/                          # React 前端
│   ├── src/
│   │   ├── App.tsx             # 主组件
│   │   ├── main.tsx
│   │   ├── electron/
│   │   │   └── api.ts         # Electron API 封装
│   │   ├── components/
│   │   │   ├── Layout.tsx     # 布局组件
│   │   │   └── StatusBar.tsx  # 状态栏
│   │   ├── pages/
│   │   │   └── Dashboard.tsx  # 仪表盘
│   │   ├── stores/
│   │   │   └── appStore.ts    # 状态管理
│   │   └── types/
│   │       └── index.ts        # 类型定义
│   └── package.json
│
├── quant-sync-server/             # Python 服务
│   ├── main.py                  # 入口 (打印 "Kitchen Ready")
│   ├── config.py                # 配置管理
│   ├── api/
│   │   ├── routes.py           # API 路由
│   │   └── schemas.py          # Pydantic 模型
│   ├── adapters/                # 适配器
│   ├── services/               # 服务层
│   │   ├── market_node.py     # 市场层
│   │   ├── model_node.py      # 模型层
│   │   ├── strategy_node.py    # 策略层
│   │   ├── capital_node.py     # 资金管理层
│   │   └── eviction_node.py   # 淘汰模块
│   └── requirements.txt
│
├── shared/                       # 共享代码
│   └── types/                   # 共享类型定义
│       ├── market.py
│       ├── model.py
│       ├── strategy.py
│       └── capital.py
│
├── tests/                       # 测试
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

### 4.2 节点基类定义 (Python)

```python
# shared/types/market.py
@dataclass
class MarketData:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float

# shared/types/model.py
@dataclass
class ModelSignal:
    direction: int  # -1, 0, 1
    confidence: float  # 0.0 ~ 1.0
    strength: float  # 0.0 ~ 1.0
    model_name: str

# shared/types/strategy.py
@dataclass
class Order:
    strategy_id: str
    symbol: str
    direction: int
    quantity: float
    stop_loss: float
    take_profit: float

# shared/types/capital.py
@dataclass
class FinalOrder:
    order: Order
    allocated_capital: float
    weight: float

# 各节点基类
class BaseMarketProvider(ABC):
    @abstractmethod
    def get_latest(self, symbol: str, interval: str) -> MarketData: pass

class BaseModel(ABC):
    @abstractmethod
    def predict(self, data: MarketData) -> ModelSignal: pass

class BaseStrategy(ABC):
    @abstractmethod
    def generate_signal(self, model_outputs: List[ModelSignal]) -> Order: pass

class BaseCapitalManager(ABC):
    @abstractmethod
    def allocate(self, orders: List[Order]) -> List[FinalOrder]: pass

class BaseEvictionManager(ABC):
    @abstractmethod
    def evaluate(self, strategies: List[Strategy]) -> EvictionLog: pass
```

### 4.3 Mock 实现

```python
# Mock 市场层
class MockMarketProvider(BaseMarketProvider):
    def get_latest(self, symbol: str, interval: str) -> MarketData:
        return MarketData(
            timestamp=datetime.now(),
            symbol=symbol,
            open=67000, high=67500, low=66800, close=67200,
            volume=12345
        )

# Mock 模型层
class MockModel(BaseModel):
    def predict(self, data: MarketData) -> ModelSignal:
        return ModelSignal(
            direction=random.choice([-1, 0, 1]),
            confidence=random.uniform(0.3, 0.9),
            strength=random.uniform(0.1, 1.0),
            model_name="mock"
        )

# Mock 策略层
class MockStrategy(BaseStrategy):
    def generate_signal(self, model_outputs: List[ModelSignal]) -> Order:
        return Order(
            strategy_id="mock",
            symbol="BTCUSDT",
            direction=1,
            quantity=0.1,
            stop_loss=65000,
            take_profit=70000
        )

# Mock 资金管理层 (等权重)
class EqualWeightCapitalManager(BaseCapitalManager):
    def allocate(self, orders: List[Order]) -> List[FinalOrder]:
        if not orders:
            return []
        weight = 1.0 / len(orders)
        return [FinalOrder(order=o, allocated_capital=10000, weight=weight) for o in orders]
```

### 4.4 验收标准

```
运行入口
├── electron/main.ts              → 能打印 "Kitchen Ready"
├── quant-sync-server/main.py     → 能打印 "Kitchen Ready"
└── web/                         → npm run dev 能启动

节点实现
├── 市场层: MockMarketProvider    → 能返回 MarketData
├── 模型层: MockModel             → 能返回 ModelSignal
├── 策略层: MockStrategy         → 能返回 Order
├── 资金层: EqualWeightCapital   → 能返回 FinalOrder
└── 淘汰层: MockEviction         → 能返回 EvictionLog

日志系统
└── 每个模块都使用统一 logger

配置管理
└── .env, config.py 正常工作
```

### 4.5 禁止事项 (厨房阶段)

```
❌ 实现真实算法 (RSI, MA, NLS 等) - 禁止
❌ 连接真实外部 API - 禁止
❌ 超过 10 行的业务逻辑 - 禁止
❌ 硬编码业务常量 - 禁止
```

---

## 五、厨师阶段清单 (M3-M5)

### M3: 模型层厨师 (NEMT Core)

| 任务 | 依赖厨房 | 验收标准 |
|------|----------|----------|
| 实现 NLS 方程 | ✅ 就绪 | 能处理 MarketData |
| 实现四相位检测 | ✅ 就绪 | 输出有效相位 |
| 实现谱分析 | ✅ 就绪 | 谱宽计算正常 |
| 实现信号生成 | ✅ 就绪 | 生成 ModelSignal |

### M4: 策略层厨师

| 任务 | 依赖厨房 | 验收标准 |
|------|----------|----------|
| 实现策略模板 | ✅ 就绪 | 能生成策略 |
| 实现回测引擎 | ✅ 就绪 | 能运行回测 |
| 实现评分系统 | ✅ 就绪 | 能计算评分 |
| 实现淘汰机制 | ✅ 就绪 | 能激活/淘汰 |

### M5: 资金/淘汰层厨师

| 任务 | 依赖厨房 | 验收标准 |
|------|----------|----------|
| 实现权重分配 | ✅ 就绪 | 根据相位调整 |
| 实现资金调度 | ✅ 就绪 | 控制仓位 |
| 实现风控规则 | ✅ 就绪 | ATR 止损 |
| 实现进化机制 | ✅ 就绪 | 自动淘汰/生成 |

---

## 六、详细里程碑

### M1: 厨房搭建 (v0.1-kitchen) 🏗️
```
周期: 2026-04-19 ~ 2026-04-25
目标: 让系统能空转起来

产出:
- [ ] 项目目录结构
- [ ] 所有节点基类定义
- [ ] 所有节点 Mock 实现
- [ ] Electron 能启动
- [ ] React 页面能加载
- [ ] Python API 能访问

验收标准:
- [ ] 运行 "Kitchen Ready" 消息
- [ ] 无红色错误
- [ ] 日志正常输出
- [ ] Mock 数据能流通整个链路
```

### M2: 市场层厨师 (v0.2-chef) 👨‍🍳
```
周期: 2026-04-26 ~ 2026-05-02
目标: 接入真实市场数据

产出:
- [ ] Binance 数据源
- [ ] 数据清洗/对齐
- [ ] SQLite 存储
- [ ] Redis 事件总线

验收标准:
- [ ] 能获取实时 K 线
- [ ] Mock/真实可切换
```

### M3: 模型层厨师 (v0.3-chef) 👨‍🍳
```
周期: 2026-05-03 ~ 2026-05-09
目标: 实现 NEMT 核心算法

产出:
- [ ] NLS 方程
- [ ] 四相位检测
- [ ] 谱分析
- [ ] 信号生成

验收标准:
- [ ] NEMT Core 能输出信号
- [ ] 与 Mock 层对接
```

### M4: 策略层厨师 (v0.4-chef) 👨‍🍳
```
周期: 2026-05-10 ~ 2026-05-16
目标: 实现策略系统

产出:
- [ ] 策略工厂
- [ ] 策略模板
- [ ] 回测引擎
- [ ] 评分系统

验收标准:
- [ ] 能生成策略
- [ ] 能运行回测
- [ ] 能评分排名
```

### M5: 资金/淘汰层厨师 (v0.5-chef) 👨‍🍳
```
周期: 2026-05-17 ~ 2026-05-23
目标: 实现大脑决策和进化

产出:
- [ ] 权重分配
- [ ] 资金调度
- [ ] 风控规则
- [ ] 进化机制

验收标准:
- [ ] 能自动管理策略
- [ ] 能淘汰/生成策略
```

### M6: 生产化 (v1.0) 🚀
```
周期: 2026-05-24 ~ 2026-05-31
目标: 准备生产环境

产出:
- [ ] Electron 打包
- [ ] 完整测试
- [ ] 监控告警
- [ ] 文档完善

验收标准:
- [ ] 可安装运行
- [ ] 无明显 Bug
```

---

## 七、已完成事项

| 模块 | 状态 | 完成时间 | 备注 |
|------|------|----------|------|
| NEMT 核心算法 | ✅ 已完成 | 2026-04-18 | NLS/相位/信号 |
| 四相位状态机 | ✅ 已完成 | 2026-04-18 | |
| 信号指标 | ✅ 已完成 | 2026-04-18 | DCI/Vortex/SR |
| 风险管理 | ✅ 已完成 | 2026-04-18 | ATR/杠杆/回撤 |
| 链上数据 | ✅ 已完成 | 2026-04-18 | MVRV/NUPL |
| 执行框架 | ✅ 已完成 | 2026-04-18 | Predict/Signal/Validate |
| Web 前端 | ✅ 已完成 | 2026-04-18 | 模拟器界面 |
| API 服务器 | ✅ 已完成 | 2026-04-18 | quant-sync-server |

---

## 八、相关文档

- [NEMT_Quant_OS_Electron.md](./NEMT_Quant_OS_Electron.md) - 完整架构文档
- [PRD.md](./PRD.md) - 产品需求文档
- [SPEC.md](./SPEC.md) - 技术规格说明

---

## 一句话总结

> **厨房理论 = 先让系统空转起来，再让业务跑起来。**
> **多节点 = 独立模块并行开发，各有输入/输出/验收标准。**

*文档版本: 0.3 (多节点+厨房理论版)*
*创建日期: 2026-04-19*
