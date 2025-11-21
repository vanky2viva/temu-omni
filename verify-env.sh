#!/bin/bash

# =================================================================
# 环境变量验证脚本
# 用于检查 .env.production 文件是否正确加载
# =================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   环境变量验证${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 .env.production 文件
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ 错误: 找不到 .env.production 文件${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 找到 .env.production 文件${NC}"
echo ""

# 检查必需的环境变量
echo "检查必需的环境变量..."
echo ""

REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "SECRET_KEY"
    "DEFAULT_ADMIN_USERNAME"
    "DEFAULT_ADMIN_PASSWORD"
    "DEFAULT_ADMIN_EMAIL"
    "TEMU_APP_KEY"
    "TEMU_APP_SECRET"
)

MISSING_VARS=()
WEAK_VARS=()

for VAR in "${REQUIRED_VARS[@]}"; do
    VALUE=$(grep "^${VAR}=" .env.production | cut -d'=' -f2-)
    
    if [ -z "$VALUE" ]; then
        MISSING_VARS+=("$VAR")
        echo -e "${RED}❌ $VAR: 未设置${NC}"
    elif [[ "$VALUE" == *"请修改"* ]] || [[ "$VALUE" == *"your_"* ]] || [[ "$VALUE" == *"ChangeMe"* ]]; then
        WEAK_VARS+=("$VAR")
        echo -e "${YELLOW}⚠️  $VAR: 仍使用默认值，请修改${NC}"
    else
        # 显示部分值（隐藏敏感信息）
        MASKED_VALUE=$(echo "$VALUE" | head -c 8)
        if [ ${#VALUE} -gt 8 ]; then
            MASKED_VALUE="${MASKED_VALUE}..."
        fi
        echo -e "${GREEN}✅ $VAR: ${MASKED_VALUE} (长度: ${#VALUE})${NC}"
    fi
done

echo ""

# 检查密码强度
echo "检查密码强度..."
echo ""

# 检查 POSTGRES_PASSWORD
POSTGRES_PASS=$(grep "^POSTGRES_PASSWORD=" .env.production | cut -d'=' -f2-)
if [ ${#POSTGRES_PASS} -lt 16 ]; then
    echo -e "${YELLOW}⚠️  POSTGRES_PASSWORD 长度不足 16 位（当前: ${#POSTGRES_PASS}）${NC}"
else
    echo -e "${GREEN}✅ POSTGRES_PASSWORD 长度足够（${#POSTGRES_PASS} 位）${NC}"
fi

# 检查 REDIS_PASSWORD
REDIS_PASS=$(grep "^REDIS_PASSWORD=" .env.production | cut -d'=' -f2-)
if [ ${#REDIS_PASS} -lt 16 ]; then
    echo -e "${YELLOW}⚠️  REDIS_PASSWORD 长度不足 16 位（当前: ${#REDIS_PASS}）${NC}"
else
    echo -e "${GREEN}✅ REDIS_PASSWORD 长度足够（${#REDIS_PASS} 位）${NC}"
fi

# 检查 SECRET_KEY
SECRET=$(grep "^SECRET_KEY=" .env.production | cut -d'=' -f2-)
if [ ${#SECRET} -lt 32 ]; then
    echo -e "${YELLOW}⚠️  SECRET_KEY 长度不足 32 位（当前: ${#SECRET}）${NC}"
else
    echo -e "${GREEN}✅ SECRET_KEY 长度足够（${#SECRET} 位）${NC}"
fi

echo ""

# 测试 Docker Compose 是否能正确读取环境变量
echo "测试 Docker Compose 环境变量读取..."
echo ""

# 检查 docker-compose.prod.yml 中的 env_file 配置
if ! grep -q "env_file:" docker-compose.prod.yml; then
    echo -e "${RED}❌ 警告: docker-compose.prod.yml 中没有 env_file 配置${NC}"
    echo "   这可能导致环境变量无法正确读取"
else
    echo -e "${GREEN}✅ docker-compose.prod.yml 已配置 env_file${NC}"
fi

# 统计 env_file 配置的服务数量
ENV_FILE_COUNT=$(grep -c "env_file:" docker-compose.prod.yml || echo "0")
echo -e "${GREEN}   配置了 env_file 的服务数量: ${ENV_FILE_COUNT}${NC}"

echo ""

# 最终报告
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   验证结果${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}❌ 缺少必需的环境变量: ${MISSING_VARS[*]}${NC}"
    echo ""
    exit 1
fi

if [ ${#WEAK_VARS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  以下变量仍使用默认值，建议修改:${NC}"
    for VAR in "${WEAK_VARS[@]}"; do
        echo "   - $VAR"
    done
    echo ""
    echo "建议操作:"
    echo "  1. 编辑 .env.production"
    echo "  2. 修改上述变量为安全值"
    echo "  3. 重新运行此脚本验证"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ 所有环境变量配置正确！${NC}"
echo ""

echo "生成密码命令（如需要）："
echo "  数据库密码: openssl rand -base64 32"
echo "  Redis密码:  openssl rand -base64 32"
echo "  Secret Key: python3 -c \"import secrets; print(secrets.token_urlsafe(48))\""
echo ""

echo -e "${GREEN}🎉 环境变量验证通过！可以安全部署。${NC}"
echo ""

