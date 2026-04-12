# NEMT 分析工具包 - 文档索引

本文档目录帮助您快速找到所需的分析指南。

---

## 快速导航

| 需求 | 文档 |
|:---|:---|
| 我想看K线图和成交量的含义 | [01_KLINE_ANALYSIS.md](results/docs/01_KLINE_ANALYSIS.md) |
| 我想知道收益率分布怎么看 | [02_RETURNS_ANALYSIS.md](results/docs/02_RETURNS_ANALYSIS.md) |
| 我想知道什么是波动率聚类 | [03_VOLATILITY_CLUSTERING.md](results/docs/03_VOLATILITY_CLUSTERING.md) |
| 我想知道不同时间尺度怎么看 | [04_MULTI_SCALE_ANALYSIS.md](results/docs/04_MULTI_SCALE_ANALYSIS.md) |
| 我想理解Hurst指数是什么 | [05_HURST_ANALYSIS.md](results/docs/05_HURST_ANALYSIS.md) |
| 我想知道怎么解读分析报告 | [06_INTELLIGENCE_REPORT.md](results/docs/06_INTELLIGENCE_REPORT.md) |

---

## 按学习路径

### 入门路径 (新手推荐)

```
第一步 → [01_KLINE_ANALYSIS.md]
         K线图基础，这是最直观的分析

第二步 → [02_RETURNS_ANALYSIS.md]
         理解收益率和波动率的概念

第三步 → [06_INTELLIGENCE_REPORT.md]
         学会看综合分析报告
```

### 进阶路径 (深度分析)

```
第一步 → [03_VOLATILITY_CLUSTERING.md]
         理解波动率聚类，ARCH效应

第二步 → [04_MULTI_SCALE_ANALYSIS.md]
         理解多尺度相关性的意义

第三步 → [05_HURST_ANALYSIS.md]
         理解Hurst指数和分形市场理论
```

---

## 按指标类型

### 价格类指标

- [K线图](../results/docs/01_KLINE_ANALYSIS.md) - 移动平均线、成交量

### 收益类指标

- [收益率分析](../results/docs/02_RETURNS_ANALYSIS.md) - 偏度、峰度、直方图
- [Q-Q图](../results/docs/02_RETURNS_ANALYSIS.md) - 分布检验

### 波动率指标

- [波动率聚类](../results/docs/03_VOLATILITY_CLUSTERING.md) - ARCH效应、热力图
- [多尺度相关](../results/docs/04_MULTI_SCALE_ANALYSIS.md) - 滚动相关、尺度分解
- [Hurst分析](../results/docs/05_HURST_ANALYSIS.md) - R/S分析、DFA

### 综合指标

- [智能报告](../results/docs/06_INTELLIGENCE_REPORT.md) - 市场状态诊断、VaR

---

## 按问题类型

### "图表怎么看？"

| 问题 | 答案文档 |
|:---|:---|
| 均线多头/空头排列是什么？ | [01_KLINE_ANALYSIS.md - 均线系统](../results/docs/01_KLINE_ANALYSIS.md#图1-价格走势图) |
| 成交量红绿柱代表什么？ | [01_KLINE_ANALYSIS.md - 成交量](../results/docs/01_KLINE_ANALYSIS.md#图2-成交量柱状图) |
| 直方图里的分布形状说明什么？ | [02_RETURNS_ANALYSIS.md - 收益率分布](../results/docs/02_RETURNS_ANALYSIS.md#21-收益率分布直方图) |
| 热力图上的深色区域是什么意思？ | [03_VOLATILITY_CLUSTERING.md - 热力图](../results/docs/03_VOLATILITY_CLUSTERING.md#13-波动率热力图) |
| R/S图上的斜率代表什么？ | [05_HURST_ANALYSIS.md - R/S分析](../results/docs/05_HURST_ANALYSIS.md#图1-rs分析图) |

### "数据怎么算的？"

| 问题 | 答案文档 |
|:---|:---|
| 移动平均线怎么计算？ | [01_KLINE_ANALYSIS.md - 公式](../results/docs/01_KLINE_ANALYSIS.md#四指标计算公式) |
| 收益率怎么计算？ | [02_RETURNS_ANALYSIS.md - 统计量](../results/docs/02_RETURNS_ANALYSIS.md#二关键指标解读) |
| ARCH效应怎么衡量？ | [03_VOLATILITY_CLUSTERING.md - ARCH系数](../results/docs/03_VOLATILITY_CLUSTERING.md#三核心指标解读) |
| Hurst指数怎么计算？ | [05_HURST_ANALYSIS.md - 定义](../results/docs/05_HURST_ANALYSIS.md#一核心概念hurst指数是什么) |

### "市场现在什么状态？"

| 问题 | 答案文档 |
|:---|:---|
| 市场是趋势还是震荡？ | [05_HURST_ANALYSIS.md - 典型市场模式](../results/docs/05_HURST_ANALYSIS.md#三典型市场模式) |
| 现在波动率高还是低？ | [02_RETURNS_ANALYSIS.md - 波动率阶段](../results/docs/02_RETURNS_ANALYSIS.md#四实战应用) |
| 风险有多高？ | [06_INTELLIGENCE_REPORT.md - 风险评估](../results/docs/06_INTELLIGENCE_REPORT.md#5-风险评估) |
| 极端事件会不会频繁发生？ | [02_RETURNS_ANALYSIS.md - 峰度](../results/docs/02_RETURNS_ANALYSIS.md#三市场状态判断) |

### "我应该怎么操作？"

| 策略类型 | 答案文档 |
|:---|:---|
| 趋势跟踪怎么做？ | [05_HURST_ANALYSIS.md - 策略对照表](../results/docs/05_HURST_ANALYSIS.md#四hurst指数实战应用) |
| 均值回归策略怎么做？ | [05_HURST_ANALYSIS.md - 反转策略](../results/docs/05_HURST_ANALYSIS.md#四hurst指数实战应用) |
| 波动率交易怎么做？ | [03_VOLATILITY_CLUSTERING.md - 实战应用](../results/docs/03_VOLATILITY_CLUSTERING.md#五实战应用) |
| 多尺度怎么配合？ | [04_MULTI_SCALE_ANALYSIS.md - 实战应用](../results/docs/04_MULTI_SCALE_ANALYSIS.md#四相关性分析实战) |

---

## 指标速查表

### Hurst指数判断

```
H > 0.6     → 强趋势市场 → 趋势跟踪策略
0.5 < H < 0.6  → 弱趋势 → 轻仓趋势
H ≈ 0.5     → 随机游走 → 观望
0.4 < H < 0.5  → 弱回归 → 反转策略
H < 0.4     → 强回归 → 强反转
```

### ARCH效应判断

```
ARCH > 0.4  → 强聚类 → 买入波动率
0.2 < ARCH < 0.4  → 中等聚类 → 中性策略
ARCH < 0.2  → 弱聚类 → 卖出波动率
```

### 峰度判断

```
kurt < 3    → 薄尾 → 极端事件少
3 < kurt < 5  → 正常 → 正态分布
5 < kurt < 7  → 厚尾 → 警惕
kurt > 7    → 极厚尾 → 极度危险
```

### 偏度判断

```
skew < -0.5  → 强烈左偏 → 下跌风险大
-0.5 < skew < -0.2  → 轻度左偏 → 略偏风险
-0.2 < skew < 0.2  → 基本对称 → 平衡
0.2 < skew < 0.5  → 轻度右偏 → 略偏机会
skew > 0.5   → 强烈右偏 → 上涨潜力大
```

### 市场状态分类

| 组合 | 市场类型 | 策略 |
|:---|:---|:---|
| H高 + ARCH高 + kurt高 | 混沌市场 | 对冲+轻仓 |
| H高 + ARCH低 | 稳定趋势 | 趋势跟踪 |
| H低 + ARCH高 | 波动市场 | 反转+买期权 |
| H低 + ARCH低 | 震荡市场 | 区间操作 |

---

## 典型案例解读

### 案例1: 牛市行情
```
Hurst: 0.67  (趋势)
ARCH:  0.38  (聚类)
峰度:  5.8   (厚尾)

→ 趋势动量市场
→ 趋势跟踪策略
→ 但要注意厚尾风险
```

### 案例2: 熊市行情
```
Hurst: 0.43  (回归)
ARCH:  0.55  (强聚类)
峰度:  8.2   (极厚尾)
偏度:  -0.72 (左偏)

→ 均值回归+高波动
→ 反弹做空，快进快出
→ 用期权对冲尾部风险
```

### 案例3: 横盘震荡
```
Hurst: 0.52  (随机)
ARCH:  0.15  (弱聚类)
峰度:  3.8   (正常)
偏度:  -0.05 (对称)

→ 随机游走
→ 区间操作或观望
→ 可卖期权赚时间价值
```

---

## 继续阅读

- [matlab/README.md](../matlab/README.md) - 工具包使用说明
- [results/RESULTS_CLASSIFICATION.md](../results/RESULTS_CLASSIFICATION.md) - 指标分类与阈值
