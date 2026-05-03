# NEMT 分析结果目录

本目录包含分析输出的所有图表和报告。

---

## 目录结构

```
results/
├── docs/           # 分析文档指南
│   ├── README.md   # 文档索引
│   ├── 01_KLINE_ANALYSIS.md
│   ├── 02_RETURNS_ANALYSIS.md
│   ├── 03_VOLATILITY_CLUSTERING.md
│   ├── 04_MULTI_SCALE_ANALYSIS.md
│   ├── 05_HURST_ANALYSIS.md
│   └── 06_INTELLIGENCE_REPORT.md
├── plots/          # 图表输出
└── reports/        # 报告输出
```

---

## plots/ - 图表输出

运行分析脚本后，图表会自动保存到对应子文件夹：

| 子文件夹 | 内容 |
|:---|:---|
| `01_kline/` | K线图和成交量图 |
| `02_returns/` | 收益率分析图 |
| `03_dashboard/` | 综合仪表盘 |
| `04_volatility/` | 波动率聚类图 |
| `05_multiscale/` | 多尺度分析图 |
| `06_hurst/` | Hurst分析图 |

### 命名规则

```
{日期}_{脚本名}.png
例如: 20260412_NEMT_QuickPlot.png
```

---

## reports/ - 报告输出

Markdown格式的分析报告会自动保存到此目录：

| 文件 | 内容 |
|:---|:---|
| `{日期}_{时间}_analysis_report.md` | 综合分析报告 |

### 报告内容

报告包含：
1. 执行摘要表格
2. 收益率统计特征
3. 市场状态解读
4. 风险评估
5. 分布特征分析
6. 策略建议
7. 综合结论
8. 指标说明

---

## docs/ - 分析文档

详细的图表解读和指标说明文档：

### 图表解读

| 文档 | 对应图表 |
|:---|:---|
| `01_KLINE_ANALYSIS.md` | K线图、成交量、移动平均线 |
| `02_RETURNS_ANALYSIS.md` | 收益率分布、Q-Q图、累计收益率、滚动波动率 |
| `03_VOLATILITY_CLUSTERING.md` | 波动率热力图、ARCH自相关 |
| `04_MULTI_SCALE_ANALYSIS.md` | 多尺度相关矩阵、相关性衰减曲线 |
| `05_HURST_ANALYSIS.md` | R/S分析图、DFA分析图 |
| `06_INTELLIGENCE_REPORT.md` | 综合诊断报告 |

---

## 快速开始

### 1. 查看文档
```bash
# 打开文档索引
results/docs/README.md
```

### 2. 查看图表
```bash
# 图表保存在:
results/plots/01_kline/
results/plots/03_dashboard/
# 等
```

### 3. 查看报告
```bash
# 最新报告在:
results/reports/
```

---

## 分析流程

```
┌─────────────────────────────────────────────┐
│              运行分析脚本                    │
├─────────────────────────────────────────────┤
│                                             │
│  NEMT_QuickPlot       →  plots/01_kline/   │
│  NEMT_MainAnalysis    →  plots/02_returns/ │
│  NEMT_Dashboard       →  plots/03_dashboard/│
│  NEMT_Volatility...   →  plots/04_volatility/│
│  NEMT_MultiScale...   →  plots/05_multiscale/│
│  NEMT_HurstAnalysis   →  plots/06_hurst/   │
│                                             │
│  NEMT_FullAnalysis    →  运行全部分析      │
│                                             │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              生成报告                       │
├─────────────────────────────────────────────┤
│                                             │
│  NEMT_IntelligenceReport  →  命令行输出    │
│  NEMT_ExportReport        →  reports/     │
│                                             │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              查看文档                       │
├─────────────────────────────────────────────┤
│                                             │
│  docs/ 目录中包含完整的图表解读说明        │
│                                             │
│  先看文档 → 理解图表 → 得出结论           │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 继续学习

- [docs/README.md](docs/README.md) - 文档索引和快速导航
- [docs/01_KLINE_ANALYSIS.md](docs/01_KLINE_ANALYSIS.md) - K线图解读
- [docs/06_INTELLIGENCE_REPORT.md](docs/06_INTELLIGENCE_REPORT.md) - 报告解读
