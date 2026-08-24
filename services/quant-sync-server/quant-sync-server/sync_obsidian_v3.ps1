# NEMT Obsidian Sync Script v3
# ================================
# 使用 PowerShell 确保中文文件名正确处理

$API_KEY = "2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"
$BASE_URL = "https://127.0.0.1:27124"

# 忽略 SSL 警告
add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

$headers = @{
    "Authorization" = "Bearer $API_KEY"
    "Content-Type" = "text/plain; charset=utf-8"
}

Write-Host "============================================================"
Write-Host "NEMT Simulator - Obsidian Sync v3"
Write-Host "============================================================"

# 测试连接
Write-Host ""
Write-Host "[INFO] Testing connection..."
try {
    $test = Invoke-RestMethod -Uri "$BASE_URL/" -Method Get -Headers @{ "Authorization" = "Bearer $API_KEY" }
    Write-Host "[OK] Connected to Obsidian"
} catch {
    Write-Host "[FAIL] Cannot connect: $_"
    exit 1
}

# 创建文件夹
Write-Host ""
Write-Host "[INFO] Creating folders..."
$folders = @("架构设计", "产品需求", "开发任务", "理论", "代码模块", "Notion数据")
foreach ($folder in $folders) {
    try {
        Invoke-RestMethod -Uri "$BASE_URL/vault/$folder/" -Method Post -Headers $headers
        Write-Host "  [OK] $folder/"
    } catch {}
}

# 笔记内容定义
$notes = @{}

# 00-项目总览
$notes["00-项目总览.md"] = @"
# NEMT 量化交易系统 - 项目总览

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

- nemt_os/ - 核心回测引擎
- quant-sync-server/ - 量化同步服务
- web/ - React 前端
- docs/ - 文档

---

## 核心模块

| 模块 | 状态 | 说明 |
|------|------|------|
| NEMT 核心算法 | ✅ | NLS方程、谱分析 |
| 四相位状态机 | ✅ | A/B/C/D 自动识别 |
| 信号指标 | ✅ | DCI、涡旋、随机共振 |
| 风险管理 | ✅ | ATR止损、动态仓位 |
| 执行框架 | ✅ | 预测→信号→验证→加仓 |
| Web 前端 | ✅ | React 可视化界面 |
| Obsidian MCP | ✅ | 知识库同步 |

---

## 快速链接

- [[架构设计/项目架构]] - 完整系统架构
- [[代码模块/模块总览]] - 代码模块说明
- [[Notion数据/科技树]] - 技术升级路径
"@

# 架构设计
$notes["架构设计/项目架构.md"] = @"
# NEMT Quant OS - 系统架构

> 更新时间: 2026-04-19

---

## 整体架构

NEMT Quant OS 是一个基于非平衡市场理论的自进化量化交易系统。

### 核心层次

1. **市场层** - 数据获取、K线结构
2. **NEMT Core** - NLS方程、频谱分析
3. **信号层** - DCI、涡旋、共振检测
4. **策略层** - 多策略管理
5. **风控层** - 动态仓位、止损
6. **执行层** - 订单管理
7. **大脑层** - 决策控制
8. **进化层** - 策略淘汰

### 数据流向

市场数据 → 市场层 → NEMT Core → 信号层 → 策略层 → 大脑层 → 执行层 → 风控层
"@

# 代码模块总览
$notes["代码模块/模块总览.md"] = @"
# 代码模块总览

> 更新时间: 2026-04-19

---

## nemt_os 核心模块

### 模块列表

| 文件 | 模块名 | 功能 |
|------|--------|------|
| main.py | 主入口 | 命令行入口 |
| backtest.py | 回测引擎 | 事件循环 |
| brain.py | 大脑层 | 决策控制 |
| evolution.py | 进化层 | 策略淘汰 |
| risk.py | 风控层 | 风险管理 |
| strategy.py | 策略层 | 策略管理 |
| signal_layer.py | 信号层 | 信号生成 |
| execution.py | 执行层 | 订单执行 |
| data_layer.py | 数据层 | 数据管理 |
| market.py | 市场层 | 数据获取 |
| dashboard.py | 控制台 | 可视化 |

### 关键接口

\`\`\`python
# 回测入口
run_backtest(data_path, initial_capital, start_date, end_date)

# 大脑层
class Brain:
    def allocate_weights(self, market_state)
    def get_combined_signal(self, signals)

# 风控层
class RiskManager:
    def check_order(self, order)
    def get_risk_mode()
\`\`\`

---

## quant-sync-server 模块

### 模块列表

| 文件 | 功能 |
|------|------|
| main.py | 服务入口 |
| api_server.py | HTTP API |
| obsidian_mcp_server.py | Obsidian MCP |
| notion_adapter.py | Notion 适配器 |
| data_fetcher.py | 数据获取 |
| nls_solver.py | NLS 求解器 |

### API 端点

- POST /api/v1/pipeline/execute
- GET /api/v1/strategies
- POST /api/v1/notion/sync
"@

# 同步笔记
Write-Host ""
Write-Host "[INFO] Syncing notes..."
$success = 0
$total = $notes.Count

foreach ($path in $notes.Keys) {
    $content = $notes[$path]
    try {
        Invoke-RestMethod -Uri "$BASE_URL/vault/$path" -Method Put -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($content))
        Write-Host "  [OK] $path"
        $success++
    } catch {
        Write-Host "  [FAIL] $path : $_"
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "Sync Complete! ($success/$total notes)"
Write-Host "============================================================"
