$API_KEY = "2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"
$BASE_URL = "https://127.0.0.1:27124"

add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) { return true; }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

Write-Host "============================================================"
Write-Host "NEMT Simulator - Obsidian Sync"
Write-Host "============================================================"

$r = Invoke-RestMethod -Uri "$BASE_URL/vault/" -Method Get -Headers @{Authorization = "Bearer $API_KEY"}
Write-Host ""
Write-Host "[OK] Connected. Current files: $($r.files.Count)"

$headers = @{ Authorization = "Bearer $API_KEY"; "Content-Type" = "text/plain; charset=utf-8" }

# ============================================================
# NOTE DEFINITIONS
# ============================================================

$overview = @"
# NEMT 量化交易系统 - 项目总览

更新时间: 2026-04-19

## 项目愿景

**NEMT = Non-Equilibrium Market Theory (非平衡市场理论)**

一个让策略在市场中自主生存、竞争、进化的智能量化交易系统。

## 核心理念

- 不是设计一个"赚钱的策略"，而是设计一个"让好策略脱颖而出的生态系统"
- 策略不是静态的，而是动态适应市场相位的
- 风险不是预设的，而是由市场状态动态感知的

## 项目结构

```
NEMT-Simulator/
├── nemt_os/            # 核心回测引擎
│   ├── nemt/          # NEMT 核心模块
│   └── tests/         # 单元测试
├── quant-sync-server/  # 量化同步服务
├── web/               # React 前端
└── docs/              # 文档
```

## 核心模块

| 模块 | 状态 | 说明 |
|------|------|------|
| NEMT 核心算法 | 完成 | NLS方程、谱分析 |
| 四相位状态机 | 完成 | A/B/C/D 自动识别 |
| 信号指标 | 完成 | DCI、涡旋、随机共振 |
| 风险管理 | 完成 | ATR止损、动态仓位 |
| 执行框架 | 完成 | 预测→信号→验证→加仓 |
| Web 前端 | 完成 | React 可视化界面 |
| Obsidian MCP | 完成 | 知识库同步 |

## 开发阶段

- [x] Phase 1: Obsidian MCP 集成
- [x] Phase 2: 项目知识库完善
- [ ] Phase 3: 厨房阶段 - 架构搭建
- [ ] Phase 4: 厨房阶段 - 数据层
- [ ] Phase 5: 厨师阶段 - NEMT Core
- [ ] Phase 6: 生产化

## 快速链接

- [[架构设计/项目架构]] - 完整系统架构
- [[代码模块/模块总览]] - 代码模块说明
- [[Notion数据/科技树]] - 技术升级路径
"@

$architecture = @"
# NEMT Quant OS - 系统架构

更新时间: 2026-04-19

## 整体架构

NEMT Quant OS 是一个基于非平衡市场理论的自进化量化交易系统。

## 核心层次

1. **市场层 (Market Layer)** - 数据获取、K线结构、实时价格
2. **NEMT Core** - NLS非线性薛定谔方程、频谱分析、共振检测
3. **信号层 (Signal Layer)** - DCI方向一致性指数、涡旋检测、随机共振检测
4. **策略层 (Strategy Layer)** - 多策略管理、策略池
5. **风控层 (Risk Layer)** - 相位驱动仓位、ATR止损、回撤控制
6. **执行层 (Execution Layer)** - 订单管理、持仓跟踪
7. **大脑层 (Brain Layer)** - 策略权重分配、资金调度、风险模式切换
8. **进化层 (Evolution Layer)** - 策略评分、自动淘汰、新策略生成

## 数据流向

```
市场数据 → 市场层 → NEMT Core → 信号层 → 策略层
                                         ↓
                                  大脑层 (决策)
                                         ↓
风控层 ← 执行层 ← 大脑层 (执行指令)
```

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
"@

$codeOverview = @"
# 代码模块总览

更新时间: 2026-04-19

## nemt_os 核心模块

### 目录结构

```
nemt_os/
├── main.py              # 主入口
├── nemt/
│   ├── brain.py        # 大脑层
│   ├── evolution.py    # 进化层
│   ├── risk.py         # 风控层
│   ├── strategy.py     # 策略层
│   ├── signal_layer.py # 信号层
│   ├── execution.py    # 执行层
│   ├── data_layer.py  # 数据层
│   ├── market.py      # 市场层
│   ├── dashboard.py   # 控制台
│   ├── backtest.py    # 回测引擎
│   └── config/        # 配置
└── tests/             # 测试
```

### 模块详解

| 文件 | 模块名 | 功能 |
|------|--------|------|
| main.py | 主入口 | 命令行入口 |
| backtest.py | 回测引擎 | 事件循环、策略执行 |
| brain.py | 大脑层 | 决策控制、权重分配 |
| evolution.py | 进化层 | 策略淘汰、新策略生成 |
| risk.py | 风控层 | 四级风控、仓位限制 |
| strategy.py | 策略层 | 趋势/均值回归/动量策略 |
| signal_layer.py | 信号层 | RSI/ATR/MACD/布林带 |
| execution.py | 执行层 | 订单生成、持仓管理 |
| data_layer.py | 数据层 | 统一数据接口 |
| market.py | 市场层 | 数据加载、状态检测 |
| dashboard.py | 控制台 | 可视化、报告生成 |

### 关键接口

```python
# 回测入口
run_backtest(data_path, initial_capital, start_date, end_date)

# 大脑层
class Brain:
    def allocate_weights(self, market_state)
    def get_combined_signal(self, signals)
    def decide(self, market_data, signals)

# 风控层
class RiskManager:
    def check_order(self, order)
    def get_risk_mode()
    def calculate_position_size(self, signal, phase)
```

---

## quant-sync-server 模块

### 目录结构

```
quant-sync-server/
├── main.py                  # 服务入口
├── api_server.py           # HTTP API
├── config.py               # 配置
├── database.py              # 数据库
├── models.py               # 数据模型
├── obsidian_mcp_server.py  # Obsidian MCP
├── notion_adapter.py       # Notion 适配器
├── adapters/               # 外部适配器
├── routers/                # API 路由
└── transformers/          # 数据转换
```

### API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| /api/v1/pipeline/execute | POST | 执行 Pipeline |
| /api/v1/strategies | GET | 获取策略列表 |
| /api/v1/notion/sync | POST | 同步 Notion |

---

## 测试

```bash
cd nemt_os
python -m pytest tests/ -v
```

### 覆盖率目标

- nemt_core.py: > 90%
- nemt_signals.py: > 85%
- nemt_risk.py: > 80%
- **整体**: > 80%
"@

# ============================================================
# SYNC NOTES
# ============================================================

Write-Host ""
Write-Host "[INFO] Syncing notes..."

$notes = @{
    "00-项目总览.md" = $overview
    "架构设计/项目架构.md" = $architecture
    "代码模块/模块总览.md" = $codeOverview
}

$count = 0
foreach ($path in $notes.Keys) {
    $content = $notes[$path]
    Invoke-RestMethod -Uri "$BASE_URL/vault/$path" -Method Put -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($content))
    Write-Host "  [OK] $path"
    $count++
}

Write-Host ""
Write-Host "============================================================"
Write-Host "Sync Complete! ($count notes)"
Write-Host "============================================================"
