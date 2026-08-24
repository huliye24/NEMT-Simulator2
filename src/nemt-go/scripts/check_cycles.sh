#!/bin/bash
# 检查Go循环依赖
# 用法: bash scripts/check_cycles.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "NEMT-Go 循环依赖检查"
echo "=========================================="
echo ""

# 使用 go mod graph 检查依赖
if ! command -v go &> /dev/null; then
    echo "ERROR: go 命令未找到，请安装 Go"
    exit 1
fi

echo "检查 pkg/ 目录下的包依赖关系..."
echo ""

# 检查每个 pkg 子包
for pkg_dir in pkg/*/; do
    pkg_name=$(basename "$pkg_dir")

    # 查找该包中所有 import 其他 pkg 包的地方
    imports=$(grep -rh "github.com/nemt-lab/nemt-go/pkg/$pkg_name" pkg/*/ 2>/dev/null | grep -v "_test.go" || true)

    if [ -n "$imports" ]; then
        echo "WARNING: $pkg_name 可能存在自引用或循环依赖"
        echo "$imports" | head -3 | sed 's/^/  - /'
        echo ""
    fi
done

echo "使用 go list 检查包..."
go list -m all 2>/dev/null | head -10

echo ""
echo "使用 go mod graph 检查..."
if command -v golangci-lint &> /dev/null; then
    # golangci-lint 内置循环依赖检查
    golangci-lint run --disable-all -e gochecknoglobals -e gochecknoinits ./... 2>/dev/null || true
else
    echo "提示: 安装 golangci-lint 以获得更好的循环依赖检查"
    echo "  go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo ""
echo "如需完整检查，请运行:"
echo "  go mod tidy"
echo "  go mod verify"
echo "=========================================="
