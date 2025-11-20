#!/bin/bash

# 本地启动 Temu API 代理服务器（用于测试）

set -e

echo "=========================================="
echo "🚀 启动 Temu API 代理服务器（本地测试）"
echo "=========================================="

cd "$(dirname "$0")/backend"

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
pip install -q -r app/proxy/requirements.txt

# 启动代理服务器
echo "🚀 启动代理服务器..."
echo "   访问地址: http://localhost:8001"
echo "   健康检查: http://localhost:8001/health"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

cd app/proxy
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

