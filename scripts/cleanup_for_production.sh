#!/bin/bash
# 生产环境准备脚本 - 清理测试文件和整理文档

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_DIR="$PROJECT_ROOT/archive"

echo "🧹 开始清理项目文件..."

# 创建归档目录
mkdir -p "$ARCHIVE_DIR/scripts/test"
mkdir -p "$ARCHIVE_DIR/scripts/debug"
mkdir -p "$ARCHIVE_DIR/scripts/check"
mkdir -p "$ARCHIVE_DIR/docs/old"

# 移动测试脚本
echo "📦 归档测试脚本..."
cd "$PROJECT_ROOT/backend/scripts"
for file in test_*.py; do
    if [ -f "$file" ]; then
        mv "$file" "$ARCHIVE_DIR/scripts/test/"
        echo "  ✅ 已归档: $file"
    fi
done

# 移动调试脚本
echo "📦 归档调试脚本..."
for file in debug_*.py; do
    if [ -f "$file" ]; then
        mv "$file" "$ARCHIVE_DIR/scripts/debug/"
        echo "  ✅ 已归档: $file"
    fi
done

# 移动检查脚本（保留部分重要脚本）
echo "📦 归档检查脚本..."
for file in check_*.py query_*.py show_*.py list_*.py compare_*.py; do
    if [ -f "$file" ]; then
        # 保留重要的验证脚本
        if [[ "$file" == "verify_order_amount_and_collection.py" ]] || \
           [[ "$file" == "verify_db_empty.py" ]]; then
            echo "  ⏭️  保留: $file"
            continue
        fi
        mv "$file" "$ARCHIVE_DIR/scripts/check/"
        echo "  ✅ 已归档: $file"
    fi
done

# 清理临时文件
echo "🧹 清理临时文件..."
cd "$PROJECT_ROOT"
rm -f *.db *.db-journal
rm -f backend/*.db backend/*.db-journal

echo "✅ 清理完成！"
echo ""
echo "📋 归档位置:"
echo "  - 测试脚本: $ARCHIVE_DIR/scripts/test/"
echo "  - 调试脚本: $ARCHIVE_DIR/scripts/debug/"
echo "  - 检查脚本: $ARCHIVE_DIR/scripts/check/"

