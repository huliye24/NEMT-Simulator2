#!/bin/bash
# 云服务器从GitHub拉取代码

REPO="https://github.com/huliye24/NEMT-Simulator2.git"
TARGET_DIR="/root/nemt-workspace"

echo "=========================================="
echo "  从GitHub拉取代码"
echo "=========================================="
echo "仓库: $REPO"
echo "目标: $TARGET_DIR"
echo ""

cd /root

# 如果目录存在则更新，不存在则克隆
if [ -d "$TARGET_DIR/.git" ]; then
    echo "目录已存在，执行更新..."
    cd "$TARGET_DIR"
    git pull origin main
else
    echo "克隆仓库..."
    git clone "$REPO" "$TARGET_DIR"
fi

echo ""
echo "=========================================="
echo "  拉取完成!"
echo "=========================================="

# 显示文件数量
cd "$TARGET_DIR"
FILE_COUNT=$(find . -type f | wc -l)
echo "文件总数: $FILE_COUNT"
