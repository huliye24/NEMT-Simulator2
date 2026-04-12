# NEMT Simulator 结果分类规范

## 文件夹结构

```
NEMT Simulator/
├── matlab/
│   ├── scripts/          # 分析脚本
│   └── matlab_data/      # 原始数据 (.mat)
│
├── results/              # 分析结果
│   ├── plots/            # 基础图表
│   │   ├── 01_price/         # 价格分析
│   │   ├── 02_returns/       # 收益率分析
│   │   ├── 03_volatility/    # 波动率分析
│   │   ├── 04_distribution/  # 分布检验
│   │   ├── 05_correlation/    # 相关性分析
│   │   └── 06_hurst/         # 分形分析
│   │
│   ├── figures/          # 组合图表
│   │   ├── dashboard/         # 仪表盘
│   │   ├── comparison/        # 对比分析
│   │   └── summary/           # 汇总图
│   │
│   └── reports/          # 分析报告
│       ├── daily/             # 日报
│       ├── weekly/            # 周报
│       └── monthly/           # 月报
│
└── README.md
```

## 命名规范

### 图表命名格式

```
[日期]_[数据类型]_[时间尺度]_[分析类型].png
```

**示例：**
- `20260412_BTC_1h_price_candlestick.png`
- `20260412_BTC_1h_returns_histogram.png`
- `20260412_BTC_1h_volatility_rolling.png`
- `20260412_BTC_1h_distribution_qq.png`
- `20260412_BTC_1h_correlation_acf.png`
- `20260412_BTC_1h_hurst_rs.png`

### 报告命名格式

```
[日期]_[数据类型]_[报告类型].md
```

**示例：**
- `20260412_BTC_1h_daily_report.md`
- `20260412_BTC_1h_weekly_summary.md`

---

## 分析结果分类

### 1. 价格分析 (`plots/01_price/`)

| 分析内容 | 输出图表 |
|---------|---------|
| K线图 | candlestick.png |
| 价格走势 | price_line.png |
| OHLC对比 | ohlc_comparison.png |
| 成交量 | volume_bar.png |

**脚本：** `NEMT_QuickPlot.m`

---

### 2. 收益率分析 (`plots/02_returns/`)

| 分析内容 | 输出图表 |
|---------|---------|
| 收益率直方图 | returns_histogram.png |
| 累计收益率 | cum_returns.png |
| 日收益率散点 | daily_scatter.png |
| 收益率热力图 | returns_heatmap.png |

**脚本：** `NEMT_MainAnalysis.m`

---

### 3. 波动率分析 (`plots/03_volatility/`)

| 分析内容 | 输出图表 |
|---------|---------|
| 滚动波动率 | rolling_volatility.png |
| 波动率锥 | volatility_cone.png |
| 波动率聚类 | vol_clustering.png |
| 波动率热力图 | vol_heatmap.png |
| ARCH效应 | arch_effect.png |

**脚本：** `NEMT_VolatilityClustering.m`

---

### 4. 分布检验 (`plots/04_distribution/`)

| 分析内容 | 输出图表 |
|---------|---------|
| Q-Q图 | qq_plot.png |
| 概率图 | probability_plot.png |
| 分布拟合 | distribution_fit.png |
| 尾部分析 | tail_analysis.png |

**脚本：** `NEMT_Dashboard.m`, `NEMT_MainAnalysis.m`

---

### 5. 相关性分析 (`plots/05_correlation/`)

| 分析内容 | 输出图表 |
|---------|---------|
| 自相关函数 | acf.png |
| 偏自相关 | pacf.png |
| 交叉相关 | ccf.png |
| 多尺度相关 | multi_scale_corr.png |
| 相关性热力图 | corr_heatmap.png |

**脚本：** `NEMT_MultiScaleAnalysis.m`

---

### 6. 分形分析 (`plots/06_hurst/`)

| 分析内容 | 输出图表 |
|---------|---------|
| R/S分析图 | rs_analysis.png |
| Hurst指数 | hurst_value.png |
| 半变异函数 | semivariogram.png |
| 功率谱 | power_spectrum.png |
| 多尺度波动率 | multi_scale_vol.png |

**脚本：** `NEMT_HurstAnalysis.m`

---

## 使用流程

```matlab
%% 1. 导入数据
cd E:\NEMT Simulator\matlab\scripts
load('..\matlab_data\BTC_1h.mat')

%% 2. 运行分析
NEMT_QuickPlot
NEMT_MainAnalysis
NEMT_Dashboard
NEMT_VolatilityClustering
NEMT_MultiScaleAnalysis
NEMT_HurstAnalysis

%% 3. 保存图表
% MATLAB Figure窗口 → File → Save As → 选择对应分类文件夹
```

## MATLAB自动保存脚本

```matlab
%% SaveFigure - 自动保存当前图表
function SaveFigure(category, name)
    saveDir = sprintf('..\\results\\plots\\%s', category);
    if ~exist(saveDir, 'dir'), mkdir(saveDir); end
    filename = sprintf('%s\\%s_%s.png', saveDir, datestr(now,'yyyymmdd'), name);
    saveas(gcf, filename);
    fprintf('已保存: %s\n', filename);
end

% 使用方法
% figure; plot(rand(100)); SaveFigure('01_price', 'test_plot');
```

---

## 完整分析流程

```matlab
%% 完整一键分析 (推荐)
cd E:\NEMT Simulator\matlab\scripts
load('..\matlab_data\BTC_1h.mat')
NEMT_FullAnalysis        % 运行全部分析并生成报告
```

### 或者分步运行

```matlab
%% 1. 图表分析
NEMT_QuickPlot           % K线图
NEMT_MainAnalysis        % 主分析
NEMT_Dashboard           % 仪表盘
NEMT_VolatilityClustering  % 波动率聚类
NEMT_MultiScaleAnalysis  % 多尺度相关
NEMT_HurstAnalysis       % Hurst分形

%% 2. 保存所有图表
NEMT_SaveAll

%% 3. 生成报告
report = NEMT_IntelligenceReport  % 智能诊断
NEMT_ExportReport(report)         % 导出Markdown报告
```

---

## 智能报告解读

### Hurst指数判断

| H值 | 市场特征 | 策略建议 |
|:---|:---|:---|
| H > 0.6 | 强趋势持续 | 趋势跟踪 |
| 0.5 < H < 0.6 | 弱趋势持续 | 轻仓趋势 |
| H ≈ 0.5 | 随机游走 | 观望/期权 |
| 0.4 < H < 0.5 | 弱均值回归 | 反转策略 |
| H < 0.4 | 强均值回归 | 反转策略 |

### ARCH效应判断

| ARCH值 | 含义 | 交易启示 |
|:---|:---|:---|
| > 0.4 | 强聚类 | 买入波动率 |
| 0.2 - 0.4 | 中等聚类 | 波动率突破 |
| < 0.2 | 弱聚类 | 卖出波动率 |

### 峰度判断

| 峰度 | 风险等级 | 建议 |
|:---|:---|:---|
| > 7 | 极高风险 | 尾部对冲，轻仓 |
| 5 - 7 | 高风险 | 设置严格止损 |
| 3 - 5 | 正常 | 正常操作 |
| < 3 | 低风险 | 可适当加仓 |

### 市场状态类型

| 状态 | Hurst | ARCH | 峰度 | 策略 |
|:---|:---:|:---:|:---:|:---|
| 稳定趋势 | 高 | 低 | 正常 | 趋势跟踪 |
| 高波动混沌 | 高 | 高 | 高 | 对冲+轻仓 |
| 均值回归稳定 | 低 | 低 | 正常 | 反转策略 |
| 均值回归高波动 | 低 | 高 | 高 | 反转+买vol |

---

## 科研报告结构

### 日报模板 (`reports/daily/`)

```markdown
# BTC/USDT 日报 - YYYY-MM-DD

## 1. 市场概览
- 收盘价:
- 日收益率:
- 波动率:

## 2. 统计特征
- 均值:
- 标准差:
- 偏度:
- 峰度:

## 3. 异常检测
- 异常波动次数:
- 最大回撤:

## 4. 结论
```

### 周报/月报模板 (`reports/weekly/`, `reports/monthly/`)

```markdown
# BTC/USDT [周/月]报 - YYYY-MM-DD

## 1. 摘要
## 2. 收益率分析
## 3. 波动率特征
## 4. 相关性结构
## 5. 分形特性 (Hurst指数)
## 6. 风险指标
## 7. 结论与展望
```

---

## 快速分类检查清单

- [ ] `plots/01_price/` - 价格K线图、成交量图
- [ ] `plots/02_returns/` - 收益率分布、累计收益
- [ ] `plots/03_volatility/` - 波动率聚类、热力图
- [ ] `plots/04_distribution/` - Q-Q图、分布拟合
- [ ] `plots/05_correlation/` - ACF、交叉相关
- [ ] `plots/06_hurst/` - R/S分析、Hurst指数
- [ ] `figures/dashboard/` - 综合仪表盘截图
- [ ] `reports/` - 日/周/月报文档
