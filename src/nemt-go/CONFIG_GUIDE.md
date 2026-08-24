# NEMT-Go 配置指南

## 概述

本目录包含用于约束和规范 NEMT-Go 项目代码的配置文件。

## 文件列表

| 文件 | 用途 |
|------|------|
| `.editorconfig` | 编辑器统一配置 (缩进、换行等) |
| `.golangci.yaml` | Go Linter 配置 |
| `GoLandSettings.xml` | GoLand Inspections 配置 |
| `go.imports.xml` | Import 顺序配置 |
| `.idea/go.xml` | Go SDK 和模块配置 |
| `.idea/inspection.xml` | 代码检查配置 |
| `.idea/editor.xml` | 编辑器配置 |
| `scripts/check_structure.sh` | 包结构检查脚本 (Linux/macOS) |
| `scripts/check_structure.bat` | 包结构检查脚本 (Windows) |
| `scripts/check_cycles.sh` | 循环依赖检查脚本 |

## 快速配置 GoLand

### 1. 导入配置

在 GoLand 中：
1. `File → Import Settings`
2. 选择 `GoLandSettings.xml`
3. 重启 GoLand

### 2. 手动配置

#### Import 顺序
`File → Settings → Editor → Code Style → Go → Imports`

```
Section order:
1. STD (Go 标准库)
2. EXT (第三方库)
3. PROJECT (github.com/nemt-lab/nemt-go)

Local package prefix: github.com/nemt-lab/nemt-go
```

#### Inspections
`File → Settings → Editor → Inspections → Go`

启用以下检查：
- [x] Error handling - Unchecked error (errcheck)
- [x] Error handling - Error returning not checked
- [x] Go vet
- [x] Unreachable code
- [x] Unused variable
- [x] Incorrect imports order
- [x] Nilness

#### gofmt 设置
`File → Settings → Go → Tools → File Watchers`

添加 gofmt 和 goimports 作为 File Watcher。

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 包名 | 小写下划线 | `market_data` |
| 文件名 | snake_case | `market_data.go` |
| 类型/结构体 | PascalCase | `MarketData` |
| 接口 | PascalCase | `IMarketProvider` |
| 函数/变量 | camelCase | `getMarketData` |
| 常量 | ALL_CAPS | `MAX_RETRY_COUNT` |

## 包结构规范

```
cmd/
├── collector/main.go    # ✓ 正确
├── collector/other.go  # ✗ 错误 - cmd/ 只允许 main.go
└── gateway/main.go

pkg/
├── cache/
├── config/
├── gateway/
└── ...
```

## Import 顺序示例

```go
import (
    "context"                    // 标准库
    "encoding/json"              // 标准库
    "time"                       // 标准库

    "github.com/gin-gonic/gin"  // 第三方库
    "github.com/google/uuid"    // 第三方库

    "github.com/nemt-lab/nemt-go/pkg/config"  // 本地包
    "github.com/nemt-lab/nemt-go/pkg/logger"  // 本地包
)
```

## 运行检查

### 包结构检查
```bash
# Linux/macOS
bash scripts/check_structure.sh

# Windows
scripts\check_structure.bat
```

### 循环依赖检查
```bash
bash scripts/check_cycles.sh
```

### Linter 检查
```bash
# 安装 golangci-lint
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# 运行检查
golangci-lint run ./...
```

## IDE 设置

### GoLand
1. 安装 Go 插件 (预装)
2. 启用 gofmt 和 goimports
3. 设置 File Watcher

### VS Code
安装插件：
- `golang.go`
- `golangci-lint`

配置 `.vscode/settings.json`:
```json
{
  "go.formatTool": "goimports",
  "go.lintTool": "golangci-lint",
  "go.lintOnSave": "package",
  "go.useLanguageServer": true
}
```

## 常见问题

### Q: Import 顺序不生效
A: 确保 `File → Settings → Editor → Code Style → Go → Imports` 中启用了 "Organize Imports on Save"

### Q: 检测不到 .editorconfig
A: 确保 GoLand 安装了 EditorConfig 插件

### Q: golangci-lint 报错
A: 运行 `go mod tidy` 更新依赖
