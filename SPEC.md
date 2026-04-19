# NEMT量化系统 · 技术规格说明 (SPEC)

> 版本: v0.1 | 更新: 2026-04-19 | 状态: 🚧 进行中

---

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        NEMT Quant OS - 系统架构                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌─────────────────────────────────────────────────────────────┐    │
│    │                    Web UI (React + TS)                      │    │
│    │    ┌──────────┬──────────┬──────────┬──────────┬──────────┐ │    │
│    │    │ 模拟器   │  指标    │  看板    │  理论    │  Notion │ │    │
│    │    └──────────┴──────────┴──────────┴──────────┴──────────┘ │    │
│    └─────────────────────────────────────────────────────────────┘    │
│                                    │                                   │
│                    ┌───────────────┴───────────────┐                  │
│                    │         API Layer            │                  │
│                    │   (FastAPI / HTTP Server)    │                  │
│                    └───────────────┬───────────────┘                  │
│                                    │                                   │
│    ┌────────────────────────────────┴────────────────────────────┐   │
│    │                    Node Modules (Python)                       │   │
│    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │   │
│    │  │ Market   │ │   NEMT   │ │  Signal  │ │   Risk   │        │   │
│    │  │  Layer   │ │   Core   │ │  Layer   │ │  Layer   │        │   │
│    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │   │
│    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │   │
│    │  │ OnChain  │ │ Strategy │ │Execution │ │  Brain   │        │   │
│    │  │  Layer   │ │  Layer   │ │  Layer   │ │  Layer   │        │   │
│    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │   │
│    └─────────────────────────────────────────────────────────────┘   │
│                                    │                                   │
│                    ┌───────────────┼───────────────┐                  │
│                    │               │               │                  │
│            ┌───────┴───────┐ ┌─────┴─────┐ ┌──────┴──────┐         │
│            │  Data Sources │ │  Notion   │ │   Go Server │         │
│            │   Binance    │ │   API     │ │  (执行器)    │         │
│            └──────────────┘ └───────────┘ └──────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Node模块定义

#### Node 1: MarketLayer (市场感知Node)

**输入**:
- K线数据 (OHLCV)
- 实时价格

**输出**:
- 市场状态分类 (趋势/震荡/高波动)
- 基础技术指标

**文件**: `data_fetcher.py`

```python
# 接口定义
class MarketLayer:
    def fetch_klines(self, symbol: str, interval: str) -> pd.DataFrame
    def get_market_state(self, data: pd.DataFrame) -> MarketState
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]
```

#### Node 2: NEMTCore (核心算法Node)

**输入**:
- 市场K线数据
- 参数配置 (alpha, beta, noise, dt, dx, steps)

**输出**:
- 频谱分析结果
- 谱宽 (spectralWidth)
- 平均频率 (meanFrequency)
- 共振峰数量

**文件**: `nemt_core.py`

```python
# 接口定义
class NEMTCore:
    def initialize_state(self, data: np.ndarray) -> State
    def evolve(self, state: State, steps: int) -> EvolutionResult
    def analyze_spectrum(self, state: State) -> SpectrumAnalysis
    def detect_resonance(self, spectrum: SpectrumAnalysis) -> List[Peak]
```

#### Node 3: SignalLayer (信号生成Node)

**输入**:
- NEMT分析结果
- 市场K线数据

**输出**:
- DCI (方向一致性指数)
- 涡旋信号 (4条件)
- 随机共振信号 (3条件)
- 综合信号评分

**文件**: `nemt_signals.py`

```python
# 接口定义
class SignalLayer:
    def calculate_dci(self, prices: np.ndarray) -> float
    def detect_vortex(self, nemt_result: SpectrumAnalysis, prices: np.ndarray) -> VortexSignal
    def detect_stochastic_resonance(self, signal: VortexSignal) -> ResonanceSignal
    def generate_signal(self, nemt_result: SpectrumAnalysis, market_data: pd.DataFrame) -> TradingSignal
```

#### Node 4: RiskLayer (风险管理Node)

**输入**:
- 交易信号
- 当前市场相位
- 账户状态

**输出**:
- 仓位建议
- 止损价格
- 杠杆倍数
- 风险评分

**文件**: `nemt_risk.py`

```python
# 接口定义
class RiskLayer:
    def calculate_position_size(self, signal: TradingSignal, phase: MarketPhase) -> float
    def calculate_stop_loss(self, entry_price: float, signal: TradingSignal, phase: MarketPhase) -> float
    def calculate_take_profit(self, entry_price: float, signal: TradingSignal) -> float
    def calculate_leverage(self, phase: MarketPhase) -> int
    def check_drawdown(self, account: Account) -> DrawdownLevel
```

#### Node 5: OnChainLayer (链上数据Node)

**输入**:
- 交易所地址余额
- 历史UTXO数据

**输出**:
- MVRV比率
- MVRV Z-Score
- NUPL比率
- 交易所余额趋势
- 链上健康评分 (0-10)

**文件**: `nemt_onchain.py`

```python
# 接口定义
class OnChainLayer:
    def calculate_mvrv(self, market_cap: float, realized_cap: float) -> MVRVResult
    def calculate_nupl(self, supply: float, unrealized_pnl: float) -> NUPLResult
    def analyze_exchange_flow(self, balances: List[float]) -> ExchangeFlowAnalysis
    def get_health_score(self) -> int  # 0-10
```

#### Node 6: PhaseStateMachine (相位状态机Node)

**输入**:
- NEMT分析结果
- DCI指标
- 谱宽数据

**输出**:
- 当前相位 (A/B/C/D)
- 相位置信度
- 相位转换信号

**文件**: `nemt_state_machine.py`

```python
# 接口定义
class PhaseStateMachine:
    def identify_phase(self, nemt_result: SpectrumAnalysis, dci: float) -> MarketPhase
    def get_phase_confidence(self, phase: MarketPhase) -> float  # 0-1
    def on_phase_change(self, old_phase: MarketPhase, new_phase: MarketPhase) -> PhaseChangeEvent
    def get_phase_stats(self) -> PhaseStats
```

#### Node 7: ExecutionLayer (执行层Node)

**输入**:
- 交易信号
- 风控决策
- 验证清单

**输出**:
- 订单请求
- 执行结果
- 持仓更新

**文件**: `nemt_execution.py`

```python
# 接口定义
class ExecutionLayer:
    def predict(self, signal: TradingSignal) -> Prediction
    def generate_entry_signal(self, prediction: Prediction) -> EntrySignal
    def validate_entry(self, signal: EntrySignal, phase: MarketPhase) -> ValidationResult
    def add_position(self, signal: EntrySignal, validation: ValidationResult) -> Position
    def manage_exits(self, position: Position) -> ExitDecision
```

#### Node 8: BrainLayer (大脑Node) ⚠️ 待实现

**输入**:
- 所有Layer的输出
- 账户状态
- 策略表现

**输出**:
- 策略权重分配
- 资金调度决策
- 风险模式切换
- 策略生死判断

**状态**: 🔄 规划中

---

## 2. 数据模型

### 2.1 核心数据结构

```typescript
// NEMT参数配置
interface NEMTParams {
  alpha: number;      // 非线性系数 [0.01, 0.5]
  beta: number;       // 色散系数 [0.1, 2.0]
  noise: number;     // 噪声水平 [0.0, 1.0]
  dt: number;        // 时间步长 [0.001, 0.1]
  dx: number;        // 空间步长 [0.1, 2.0]
  steps: number;     // 演化步数 [100, 1000]
  n: number;         // 样本数量 [100, 10000]
  dataSource: string; // 数据源 "BTCUSDT"
  interval: string;  // K线周期 "1m"
}

// 市场相位
enum MarketPhase {
  NOISE = 'A',      // 高噪声混乱期
  VORTEX = 'B',     // 涡旋蓄力期
  RESONANCE = 'C',  // 临界爆发前夜
  TREND = 'D'       // 趋势运行期
}

// 四相位配置
const PHASE_CONFIG = {
  [MarketPhase.NOISE]: {
    name: '高噪声混乱期',
    maxPosition: 0.20,   // 20%
    singleRisk: 0.01,    // 1%
    leverage: 0,         // 无杠杆
    strategy: '持有底仓，不做短线'
  },
  [MarketPhase.VORTEX]: {
    name: '涡旋蓄力期',
    maxPosition: 0.50,   // 50%
    singleRisk: 0.02,    // 2%
    leverage: 1,         // 1x
    strategy: '识别边界，预设条件单'
  },
  [MarketPhase.RESONANCE]: {
    name: '临界爆发前夜',
    maxPosition: 0.70,   // 70%
    singleRisk: 0.03,     // 3%
    leverage: 2,          // 2x
    strategy: '提高敏感度，敢于追入'
  },
  [MarketPhase.TREND]: {
    name: '趋势运行期',
    maxPosition: 1.00,   // 100%
    singleRisk: 0.02,    // 2%
    leverage: 1,         // 1x
    strategy: '持仓为主，回调加仓'
  }
};

// 交易信号
interface TradingSignal {
  type: 'buy' | 'sell' | 'hold';
  symbol: string;
  price: number;
  confidence: number;      // 0-1
  strategy: string;
  reason: string;
  indicators: {
    dci: number;
    spectralWidth: number;
    meanFrequency: number;
    vortexScore: number;
    resonanceScore: number;
  };
  timestamp: string;
}

// 持仓
interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  stopLoss: number;
  takeProfit: number;
  leverage: number;
  phase: MarketPhase;
  openedAt: string;
}

// 回撤等级
enum DrawdownLevel {
  GREEN = 'green',    // < 5%
  YELLOW = 'yellow',  // 5-10%
  ORANGE = 'orange',  // 10-20%
  RED = 'red'        // > 20%
}
```

### 2.2 数据库Schema

```
Notion Databases:
├── StrategyDB (策略数据库)
│   ├── Name (title)
│   ├── Alpha (number)
│   ├── Beta (number)
│   ├── Noise (number)
│   ├── Phase (select: A/B/C/D)
│   ├── Enabled (checkbox)
│   └── CreatedAt (date)
│
├── BacktestDB (回测数据库)
│   ├── Name (title)
│   ├── Strategy (relation)
│   ├── WinRate (number)
│   ├── TotalPnL (number)
│   ├── MaxDrawdown (number)
│   ├── SharpeRatio (number)
│   └── ExecutionTime (number)
│
├── SignalDB (信号数据库)
│   ├── Name (title)
│   ├── Symbol (select)
│   ├── Action (select: Buy/Sell/Hold)
│   ├── Price (number)
│   ├── Confidence (number)
│   └── Reason (rich_text)
│
├── DesignSchemesDB (方案数据库) 🔄 待创建
│   ├── Name (title)
│   ├── Status (select)
│   ├── Background (rich_text)
│   ├── DesignDecisions (rich_text)
│   ├── AffectedModules (multi_select)
│   ├── AcceptanceCriteria (rich_text)
│   ├── EstimatedHours (number)
│   └── ActualHours (number)
│
└── MilestonesDB (里程碑数据库) 🔄 待创建
    ├── Name (title)
    ├── Status (select)
    ├── StartDate (date)
    ├── EndDate (date)
    ├── Progress (number)
    ├── Dependencies (relation)
    └── Notes (rich_text)
```

---

## 3. API规格

### 3.1 HTTP API (quant-sync-server)

#### 基础信息
- Base URL: `http://localhost:8080`
- 认证: Bearer Token (NOTION_TOKEN)
- 格式: JSON

#### Endpoints

##### Pipeline执行
```
POST /api/v1/pipeline/execute
Request:
{
  "action": "run_backtest" | "generate_signal" | "full_pipeline",
  "params": {
    "symbol": "BTCUSDT",
    "interval": "1m",
    "strategy_id": "optional"
  }
}
Response:
{
  "success": true,
  "data": {
    "phase": "D",
    "signals": [...],
    "positions": [...],
    "metrics": {...}
  }
}
```

##### 获取策略列表
```
GET /api/v1/strategies
Response:
{
  "strategies": [
    {
      "id": "xxx",
      "name": "DCI Momentum",
      "enabled": true,
      "phase": "D"
    }
  ]
}
```

##### 保存回测结果
```
POST /api/v1/backtest/results
Request:
{
  "strategy_id": "xxx",
  "results": {...}
}
```

##### Notion同步
```
POST /api/v1/notion/sync
Request:
{
  "action": "sync_theory" | "sync_strategies" | "sync_results",
  "target_page_id": "xxx"
}
```

### 3.2 WebSocket API (实时数据)

```
WS /ws/stream
Messages:
- { "type": "price", "data": {...} }
- { "type": "signal", "data": {...} }
- { "type": "position", "data": {...} }
- { "type": "phase_change", "data": {"old": "C", "new": "D"} }
```

---

## 4. 技术选型

### 4.1 后端技术栈

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **核心算法** | Python | 3.10+ | NEMT核心实现 |
| **数值计算** | NumPy/SciPy | - | 矩阵运算、FFT |
| **数据处理** | Pandas | - | K线数据处理 |
| **API框架** | FastAPI | 0.100+ | HTTP服务 |
| **数据可视化** | Matplotlib | - | 图表生成 |
| **Notion集成** | requests | - | Notion API调用 |

### 4.2 前端技术栈

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **框架** | React | 18+ | UI框架 |
| **语言** | TypeScript | 5+ | 类型安全 |
| **构建** | Vite | 5+ | 快速构建 |
| **样式** | CSS | - | 样式系统 |
| **图表** | 内置Canvas | - | 自定义图表 |

### 4.3 基础设施

| 组件 | 技术 | 说明 |
|------|------|------|
| **容器化** | Docker | 容器化部署 |
| **编排** | Docker Compose | 本地开发 |
| **反向代理** | Nginx | 生产环境 |
| **实时通讯** | WebSocket | 实时数据流 |

---

## 5. 项目结构

```
NEMT-Simulator/
├── nemt_core.py                 # NLS方程核心算法
├── nemt_signals.py              # 信号指标
├── nemt_onchain.py              # 链上数据
├── nemt_state_machine.py        # 四相位状态机
├── nemt_execution.py            # 执行框架
├── nemt_risk.py                 # 风险管理
├── data_fetcher.py              # 数据获取
├── visualizer.py                # 可视化
├── experiments.py               # 实验模块
├── main.py                      # 主程序入口
│
├── quant-sync-server/           # 量化同步服务器
│   ├── api_server.py           # HTTP API
│   ├── config.py               # 配置
│   ├── database.py             # 数据库
│   ├── models.py               # 数据模型
│   ├── adapters/
│   │   └── notion_adapter.py  # Notion适配器
│   └── requirements.txt
│
├── web/                        # Web前端
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/         # React组件
│   │   ├── services/           # 业务服务
│   │   ├── utils/             # 工具函数
│   │   └── types/             # TypeScript类型
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                       # 文档
│
├── PRD.md                      # 产品需求文档
├── SPEC.md                     # 技术规格说明
├── TASKS.md                    # 开发任务清单
└── README.md                   # 项目说明
```

---

## 6. 测试策略

### 6.1 测试分层

```
┌─────────────────────────────────────┐
│         E2E Tests (端到端)          │  ← 模拟完整用户流程
├─────────────────────────────────────┤
│       Integration Tests (集成)       │  ← 测试Node间协作
├─────────────────────────────────────┤
│         Unit Tests (单元)           │  ← 测试单个函数/类
└─────────────────────────────────────┘
```

### 6.2 测试覆盖目标

| 组件 | 覆盖率目标 |
|------|-----------|
| nemt_core.py | > 90% |
| nemt_signals.py | > 85% |
| nemt_state_machine.py | > 90% |
| nemt_risk.py | > 80% |
| nemt_execution.py | > 80% |
| **整体** | > 80% |

---

## 7. 性能基准

### 7.1 基准测试环境

- CPU: 8 cores
- RAM: 16GB
- Python 3.10

### 7.2 性能指标

| 操作 | 目标耗时 | 说明 |
|------|----------|------|
| NEMT演化 (1000步) | < 500ms | 核心计算 |
| 信号生成 | < 50ms | 完整信号计算 |
| 相位识别 | < 10ms | 状态判断 |
| API响应 | < 200ms | HTTP请求 |
| 页面加载 | < 2s | 首次加载 |

---

## 8. 错误处理

### 8.1 错误分类

| 错误类型 | 代码范围 | 处理方式 |
|----------|----------|----------|
| **ValidationError** | 400 | 返回详细错误信息 |
| **AuthenticationError** | 401 | 要求重新认证 |
| **NotFoundError** | 404 | 返回404及建议 |
| **RateLimitError** | 429 | 自动重试+退避 |
| **InternalError** | 500 | 记录日志+返回通用错误 |

### 8.2 日志规范

```python
# 日志格式
{
  "timestamp": "2026-04-19T12:00:00Z",
  "level": "INFO|WARN|ERROR",
  "module": "module_name",
  "message": "description",
  "context": {
    "request_id": "xxx",
    "user_id": "xxx",
    ...extra
  }
}
```

---

## 9. 安全考虑

### 9.1 数据安全

- API密钥使用环境变量存储
- 敏感数据不记录日志
- Notion Token定期轮换

### 9.2 运行时安全

- 策略执行超时保护 (30秒)
- 仓位上限检查
- 单笔亏损自动熔断

---

## 10. 附录

### 10.1 依赖版本

```
# requirements.txt
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
matplotlib>=3.7.0
requests>=2.28.0
fastapi>=0.100.0
uvicorn>=0.22.0
python-dotenv>=1.0.0
```

### 10.2 参考文档

- [PRD.md](./PRD.md) - 产品需求文档
- [TASKS.md](./TASKS.md) - 开发任务清单
- [NEMT_Quant_OS_Design.md](./NEMT_Quant_OS_Design.md) - 量化OS设计
