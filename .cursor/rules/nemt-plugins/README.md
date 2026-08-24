# NEMT Plugins

基于 spec-kit-cn 和 pm-skills 的 NEMT 策略开发技能市场，并整合了 freqtrade 的回测引擎和交易执行框架。

## 工作流

```
/discover              发现策略机会
    ↓
/write-strategy        创建策略规范
    ↓
/plan-strategy         技术实施计划
    ↓
/backtest              历史回测
    ↓
/live-trade            实时交易
    ↓
/monitor               策略监控
```

## 目录结构

```
nemt-plugins/
├── constitution/       # NEMT 项目章程
│   └── SKILL.md
├── shared/            # 共享概念和技能
│   └── nemt-concepts.md
├── templates/        # 模板文件
│   ├── strategy-spec-template.md
│   └── strategy-plan-template.md
├── discover/          # 策略发现
│   └── SKILL.md
├── write-strategy/   # 策略规范
│   └── SKILL.md
├── plan-strategy/    # 技术计划
│   └── SKILL.md
├── backtest/         # 回测执行
│   └── SKILL.md
├── live-trade/       # 实时交易
│   └── SKILL.md
└── monitor/          # 策略监控
    └── SKILL.md
```

## 整合的外部项目

| 项目 | 来源 | 整合内容 |
|------|------|----------|
| **spec-kit-cn** | linfee/spec-kit-cn | 规范驱动开发流程 |
| **pm-skills** | phuryn/pm-skills | 产品管理技能和框架 |
| **AI-PD-Toolkit** | TechNomadCode/AI-Product-Development-Toolkit | 引导式 PRD 生成 |
| **freqtrade** | freqtrade/freqtrade | 回测引擎、策略接口、交易执行 |
| **Lean** | QuantConnect/Lean | 事件驱动算法、参数优化器 |
| **vnpy** | vnpy/vnpy | EventEngine、Gateway、MainEngine、AI因子 |
| **nautilus_AItrader** | Patrick-code-Bot/nautilus_AItrader | DeepSeek AI 分析、情绪数据、风险管理 |

## freqtrade 整合

NEMT 整合了 freqtrade 的核心代码：

### 代码模块 (`web/src/strategy/`)

```
web/src/strategy/
├── interfaces/         # 策略接口 (freqtrade IStrategy)
├── templates/         # 策略模板
├── indicators/       # 技术指标库
├── backtest/         # 回测引擎 (freqtrade backtesting.py)
├── exchange/         # 交易所适配器
├── config/          # 配置系统
└── types/           # 类型定义
```

## vnpy 整合

NEMT 整合了 vnpy 的核心架构：

### 代码模块 (`web/src/trader/`)

```
web/src/trader/
├── event/            # 事件引擎 (vnpy EventEngine)
│   └── eventEngine.ts
├── gateway/          # 交易所网关 (vnpy BaseGateway)
│   └── baseGateway.ts
├── engine/           # 核心引擎 (vnpy MainEngine)
│   ├── mainEngine.ts
│   └── logger.ts
└── alpha/            # AI 量化模块 (vnpy.alpha)
    ├── dataset/     # 因子特征工程 (Alpha158)
    ├── model/      # ML 模型 (Lasso, LightGBM, MLP)
    └── strategy/    # AI 策略
```

### vnpy 核心组件

| 组件 | 说明 |
|------|------|
| **EventEngine** | 事件驱动引擎，支持事件注册/发布 |
| **BaseGateway** | 交易所适配器基类，支持多交易所 |
| **MainEngine** | 主引擎，统一管理 Gateway、Engine、App |
| **DataEngine** | 数据引擎，缓存 Tick/Bar |
| **TradeEngine** | 交易引擎，订单管理 |
| **SignalEngine** | 信号引擎，信号处理 |
| **Alpha158** | 因子库 (Qlib 158 因子) |
| **ML Models** | ML 模型 (Linear, Ridge, RF, MLP) |

### IStrategy 接口

借鉴 freqtrade IStrategy，定义标准策略接口：

```typescript
class IStrategy {
  INTERFACE_VERSION: 3

  // 核心方法
  populateIndicators(dataframe, metadata)  // 计算指标
  populateEntryTrend(dataframe, metadata) // 入场信号
  populateExitTrend(dataframe, metadata)  // 出场信号

  // 可选方法
  customStoploss(...)    // 自定义止损
  confirmTradeEntry(...)  // 入场确认
  confirmTradeExit(...)  // 出场确认
}
```

### 技术指标

整合了完整的技术指标库 (借鉴 TA-Lib)：

- **动量指标**: RSI, MACD, Stochastic, ADX
- **趋势指标**: SMA, EMA, Bollinger Bands
- **波动率**: ATR
- **成交量**: OBV, VWAP

### 回测引擎

借鉴 freqtrade backtesting.py：

- 历史数据回测
- 订单执行模拟
- 绩效计算 (夏普、索提诺、最大回撤)
- 交易记录和报告

### AlgorithmManager (Lean-inspired)

借鉴 QuantConnect Lean QCAlgorithm：

```typescript
class QCAlgorithm {
  Initialize()                    // 初始化
  OnData(slice: Slice)          // 每个时间步事件
  OnOrderEvent(event)            // 订单事件
  OnEndOfDay(symbol?)           // 每日收盘事件
  MarketOrder(symbol, qty)       // 市价单
  LimitOrder(symbol, qty, price) // 限价单
  SetHoldings(symbol, pct)       // 设置持仓比例
  Liquidate(symbol?)            // 清仓
  History(symbol, bars)          // 历史数据
}
```

### Optimizer (Lean-inspired)

借鉴 QuantConnect Optimizer：

- GridSearchOptimizer: 网格搜索
- RandomSearchOptimizer: 随机搜索
- 约束条件 (最大回撤限制)
- 并行优化支持

## 快速开始

1. 发现新策略: `/discover [主题]`
2. 编写规范: `/write-strategy [策略描述]`
3. 制定计划: `/plan-strategy`
4. 运行回测: `/backtest`
5. 启动实战: `/live-trade`
6. 监控表现: `/monitor`

## nautilus_AItrader 整合

NEMT 整合了 nautilus_AItrader 的 AI 交易能力：

### 代码模块 (`web/src/ai/`)

```
web/src/ai/
├── client/          # AI 客户端
│   └── deepseekClient.ts    # DeepSeek AI 分析
├── sentiment/      # 情绪数据
│   └── sentimentFetcher.ts   # Fear & Greed 指数
├── strategy/       # AI 策略
│   └── aiStrategy.ts        # DeepSeek AI 交易策略
└── risk/          # 风险管理
    └── riskManager.ts        # 高级风险管理
```

### AI 交易特性

| 组件 | 说明 |
|------|------|
| **DeepSeekAnalyzer** | AI 市场分析，生成交易信号 |
| **SentimentFetcher** | 市场情绪数据 (Fear & Greed) |
| **DeepSeekAIStrategy** | 完整 AI 交易策略 |
| **RiskManager** | SL/TP、追踪止损、分批止盈、OCO |

## 参考资料

- **spec-kit-cn**: https://github.com/linfee/spec-kit-cn
- **pm-skills**: https://github.com/phuryn/pm-skills
- **AI-PD-Toolkit**: https://github.com/TechNomadCode/AI-Product-Development-Toolkit
- **freqtrade**: https://github.com/freqtrade/freqtrade
- **Lean**: https://github.com/QuantConnect/Lean
- **vnpy**: https://github.com/vnpy/vnpy
- **nautilus_AItrader**: https://github.com/Patrick-code-Bot/nautilus_AItrader
