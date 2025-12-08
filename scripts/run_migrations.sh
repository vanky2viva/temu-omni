#!/bin/bash

# 服务器端数据库迁移脚本
# 用于检查和运行数据库迁移

set -e

echo "=========================================="
echo "  数据库迁移工具"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查后端容器
BACKEND_CONTAINER=$(docker ps | grep "temu-omni-backend" | awk '{print $1}' | head -1)

if [ -z "$BACKEND_CONTAINER" ]; then
    echo -e "${RED}❌ 后端容器未运行${NC}"
    echo "   请先启动后端服务: docker-compose -f docker-compose.prod.yml up -d backend"
    exit 1
fi

echo -e "${GREEN}✅ 后端容器: $BACKEND_CONTAINER${NC}"
echo ""

# 1. 检查当前迁移版本
echo -e "${YELLOW}[1] 检查当前数据库迁移版本...${NC}"
CURRENT_VERSION=$(docker exec $BACKEND_CONTAINER alembic current 2>&1 || echo "error")

if [[ "$CURRENT_VERSION" == *"error"* ]] || [[ "$CURRENT_VERSION" == *"Target database is not up to date"* ]]; then
    echo -e "${YELLOW}⚠️  无法获取当前版本，可能数据库未初始化迁移${NC}"
    echo "$CURRENT_VERSION"
    CURRENT_VERSION=""
else
    if [ -z "$CURRENT_VERSION" ] || [[ "$CURRENT_VERSION" == *"(empty)"* ]]; then
        echo -e "${YELLOW}⚠️  数据库未应用任何迁移${NC}"
    else
        echo -e "${GREEN}✅ 当前版本:${NC}"
        echo "$CURRENT_VERSION"
    fi
fi
echo ""

# 2. 检查待执行的迁移
echo -e "${YELLOW}[2] 检查待执行的迁移...${NC}"
PENDING_MIGRATIONS=$(docker exec $BACKEND_CONTAINER alembic heads 2>&1)
HEAD_VERSION=$(echo "$PENDING_MIGRATIONS" | grep -oP '(?<=\(head\): )\w+' | head -1)

if [ ! -z "$HEAD_VERSION" ]; then
    echo -e "${GREEN}✅ 最新迁移版本: $HEAD_VERSION${NC}"
    
    # 检查是否有待执行的迁移
    HISTORY=$(docker exec $BACKEND_CONTAINER alembic history 2>&1)
    echo "迁移历史:"
    echo "$HISTORY" | head -20
else
    echo -e "${YELLOW}⚠️  无法获取最新迁移版本${NC}"
    echo "$PENDING_MIGRATIONS"
fi
echo ""

# 3. 检查数据库表结构
echo -e "${YELLOW}[3] 检查数据库表结构...${NC}"
TABLES=$(docker exec $BACKEND_CONTAINER python3 -c "
import os
import sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '')
try:
    from app.core.database import engine
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for table in sorted(tables):
        print(table)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

if [[ "$TABLES" == *"ERROR"* ]]; then
    echo -e "${RED}❌ 查询数据库表失败: $TABLES${NC}"
else
    TABLE_COUNT=$(echo "$TABLES" | grep -v "^$" | wc -l)
    echo -e "${GREEN}✅ 数据库中有 $TABLE_COUNT 个表${NC}"
    echo "表列表:"
    echo "$TABLES" | grep -v "^$" | head -20
fi
echo ""

# 4. 检查关键表是否存在
echo -e "${YELLOW}[4] 检查关键表是否存在...${NC}"
REQUIRED_TABLES=("shops" "orders" "products" "users" "import_history")
MISSING_TABLES=()

for table in "${REQUIRED_TABLES[@]}"; do
    if echo "$TABLES" | grep -q "^${table}$"; then
        echo -e "${GREEN}✅ 表 $table 存在${NC}"
    else
        echo -e "${RED}❌ 表 $table 不存在${NC}"
        MISSING_TABLES+=("$table")
    fi
done
echo ""

# 5. 检查shops表的字段
echo -e "${YELLOW}[5] 检查shops表的字段...${NC}"
SHOP_COLUMNS=$(docker exec $BACKEND_CONTAINER python3 -c "
import os
import sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '')
try:
    from app.core.database import engine
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # 检查shops表是否存在
    tables = inspector.get_table_names()
    if 'shops' in tables:
        columns = inspector.get_columns('shops')
        for col in columns:
            print(f\"{col['name']}: {col['type']}\")
    else:
        print('ERROR: shops table not found')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

if [[ "$SHOP_COLUMNS" == *"ERROR"* ]]; then
    echo -e "${RED}❌ 查询shops表字段失败: $SHOP_COLUMNS${NC}"
else
    echo -e "${GREEN}✅ shops表字段:${NC}"
    echo "$SHOP_COLUMNS"
    
    # 检查关键字段
    if echo "$SHOP_COLUMNS" | grep -q "cn_access_token"; then
        echo -e "${GREEN}✅ CN API字段已存在${NC}"
    else
        echo -e "${YELLOW}⚠️  CN API字段不存在，需要运行迁移${NC}"
    fi
fi
echo ""

# 6. 询问是否运行迁移
if [ ${#MISSING_TABLES[@]} -gt 0 ] || [[ "$SHOP_COLUMNS" == *"ERROR"* ]] || ! echo "$SHOP_COLUMNS" | grep -q "cn_access_token"; then
    echo -e "${YELLOW}[6] 发现数据库结构问题，建议运行迁移${NC}"
    echo ""
    read -p "是否立即运行数据库迁移? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${YELLOW}正在运行数据库迁移...${NC}"
        
        # 运行迁移
        MIGRATION_OUTPUT=$(docker exec $BACKEND_CONTAINER alembic upgrade head 2>&1)
        
        if [[ "$MIGRATION_OUTPUT" == *"Running upgrade"* ]] || [[ "$MIGRATION_OUTPUT" == *"INFO"* ]]; then
            echo -e "${GREEN}✅ 迁移执行成功${NC}"
            echo "$MIGRATION_OUTPUT"
        elif [[ "$MIGRATION_OUTPUT" == *"Target database is already up to date"* ]]; then
            echo -e "${GREEN}✅ 数据库已是最新版本${NC}"
        else
            echo -e "${RED}❌ 迁移执行失败:${NC}"
            echo "$MIGRATION_OUTPUT"
            exit 1
        fi
    else
        echo -e "${YELLOW}跳过迁移${NC}"
    fi
else
    echo -e "${GREEN}[6] 数据库结构正常，无需迁移${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  迁移检查完成"
echo "==========================================${NC}"
echo ""












