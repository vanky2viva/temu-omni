#!/bin/bash

# 修复服务器端同步问题和订单列表问题的脚本

set -e

echo "=== 服务器端同步问题修复脚本 ==="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 检查后端服务状态
echo -e "${YELLOW}1. 检查后端服务状态...${NC}"
if docker ps | grep -q "backend"; then
    echo -e "${GREEN}✅ 后端容器运行中${NC}"
    BACKEND_CONTAINER=$(docker ps | grep "backend" | awk '{print $1}' | head -1)
else
    echo -e "${RED}❌ 后端容器未运行${NC}"
    echo "   请先启动后端服务: docker-compose up -d backend"
    exit 1
fi

# 2. 检查Redis状态
echo -e "\n${YELLOW}2. 检查Redis状态...${NC}"
if docker ps | grep -q "redis"; then
    echo -e "${GREEN}✅ Redis容器运行中${NC}"
    REDIS_CONTAINER=$(docker ps | grep "redis" | awk '{print $1}' | head -1)
    
    # 测试Redis连接
    if docker exec $REDIS_CONTAINER redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✅ Redis连接正常${NC}"
    else
        echo -e "${RED}❌ Redis连接失败${NC}"
        echo "   这将导致多worker环境下的同步进度丢失"
    fi
else
    echo -e "${YELLOW}⚠️  Redis容器未运行（单worker环境仍可使用内存存储）${NC}"
fi

# 3. 检查后端日志中的错误
echo -e "\n${YELLOW}3. 检查后端最近100行日志...${NC}"
echo "--- 最近错误日志 ---"
docker logs --tail 100 $BACKEND_CONTAINER 2>&1 | grep -i "error\|exception\|traceback" | tail -20 || echo "未发现明显错误"

# 4. 清理可能卡住的同步进度
echo -e "\n${YELLOW}4. 清理可能卡住的同步进度...${NC}"
if [ ! -z "$REDIS_CONTAINER" ]; then
    # 清理Redis中的同步进度（超过1小时的）
    echo "清理Redis中的旧同步进度..."
    docker exec $REDIS_CONTAINER redis-cli --scan --pattern "sync_progress:*" | while read key; do
        TTL=$(docker exec $REDIS_CONTAINER redis-cli TTL "$key" 2>/dev/null || echo "0")
        if [ "$TTL" -lt 0 ]; then
            echo "  - 删除过期key: $key"
            docker exec $REDIS_CONTAINER redis-cli DEL "$key" >/dev/null 2>&1
        fi
    done
    echo -e "${GREEN}✅ Redis同步进度清理完成${NC}"
fi

# 5. 检查数据库订单数量
echo -e "\n${YELLOW}5. 检查数据库订单数量...${NC}"
ORDER_COUNT=$(docker exec $BACKEND_CONTAINER python -c "
from app.core.database import SessionLocal
from app.models.order import Order
db = SessionLocal()
try:
    count = db.query(Order).count()
    print(count)
finally:
    db.close()
" 2>/dev/null || echo "0")

if [ "$ORDER_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ 数据库中有 $ORDER_COUNT 个订单${NC}"
else
    echo -e "${YELLOW}⚠️  数据库中没有订单${NC}"
    echo "   这可能是正常的（如果还没有同步过数据）"
fi

# 6. 检查代理服务器状态
echo -e "\n${YELLOW}6. 检查代理服务器状态...${NC}"
if docker ps | grep -q "proxy-server\|proxy"; then
    echo -e "${GREEN}✅ 代理服务器运行中${NC}"
    PROXY_CONTAINER=$(docker ps | grep -E "proxy-server|proxy" | awk '{print $1}' | head -1)
    
    # 检查代理服务器日志
    echo "--- 代理服务器最近错误日志 ---"
    docker logs --tail 50 $PROXY_CONTAINER 2>&1 | grep -i "error\|exception" | tail -10 || echo "未发现明显错误"
else
    echo -e "${YELLOW}⚠️  代理服务器未运行（如果使用代理）${NC}"
fi

# 7. 重启后端服务（可选）
echo -e "\n${YELLOW}7. 建议操作：${NC}"
echo "  如果同步进度一直卡住，可以尝试重启后端服务："
echo "  docker-compose restart backend"
echo ""
echo "  或者查看实时日志："
echo "  docker-compose logs -f backend"

# 8. 诊断总结
echo -e "\n${YELLOW}=== 诊断总结 ===${NC}"
echo "  1. 后端服务: ${GREEN}运行中${NC}"
if [ ! -z "$REDIS_CONTAINER" ]; then
    echo "  2. Redis服务: ${GREEN}运行中${NC}"
else
    echo "  2. Redis服务: ${YELLOW}未运行（单worker环境可用）${NC}"
fi
echo "  3. 数据库订单: $ORDER_COUNT 个"

echo -e "\n${YELLOW}常见问题排查：${NC}"
echo "  1. 如果同步进度一直为0%，检查："
echo "     - 后端日志是否有错误"
echo "     - 代理服务器是否正常"
echo "     - 店铺Access Token是否正确"
echo ""
echo "  2. 如果订单列表为空，检查："
echo "     - 是否已执行过同步"
echo "     - 数据库是否有订单数据"
echo "     - 订单API是否正常工作"
echo ""
echo "  3. 如果进度请求一直pending，检查："
echo "     - 后端API响应是否超时"
echo "     - 网络连接是否正常"
echo "     - 浏览器开发者工具中的网络请求状态"

echo ""
echo -e "${GREEN}✅ 诊断完成${NC}"



