#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEMT 项目 - 完整 Obsidian 同步脚本 v2
=====================================
支持中文文件名
"""

import os
import sys
import requests
from urllib.parse import quote

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 加载配置
env_path = os.path.join(os.path.dirname(__file__), 'obsidian.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")
BASE_URL = "https://127.0.0.1:27124"

def create_note(path: str, content: str) -> bool:
    """创建或更新笔记"""
    try:
        # URL 编码路径 (中文文件名需要)
        encoded_path = quote(path, safe='/')
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'text/plain; charset=utf-8',
        }
        response = requests.put(
            f"{BASE_URL}/vault/{encoded_path}",
            headers=headers,
            data=content.encode('utf-8'),
            verify=False
        )
        return response.status_code == 204
    except Exception as e:
        print(f"Error creating {path}: {e}")
        return False

def create_folder(folder: str) -> bool:
    """创建文件夹"""
    try:
        encoded_folder = quote(folder, safe='/')
        requests.post(
            f"{BASE_URL}/vault/{encoded_folder}/",
            headers={'Authorization': f'Bearer {API_KEY}'},
            verify=False
        )
        return True
    except:
        return True

def check_connection() -> bool:
    try:
        response = requests.get(
            f"{BASE_URL}/vault/",
            headers={'Authorization': f'Bearer {API_KEY}'},
            verify=False
        )
        return response.status_code == 200
    except:
        return False


# ============ 笔记内容 ============

def get_index_note():
    return """# NEMT 量化交易系统 - 项目总览

> 更新时间: 2026-04-19
> 状态: 开发中

---

## 项目愿景

**NEMT = Non-Equilibrium Market Theory (非平衡市场理论)**

一个基于"非平衡市场理论"的智能量化交易系统，让策略在市场中自主生存、竞争、进化。

### 核心理念

- 不是设计一个"赚钱的策略"，而是设计一个"让好策略脱颖而出的生态系统"
- 策略不是静态的，而是动态适应市场相位的
- 风险不是预设的，而是由市场状态动态感知的

---

## 项目结构

```
NEMT-Simulator/
├── nemt_os/            # 核心回测引擎
│   ├── nemt/          # NEMT 核心模块
│   └── tests/         # 单元测试
├── quant-sync-server/  # 量化同步服务
│   ├── adapters/      # 外部适配器
│   ├── routers/       # API 路由
│   └── transformers/  # 数据转换
├── web/               # React 前端
└── docs/              # 文档
```

---

## 核心模块

| 模块 | 状态 | 说明 |
|------|------|------|
| NEMT 核心算法 | ✅ 完成 | NLS方程、谱分析 |
| 四相位状态机 | ✅ 完成 | A/B/C/D 自动识别 |
| 信号指标 | ✅ 完成 | DCI、涡旋、随机共振 |
| 风险管理 | ✅ 完成 | ATR止损、动态仓位 |
| 执行框架 | ✅ 完成 | 预测→信号→验证→加仓 |
| Web 前端 | ✅ 完成 | React 可视化界面 |
| MCP 服务器 | 🔧 进行中 | quant-sync-server |

---

## 开发阶段

- [x] Phase 1: Obsidian MCP 集成
- [x] Phase 2: 项目知识库完善
- [ ] Phase 3: 厨房阶段 - 架构搭建
- [ ] Phase 4: 厨房阶段 - 数据层
- [ ] Phase 5: 厨师阶段 - NEMT Core
- [ ] Phase 6: 生产化

---

## 快速链接

- [[架构设计/项目架构]] - 完整系统架构
- [[架构设计/多节点设计]] - 多节点系统设计
- [[产品需求/PRD]] - 产品需求文档
- [[产品需求/SPEC]] - 技术规格说明
- [[开发任务/任务清单]] - 开发任务总览
- [[理论/NEMT理论]] - NEMT 核心理论
- [[代码模块/模块总览]] - 代码模块说明
"""


def get_code_overview_note():
    return """# 代码模块总览

> 更新时间: 2026-04-19

---

## nemt_os 核心模块

### 目录结构

```
nemt_os/
├── main.py              # 主入口
├── nemt/
│   ├── __init__.py
│   ├── brain.py         # 大脑层
│   ├── evolution.py     # 进化层
│   ├── risk.py          # 风控层
│   ├── strategy.py      # 策略层
│   ├── signal_layer.py  # 信号层
│   ├── execution.py     # 执行层
│   ├── data_layer.py    # 数据层
│   ├── market.py        # 市场层
│   ├── dashboard.py     # 控制台
│   ├── backtest.py      # 回测引擎
│   └── config/
│       ├── __init__.py
│       └── settings.py  # 配置
└── tests/
    ├── __init__.py
    └── test_nemt.py     # 单元测试
```

---

## 核心模块详解

### brain.py - 大脑层

系统决策中心，根据市场状态动态调整策略权重。

**核心功能:**
- 策略权重动态分配
- 市场状态感知
- 决策控制

**关键类:**
```python
class Brain:
    def allocate_weights(self, market_state)
    def get_combined_signal(self, signals)
    def decide(self, market_data, signals)
```

---

### evolution.py - 进化层

策略生态管理，自动评分和淘汰。

**核心功能:**
- 策略评分系统
- 自动淘汰机制
- 新策略生成

**关键类:**
```python
class EvolutionManager:
    def score_strategy(self, strategy)
    def should_evict(self, strategy)
    def generate_new_strategy(self)
```

---

### risk.py - 风控层

风险管理控制，四级风控模式。

**核心功能:**
- 四级风控模式 (NORMAL/CAUTION/DEFENSE/SHUTDOWN)
- 仓位限制
- ATR 止损

**关键类:**
```python
class RiskManager:
    def check_order(self, order)
    def get_risk_mode(self)
    def calculate_position_size(self, signal, phase)
```

---

### strategy.py - 策略层

策略管理，支持多种策略类型。

**核心功能:**
- 策略基类定义
- 趋势/均值回归/动量策略
- 策略池管理

**关键类:**
```python
class Strategy:
    def generate_signal(self, data)
    def update_performance(self, pnl)

class StrategyPool:
    def add_strategy(self, strategy)
    def remove_strategy(self, strategy_id)
    def get_active_strategies(self)
```

---

### signal_layer.py - 信号层

信号生成和计算。

**核心功能:**
- 技术指标计算 (RSI, ATR, MACD, 布林带)
- 信号生成器
- 三种信号类型

**关键类:**
```python
class SignalGenerator:
    def calculate_rsi(self, prices, period=14)
    def calculate_atr(self, highs, lows, closes, period=14)
    def generate_signals(self, data)
```

---

### execution.py - 执行层

订单执行和持仓管理。

**核心功能:**
- 订单生成
- 持仓管理
- 交易记录

**关键类:**
```python
class ExecutionLayer:
    def create_order(self, signal)
    def execute_order(self, order)
    def update_position(self, trade)
```

---

### data_layer.py - 数据层

数据管理和质量控制。

**核心功能:**
- 统一数据接口
- 数据质量验证
- 历史数据获取

**关键类:**
```python
class DataLayer:
    def get_current_bar(self)
    def get_history(self, lookback)
    def validate_data(self, data)
```

---

### market.py - 市场层

市场数据获取和状态检测。

**核心功能:**
- CSV 数据加载
- 数据分割 (train/test)
- 市场状态检测

**关键类:**
```python
class Market:
    def load_data(self, filepath)
    def split_train_test(self, test_size=0.2)
    def detect_regime(self, data)
```

---

### dashboard.py - 控制台

性能监控和可视化。

**核心功能:**
- 实时指标展示
- Equity Curve 绘制
- 策略对比

**关键类:**
```python
class Dashboard:
    def record_equity(self, equity, timestamp)
    def print_summary(self)
    def plot_equity_curve(self)
    def save_results(self)
```

---

### backtest.py - 回测引擎

事件驱动的回测循环。

**核心功能:**
- Bar 循环遍历
- 策略执行
- 性能计算

**关键函数:**
```python
def run_backtest(data_path, initial_capital, start_date, end_date)
```

---

## quant-sync-server 模块

### 目录结构

```
quant-sync-server/
├── main.py                 # 服务入口
├── config.py               # 配置
├── database.py            # 数据库
├── models.py              # 数据模型
├── adapters/
│   ├── notion_adapter.py  # Notion 适配器
│   └── matlab_bridge.py  # MATLAB 桥接
├── routers/
│   └── signal_router.py   # 信号路由
├── transformers/
│   └── data_transformer.py
├── api_server.py          # API 服务器
├── obsidian_mcp_server.py # Obsidian MCP
└── sync_*.py             # 同步脚本
```

---

## 测试

### 运行单元测试

```bash
cd nemt_os
python -m pytest tests/ -v
```

### 测试覆盖率目标

- nemt_core.py: > 90%
- nemt_signals.py: > 85%
- nemt_state_machine.py: > 90%
- nemt_risk.py: > 80%
- nemt_execution.py: > 80%
- **整体**: > 80%
"""


def get_architecture_note():
    return """# NEMT Quant OS - 系统架构

> 更新时间: 2026-04-19

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      NEMT Quant OS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │    Web UI    │    │   Python     │    │   Notion     │  │
│   │   (React)    │ ←→ │   Core       │ ←→ │   知识库     │  │
│   └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
│          ↓                ↓                ↓                │
│   ┌──────────────────────────────────────────────────────┐   │
│   │                 Node Modules (Python)                  │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │   │
│   │  │ Market   │ │   NEMT   │ │  Signal  │ │  Risk  │ │   │
│   │  │  Layer   │ │   Core   │ │  Layer   │ │  Layer │ │   │
│   │  └──────────┘ └──────────┘ └──────────┘ └────────┘ │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │   │
│   │  │ OnChain  │ │ Strategy │ │Execution │ │ Brain  │ │   │
│   │  │  Layer   │ │  Layer   │ │  Layer   │ │  Layer │ │   │
│   │  └──────────┘ └──────────┘ └──────────┘ └────────┘ │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心节点

### 市场层 (Market Layer)
- 获取市场数据
- K线数据结构
- 实时价格流

### NEMT Core (核心算法)
- NLS 非线性薛定谔方程
- 频谱分析
- 共振检测

### 信号层 (Signal Layer)
- DCI 方向一致性指数
- 涡旋检测
- 随机共振检测

### 风控层 (Risk Layer)
- 相位驱动仓位
- ATR 止损
- 回撤控制

### 执行层 (Execution Layer)
- 预测 → 信号 → 验证 → 加仓
- 订单管理
- 持仓跟踪

### 大脑层 (Brain Layer)
- 策略权重分配
- 资金调度决策
- 风险模式切换

### 进化层 (Evolution Layer)
- 策略评分
- 自动淘汰
- 新策略生成

---

## 数据流向

```
市场数据 → 市场层 → NEMT Core → 信号层 → 策略层
                                         ↓
                                  大脑层 (决策)
                                         ↓
风控层 ← 执行层 ← 大脑层 (执行指令)
    ↑
    └── 实时监控 + 异常告警
```

---

## 技术栈

### 后端
- Python 3.10+
- NumPy/SciPy (数值计算)
- Pandas (数据处理)
- FastAPI (HTTP服务)

### 前端
- React 18+
- TypeScript 5+
- Vite 5+

### 基础设施
- Docker (容器化)
- Redis (事件总线)
- Notion (知识库)
- Obsidian (第二知识库)
"""


# ============ 主函数 ============

def main():
    print("=" * 60)
    print("NEMT Simulator - 完整 Obsidian 同步 v2")
    print("=" * 60)
    
    if not API_KEY:
        print("[ERROR] OBSIDIAN_API_KEY not configured!")
        return
    
    if not check_connection():
        print("[FAIL] Cannot connect to Obsidian")
        return
    
    print("[OK] Connected to Obsidian")
    
    # 创建文件夹结构
    folders = [
        "架构设计",
        "产品需求",
        "开发任务",
        "理论",
        "代码模块",
    ]
    
    print("\n[INFO] Creating folders...")
    for folder in folders:
        create_folder(folder)
    
    # 笔记列表
    notes = [
        ("00-项目总览.md", get_index_note()),
        ("架构设计/项目架构.md", get_architecture_note()),
        ("代码模块/模块总览.md", get_code_overview_note()),
    ]
    
    print("\n[INFO] Creating notes...")
    success = 0
    for path, content in notes:
        if create_note(path, content):
            print(f"  [OK] {path}")
            success += 1
        else:
            print(f"  [FAIL] {path}")
    
    print()
    print("=" * 60)
    print(f"Sync Complete! ({success}/{len(notes)} notes)")
    print("=" * 60)


if __name__ == "__main__":
    main()
