# ============================================================================
# Cursor COS Memory Sync Script
# 同步Cursor记忆到腾讯云COS
# ============================================================================
# Usage:
#   .\sync-memory.ps1 -Mode download    # 下载记忆
#   .\sync-memory.ps1 -Mode upload      # 上传记忆
#   .\sync-memory.ps1 -Mode sync        # 完整同步
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("download", "upload", "sync")]
    [string]$Mode = "download",

    [Parameter(Mandatory=$false)]
    [string]$Project = ""
)

$ErrorActionPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 颜色输出
function Write-Status {
    param([string]$Status, [string]$Message)
    switch ($Status) {
        "INFO"    { Write-Host "[INFO]    " -NoNewline -ForegroundColor Cyan; Write-Host $Message }
        "SUCCESS" { Write-Host "[SUCCESS] " -NoNewline -ForegroundColor Green; Write-Host $Message }
        "WARN"    { Write-Host "[WARN]    " -NoNewline -ForegroundColor Yellow; Write-Host $Message }
        "ERROR"   { Write-Host "[ERROR]   " -NoNewline -ForegroundColor Red; Write-Host $Message }
        "PROGRESS" { Write-Host "[PROGRESS]" -NoNewline -ForegroundColor Magenta; Write-Host $Message }
    }
}

# 获取项目名称
function Get-ProjectName {
    # 当前目录就是项目根目录
    $projectRoot = $PSScriptRoot

    # 检测主要项目目录
    $projects = @("electron", "nemt-os", "nemt-go", "frontend", "backend", "src")
    foreach ($proj in $projects) {
        if (Test-Path "$projectRoot\$proj") {
            return $proj
        }
    }

    # 使用当前目录名
    return (Split-Path -Leaf $projectRoot).ToLower().Replace(" ", "-")
}

# 主流程 - 下载
function Sync-Download {
    param([string]$ProjectName)

    Write-Status "INFO" "Downloading memory for: $ProjectName"
    Write-Host ""

    $result = & python "$PSScriptRoot\cursor_memory_cos.py" download -p $ProjectName

    if ($LASTEXITCODE -eq 0) {
        Write-Status "SUCCESS" "Memory downloaded successfully"
    } else {
        Write-Status "ERROR" "Download failed"
        Write-Host $result
    }
}

# 主流程 - 上传
function Sync-Upload {
    param([string]$ProjectName)

    Write-Status "INFO" "Uploading session memory for: $ProjectName"
    Write-Host ""

    # 检查是否有本地缓存的会话数据
    $cacheDir = "$PSScriptRoot\.cursor\memory-cos-cache\$ProjectName"

    if (Test-Path "$cacheDir\sessions") {
        $sessions = Get-ChildItem "$cacheDir\sessions" -Filter "*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

        if ($sessions) {
            Write-Status "INFO" "Found session: $($sessions.Name)"

            # 上传最新会话
            $result = & python "$PSScriptRoot\cursor_memory_cos.py" upload -p $ProjectName

            if ($LASTEXITCODE -eq 0) {
                Write-Status "SUCCESS" "Session uploaded"
            }
        }
    }

    # 如果没有会话，也上传patterns和failures
    Write-Status "INFO" "Syncing patterns and failures..."

    $patternsLocal = "$cacheDir\patterns.json"
    $failuresLocal = "$cacheDir\failures.json"

    if ((Test-Path $patternsLocal) -or (Test-Path $failuresLocal)) {
        $result = & python "$PSScriptRoot\cursor_memory_cos.py" sync -p $ProjectName

        if ($LASTEXITCODE -eq 0) {
            Write-Status "SUCCESS" "Patterns and failures synced"
        }
    }

    Write-Host ""
    Write-Status "SUCCESS" "Upload complete"
}

# 主流程 - 完整同步
function Sync-Full {
    param([string]$ProjectName)

    Write-Status "INFO" "Full sync for: $ProjectName"
    Write-Host ""

    # 1. 下载最新记忆
    Write-Status "PROGRESS" "Step 1/3: Downloading..."
    & python "$PSScriptRoot\cursor_memory_cos.py" download -p $ProjectName

    # 2. 上传本地缓存
    Write-Status "PROGRESS" "Step 2/3: Uploading local cache..."
    & python "$PSScriptRoot\cursor_memory_cos.py" sync -p $ProjectName

    # 3. 显示摘要
    Write-Status "PROGRESS" "Step 3/3: Summary"
    $cacheDir = "$PSScriptRoot\.cursor\memory-cos-cache\$ProjectName"

    if (Test-Path "$cacheDir\patterns.json") {
        $patterns = Get-Content "$cacheDir\patterns.json" | ConvertFrom-Json
        Write-Status "INFO" "Patterns: $($patterns.Count)"
    }

    if (Test-Path "$cacheDir\failures.json") {
        $failures = Get-Content "$cacheDir\failures.json" | ConvertFrom-Json
        Write-Status "INFO" "Failures recorded: $($failures.Count)"
    }

    Write-Host ""
    Write-Status "SUCCESS" "Full sync complete!"
}

# ============================================================================
# Main
# ============================================================================

$ProjectName = if ($Project) { $Project } else { Get-ProjectName }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Cursor COS Memory Sync" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Mode:    $Mode"
Write-Host "  Project: $ProjectName"
Write-Host "  COS:     cursormerory-1390947672"
Write-Host ""

switch ($Mode) {
    "download" { Sync-Download $ProjectName }
    "upload"   { Sync-Upload $ProjectName }
    "sync"     { Sync-Full $ProjectName }
}

Write-Host ""
