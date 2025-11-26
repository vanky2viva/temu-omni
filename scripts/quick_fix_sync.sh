#!/bin/bash

# 快速修复同步问题脚本

set -e

echo "=========================================="
echo "  快速修复同步问题"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 获取容器ID
BACKEND_CONTAINER=$(docker ps | grep "temu-omni-backend" | awk '{print $1}' | head -1)
REDIS_CONTAINER=$(docker ps | grep "temu-omni-redis" | awk '{print $1}' | head -1)

if [ -z "$BACKEND_CONTAINER" ]; then
    echo -e "${RED}❌ 后端容器未运行${NC}"
    exit 1
fi

# 1. 清理Redis中的同步进度
if [ ! -z "$REDIS_CONTAINER" ]; then
    echo -e "${YELLOW}[1] 清理Redis中的同步进度...${NC}"
    
    # 查找所有同步进度key
    KEYS=$(docker exec $REDIS_CONTAINER redis-cli -a ${REDIS_PASSWORD:-redis_password} --scan --pattern "sync_progress:*" 2>/dev/null || echo "")
    
    if [ ! -z "$KEYS" ]; then
        echo "$KEYS" | while read key; do
            if [ ! -z "$key" ]; then
                docker exec $REDIS_CONTAINER redis-cli -a ${REDIS_PASSWORD:-redis_password} DEL "$key" >/dev/null 2>&1
                echo "  ✅ 删除: $key"
            fi
        done
        echo -e "${GREEN}✅ 同步进度已清理${NC}"
    else
        echo -e "${GREEN}✅ 没有需要清理的同步进度${NC}"
    fi
    echo ""
fi

# 2. 重启后端服务
echo -e "${YELLOW}[2] 重启后端服务...${NC}"
cd ~/temu-omni || cd /root/temu-omni || { echo -e "${RED}❌ 找不到项目目录${NC}"; exit 1; }

if [ -f "docker-compose.prod.yml" ]; then
    docker-compose -f docker-compose.prod.yml restart backend
    echo -e "${GREEN}✅ 后端服务已重启${NC}"
else
    docker restart $BACKEND_CONTAINER
    echo -e "${GREEN}✅ 后端容器已重启${NC}"
fi

echo ""

# 3. 等待服务启动
echo -e "${YELLOW}[3] 等待服务启动（10秒）...${NC}"
sleep 10

# 检查服务状态
if docker ps | grep -q "temu-omni-backend"; then
    echo -e "${GREEN}✅ 后端服务运行正常${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    echo "   请查看日志: docker logs $BACKEND_CONTAINER"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  修复完成"
echo "==========================================${NC}"
echo ""
echo "下一步："
echo "  1. 刷新浏览器页面"
echo "  2. 重新尝试同步数据"
echo "  3. 如果还有问题，查看日志："
echo "     docker-compose -f docker-compose.prod.yml logs -f backend"
echo ""


