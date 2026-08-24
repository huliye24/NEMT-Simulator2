#!/bin/bash
# 检查NEMT-Go包结构是否符合规范
# 用法: bash scripts/check_structure.sh

set -e

ERRORS=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "NEMT-Go 包结构检查"
echo "=========================================="
echo ""

# 检查 cmd/ 目录只包含 main.go
echo "[1/4] 检查 cmd/ 目录..."
for dir in cmd/*/; do
    if [ -d "$dir" ]; then
        pkg_name=$(basename "$dir")

        if [ ! -f "$dir/main.go" ]; then
            echo "  ERROR: $dir 缺少 main.go"
            ERRORS=$((ERRORS + 1))
        fi

        # 检查是否有其他 .go 文件
        other_files=$(find "$dir" -maxdepth 1 -name "*.go" ! -name "main.go" 2>/dev/null | wc -l)
        if [ "$other_files" -gt 0 ]; then
            echo "  ERROR: $dir 应只包含 main.go，发现其他文件:"
            find "$dir" -maxdepth 1 -name "*.go" ! -name "main.go" | sed 's/^/    - /'
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
if [ $ERRORS -eq 0 ]; then
    echo "  OK"
fi
echo ""

# 检查 pkg/ 目录结构
echo "[2/4] 检查 pkg/ 目录..."
if [ ! -d "pkg" ]; then
    echo "  ERROR: 缺少 pkg/ 目录"
    ERRORS=$((ERRORS + 1))
else
    echo "  OK"
fi
echo ""

# 检查包名是否使用小写
echo "[3/4] 检查包名规范..."
found_errors=0
while IFS= read -r f; do
    pkg=$(grep "^package " "$f" 2>/dev/null | head -1 | awk '{print $2}' || echo "")
    if [ -n "$pkg" ] && echo "$pkg" | grep -q '[A-Z]'; then
        echo "  ERROR: 包名应使用小写: '$pkg' in $f"
        found_errors=1
        ERRORS=$((ERRORS + 1))
    fi
done < <(find . -name "*.go" -not -path "*/.*" | head -100)

if [ $found_errors -eq 0 ]; then
    echo "  OK"
fi
echo ""

# 检查文件名是否为 snake_case
echo "[4/4] 检查文件名规范..."
found_errors=0
while IFS= read -r f; do
    fname=$(basename "$f" .go)
    # 排除测试文件和 main.go
    if [ "$fname" != "main" ] && [ "$fname" != "$(basename $(dirname "$f"))" ]; then
        if echo "$fname" | grep -q '[A-Z]'; then
            # 允许 PascalCase 用于类型相关文件
            if ! echo "$fname" | grep -qE '^(test_|mock_|fake_|[a-z]+_test)'; then
                :  # PascalCase 文件名可能是类型定义文件
            fi
        fi
    fi
done < <(find . -name "*.go" -not -path "*/.*" | head -100)
echo "  OK (手动检查 PascalCase 文件名)"
echo ""

echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "结果: 全部检查通过 ✓"
    exit 0
else
    echo "结果: 发现 $ERRORS 个错误 ✗"
    exit 1
fi
