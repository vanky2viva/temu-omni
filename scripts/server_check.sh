#!/bin/bash

# 服务器端快速诊断脚本
# 用于诊断同步进度和订单列表问题

set -e

echo "=========================================="
echo "  服务器端同步问题诊断工具"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 检查服务状态
echo -e "${YELLOW}[1] 检查服务状态...${NC}"
echo ""

# 检查后端容器
if docker ps | grep -q "temu-omni-backend"; then
    BACKEND_CONTAINER=$(docker ps | grep "temu-omni-backend" | awk '{print $1}' | head -1)
    echo -e "${GREEN}✅ 后端容器运行中: $BACKEND_CONTAINER${NC}"
else
    echo -e "${RED}❌ 后端容器未运行${NC}"
    echo "   请执行: docker-compose -f docker-compose.prod.yml ps"
    exit 1
fi

# 检查Redis容器
if docker ps | grep -q "temu-omni-redis"; then
    REDIS_CONTAINER=$(docker ps | grep "temu-omni-redis" | awk '{print $1}' | head -1)
    echo -e "${GREEN}✅ Redis容器运行中: $REDIS_CONTAINER${NC}"
    
    # 测试Redis连接
    if docker exec $REDIS_CONTAINER redis-cli -a ${REDIS_PASSWORD:-redis_password} ping 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✅ Redis连接正常${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis连接测试失败（可能密码不正确）${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Redis容器未运行${NC}"
fi

# 检查数据库容器
if docker ps | grep -q "temu-omni-postgres"; then
    echo -e "${GREEN}✅ 数据库容器运行中${NC}"
else
    echo -e "${YELLOW}⚠️  数据库容器未运行${NC}"
fi

echo ""

# 2. 检查后端日志（最近错误）
echo -e "${YELLOW}[2] 检查后端最近错误日志...${NC}"
echo "--- 最近50行日志中的错误 ---"
docker logs --tail 200 $BACKEND_CONTAINER 2>&1 | grep -iE "error|exception|traceback|failed" | tail -15 || echo "未发现明显错误"
echo ""

# 3. 检查数据库订单数量
echo -e "${YELLOW}[3] 检查数据库订单数量...${NC}"
ORDER_COUNT=$(docker exec $BACKEND_CONTAINER python3 -c "
import os
import sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '')
try:
    from app.core.database import SessionLocal
    from app.models.order import Order
    db = SessionLocal()
    try:
        count = db.query(Order).count()
        print(count)
    finally:
        db.close()
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

if [[ "$ORDER_COUNT" =~ ^[0-9]+$ ]]; then
    if [ "$ORDER_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ 数据库中有 $ORDER_COUNT 个订单${NC}"
    else
        echo -e "${YELLOW}⚠️  数据库中没有订单（可能是正常的，如果还没有同步过）${NC}"
    fi
else
    echo -e "${RED}❌ 查询订单失败: $ORDER_COUNT${NC}"
fi
echo ""

# 4. 检查Redis中的同步进度
echo -e "${YELLOW}[4] 检查Redis中的同步进度...${NC}"
if [ ! -z "$REDIS_CONTAINER" ]; then
    PROGRESS_KEYS=$(docker exec $REDIS_CONTAINER redis-cli -a ${REDIS_PASSWORD:-redis_password} --scan --pattern "sync_progress:*" 2>/dev/null | wc -l)
    if [ "$PROGRESS_KEYS" -gt 0 ]; then
        echo -e "${GREEN}✅ 发现 $PROGRESS_KEYS 个同步进度记录${NC}"
        echo "   进度记录详情:"
        docker exec $REDIS_CONTAINER redis-cli -a ${REDIS_PASSWORD:-redis_password} --scan --pattern "sync_progress:*" 2>/dev/null | head -5 | while read key; do
            VALUE=$(docker exec $REDIS_CONTAINER redis-cli -a ${REDIS_PASSWORD:-redis_password} GET "$key" 2>/dev/null)
            echo "   - $key: ${VALUE:0:100}..."
        done
    else
        echo -e "${YELLOW}⚠️  没有发现同步进度记录${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Redis未运行，无法检查同步进度${NC}"
fi
echo ""

# 5. 检查店铺数据
echo -e "${YELLOW}[5] 检查店铺数据...${NC}"
SHOP_COUNT=$(docker exec $BACKEND_CONTAINER python3 -c "
import os
import sys
sys.path.insert(0, '/app')
try:
    from app.core.database import SessionLocal
    from app.models.shop import Shop
    db = SessionLocal()
    try:
        shops = db.query(Shop).all()
        print(f'{len(shops)}|')
        for shop in shops:
            print(f'  - {shop.shop_name} (ID: {shop.id}, 授权: {bool(shop.access_token)})')
    finally:
        db.close()
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

SHOP_NUM=$(echo "$SHOP_COUNT" | head -1 | cut -d'|' -f1)
if [[ "$SHOP_NUM" =~ ^[0-9]+$ ]]; then
    echo -e "${GREEN}✅ 发现 $SHOP_NUM 个店铺${NC}"
    echo "$SHOP_COUNT" | tail -n +2
else
    echo -e "${RED}❌ 查询店铺失败: $SHOP_COUNT${NC}"
fi
echo ""

# 6. 检查API响应
echo -e "${YELLOW}[6] 测试API响应...${NC}"

# 检查健康检查端点
if curl -s -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API健康检查正常${NC}"
else
    echo -e "${YELLOW}⚠️  API健康检查失败（可能端点不存在）${NC}"
fi

# 检查同步进度API响应时间
echo "测试同步进度API响应..."
for shop_id in 1 2; do
    RESPONSE_TIME=$(timeout 5 curl -s -w "%{time_total}" -o /dev/null "http://localhost:8000/api/sync/shops/$shop_id/progress" 2>&1 || echo "timeout")
    if [ "$RESPONSE_TIME" != "timeout" ]; then
        if [[ "$RESPONSE_TIME" =~ ^[0-9.]+$ ]]; then
            if (( $(echo "$RESPONSE_TIME < 5" | bc -l) )); then
                echo -e "${GREEN}✅ 店铺 $shop_id 同步进度API响应正常 (${RESPONSE_TIME}s)${NC}"
            else
                echo -e "${YELLOW}⚠️  店铺 $shop_id 同步进度API响应较慢 (${RESPONSE_TIME}s)${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  店铺 $shop_id 同步进度API响应异常: $RESPONSE_TIME${NC}"
        fi
    else
        echo -e "${RED}❌ 店铺 $shop_id 同步进度API超时（可能卡住）${NC}"
    fi
done
echo ""

# 7. 清理卡住的同步进度（可选）
echo -e "${YELLOW}[7] 建议操作${NC}"
echo ""
echo "如果同步进度一直卡住，可以尝试："
echo "  1. 清理Redis中的旧同步进度："
echo "     docker exec $REDIS_CONTAINER redis-cli -a \${REDIS_PASSWORD:-redis_password} --scan --pattern 'sync_progress:*' | xargs -I {} docker exec $REDIS_CONTAINER redis-cli -a \${REDIS_PASSWORD:-redis_password} DEL {}"
echo ""
echo "  2. 重启后端服务："
echo "     docker-compose -f docker-compose.prod.yml restart backend"
echo ""
echo "  3. 查看实时日志："
echo "     docker-compose -f docker-compose.prod.yml logs -f backend"
echo ""

# 8. 诊断总结
echo -e "${YELLOW}=========================================="
echo "  诊断总结"
echo "==========================================${NC}"
echo ""
echo "如果发现问题："
echo "  - 同步进度无反应：检查后端日志，可能是同步任务卡住"
echo "  - 没有订单列表：确保已执行过同步操作，检查数据库是否有订单"
echo "  - API超时：检查后端服务是否正常运行，查看日志"
echo ""
echo -e "${GREEN}✅ 诊断完成${NC}"


