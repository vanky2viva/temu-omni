#!/bin/bash

# =================================================================
# 清理开发环境文件脚本
# 在部署到生产环境前运行此脚本
# =================================================================

set -e

echo "🧹 开始清理开发环境文件..."

# 删除 Python 缓存文件
echo "清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true

# 删除测试缓存
echo "清理测试缓存..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

# 删除 OS 临时文件
echo "清理系统临时文件..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true

# 删除日志文件
echo "清理日志文件..."
find . -type f -name "*.log" -delete 2>/dev/null || true

# 删除临时数据库文件
echo "清理临时数据库..."
find . -type f -name "*.db" -not -path "*/alembic/*" -delete 2>/dev/null || true
find . -type f -name "*.sqlite" -delete 2>/dev/null || true
find . -type f -name "*.sqlite3" -delete 2>/dev/null || true

# 删除前端构建缓存
if [ -d "frontend/node_modules" ]; then
    echo "⚠️  frontend/node_modules 存在（保留，Docker构建时会处理）"
fi

# 删除 IDE 配置文件（可选）
# echo "清理 IDE 配置..."
# rm -rf .vscode .idea *.swp *.swo 2>/dev/null || true

echo "✅ 清理完成！"
echo ""
echo "已清理的内容："
echo "  - Python 缓存文件 (__pycache__, *.pyc)"
echo "  - 测试缓存 (.pytest_cache)"
echo "  - 系统临时文件 (.DS_Store, Thumbs.db)"
echo "  - 日志文件 (*.log)"
echo "  - 临时数据库文件 (*.db, *.sqlite)"
echo ""
echo "💡 提示："
echo "  - node_modules 将在 Docker 构建时自动处理"
echo "  - .env 文件已通过 .dockerignore 排除"
echo ""

