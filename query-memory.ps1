# ============================================================================
# Cursor Memory Query Tool
# 查询COS中存储的记忆和经验
# ============================================================================
# Usage:
#   .\query-memory.ps1                       # 查看所有项目索引
#   .\query-memory.ps1 -Project electron     # 查看electron项目记忆
#   .\query-memory.ps1 -Project electron -Keyword "MCP"
#   .\query-memory.ps1 -Project electron -Tag mcp,configuration
#   .\query-memory.ps1 -Recent 10            # 查看最近的会话
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$Project = "",

    [Parameter(Mandatory=$false)]
    [string]$Keyword = "",

    [Parameter(Mandatory=$false)]
    [string[]]$Tag = @(),

    [Parameter(Mandatory=$false)]
    [int]$Recent = 0,

    [Parameter(Mandatory=$false)]
    [ValidateSet("patterns", "failures", "sessions", "all")]
    [string]$Type = "all"
)

$ErrorActionPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 颜色输出
function Write-Title {
    param([string]$Text)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host "── $Text ──" -ForegroundColor Yellow
    Write-Host ""
}

# 获取项目名称
function Get-ProjectName {
    if ($Project) { return $Project }

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

# 查询全局索引
function Query-Index {
    Write-Title "Memory Index"

    $result = & python "$PSScriptRoot\cursor_memory_cos.py" query -p "" 2>&1

    if ($LASTEXITCODE -ne 0 -or $result -match "error|fail") {
        Write-Host "  No index found or COS connection failed" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Run '.\sync-memory.ps1 -Mode sync' to initialize" -ForegroundColor Gray
        return
    }

    # 解析JSON输出
    try {
        $index = $result | ConvertFrom-Json
        if ($index.projects) {
            $index.projects.PSObject.Properties | ForEach-Object {
                $proj = $_
                Write-Host "  $($proj.Name)" -ForegroundColor Green -NoNewline
                Write-Host "  |  Sessions: $($proj.Value.session_count)  |  Patterns: $($proj.Value.patterns_count)  |  Last: $($proj.Value.last_session)"
            }
        } else {
            Write-Host "  No projects in index yet" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  Index: $result" -ForegroundColor Gray
    }

    Write-Host ""
}

# 查询patterns
function Query-Patterns {
    param([string]$ProjectName)

    Write-Section "Patterns"

    $cmd = "python `"$PSScriptRoot\cursor_memory_cos.py`" query -p $ProjectName"
    if ($Keyword) { $cmd += " -k `"$Keyword`"" }
    if ($Tag.Count -gt 0) { $cmd += " -t $($Tag -join ' ')" }

    $result = Invoke-Expression $cmd

    if ($result -match "\[\]" -or $result -match "error") {
        Write-Host "  No patterns found" -ForegroundColor Gray
        return
    }

    try {
        $patterns = $result | ConvertFrom-Json
        if ($patterns -is [System.Array]) {
            $patterns | ForEach-Object -IndexUnit {
                $i = $_
                $p = $_
                Write-Host "  [$i] " -ForegroundColor Green -NoNewline
                Write-Host "$($p.problem)" -ForegroundColor White
                Write-Host "     Solution: $($p.solution)" -ForegroundColor Gray
                if ($p.tags) {
                    Write-Host "     Tags: $($p.tags -join ', ')" -ForegroundColor DarkGray
                }
                Write-Host "     Seen: $($p.occurrences) times" -ForegroundColor DarkGray
                Write-Host ""
            }
        } else {
            Write-Host "  $result" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  $result" -ForegroundColor Gray
    }
}

# 查询failures
function Query-Failures {
    param([string]$ProjectName)

    Write-Section "Failures (Lessons Learned)"

    $cacheDir = "$PSScriptRoot\.cursor\memory-cos-cache\$ProjectName"

    if (Test-Path "$cacheDir\failures.json") {
        $failures = Get-Content "$cacheDir\failures.json" | ConvertFrom-Json

        $failures | ForEach-Object -IndexUnit {
            $i = $_
            $f = $_
            Write-Host "  [$i] " -ForegroundColor Red -NoNewline
            Write-Host "$($f.problem)" -ForegroundColor White
            Write-Host "     Reason: $($f.reason)" -ForegroundColor Gray
            if ($f.avoid) {
                Write-Host "     Avoid: $($f.avoid)" -ForegroundColor DarkGray
            }
            Write-Host "     Date: $($f.timestamp)" -ForegroundColor DarkGray
            Write-Host ""
        }
    } else {
        Write-Host "  No failures recorded" -ForegroundColor Gray
    }
}

# 查询sessions
function Query-Sessions {
    param([string]$ProjectName)

    Write-Section "Recent Sessions"

    $cacheDir = "$PSScriptRoot\.cursor\memory-cos-cache\$ProjectName"

    if (Test-Path "$cacheDir\sessions") {
        $sessions = Get-ChildItem "$cacheDir\sessions" -Filter "*.json" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First $Recent

        if ($Recent -gt 0) {
            $sessions = $sessions | Select-Object -First $Recent
        }

        foreach ($session in $sessions) {
            $data = Get-Content $session.FullName | ConvertFrom-Json
            Write-Host "  $($session.Name)" -ForegroundColor Green -NoNewline
            Write-Host "  |  Resolved: $($data.resolved.Count)  |  Failed: $($data.failed.Count)"

            if ($data.notes) {
                Write-Host "     $($data.notes.Substring(0, [Math]::Min(80, $data.notes.Length)))..." -ForegroundColor Gray
            }
            Write-Host ""
        }
    } else {
        Write-Host "  No sessions cached locally" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Run '.\sync-memory.ps1 -Mode download' first" -ForegroundColor DarkGray
    }
}

# ============================================================================
# Main
# ============================================================================

if ($Recent -gt 0) {
    Write-Title "Recent Sessions"
    $sessions = & python "$PSScriptRoot\cursor_memory_cos.py" query -p $Project 2>&1
    # 简单显示
    $ProjectName = Get-ProjectName
    $cacheDir = "$PSScriptRoot\.cursor\memory-cos-cache\$ProjectName"
    if (Test-Path "$cacheDir\sessions") {
        Get-ChildItem "$cacheDir\sessions" -Filter "*.json" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First $Recent |
            ForEach-Object {
                Write-Host "  $($_.Name)" -ForegroundColor Green
            }
    }
    exit 0
}

if (-not $Project) {
    # 显示索引
    Query-Index
    Write-Host ""
    Write-Host "Usage: " -ForegroundColor White -NoNewline
    Write-Host ".\query-memory.ps1 -Project <name> [-Keyword <text>] [-Tag <tag1,tag2>]" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\query-memory.ps1 -Project electron" -ForegroundColor Gray
    Write-Host "  .\query-memory.ps1 -Project electron -Keyword MCP" -ForegroundColor Gray
    Write-Host "  .\query-memory.ps1 -Project electron -Tag mcp,configuration" -ForegroundColor Gray
    exit 0
}

$ProjectName = Get-ProjectName

Write-Title "Memory: $ProjectName"

switch ($Type) {
    "patterns" { Query-Patterns $ProjectName }
    "failures" { Query-Failures $ProjectName }
    "sessions" { Query-Sessions $ProjectName }
    "all" {
        Query-Patterns $ProjectName
        Query-Failures $ProjectName
        Query-Sessions $ProjectName
    }
}

Write-Host ""
