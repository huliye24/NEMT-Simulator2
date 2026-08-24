# NEMT Obsidian Sync - Simple Version
# =====================================

$API_KEY = "2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"
$BASE_URL = "https://127.0.0.1:27124"

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

Write-Host "NEMT Obsidian Sync"

# Test connection
$r = Invoke-RestMethod -Uri "$BASE_URL/vault/" -Method Get -Headers @{Authorization = "Bearer $API_KEY"}
Write-Host "Connected. Files: $($r.files.Count)"

# Create folders
$folders = @(
    "架构设计",
    "产品需求",
    "开发任务",
    "理论",
    "代码模块"
)

foreach ($f in $folders) {
    Invoke-RestMethod -Uri "$BASE_URL/vault/$f/" -Method Post -Headers @{Authorization = "Bearer $API_KEY"} -ErrorAction SilentlyContinue | Out-Null
    Write-Host "Folder: $f"
}

# Create notes
$headers = @{
    Authorization = "Bearer $API_KEY"
    "Content-Type" = "text/plain; charset=utf-8"
}

$notes = @{
    "00-项目总览.md" = @"
# NEMT 量化交易系统 - 项目总览

更新时间: 2026-04-19

## 项目愿景

NEMT = Non-Equilibrium Market Theory (非平衡市场理论)

让策略在市场中自主生存、竞争、进化。

## 核心模块

- nemt_os - 核心回测引擎
- quant-sync-server - 量化同步服务
- web - React 前端

## 开发阶段

- [x] Phase 1: Obsidian MCP 集成
- [x] Phase 2: 项目知识库完善
- [ ] Phase 3: 厨房阶段 - 架构搭建
- [ ] Phase 4: 厨房阶段 - 数据层
- [ ] Phase 5: 厨师阶段 - NEMT Core
- [ ] Phase 6: 生产化

## 快速链接

- [[架构设计/项目架构]]
- [[代码模块/模块总览]]
"@

    "架构设计/项目架构.md" = @"
# NEMT Quant OS - 系统架构

更新时间: 2026-04-19

## 核心层次

1. 市场层 - 数据获取
2. NEMT Core - NLS方程
3. 信号层 - DCI/涡旋
4. 策略层 - 多策略管理
5. 风控层 - 风险管理
6. 执行层 - 订单执行
7. 大脑层 - 决策控制
8. 进化层 - 策略淘汰

## 数据流向

市场 → 市场层 → NEMT Core → 信号层 → 策略层
                                       ↓
                                大脑层 (决策)
                                       ↓
风控层 ← 执行层 ← 大脑层 (执行)
"@

    "代码模块/模块总览.md" = @"
# 代码模块总览

更新时间: 2026-04-19

## nemt_os 模块

| 文件 | 功能 |
|------|------|
| main.py | 主入口 |
| backtest.py | 回测引擎 |
| brain.py | 大脑层 |
| evolution.py | 进化层 |
| risk.py | 风控层 |
| strategy.py | 策略层 |
| signal_layer.py | 信号层 |
| execution.py | 执行层 |
| data_layer.py | 数据层 |
| market.py | 市场层 |
| dashboard.py | 控制台 |

## quant-sync-server 模块

| 文件 | 功能 |
|------|------|
| main.py | 服务入口 |
| api_server.py | HTTP API |
| obsidian_mcp_server.py | Obsidian MCP |
| notion_adapter.py | Notion 适配器 |
"@
}

Write-Host ""
Write-Host "Syncing notes..."
$count = 0
foreach ($path in $notes.Keys) {
    $content = $notes[$path]
    Invoke-RestMethod -Uri "$BASE_URL/vault/$path" -Method Put -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($content))
    Write-Host "  OK: $path"
    $count++
}

Write-Host ""
Write-Host "Done! $count notes synced."
