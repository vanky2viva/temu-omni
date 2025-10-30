#!/bin/bash

# Temu API 集成一键部署脚本
# 使用方法: ./setup_api_integration.sh

set -e  # 遇到错误立即退出

echo "========================================"
echo "🚀 Temu API 集成部署"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python环境
echo "📋 检查环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 python3，请先安装 Python 3.8+${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 环境正常${NC}"
echo ""

# 切换到backend目录
cd backend

# 检查并安装依赖
echo "========================================"
echo "📦 检查Python依赖"
echo "========================================"
echo ""

if [ -f "requirements.txt" ]; then
    echo "安装依赖包..."
    pip3 install -q -r requirements.txt 2>&1 | grep -v "Requirement already satisfied" || true
    echo -e "${GREEN}✅ 依赖检查完成${NC}"
else
    echo -e "${YELLOW}⚠️  未找到 requirements.txt${NC}"
fi

echo ""
sleep 1

# 步骤1: 数据库迁移
echo "========================================"
echo "📊 步骤 1/4: 数据库迁移"
echo "========================================"
echo ""

if python3 scripts/migrate_add_shop_environment.py; then
    echo -e "${GREEN}✅ 数据库迁移完成${NC}"
else
    echo -e "${RED}❌ 数据库迁移失败${NC}"
    exit 1
fi

echo ""
sleep 2

# 步骤2: 初始化沙盒店铺
echo "========================================"
echo "🏪 步骤 2/4: 初始化沙盒店铺"
echo "========================================"
echo ""

if python3 scripts/init_sandbox_shop.py; then
    echo -e "${GREEN}✅ 沙盒店铺初始化完成${NC}"
else
    echo -e "${RED}❌ 店铺初始化失败${NC}"
    exit 1
fi

echo ""
sleep 2

# 步骤3: 启动后端服务（后台运行）
echo "========================================"
echo "🔧 步骤 3/4: 启动后端服务"
echo "========================================"
echo ""

# 检查是否已有uvicorn进程
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo -e "${YELLOW}⚠️  后端服务已在运行${NC}"
else
    echo "启动后端服务（后台运行）..."
    nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "后端服务 PID: $BACKEND_PID"
    
    # 等待服务启动
    echo "等待服务启动..."
    sleep 5
    
    # 检查服务是否正常
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ 后端服务启动成功${NC}"
        echo "服务地址: http://localhost:8000"
        echo "API文档: http://localhost:8000/docs"
    else
        echo -e "${RED}❌ 后端服务启动失败，请查看日志: logs/backend.log${NC}"
        exit 1
    fi
fi

echo ""
sleep 2

# 步骤4: 同步数据
echo "========================================"
echo "🔄 步骤 4/4: 同步沙盒数据"
echo "========================================"
echo ""

echo "正在同步数据，这可能需要几分钟..."
echo ""

# 验证Token
echo "1️⃣ 验证Token..."
if curl -s -X POST http://localhost:8000/api/sync/shops/1/verify-token | grep -q "success.*true"; then
    echo -e "${GREEN}   ✅ Token验证成功${NC}"
else
    echo -e "${RED}   ❌ Token验证失败${NC}"
    exit 1
fi

sleep 1

# 同步所有数据
echo "2️⃣ 同步订单、商品、分类数据..."
SYNC_RESULT=$(curl -s -X POST "http://localhost:8000/api/sync/shops/1/all?full_sync=false")

if echo "$SYNC_RESULT" | grep -q '"success":true'; then
    echo -e "${GREEN}   ✅ 数据同步成功${NC}"
    
    # 提取统计信息
    echo ""
    echo "   📊 同步统计:"
    echo "$SYNC_RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    results = data.get('data', {}).get('results', {})
    orders = results.get('orders', {})
    print(f\"   - 订单: {orders.get('total', 0)} 条\")
    print(f\"   - 分类: {results.get('categories', 0)} 个\")
except:
    pass
"
else
    echo -e "${YELLOW}   ⚠️  数据同步可能失败，请检查日志${NC}"
fi

echo ""
sleep 1

# 获取同步状态
echo "3️⃣ 获取同步状态..."
STATUS_RESULT=$(curl -s http://localhost:8000/api/sync/shops/1/status)

if echo "$STATUS_RESULT" | grep -q "shop_name"; then
    echo -e "${GREEN}   ✅ 状态获取成功${NC}"
    echo ""
    echo "   📈 当前数据:"
    echo "$STATUS_RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"   - 店铺: {data.get('shop_name', 'N/A')}\")
    print(f\"   - 环境: {data.get('environment', 'N/A')}\")
    print(f\"   - 区域: {data.get('region', 'N/A')}\")
    counts = data.get('data_count', {})
    print(f\"   - 订单数: {counts.get('orders', 0)}\")
    print(f\"   - 商品数: {counts.get('products', 0)}\")
except:
    pass
"
fi

echo ""
echo "========================================"
echo "🎉 集成完成！"
echo "========================================"
echo ""
echo "📍 服务信息:"
echo "   - 后端API: http://localhost:8000"
echo "   - API文档: http://localhost:8000/docs"
echo "   - 健康检查: http://localhost:8000/health"
echo ""
echo "📊 可用功能:"
echo "   - 订单列表: GET /api/orders?shop_id=1"
echo "   - 店铺信息: GET /api/shops/1"
echo "   - 同步状态: GET /api/sync/shops/1/status"
echo ""
echo "🔧 管理命令:"
echo "   - 查看后端日志: tail -f ../logs/backend.log"
echo "   - 停止后端服务: pkill -f 'uvicorn app.main:app'"
echo "   - 重新同步: curl -X POST http://localhost:8000/api/sync/shops/1/all"
echo ""
echo "📚 文档:"
echo "   - 集成指南: ../INTEGRATION_GUIDE.md"
echo "   - API测试: ../QUICKSTART_API.md"
echo ""
echo "✨ 下一步:"
echo "   1. 打开前端应用"
echo "   2. 添加店铺选择器"
echo "   3. 集成同步按钮"
echo ""
echo "========================================"

