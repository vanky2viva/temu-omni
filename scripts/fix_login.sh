#!/bin/bash
# 快速修复登录问题脚本

set -e

echo "🔧 Temu-Omni 登录问题快速修复"
echo "================================"
echo ""

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker Desktop"
    exit 1
fi

echo "1. 检查并启动数据库服务..."
cd "$(dirname "$0")/.."

# 启动PostgreSQL和Redis
docker compose up -d postgres redis

echo "⏳ 等待数据库服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "2. 检查服务状态..."
if docker ps | grep -q temu-omni-postgres; then
    echo "✓ PostgreSQL 运行中"
else
    echo "✗ PostgreSQL 未运行"
    exit 1
fi

if docker ps | grep -q temu-omni-redis; then
    echo "✓ Redis 运行中"
else
    echo "✗ Redis 未运行"
    exit 1
fi

# 初始化数据库表（如果需要）
echo ""
echo "3. 检查数据库表..."
docker compose exec -T backend python -c "from app.core.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)" 2>/dev/null || true

# 创建默认用户（如果需要）
echo ""
echo "4. 检查默认用户..."
docker compose exec -T backend python scripts/init_default_user.py

# 测试登录
echo ""
echo "5. 测试登录API..."
response=$(curl -s -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=luffyadmin&password=luffy123!@#")

if echo "$response" | grep -q "access_token"; then
    echo "✓ 登录API测试成功"
    echo ""
    echo "✅ 修复完成！现在可以正常登录了"
    echo ""
    echo "默认登录信息："
    echo "  用户名: luffyadmin"
    echo "  密码: luffy123!@#"
else
    echo "✗ 登录API测试失败"
    echo "响应: $response"
    exit 1
fi

