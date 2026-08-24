# CapsuleNode 架构文档

## 概述

CapsuleNode 是 NEMT 系统的核心架构组件，融合了：

1. **现有 Capsule 系统** - 事件驱动、五阶段迭代、健康检查
2. **Node Schema 验证** - 输入/输出验证、约束校验
3. **AI-Readable State** - 结构化状态描述

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CapsuleNode 融合架构                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            现有成熟功能 (Capsule)                             │   │
│  │  ├── ICapsule 接口                                          │   │
│  │  ├── FractalCapsule 五阶段迭代                              │   │
│  │  ├── EventBus 事件驱动                                      │   │
│  │  ├── HealthCheck 健康检查                                   │   │
│  │  └── Metrics 指标采集                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            +                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            新增功能 (Node Schema)                           │   │
│  │  ├── Schema 验证层                                         │   │
│  │  ├── PortSchema 端口模式                                   │   │
│  │  ├── ConstraintSchema 约束模式                             │   │
│  │  ├── StateValidator 状态验证                               │   │
│  │  └── AI-Readable State AI可读状态                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 核心公式

```
Capsule (事件驱动 + 五阶段迭代 + 健康检查)
    +
Node Schema (验证 + AI 可读状态)
    =
CapsuleNode (完整 AI-native 系统)
```

## 数据流

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          完整数据流                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Market  │───▶│  Signal  │───▶│   Risk   │───▶│  Brain   │───▶│Execution │  │
│  │   Node   │    │   Node   │    │   Node   │    │   Node   │    │   Node   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │              │              │              │              │              │
│       ▼              ▼              ▼              ▼              ▼              │
│    OHLCV          Signal        风险评估       最终决策        订单执行        │
│    Phase          Confidence    批准/拒绝      EXECUTE         Portfolio       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 节点说明

### MarketNode

负责市场数据处理：
- 接收原始市场数据
- 计算 OHLCV K线
- 检测市场相位
- 发布市场事件

**输入**: `raw_feed`
**输出**: `ohlcv`, `price_update`, `phase`

### SignalNode

负责信号生成：
- 接收 OHLCV 数据
- 生成交易信号
- 计算置信度
- 发布信号事件

**输入**: `ohlcv`, `market_phase`
**输出**: `signal`, `signals_summary`

### RiskNode

负责风险管理：
- 接收交易信号
- 计算风险指标
- 应用风险规则
- 输出过滤后的信号或拒绝理由

**输入**: `signal`, `portfolio`
**输出**: `risk_approved_signal`, `risk_rejection`, `risk_metrics`

### BrainNode

负责决策大脑：
- 接收信号和风险评估
- 做最终交易决策
- 协调各节点
- 维护决策历史

**输入**: `signal`, `risk_evaluation`, `market_phase`
**输出**: `decision`, `strategy_state`

### ExecutionNode

负责订单执行：
- 接收决策
- 创建和发送订单
- 跟踪订单状态
- 管理持仓

**输入**: `decision`
**输出**: `order`, `fill`, `portfolio`

## Schema 定义

每个节点都有三个 Schema：

### Input Ports

```python
INPUT_PORTS = [
    PortSchema(
        name="raw_feed",
        data_type="object",
        required=True,
        description="Raw market feed",
        properties={
            "symbol": {"type": "string"},
            "price": {"type": "number"},
            "volume": {"type": "number"},
            "timestamp": {"type": "integer"}
        },
        required_fields=["symbol", "price", "timestamp"],
    ),
]
```

### Output Ports

```python
OUTPUT_PORTS = [
    PortSchema(
        name="ohlcv",
        data_type="object",
        required=True,
        description="OHLCV bars",
        properties={
            "symbol": {"type": "string"},
            "open": {"type": "number"},
            "high": {"type": "number"},
            "low": {"type": "number"},
            "close": {"type": "number"},
            "volume": {"type": "number"}
        },
        required_fields=["symbol", "close"],
    ),
]
```

### Constraints

```python
CONSTRAINTS = [
    ConstraintSchema(
        name="max_latency_ms",
        constraint_type="runtime",
        value=1000,
        description="Maximum processing latency",
        min_value=0,
        max_value=10000,
    ),
]
```

## AI-Readable State

每个节点都导出一个 AI 可读的状态：

```python
node = MarketNode()
node.init()

# 获取 AI 可读状态
state = node.export_state()
print(state)

# 或者导出 JSON
json_str = node.export_json()
```

输出格式：

```json
{
  "node": {
    "id": "market_node",
    "name": "Market Data Node",
    "version": "1.0.0"
  },
  "state": {
    "capsule_state": "idle",
    "phase": "execution_complete"
  },
  "schemas": {
    "inputs": [...],
    "outputs": [...],
    "constraints": [...]
  },
  "metrics": {
    "exec_count": 10,
    "error_count": 0
  }
}
```

## 五阶段迭代

每个 CapsuleNode 支持五阶段迭代：

```python
class MarketNode(FractalCapsuleNode):

    def _observe_phase_impl(self) -> Dict:
        """【看】观察阶段"""
        return {
            "inputs": {...},
            "outputs": {...},
            "constraints": {...},
        }

    def _design_phase_impl(self) -> Dict:
        """【画】设计阶段"""
        return {
            "public_api": {...},
            "internal_structure": {...},
        }

    def implement_phase(self):
        """【填】实现阶段"""
        ...

    def verify_phase(self) -> Dict:
        """【验】验证阶段"""
        return {"checks": {...}}

    def integrate_phase(self):
        """【连】集成阶段"""
        ...
```

## 生命周期

```
CREATED -> INITIALIZING -> INITIALIZED -> RUNNING -> STOPPING -> STOPPED
                    │                        │
                    ▼                        ▼
                ERROR                    IDLE/PAUSED
```

## 使用示例

### 基本使用

```python
from capsules import MarketNode

# 创建节点
node = MarketNode()

# 初始化
node.init()

# 执行
outputs = node.run({
    "raw_feed": {
        "symbol": "BTCUSDT",
        "price": 50000,
        "volume": 100,
        "timestamp": 1714281600
    }
})

# 获取 AI 可读状态
print(node.export_json())

# 关闭
node.shutdown()
```

### 使用 Pipeline 管理器

```python
from tools.node_manager import PipelineNodeManager
from capsules import MarketNode, SignalNode, RiskNode, BrainNode, ExecutionNode

# 创建管理器
manager = PipelineNodeManager()

# 注册节点
manager.register(MarketNode, "market")
manager.register(SignalNode, "signal")
manager.register(RiskNode, "risk")
manager.register(BrainNode, "brain")
manager.register(ExecutionNode, "execution")

# 定义流程
manager.define_pipeline([
    ("market", "signal"),
    ("signal", "risk"),
    ("risk", "brain"),
    ("brain", "execution"),
])

# 初始化
manager.init_all()

# 执行
result = manager.execute_pipeline({
    "raw_feed": {...}
})

# 关闭
manager.shutdown_all()
```

## 文件结构

```
nemt_os/nemt/core/capsule_node/
├── __init__.py               # 导出
├── base.py                   # CapsuleNode 基类
├── capsules/
│   ├── __init__.py
│   ├── market_node.py        # 市场数据节点
│   ├── signal_node.py        # 信号节点
│   ├── risk_node.py         # 风险管理节点
│   ├── brain_node.py        # 决策大脑节点
│   └── execution_node.py    # 订单执行节点
├── schemas/
│   ├── market_node.yaml      # MarketNode Schema
│   ├── signal_node.yaml      # SignalNode Schema
│   ├── risk_node.yaml       # RiskNode Schema
│   ├── brain_node.yaml      # BrainNode Schema
│   └── execution_node.yaml  # ExecutionNode Schema
└── tools/
    ├── __init__.py
    ├── schema_generator.py   # Schema 生成器
    ├── validator_cli.py      # CLI 验证工具
    ├── state_exporter.py    # 状态导出工具
    └── node_manager.py       # 节点管理器
```

## 验证流程

```
输入数据
    │
    ▼
Schema 验证
    │
    ├─── 验证失败 ────▶ 抛出 ValueError
    │
    ▼
执行处理
    │
    ▼
Schema 验证
    │
    ├─── 验证失败 ────▶ 抛出 ValueError
    │
    ▼
返回输出
```

## 工具

### Schema 生成器

```bash
python tools/schema_generator.py
```

### CLI 验证工具

```bash
# 验证 JSON 文件
python tools/validator_cli.py validate data.json --schema schemas/market_node.yaml

# 验证 JSON 字符串
python tools/validator_cli.py validate-json '{"raw_feed": {...}}'

# 生成示例 Schema
python tools/validator_cli.py sample-schema
```

### 状态导出工具

```python
from tools.state_exporter import StateExporter

exporter = StateExporter()
exporter.save(node, "market_state.md", format="md")
```
