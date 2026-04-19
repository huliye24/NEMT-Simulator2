# NEMT Simulator

**非平衡市场理论模拟器 (Non-Equilibrium Market Theory Simulator)**

一个基于量子物理的市场结构分析工具，用于研究加密货币市场在噪声下的谱结构响应。

## 核心模型

改进的非线性薛定谔方程 (NLS):

```
i∂ψ/∂t + α∂²ψ/∂x² + β|ψ|²ψ = η(x,t)
```

**参数说明:**
- ψ (psi): 市场状态复振幅
- α (alpha): 扩散系数（市场流动性）
- β (beta): 非线性系数（情绪/杠杆/羊群效应）
- η (eta): 噪声（外部扰动/随机交易）

## 技术架构

```
NEMT Simulator/
├── web/                    # Web 前端 (React + Vite + Chart.js)
│   ├── src/
│   │   ├── App.tsx        # 主应用
│   │   ├── components/    # UI 组件
│   │   ├── utils/        # NEMT 核心算法 (TypeScript)
│   │   └── types/        # 类型定义
│   └── package.json
│
├── nemt_core.py           # Python 核心模拟器
├── experiments.py         # 三个核心实验
├── visualizer.py          # Python 可视化
├── data_fetcher.py       # Binance 数据获取
├── main.py               # Python 入口程序
│
└── NEMT_Vision/          # 愿景与原则文档
    ├── VISION.md         # 核心愿景
    ├── BOUNDARIES.md     # 边界定义
    └── Principles/       # 原则详解
```

## 快速开始

### Web 界面

```bash
cd web
npm install
npm run dev
```

访问 http://localhost:3000

### Python 版本

```bash
pip install -r requirements.txt
python main.py --demo
```

## 三个核心实验

1. **噪声扫描实验**: 研究不同噪声水平下的谱结构响应
2. **非线性扫描实验**: 研究情绪/杠杆效应对市场的影响
3. **真实vs模拟对比**: 比较原始价格与模拟后的差异

## 部署

### Cloudflare Pages

本项目配置了 GitHub Actions 自动部署到 Cloudflare Pages。

详见 [web/README.md](web/README.md)

## 许可证

MIT
