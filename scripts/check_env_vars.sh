#!/bin/bash
# 检查环境变量配置脚本

echo "=========================================="
echo "🔍 环境变量配置检查"
echo "=========================================="
echo ""

# 检查是否在项目目录
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查 .env.production 文件
if [ -f ".env.production" ]; then
    echo "✅ 找到 .env.production 文件"
    echo ""
    echo "检查必需的环境变量:"
    echo "----------------------------------------"
    
    # 检查必需变量
    REQUIRED_VARS=(
        "SECRET_KEY"
        "POSTGRES_PASSWORD"
        "TEMU_APP_KEY"
        "TEMU_APP_SECRET"
        "TEMU_API_PROXY_URL"
    )
    
    MISSING_VARS=()
    
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env.production; then
            value=$(grep "^${var}=" .env.production | cut -d'=' -f2-)
            if [ -z "$value" ] || [ "$value" = "请修改为强密码" ] || [ "$value" = "请生成一个随机的密钥（至少32位）" ]; then
                echo "⚠️  $var: 未设置或使用默认值"
                MISSING_VARS+=("$var")
            else
                # 隐藏敏感信息，只显示前4个字符
                masked_value="${value:0:4}****"
                echo "✅ $var: 已设置 ($masked_value)"
            fi
        else
            echo "❌ $var: 未找到"
            MISSING_VARS+=("$var")
        fi
    done
    
    echo ""
    
    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        echo "⚠️  发现 ${#MISSING_VARS[@]} 个未配置的环境变量:"
        for var in "${MISSING_VARS[@]}"; do
            echo "   - $var"
        done
        echo ""
        echo "请编辑 .env.production 文件并设置这些变量"
    else
        echo "✅ 所有必需的环境变量都已配置"
    fi
else
    echo "❌ 未找到 .env.production 文件"
    echo ""
    echo "请创建 .env.production 文件:"
    echo "  cp env.production.example .env.production"
    echo "  nano .env.production"
fi

echo ""
echo "检查 backend/.env 文件..."
echo "----------------------------------------"
if [ -f "backend/.env" ]; then
    echo "✅ 找到 backend/.env 文件"
    
    # 检查关键变量
    if grep -q "^SECRET_KEY=" backend/.env; then
        echo "✅ SECRET_KEY: 已设置"
    else
        echo "⚠️  SECRET_KEY: 未设置"
    fi
    
    if grep -q "^DATABASE_URL=" backend/.env; then
        echo "✅ DATABASE_URL: 已设置"
    else
        echo "⚠️  DATABASE_URL: 未设置"
    fi
else
    echo "⚠️  未找到 backend/.env 文件"
    echo "  建议创建: cp backend/env.template backend/.env"
fi

echo ""
echo "=========================================="
echo "📋 检查容器环境变量"
echo "=========================================="
echo ""

# 检查后端容器的环境变量
if docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-backend.*Up"; then
    echo "检查后端容器环境变量:"
    echo "----------------------------------------"
    
    SECRET_KEY=$(docker-compose -f docker-compose.prod.yml exec -T backend env | grep "^SECRET_KEY=" | cut -d'=' -f2-)
    if [ -z "$SECRET_KEY" ]; then
        echo "❌ SECRET_KEY: 未设置（这会导致后端无法启动）"
    else
        echo "✅ SECRET_KEY: 已设置"
    fi
    
    DATABASE_URL=$(docker-compose -f docker-compose.prod.yml exec -T backend env | grep "^DATABASE_URL=" | cut -d'=' -f2-)
    if [ -z "$DATABASE_URL" ]; then
        echo "❌ DATABASE_URL: 未设置（这会导致数据库连接失败）"
    else
        echo "✅ DATABASE_URL: 已设置"
    fi
else
    echo "⚠️  后端容器未运行，无法检查环境变量"
fi

echo ""
echo "=========================================="


