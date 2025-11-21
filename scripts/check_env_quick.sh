#!/bin/bash
# 快速检查环境变量配置

echo "=========================================="
echo "🔍 环境变量快速检查"
echo "=========================================="
echo ""

if [ ! -f ".env.production" ]; then
    echo "❌ .env.production 文件不存在"
    exit 1
fi

echo "检查必需的环境变量:"
echo "----------------------------------------"

# 检查变量列表
VARS=(
    "SECRET_KEY"
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "TEMU_APP_KEY"
    "TEMU_APP_SECRET"
    "TEMU_API_PROXY_URL"
)

MISSING=0

for var in "${VARS[@]}"; do
    # 检查变量是否存在且不为空
    value=$(grep "^${var}=" .env.production 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//')
    
    if [ -z "$value" ] || [ "$value" = "请修改为强密码" ] || [ "$value" = "请生成一个随机的密钥（至少32位）" ] || [ "$value" = "your_app_key_here" ] || [ "$value" = "your_app_secret_here" ]; then
        echo "❌ $var: 未设置或使用默认值"
        MISSING=$((MISSING + 1))
    else
        # 显示前4个字符，隐藏敏感信息
        if [ ${#value} -gt 4 ]; then
            masked="${value:0:4}****"
        else
            masked="****"
        fi
        echo "✅ $var: 已设置 ($masked)"
    fi
done

echo ""
echo "检查可选的环境变量:"
echo "----------------------------------------"

OPTIONAL_VARS=(
    "TEMU_CN_APP_KEY"
    "TEMU_CN_APP_SECRET"
)

for var in "${OPTIONAL_VARS[@]}"; do
    value=$(grep "^${var}=" .env.production 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//')
    if [ -n "$value" ] && [ "$value" != "your_cn_app_key_here" ] && [ "$value" != "your_cn_app_secret_here" ]; then
        masked="${value:0:4}****"
        echo "✅ $var: 已设置 ($masked)"
    else
        echo "ℹ️  $var: 未设置（可选）"
    fi
done

echo ""
echo "=========================================="
if [ $MISSING -eq 0 ]; then
    echo "✅ 所有必需的环境变量都已配置"
    echo ""
    echo "💡 如果容器仍有问题，请重启服务:"
    echo "   docker-compose -f docker-compose.prod.yml down"
    echo "   docker-compose -f docker-compose.prod.yml up -d"
else
    echo "⚠️  发现 $MISSING 个未配置的环境变量"
    echo ""
    echo "请编辑 .env.production 文件并设置这些变量:"
    echo "   nano .env.production"
fi
echo "=========================================="


