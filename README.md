# NEMT Simulator V1
## 非平衡市场模拟器 (BTC实验版)

### 核心数学模型

改进的非线性薛定谔方程 (NLS):

```
i∂ψ/∂t + α∂²ψ/∂x² + β|ψ|²ψ = η(x,t)
```

**参数说明:**
- ψ (psi): 市场状态复振幅
- α (alpha): 扩散系数（市场流动性）
- β (beta): 非线性系数（情绪/杠杆/羊群效应）
- η (eta): 噪声（外部扰动/随机交易）

### 安装

```bash
pip install -r requirements.txt
```

### 使用方法

```bash
# 获取BTC数据并运行完整模拟
python main.py

# 仅获取数据
python main.py --fetch

# 使用演示数据（无需网络）
python main.py --demo

# 指定K线周期
python main.py --interval 5m
python main.py --interval 1h
python main.py --interval 4h
```

### 项目结构

```
NEMT Simulator/
├── emt_core.py        # 核心模拟器
├── data_fetcher.py    # 数据获取
├── visualizer.py      # 可视化
├── experiments.py     # 实验模块
├── main.py           # 主程序
├── requirements.txt  # 依赖
└── README.md         # 说明文档
```

### 三个核心实验

1. **噪声扫描实验**: 研究不同噪声水平下的谱结构响应
2. **非线性扫描实验**: 研究情绪/杠杆效应对市场的影响
3. **真实vs模拟对比**: 比较原始价格与模拟后的差异

### 输出

- `output/spectrum.png`: 频谱结构图
- `output/evolution.png`: 时空演化图
- `output/resonance.png`: 共振分析图
- `output/noise_experiment.png`: 噪声实验结果
- `output/nonlinear_experiment.png`: 非线性实验结果
- `output/comparison.png`: 对比分析图
- `output/summary.txt`: 文本摘要

### 核心指标

**谱宽 (Spectral Width)**: 描述市场结构稳定性的关键指标

### 注意事项

这不是一个预测价格的系统，而是一个研究市场在噪声下结构响应的"市场物理学实验室"。
