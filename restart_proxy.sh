#!/bin/bash

# 重启 Temu API 代理服务器

set -e

# 配置
PROXY_HOST="172.236.231.45"
PROXY_USER="root"
CONTAINER_NAME="temu-api-proxy"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================="
echo "🔄 重启 Temu API 代理服务器"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}目标服务器: ${PROXY_USER}@${PROXY_HOST}${NC}"
echo -e "${YELLOW}容器名称: ${CONTAINER_NAME}${NC}"
echo ""

# 在服务器上重启容器
echo -e "${GREEN}正在重启代理服务器容器...${NC}"
ssh ${PROXY_USER}@${PROXY_HOST} << EOF
set -e

# 检查容器是否存在
if ! docker ps -a | grep -q ${CONTAINER_NAME}; then
    echo "❌ 容器 ${CONTAINER_NAME} 不存在"
    exit 1
fi

# 重启容器
echo "重启容器 ${CONTAINER_NAME}..."
docker restart ${CONTAINER_NAME}

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查服务状态
if docker ps | grep -q ${CONTAINER_NAME}; then
    echo "✅ 代理服务器已成功重启"
    echo ""
    echo "容器状态:"
    docker ps | grep ${CONTAINER_NAME}
    echo ""
    echo "最近日志:"
    docker logs --tail=20 ${CONTAINER_NAME}
else
    echo "❌ 代理服务器重启失败"
    echo ""
    echo "容器日志:"
    docker logs --tail=50 ${CONTAINER_NAME}
    exit 1
fi

EOF

echo ""
echo -e "${GREEN}=========================================="
echo "✅ 重启完成！"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}测试代理服务器:${NC}"
echo "  curl http://${PROXY_HOST}:8001/health"
echo ""


