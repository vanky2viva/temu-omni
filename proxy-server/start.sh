#!/bin/bash

# 本地启动脚本（不使用 Docker）

set -e

echo "=========================================="
echo "🚀 启动 Temu API 代理服务器（本地）"
echo "=========================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -q -r requirements.txt

# 启动代理服务器
echo "🚀 启动代理服务器..."
echo "   访问地址: http://localhost:8001"
echo "   健康检查: http://localhost:8001/health"
echo "   API 文档: http://localhost:8001/docs"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload



