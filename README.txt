# NEMT 模拟器使用指南

## 系统架构

```
NEMT Simulator/
├── binance_fetcher.py          # Python数据获取
├── data/                        # 原始数据
├── matlab/                      # MATLAB分析工具箱
│   ├── initNEMT.m              # 初始化脚本
│   ├── NEMTAnalyzer.m          # 主分析程序
│   ├── nemt_core/              # 核心算法
│   │   ├── NEMTParams.m
│   │   └── NEMTSimulator.m
│   ├── experiments/            # 实验模块
│   │   ├── NoiseScanExperiment.m
│   │   └── NonlinearScanExperiment.m
│   ├── visualization/          # 可视化
│   │   └── NEMTVisualizer.m
│   └── utils/                  # 工具
│       └── DataLoader.m
└── matlab_data/               # MATLAB格式数据
```

## 快速开始

### 1. 获取数据 (Python)

```bash
python binance_fetcher.py
```

### 2. MATLAB分析

```matlab
cd matlab
initNEMT

% 方式1: 快捷运行
NEMTAnalyzer.run('BTC', '1h')

% 方式2: 分步运行
analyzer = NEMTAnalyzer('ETH', '4h');
analyzer.loadData('matlab_data');
analyzer.runNoiseScan();
analyzer.runNonlinearScan();
analyzer.visualize();
report = analyzer.generateReport();
```

## 支持的交易对和周期

| 交易对 | 代码 |
|--------|------|
| BTCUSDT | BTC |
| ETHUSDT | ETH |
| SOLUSDT | SOL |

| 周期 | 代码 |
|------|------|
| 15分钟 | 15m |
| 1小时 | 1h |
| 4小时 | 4h |

## 实验说明

### 噪声扫描实验
- 研究市场噪声对谱结构的影响
- 观察相变现象

### 非线性扫描实验
- 研究情绪/杠杆效应的强度
- 检测孤子结构

## 输出指标

- 谱宽 (Spectral Width)
- 共振峰数量
- 平均频率
