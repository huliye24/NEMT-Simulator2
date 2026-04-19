# NEMT · Quant OS 设计文档

> **NEMT = Next Evolution Market Trading System**
> 一个"策略生态 + 风控大脑 + 资金调度"的量化操作系统

---

## 目录

1. [系统概述](#1-系统概述)
2. [核心理念](#2-核心理念)
3. [系统架构总览](#3-系统架构总览)
4. [Market Layer（市场层）](#4-market-layer市场层)
5. [Data Layer（数据层）](#5-data-layer数据层)
6. [Signal Layer（信号层）](#6-signal-layer信号层)
7. [Strategy Layer（策略层）](#7-strategy-layer策略层)
8. [Execution Layer（执行层）](#8-execution-layer执行层)
9. [Risk Layer（风控层）](#9-risk-layer风控层)
10. [Brain Layer（系统大脑）](#10-brain-layer系统大脑)
11. [Performance Dashboard（总控制台）](#11-performance-dashboard总控制台)
12. [Evolution Layer（进化系统）](#12-evolution-layer进化系统)
13. [系统工作流程](#13-系统工作流程)
14. [数据库结构汇总](#14-数据库结构汇总)
15. [下一步开发路线](#15-下一步开发路线)

---

## 1. 系统概述

NEMT不是一个传统意义上的量化交易工具，而是一个**自进化的金融生态系统**。它模拟自然界的生态法则，让策略在其中竞争、适应、进化，最终形成一套能够适应市场变化的智能交易系统。

### 1.1 系统定位

| 维度 | 传统量化系统 | NEMT |
|------|-------------|------|
| 核心目标 | 追求单策略最大收益 | 构建策略生存环境 |
| 市场适应 | 固定策略参数 | 动态策略生态调整 |
| 风险管理 | 预设止损规则 | 智能风险模式切换 |
| 策略管理 | 手动选择/优化 | 自动进化/淘汰 |
| 系统演化 | 被动维护 | 主动适应 |

---

## 2. 核心理念

### 2.1 三大核心原则

```
┌─────────────────────────────────────────────────────────────────┐
│                        NEMT 核心理念                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❶ 不是做策略，而是构建策略的生存环境                              │
│     → 系统关注的是"生态健康"，而非单策略表现                        │
│                                                                 │
│  ❷ 不是预测市场，而是适应市场结构变化                              │
│     → 系统实时感知市场状态，动态调整策略权重                        │
│                                                                 │
│  ❸ 不是单点收益，而是系统长期演化能力                              │
│     → 追求的是系统整体Survival Rate，而非峰值收益                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 生态类比

| 自然生态 | NEMT 系统 |
|---------|----------|
| 物种 | 策略 |
| 生态系统 | NEMT OS |
| 自然选择 | 策略淘汰 |
| 基因突变 | 新策略生成 |
| 环境变化 | 市场状态切换 |
| 生态平衡 | 资金分配优化 |

---

## 3. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NEMT QUANT OS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    🧠 Brain Layer（系统大脑）                        │   │
│  │              ⭐ 最高决策层 · 策略生死 · 资金调度 · 风险模式            │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                            │
│  ┌──────────────┐  ┌──────────┴──────┐  ┌───────────────┐  ┌────────────┐ │
│  │   🛡️ Risk    │  │   ⚙️ Strategy  │  │  📡 Signal     │  │  💰 Exec   │ │
│  │    Layer     │  │     Layer      │  │    Layer      │  │   Layer    │ │
│  │  风控层       │  │   策略层        │  │   信号层       │  │   执行层    │ │
│  └──────────────┘  └────────────────┘  └───────────────┘  └────────────┘ │
│         │                   │                    │                  │       │
│         └───────────────────┼────────────────────┼──────────────────┘       │
│                             │                    │                          │
│  ┌─────────────────────────┴────────────────────┴──────────────────────┐   │
│  │                         📊 Data Layer（数据层）                      │   │
│  │                   统一数据入口 · 历史/实时 · 多交易所                  │   │
│  └─────────────────────────────────────┬───────────────────────────────┘   │
│                                        │                                    │
│  ┌─────────────────────────────────────┴───────────────────────────────┐   │
│  │                      📡 Market Layer（市场层）                       │   │
│  │                    市场状态感知 · 品种定义 · 宏观分析                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    📈 Dashboard（可视化控制台）                        │   │
│  │              实时监控 · 性能展示 · 系统健康状态 · 告警                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  🧬 Evolution Layer（进化系统）                      │   │
│  │              策略评分 · 自动淘汰 · 新策略生成 · 参数优化               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 数据流向

```
市场数据 → Data Layer → Signal Layer → Strategy Layer
                                              ↓
                                    Brain Layer（决策）
                                              ↓
Risk Layer ← Execution Layer ← Brain Layer（执行指令）
    ↑
    └── 实时监控 + 异常告警
```

---

## 4. Market Layer（市场层）

### 4.1 层级定义

**作用**：定义系统"输入世界"，感知外部市场环境

### 4.2 市场品种配置

```
┌─────────────────────────────────────────────────────────────┐
│                    Markets（交易品种）                        │
├──────────────┬──────────────┬──────────────┬──────────────┤
│    BTC/USDT  │   ETH/USDT    │  Altcoins    │   Macro      │
│   主交易对    │   次交易对     │   币种篮子    │   宏观指数    │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### 4.3 市场状态（Market Regimes）

| 状态 | 标识 | 特征 | 系统响应 |
|------|------|------|---------|
| 趋势市场 | `TRENDING_UP` / `TRENDING_DOWN` | 单边行情 | 增加趋势策略权重 |
| 震荡市场 | `RANGING` | 区间波动 | 增加均值回归策略权重 |
| 高波动市场 | `HIGH_VOLATILITY` | 波动率飙升 | 降低整体仓位，提高风控 |
| 流动性收缩 | `LOW_LIQUIDITY` | 买卖价差扩大 | 减少交易频次 |

### 4.4 Notion 字段设计

```
Database: Markets
├── Market Name        (Text)      - 品种名称
├── Current Price      (Number)    - 当前价格
├── Volatility         (Number)    - 波动率指标
├── Trend State        (Select)    - 趋势状态
├── Liquidity Score   (Number)    - 流动性评分
├── Volume 24h         (Number)   - 24小时成交量
├── Last Update        (Date)     - 最后更新时间
└── Status             (Select)   - Active / Inactive
```

### 4.5 市场状态检测逻辑

```python
# 市场状态检测伪代码
def detect_market_regime(market_data):
    """
    根据多维度指标判断市场状态
    """
    volatility = calculate_volatility(market_data)
    trend_strength = calculate_trend_strength(market_data)
    liquidity = estimate_liquidity(market_data)
    
    if volatility > HIGH_VOL_THRESHOLD:
        return "HIGH_VOLATILITY"
    elif liquidity < LOW_LIQ_THRESHOLD:
        return "LOW_LIQUIDITY"
    elif abs(trend_strength) > TREND_THRESHOLD:
        return "TRENDING_UP" if trend_strength > 0 else "TRENDING_DOWN"
    else:
        return "RANGING"
```

---

## 5. Data Layer（数据层）

### 5.1 层级定义

**作用**：统一市场数据入口，为上层提供标准化数据服务

### 5.2 数据源架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Sources                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Binance API │  │   OKX API   │  │  CSV Files  │         │
│  │  实时数据    │  │   实时数据   │  │  历史数据    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                 │                 │                 │
│         └────────────┬────┴────────────────┘                 │
│                      ↓                                        │
│              ┌───────────────┐                               │
│              │ Data Adapter  │                               │
│              │    标准化适配    │                               │
│              └───────┬───────┘                               │
│                      ↓                                        │
│              ┌───────────────┐                               │
│              │  Data Store   │                               │
│              │  时序数据库     │                               │
│              └───────────────┘                               │
│                      ↓                                        │
│              ┌───────────────┐                               │
│              │  Data Service │                               │
│              │   数据服务层   │                               │
│              └───────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 数据类型

| 数据类型 | 描述 | 刷新频率 | 用途 |
|---------|------|---------|------|
| Price | OHLCV价格数据 | 实时 | 策略计算 |
| Volume | 成交量数据 | 实时 | 流动性判断 |
| Order Flow | 订单流数据 | 实时 | 微观结构分析 |
| Funding Rate | 资金费率 | 每8小时 | 合约市场分析 |
| Open Interest | 未平仓合约 | 实时 | 市场情绪判断 |

### 5.4 Notion 字段设计

```
Database: Market Data
├── Timestamp       (Date)        - 数据时间戳
├── Market          (Relation)    - 关联市场
├── Open Price      (Number)      - 开盘价
├── High Price      (Number)      - 最高价
├── Low Price       (Number)      - 最低价
├── Close Price     (Number)      - 收盘价
├── Volume          (Number)      - 成交量
├── Source          (Select)      - 数据源
├── Data Quality    (Select)      - 数据质量标记
└── Created At      (Date)        - 创建时间
```

### 5.5 数据质量控制

```python
class DataQualityController:
    """数据质量控制器"""
    
    def validate(self, data_point):
        """
        验证数据点质量
        """
        checks = [
            self.check_price_range(data_point),      # 价格范围检查
            self.check_volume_positive(data_point),  # 成交量非负
            self.check_timestamp_monotonic(),         # 时间戳递增
            self.check_missing_values(),             # 缺失值检查
            self.check_outliers(),                   # 异常值检测
        ]
        return all(checks)
    
    def handle_anomaly(self, data_point):
        """
        异常数据处理策略
        """
        # 1. 标记异常
        # 2. 使用前值填充或插值
        # 3. 记录日志
        # 4. 触发告警（如有必要）
        pass
```

---

## 6. Signal Layer（信号层）

### 6.1 层级定义

**作用**：把市场数据转化为"可交易信号"，提供决策原材料

### 6.2 信号类型体系

```
┌─────────────────────────────────────────────────────────────┐
│                      Signal Types                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📈 Trend Signal（趋势信号）                                  │
│     ├── 移动平均交叉 (MA Cross)                               │
│     ├── MACD 背离                                            │
│     ├── ADX 趋势强度                                          │
│     └── 布林带突破                                            │
│                                                              │
│  🔄 Mean Reversion Signal（均值回归信号）                      │
│     ├── RSI 超买超卖                                          │
│     ├── 布林带收口                                            │
│     ├── 价格偏离均线                                           │
│     └── Keltner 通道                                         │
│                                                              │
│  📊 Volatility Signal（波动率信号）                           │
│     ├── ATR 波动率                                            │
│     ├── 波动率突破                                            │
│     └── VIX 相关性                                           │
│                                                              │
│  🚀 Momentum Signal（动量信号）                               │
│     ├── RSI 动量                                             │
│     ├── Stochastic 动量                                      │
│     ├── Price ROC                                            │
│     └── Volume Momentum                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 信号质量评估

| 指标 | 描述 | 评估标准 |
|------|------|---------|
| Signal Strength | 信号强度 (0-100) | >70 为强信号 |
| Confidence | 信号置信度 | 基于历史统计 |
| Market Condition | 适用市场状态 | 需匹配当前市场 |
| Time Horizon | 持仓时间预期 | 短/中/长 |

### 6.4 Notion 字段设计

```
Database: Signals
├── Signal Name        (Text)        - 信号名称
├── Type               (Select)      - 信号类型
├── Strength           (Number)      - 信号强度 (0-100)
├── Confidence         (Number)      - 置信度 (0-1)
├── Market             (Relation)    - 关联市场
├── Market Condition   (Select)      - 适用市场状态
├── Time Horizon       (Select)      - 时间周期
├── Direction          (Select)      - 方向 Long/Short/Neutral
├── Generated At       (Date)        - 生成时间
├── Expires At         (Date)        - 过期时间
└── Status             (Select)      - Active/Expired/Used
```

### 6.5 信号生成服务

```python
class SignalGenerator:
    """信号生成服务"""
    
    def __init__(self, data_service):
        self.data_service = data_service
        self.signal_indicators = self._load_indicators()
    
    def generate_signals(self, market):
        """
        生成所有类型的交易信号
        """
        market_data = self.data_service.get_recent_data(market)
        signals = []
        
        for indicator in self.signal_indicators:
            signal = self._calculate_signal(indicator, market_data)
            if signal.strength > self.threshold:
                signals.append(signal)
        
        return self._filter_signals(signals)
    
    def _filter_signals(self, signals):
        """
        信号过滤和聚合
        """
        # 1. 去重相似信号
        # 2. 按强度排序
        # 3. 限制同时存在的信号数量
        # 4. 考虑信号相关性
        pass
```

---

## 7. Strategy Layer（策略层）⭐核心

### 7.1 层级定义

**作用**：策略生命体系统，管理策略从诞生到淘汰的完整生命周期

### 7.2 策略本质理解

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│    传统观点：策略 = 交易规则集合                                   │
│                                                                 │
│    NEMT观点：策略 = 生物体                                       │
│                                                                 │
│    ├── 有生命周期（出生 → 存活 → 淘汰）                            │
│    ├── 有适应能力（能感知环境变化）                                │
│    ├── 有竞争关系（资源有限，优胜劣汰）                            │
│    └── 有遗传特性（参数可以继承和变异）                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 策略结构

```
┌─────────────────────────────────────────────────────────────┐
│                   Strategy Card（策略卡片）                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  基础信息                                                     │
│  ├── Name: 策略名称                                           │
│  ├── Type: 策略类型 (Trend/MeanRev/Momentum/Hybrid)          │
│  ├── Version: 版本号                                          │
│  └── Description: 策略描述                                    │
│                                                              │
│  性能指标                                                     │
│  ├── Sharpe Ratio: 夏普比率                                   │
│  ├── Max Drawdown: 最大回撤                                    │
│  ├── Win Rate: 胜率                                           │
│  ├── Profit Factor: 盈亏比                                     │
│  ├── Total Trades: 交易次数                                    │
│  └── Average Holding Time: 平均持仓时间                        │
│                                                              │
│  状态信息                                                     │
│  ├── Status: 状态 (Alive/Testing/Dormant/Dead)              │
│  ├── Capital Weight: 资金权重 (0-100%)                        │
│  ├── Created At: 创建时间                                      │
│  ├── Last Trade: 最近交易时间                                   │
│  └── Performance Score: 表现评分                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 策略生命周期状态机

```
                              ┌─────────────────┐
                              │                 │
                              │    Testing      │
                              │   (测试中)       │
                              └────────┬────────┘
                                       │
                                       │ 评分 > 阈值
                                       ↓
                              ┌─────────────────┐
                              │                 │
        评分下降 ─────────────→│    Alive        │
        持续亏损              │   (运行中)       │
        权重归零 ───────────→│                 │
                              └────────┬────────┘
                                       │
                                       │ 长期表现不佳
                                       │ 评分 < 淘汰线
                                       ↓
                              ┌─────────────────┐
                              │                 │
                              │     Dead        │
                              │   (淘汰)        │
                              │                 │
                              └─────────────────┘

        ┌─────────────────┐
        │                 │
        │    Dormant      │
        │   (休眠)        │
        │                 │
        └────────┬────────┘
                 │
                 │ 市场状态匹配
                 │ 评分上升
                 ↓
```

### 7.5 策略状态说明

| 状态 | 标识 | 说明 | 资金分配 |
|------|------|------|---------|
| 🟢 Alive | `ALIVE` | 正常运行，正在交易 | 有权重 |
| 🟡 Testing | `TESTING` | 新策略，模拟盘测试 | 小比例资金 |
| 🔴 Dead | `DEAD` | 表现不佳，已淘汰 | 无权重 |
| 🔵 Dormant | `DORMANT` | 暂时休眠，条件触发后恢复 | 保留仓位信息 |

### 7.6 策略池管理原则

> **系统不是选择策略，而是"管理策略生态"**

1. **多样性原则**：保持策略类型多样性，应对不同市场
2. **优胜劣汰**：持续评估，淘汰低效策略
3. **动态平衡**：根据市场状态调整策略权重
4. **冗余设计**：同类型策略有2-3个备选，避免单点失败

### 7.7 Notion 字段设计

```
Database: Strategies
├── Name                (Text)        - 策略名称
├── Type                (Select)      - 策略类型
├── Version             (Text)        - 版本号
├── Sharpe Ratio        (Number)      - 夏普比率
├── Max Drawdown        (Number)      - 最大回撤 (%)
├── Win Rate            (Number)      - 胜率 (%)
├── Profit Factor       (Number)      - 盈亏比
├── Total Trades        (Number)      - 总交易次数
├── Avg Holding Time    (Number)      - 平均持仓时间 (小时)
├── Status              (Select)      - 状态
├── Capital Weight      (Number)      - 资金权重 (%)
├── Performance Score   (Number)      - 表现评分
├── Created At          (Date)        - 创建时间
├── Last Trade At       (Date)        - 最近交易
├── Updated At          (Date)        - 更新时间
└── Tags                (Multi-select)- 标签
```

### 7.8 策略评分系统

```python
class StrategyScorer:
    """策略评分系统"""
    
    def calculate_score(self, strategy):
        """
        综合评分计算
        """
        scores = {
            'profitability': self._calc_profitability(strategy),   # 盈利能力
            'consistency': self._calc_consistency(strategy),       # 一致性
            'risk_adjusted': self._calc_risk_adjusted(strategy),   # 风险调整收益
            'adaptability': self._calc_adaptability(strategy),     # 适应性
        }
        
        # 加权平均
        weights = {
            'profitability': 0.3,
            'consistency': 0.2,
            'risk_adjusted': 0.3,
            'adaptability': 0.2,
        }
        
        total_score = sum(s * weights[k] for k, s in scores.items())
        return min(100, max(0, total_score))
    
    def should_evict(self, strategy):
        """
        判断策略是否应该淘汰
        """
        return (
            strategy.performance_score < 30 or
            strategy.max_drawdown > 20 or
            strategy.sharpe_ratio < 0.5
        )
```

---

## 8. Execution Layer（执行层）

### 8.1 层级定义

**作用**：连接策略决策与真实交易，负责订单执行和交易监控

### 8.2 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Order Execution Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Strategy Signal                                             │
│       │                                                      │
│       ↓                                                      │
│  ┌─────────────┐                                             │
│  │ Risk Check │ ←── 风控层审核                                │
│  └──────┬──────┘                                             │
│         │ 通过                                               │
│         ↓                                                      │
│  ┌─────────────┐                                             │
│  │ Order       │ ←── 订单类型/数量计算                          │
│  │ Generator   │                                             │
│  └──────┬──────┘                                             │
│         │                                                      │
│         ↓                                                      │
│  ┌─────────────┐                                             │
│  │ Exchange    │ ←── 交易所API下单                             │
│  │ Connector   │                                             │
│  └──────┬──────┘                                             │
│         │                                                      │
│         ↓                                                      │
│  ┌─────────────┐                                             │
│  │ Slippage   │ ←── 滑点监控                                  │
│  │ Monitor    │                                             │
│  └──────┬──────┘                                             │
│         │                                                      │
│         ↓                                                      │
│  ┌─────────────┐                                             │
│  │ Trade      │ ←── 记录成交结果                              │
│  │ Recorder   │                                             │
│  └─────────────┘                                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 执行质量指标

| 指标 | 描述 | 监控阈值 |
|------|------|---------|
| Slippage | 实际成交价与预期价差 | < 0.1% |
| Latency | 信号到成交时间 | < 500ms |
| Fill Rate | 订单完成率 | > 95% |
| Reject Rate | 订单拒绝率 | < 5% |

### 8.4 Notion 字段设计

```
Database: Trades
├── Entry Time         (Date)        - 入场时间
├── Exit Time          (Date)        - 出场时间
├── Strategy           (Relation)    - 关联策略
├── Market             (Relation)    - 交易品种
├── Direction          (Select)      - 方向 Long/Short
├── Entry Price        (Number)      - 入场价格
├── Exit Price         (Number)      - 出场价格
├── Quantity           (Number)      - 数量
├── PnL                 (Number)      - 盈亏金额
├── PnL Percent         (Number)      - 盈亏比例
├── Slippage           (Number)      - 滑点
├── Status             (Select)      - 状态 Open/Closed
├── Holding Hours      (Number)      - 持仓小时数
├── Fee                (Number)      - 手续费
└── Notes              (Text)        - 备注
```

---

## 9. Risk Layer（风控层）🔥

### 9.1 层级定义

**作用**：系统最高优先级保障，保护资金安全

### 9.2 风控规则体系

```
┌─────────────────────────────────────────────────────────────┐
│                   Risk Rules Hierarchy                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  L1: 硬性止损规则（不可绕过）                                  │
│  ├── Max Drawdown Limit    最大回撤限制                       │
│  ├── Daily Loss Limit      日亏损限制                         │
│  └── Emergency Shutdown    紧急关机触发                       │
│                                                              │
│  L2: 软性风控规则（可调整）                                    │
│  ├── Strategy Exposure Cap 单策略仓位上限                     │
│  ├── Market Exposure Cap   单市场仓位上限                     │
│  └── Correlation Limit     关联性限制                         │
│                                                              │
│  L3: 预防性规则（动态调整）                                    │
│  ├── Volatility Scaler     波动率调节器                       │
│  ├── Trend Protection      趋势保护                          │
│  └── Liquidity Buffer      流动性缓冲                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9.3 风控状态机

| 状态 | 标识 | 触发条件 | 系统响应 |
|------|------|---------|---------|
| Normal | `NORMAL` | 正常运行 | 全速运行 |
| Caution | `CAUTION` | 回撤 > 5% | 降低仓位 50% |
| Defense | `DEFENSE` | 回撤 > 10% | 降低仓位 80% |
| Shutdown | `SHUTDOWN` | 回撤 > 15% | 全部平仓，停止交易 |

### 9.4 风控规则定义

```python
class RiskRules:
    """风控规则定义"""
    
    rules = {
        # 硬性规则
        'max_drawdown_limit': {
            'threshold': 15,      # 百分比
            'action': 'SHUTDOWN',  # 触发动作
            'type': 'hard',       # 不可绕过
        },
        'daily_loss_limit': {
            'threshold': 5,         # 百分比
            'action': 'DEFENSE',  # 触发动作
            'type': 'hard',
        },
        
        # 软性规则
        'strategy_exposure_cap': {
            'threshold': 20,       # 单策略最大仓位%
            'action': 'REDUCE',   # 触发动作
            'type': 'soft',
        },
        'market_exposure_cap': {
            'threshold': 30,      # 单市场最大仓位%
            'action': 'REDUCE',
            'type': 'soft',
        },
        
        # 预防性规则
        'volatility_scaler': {
            'threshold': 2.0,      # ATR倍数
            'action': 'REDUCE_POSITION',
            'type': 'preventive',
        },
    }
```

### 9.5 Notion 字段设计

```
Database: Risk Rules
├── Rule Name          (Text)        - 规则名称
├── Type               (Select)      - 规则类型
├── Threshold          (Number)      - 阈值
├── Current Value      (Number)      - 当前值
├── Action             (Select)      - 触发动作
├── Priority           (Number)      - 优先级
├── Status             (Select)      - 启用/禁用
├── Last Triggered     (Date)        - 最后触发时间
└── Notes              (Text)        - 备注
```

### 9.6 风控执行服务

```python
class RiskController:
    """风控控制器"""
    
    def check_order(self, order):
        """
        订单提交前风控检查
        """
        for rule in self.get_active_rules():
            if not self._check_rule(order, rule):
                return False, f"风控拒绝: {rule.name}"
        return True, "通过"
    
    def check_system_risk(self):
        """
        系统级风控检查
        """
        current_drawdown = self._calculate_drawdown()
        daily_loss = self._calculate_daily_loss()
        current_mode = self._determine_risk_mode(current_drawdown, daily_loss)
        
        if current_mode != self.current_mode:
            self._switch_mode(current_mode)
        
        return current_mode
```

---

## 10. Brain Layer（系统大脑）🔥核心

### 10.1 层级定义

**作用**：NEMT的"控制中心"，管理整个生态系统

> 不是执行策略，而是管理策略生态

### 10.2 大脑核心功能

```
┌─────────────────────────────────────────────────────────────┐
│                    Brain Layer Functions                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🎯 策略权重分配                                               │
│     根据市场状态和策略表现，动态调整资金在策略间的分配            │
│                                                              │
│  💰 资金调度                                                  │
│     决定开仓/平仓时机，整体仓位水平                              │
│                                                              │
│  🛡️ 风险模式切换                                              │
│     根据系统状态，自动切换风险模式                               │
│                                                              │
│  ⚰️ 策略生死判断                                               │
│     决定策略的启用/休眠/淘汰                                    │
│                                                              │
│  📊 市场状态感知                                              │
│     实时分析市场环境，为其他决策提供依据                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 10.3 决策逻辑

```python
class BrainController:
    """系统大脑控制器"""
    
    def process_market_change(self, market_data):
        """
        市场变化处理
        """
        new_state = self._analyze_market_regime(market_data)
        
        if new_state != self.current_state:
            self._handle_state_transition(new_state)
    
    def _handle_state_transition(self, new_state):
        """
        状态转换处理
        """
        # 1. 调整策略权重
        self._rebalance_strategy_weights(new_state)
        
        # 2. 更新风险模式
        self._adjust_risk_mode(new_state)
        
        # 3. 触发休眠/激活策略
        self._manage_strategy_lifecycle(new_state)
    
    def _rebalance_strategy_weights(self, market_state):
        """
        策略权重再平衡
        """
        # 根据市场状态调整权重
        weight_map = {
            'TRENDING_UP': {'trend': 0.6, 'mean_rev': 0.2, 'momentum': 0.2},
            'TRENDING_DOWN': {'trend': 0.6, 'mean_rev': 0.1, 'momentum': 0.3},
            'RANGING': {'trend': 0.2, 'mean_rev': 0.5, 'momentum': 0.3},
            'HIGH_VOLATILITY': {'trend': 0.3, 'mean_rev': 0.4, 'momentum': 0.3},
        }
        
        target_weights = weight_map.get(market_state, {})
        self._animate_weights(target_weights)  # 渐进调整
    
    def evaluate_strategy_health(self, strategy):
        """
        评估策略健康状态
        """
        score = self.scorer.calculate_score(strategy)
        
        if score < 30:
            return 'dead'
        elif score < 50:
            return 'dormant'
        else:
            return 'alive'
```

### 10.4 决策矩阵

| 市场状态 | 趋势策略权重 | 均值回归权重 | 动量策略权重 | 整体仓位 |
|---------|------------|-------------|------------|---------|
| 趋势上涨 | 60% | 20% | 20% | 100% |
| 趋势下跌 | 60% | 10% | 30% | 80% |
| 震荡 | 20% | 50% | 30% | 70% |
| 高波动 | 30% | 40% | 30% | 50% |
| 流动性收缩 | 40% | 30% | 30% | 30% |

### 10.5 Notion 字段设计

```
Database: System Brain
├── System State          (Select)      - 系统状态
├── Active Strategies     (Number)      - 活跃策略数
├── Capital Allocation     (Select)      - 资金分配模式
├── Risk Mode             (Select)      - 风险模式
├── Market Regime         (Select)      - 当前市场状态
├── Total Capital         (Number)      - 总资金
├── Available Capital     (Number)      - 可用资金
├── Today's PnL           (Number)      - 今日盈亏
├── Drawdown              (Number)      - 当前回撤
├── Last Decision         (Date)        - 最近决策时间
└── Decision Log          (Text)        - 决策日志
```

---

## 11. Performance Dashboard（总控制台）

### 11.1 页面结构

```
┌─────────────────────────────────────────────────────────────┐
│              📊 NEMT Performance Dashboard                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Total PnL     │  │  Sharpe Ratio   │  │ Max Drawdown│ │
│  │   $12,456      │  │     2.34        │  │    -8.5%    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Equity Curve                         ││
│  │     📈                                               ││
│  │   ═══════════════════════════════════════════════    ││
│  │                                                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Strategy Performance                        ││
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐                           ││
│  │  │ S1 │ │ S2 │ │ S3 │ │ S4 │                           ││
│  │  │ +5%│ │ +3%│ │ -1%│ │ +2%│                           ││
│  │  └────┘ └────┘ └────┘ └────┘                           ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  Risk Status   │  │ System Health   │                   │
│  │   🟢 Normal    │  │   🟢 Healthy    │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 11.2 核心指标定义

| 指标 | 计算方式 | 监控阈值 |
|------|---------|---------|
| Total PnL | 累计盈亏总额 | - |
| Daily PnL | 每日盈亏 | -5% 告警 |
| Sharpe Ratio | 年化收益/波动率 | > 1.5 |
| Max Drawdown | 历史最大回撤 | > 15% 关机 |
| Win Rate | 盈利交易/总交易 | > 45% |
| Strategy Survival Rate | 存活策略/总策略 | > 50% |
| Capital Efficiency | 收益/最大持仓 | 越高越好 |

---

## 12. Evolution Layer（进化系统）⭐

### 12.1 层级定义

**作用**：系统的"自然选择"机制，确保生态持续优化

> 最高级概念：系统不是被设计的，而是被"进化"的

### 12.2 进化机制

```
┌─────────────────────────────────────────────────────────────┐
│                    Evolution System                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Strategy Scoring│───→│  Automatic       │              │
│  │  策略评分         │    │  Eviction        │              │
│  │                  │    │  自动淘汰         │              │
│  └──────────────────┘    └──────────────────┘              │
│           │                                                │
│           ↓                                                │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  New Strategy   │───→│  Parameter        │              │
│  │  Generation     │    │  Optimization     │              │
│  │  新策略生成       │    │  参数自动优化     │              │
│  └──────────────────┘    └──────────────────┘              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 12.3 进化规则

| 机制 | 触发条件 | 执行动作 |
|------|---------|---------|
| 策略淘汰 | 评分 < 30 持续 N 天 | 标记 Dead，权重归零 |
| 策略激活 | 新策略测试通过 | 进入 Alive 状态 |
| 参数变异 | 策略表现下滑 | 随机调整参数 |
| 新策略生成 | 策略池多样性不足 | 基于模板生成 |

### 12.4 进化日志

```
Database: Evolution Log
├── Event             (Text)        - 事件描述
├── Impact            (Select)      - 影响程度
├── Strategy Affected (Relation)    - 关联策略
├── Result            (Text)        - 执行结果
├── Timestamp         (Date)        - 时间戳
└── Before/After      (Text)       - 前后对比
```

---

## 13. 系统工作流程

### 13.1 完整交易流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEMT Trading Loop                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                         1. MARKET SENSE                                 ║  │
│  ║  • 获取市场数据                                                          ║  │
│  ║  • 检测市场状态（趋势/震荡/高波动）                                        ║  │
│  ║  • 更新流动性指标                                                         ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                    │                                         │
│                                    ↓                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                         2. SIGNAL GENERATE                              ║  │
│  ║  • 计算各类技术指标                                                        ║  │
│  ║  • 生成交易信号                                                           ║  │
│  ║  • 评估信号强度和置信度                                                    ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                    │                                         │
│                                    ↓                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                         3. BRAIN DECIDE                                 ║  │
│  ║  • 策略权重分配                                                           ║  │
│  ║  • 资金调度决策                                                           ║  │
│  ║  • 风险模式确认                                                           ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                    │                                         │
│                                    ↓                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                         4. RISK CHECK                                   ║  │
│  ║  • 风控规则检查                                                           ║  │
│  ║  • 仓位计算验证                                                           ║  │
│  ║  • 拒绝/通过决策                                                          ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                    │                                         │
│                                    ↓                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                         5. EXECUTE                                      ║  │
│  ║  • 生成订单                                                             ║  │
│  ║  • 交易所执行                                                           ║  │
│  ║  • 滑点监控                                                             ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                    │                                         │
│                                    ↓                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                         6. MONITOR & EVOLVE                            ║  │
│  ║  • 记录交易结果                                                           ║  │
│  ║  • 更新策略评分                                                           ║  │
│  ║  • 检查进化条件                                                           ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.2 主循环伪代码

```python
class NEMTEngine:
    """NEMT 交易引擎"""
    
    def __init__(self):
        self.market_layer = MarketLayer()
        self.data_layer = DataLayer()
        self.signal_layer = SignalLayer()
        self.strategy_layer = StrategyLayer()
        self.execution_layer = ExecutionLayer()
        self.risk_layer = RiskLayer()
        self.brain_layer = BrainLayer()
        self.evolution_layer = EvolutionLayer()
    
    def run_loop(self):
        """主循环"""
        while self.is_running:
            try:
                # 1. 市场感知
                market_data = self.market_layer.get_data()
                market_state = self.market_layer.detect_regime(market_data)
                
                # 2. 信号生成
                signals = self.signal_layer.generate(market_data)
                
                # 3. 大脑决策
                decisions = self.brain_layer.decide(
                    signals=signals,
                    market_state=market_state,
                    strategy_pool=self.strategy_layer.get_active()
                )
                
                # 4. 风控检查
                for decision in decisions:
                    approved, reason = self.risk_layer.check(decision)
                    if approved:
                        self.execution_layer.execute(decision)
                
                # 5. 监控与进化
                self.evolution_layer.check_and_evolve()
                self._update_dashboard()
                
            except Exception as e:
                self._handle_error(e)
            
            sleep(self.loop_interval)
```

---

## 14. 数据库结构汇总

### 14.1 数据库清单

| 数据库 | 所属层 | 主要字段数 | 说明 |
|-------|-------|-----------|------|
| Markets | Market Layer | 8 | 交易品种配置 |
| Market Data | Data Layer | 10 | 历史行情数据 |
| Signals | Signal Layer | 11 | 交易信号 |
| Strategies | Strategy Layer | 17 | 策略卡片 |
| Trades | Execution Layer | 15 | 交易记录 |
| Risk Rules | Risk Layer | 9 | 风控规则 |
| System Brain | Brain Layer | 11 | 系统状态 |
| Evolution Log | Evolution Layer | 6 | 进化日志 |

---

## 15. 下一步开发路线

### 15.1 阶段一：基础框架搭建

```
目标：搭建最小可用系统
├── 项目结构初始化
├── 配置文件管理
├── 日志系统
├── 市场数据获取
└── 基础数据存储
```

### 15.2 阶段二：核心逻辑实现

```
目标：实现核心交易逻辑
├── 信号生成器
├── 策略框架
├── 风控规则引擎
├── 执行层对接
└── 模拟交易测试
```

### 15.3 阶段三：智能决策系统

```
目标：实现大脑层
├── 市场状态检测
├── 策略权重调整
├── 资金调度逻辑
└── 策略生命周期管理
```

### 15.4 阶段四：进化系统

```
目标：实现自动进化
├── 策略评分系统
├── 自动淘汰机制
├── 新策略生成
└── 参数优化
```

### 15.5 阶段五：实盘对接与优化

```
目标：生产环境部署
├── 交易所API对接
├── 实时监控告警
├── 性能优化
└── Notion 数据同步
```

---

## 一句话总结

> **NEMT不是量化工具，而是一个"让策略在其中生存、竞争、进化的金融生态系统"。**

---

## 附录

---

## 附录A：技术栈建议

| 组件 | 推荐技术 |
|------|---------|
| 后端 | Python 3.10+ |
| 数据存储 | SQLite + InfluxDB |
| 实时数据 | WebSocket |
| API框架 | FastAPI |
| 任务调度 | APScheduler |
| Notion同步 | Notion API |
| 前端控制台 | React + TailwindCSS |

---

## 附录B：轻量化MVP技术栈（优先实现）

> 以下是快速上线版本的技术选型，参考 Notion PRD 文档

| 用途 | 技术 | 理由 |
|------|------|------|
| 语言 | Python 3.10+ | 生态丰富，快速原型 |
| 数据处理 | pandas, numpy | 标准量化基础 |
| 回测引擎 | 自建事件驱动循环 | 轻量，完全可控 |
| 信号计算 | ta (技术指标库) 或 自实现 | 减少依赖 |
| 可视化 | matplotlib, seaborn | 离线报表 |
| 配置管理 | pyyaml 或 dataclasses | 便于调参 |
| 日志 | 标准 logging | 调试与追踪 |
| 测试 | pytest | 确保模块正确性 |
| 项目结构 | 扁平 + 模块化 | 适合单开发者快速修改 |

**不采用**：数据库、Docker、Web 框架、消息队列、机器学习框架（除非必要）。

---

## 附录C：MVP项目目录结构

```
nemt_os/
├── data/                      # 原始数据存放
│   └── BTCUSDT-1h.csv
├── nemt/
│   ├── __init__.py
│   ├── market.py              # 市场层：加载数据，分割 train/test
│   ├── data_layer.py          # 数据层：提供 OHLCV 接口
│   ├── signal_layer.py        # 信号层：计算趋势/波动率/反转信号
│   ├── strategy.py             # 策略基类 + 内置策略
│   ├── execution.py           # 执行层：模拟订单，记录交易
│   ├── risk.py                # 风控层：检查规则
│   ├── brain.py               # 大脑层：权重分配
│   ├── dashboard.py           # 总控制台：绘图，打印指标
│   ├── evolution.py            # 进化层：策略评分，淘汰机制
│   └── backtest.py            # 主回测引擎（事件循环）
├── config/
│   └── config.yaml            # 回测参数配置
├── tests/
│   ├── test_signals.py
│   ├── test_risk.py
│   └── test_strategy.py
├── output/                    # 运行结果（图表、log）
├── requirements.txt
└── README.md
```

---

## 附录D：核心接口定义

### D.1 策略基类

```python
class Strategy:
    """策略基类"""
    
    def __init__(self, name, capital_weight):
        self.name = name
        self.capital_weight = capital_weight   # 初始权重
        self.performance = []   # 记录每日收益

    def generate_signal(self, data_row) -> float:
        """返回仓位信号：-1 (全空) 到 +1 (全多)"""
        raise NotImplementedError
    
    def update_performance(self, pnl):
        """更新策略表现记录"""
        self.performance.append(pnl)
```

### D.2 大脑层接口

```python
class Brain:
    """系统大脑"""
    
    def __init__(self, strategies):
        self.strategies = strategies

    def allocate_weights(self, lookback_days=20):
        """根据近期 Sharpe 或收益率重新分配权重"""
        pass
    
    def get_combined_signal(self):
        """返回合并后的加权信号"""
        pass
```

### D.3 风控层接口

```python
class RiskManager:
    """风控管理器"""
    
    def check_order(self, proposed_position, current_pnl, daily_pnl) -> bool:
        """检查是否违反风控规则"""
        pass
    
    def get_risk_mode(self) -> str:
        """返回当前风险模式：NORMAL / CAUTION / DEFENSE / SHUTDOWN"""
        pass
```

---

## 附录E：MVP配置示例

```yaml
# config/config.yaml
data:
  path: "data/BTCUSDT-1h.csv"
  start_date: "2023-01-01"
  end_date: "2024-01-01"

backtest:
  initial_capital: 10000
  slippage_bps: 1           # 滑点 1 基点
  commission_bps: 5         # 手续费 5 基点

risk:
  max_drawdown_pct: 0.20    # 最大回撤 20%
  daily_loss_limit_pct: 0.05
  strategy_exposure_cap: 0.4

evolution:
  eval_frequency: 20        # 每 20 个 bar 评分一次
  keep_best: 3               # 保留前 3 名策略
```

---

## 附录F：开发任务清单（共18项）

> 按优先级排序，每个任务独立可验证

### P0 —— 基础框架（必须完成才能运行）

| 任务 | 描述 | 验收标准 |
|------|------|---------|
| **T1** | 创建项目目录结构 | 目录存在，`nemt/__init__.py` 可导入 |
| **T2** | 实现市场层 `market.py` | 能读取CSV数据，打印shape，按日期切片 |
| **T3** | 实现数据层 `data_layer.py` | 提供 `get_current_bar()` 和 `get_history()` |
| **T4** | 实现配置加载（yaml + dataclass） | 从 config.yaml 读取参数 |

### P1 —— 策略与信号核心

| 任务 | 描述 | 验收标准 |
|------|------|---------|
| **T5** | 实现信号层 `signal_layer.py` | 计算 RSI、ATR、均线差，输出 0~1 信号 |
| **T6** | 定义策略基类 `Strategy` | 子类必须实现 `generate_signal()` |
| **T7** | 实现三个具体策略 | 趋势/均值回归/动量，可独立输出 -1~1 |
| **T8** | 实现执行层 `execution.py` | 模拟订单，记录滑点、手续费 |

### P2 —— 回测引擎与风控

| 任务 | 描述 | 验收标准 |
|------|------|---------|
| **T9** | 实现基础回测引擎 `backtest.py` | 遍历所有 bar，累计 PnL |
| **T10** | 实现风控层 `risk.py` | 最大回撤/日亏损/单策略暴露检查 |
| **T11** | 将风控集成到回测引擎 | 违规订单被拒绝并记录日志 |
| **T12** | 实现大脑层 `brain.py` | 动态权重分配（等权 + Sharpe加权） |

### P3 —— 进化与可视化

| 任务 | 描述 | 验收标准 |
|------|------|---------|
| **T13** | 实现进化层 `evolution.py` | 策略评分，淘汰最差策略 |
| **T14** | 集成进化机制到主循环 | 运行后至少有一个策略被休眠 |
| **T15** | 实现控制台 `dashboard.py` | 输出总 PnL、Sharpe、最大回撤、存活率 |
| **T16** | 绘制 Equity Curve | 生成 `output/equity.png` |

### P4 —— 完善与测试

| 任务 | 描述 | 验收标准 |
|------|------|---------|
| **T17** | 添加单元测试 | `pytest` 全部通过 |
| **T18** | 编写 README.md | 新机器可按说明成功运行 |

---

## 附录G：轻量化MVP功能清单

> 对应 PRD 文档的核心功能

| 模块 | 功能 | 说明 |
|------|------|------|
| 市场层 | 加载 BTC/USDT 历史数据（1h 级别） | 支持 CSV 或本地 Parquet |
| 数据层 | 提供 OHLCV、成交量、资金费率接口 | 统一 DataFrame 格式 |
| 信号层 | 计算趋势、波动率、均值回归信号 | 输出标准化信号 (0~1 或 -1/1) |
| 策略层 | 管理至少 3 个示例策略 | 每个策略可独立运行，输出仓位信号 |
| 执行层 | 模拟订单执行（无滑点/固定滑点） | 记录每笔交易的 PnL、滑点 |
| 风控层 | 全局最大回撤、日亏损上限、单策略暴露上限 | 触发后强制平仓或策略降权 |
| 大脑层 | 动态分配策略权重 | 根据近期 Sharpe 或收益调整 |
| 控制台 | 生成总 PnL 曲线、策略表现表、风险指标 | Matplotlib + 控制台输出 |
| 进化层 | 策略评分 + 淘汰最差策略 | 每 N 个交易周期触发一次 |

---

## 附录H：数据流说明

```
┌─────────────────────────────────────────────────────────────┐
│                    NEMT 事件驱动回测流程                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. market.py 加载 CSV → pandas DataFrame                  │
│                                                              │
│  2. 主循环按时间步（bar by bar）前进                         │
│                                                              │
│  3. 每个 bar 执行：                                          │
│     ├── 更新数据层                                           │
│     ├── 信号层计算当前指标                                    │
│     ├── 每个策略生成信号                                      │
│     ├── 大脑层合并信号（按权重）                               │
│     ├── 执行层模拟下单                                        │
│     ├── 风控层校验，拒绝则取消                                 │
│     ├── 更新 PnL，记录交易                                   │
│     └── 每 N 步触发进化（策略评分/淘汰）                       │
│                                                              │
│  4. 结束 → dashboard.py 输出结果                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 附录I：用户场景

| 用户 | 场景 | NEMT如何帮助 |
|------|------|-------------|
| 独立量化开发者 | 快速验证多个策略组合效果 | 运行即得系统整体风险收益 |
| 策略研究员 | 插入自己的新策略 | 只需实现 `generate_signal()` 接口 |
| 风控敏感用户 | 观察风控规则保护效果 | 回测极端行情，观察风控触发 |

---

## 附录J：非功能性需求

| 要求 | 指标 |
|------|------|
| 轻量 | 纯 Python，依赖 pandas/numpy/matplotlib，无数据库或消息队列 |
| 快速迭代 | 单次完整回测（1 年数据，3 策略）≤ 10 秒 |
| 可扩展 | 新策略只需实现 `generate_signal(data)` 接口 |
| 可验证 | 每次运行输出确定性结果（随机种子固定） |
| 无外部 API | 回测模式，所有数据本地化 |

---

## 附录K：V1不包含的范围

- 实盘交易接口
- 实时数据流
- Web UI 或 GUI
- 分布式/多进程
- 复杂的机器学习模型

---

## 附录L：运行方式

```bash
pip install -r requirements.txt
python -m nemt.backtest --config config/config.yaml
```

---

## 附录M：文件结构汇总（完整版）

```
nemt_quant_os/
├── config/
│   ├── __init__.py
│   ├── settings.py          # 主配置
│   ├── risk_rules.py        # 风控规则
│   └── strategy_config.py   # 策略配置
├── core/
│   ├── __init__.py
│   ├── engine.py            # 主引擎
│   ├── brain.py             # 大脑层
│   ├── risk_controller.py   # 风控层
│   └── evolution.py         # 进化层
├── data/
│   ├── __init__.py
│   ├── market_data.py       # 市场数据
│   ├── data_service.py      # 数据服务
│   └── storage.py            # 数据存储
├── signals/
│   ├── __init__.py
│   ├── signal_generator.py   # 信号生成
│   └── indicators/          # 技术指标
├── strategies/
│   ├── __init__.py
│   ├── base.py              # 策略基类
│   ├── trend_strategy.py    # 趋势策略
│   ├── mean_rev_strategy.py # 均值回归
│   └── strategy_pool.py     # 策略池
├── execution/
│   ├── __init__.py
│   ├── executor.py          # 执行器
│   ├── order.py             # 订单管理
│   └── exchanges/           # 交易所对接
├── notion/
│   ├── __init__.py
│   ├── client.py            # Notion客户端
│   └── sync.py              # 数据同步
├── dashboard/
│   ├── __init__.py
│   └── web/                 # 前端控制台
├── logs/
├── tests/
├── requirements.txt
├── README.md
└── main.py
```

---

*文档版本：1.1*
*创建日期：2026-04-18*
*最后更新：2026-04-18*
*资料来源：Notion PRD + SPEC + TASKS 文档*
