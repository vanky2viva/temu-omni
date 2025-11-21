#!/bin/bash
# 更新代码并重新构建Docker镜像

echo "=========================================="
echo "🔄 更新代码并重新构建"
echo "=========================================="
echo ""

cd /home/ubuntu/temu-omni || exit 1

# 1. 拉取最新代码
echo "1️⃣  拉取最新代码..."
git pull
echo ""

# 2. 停止服务
echo "2️⃣  停止服务..."
docker-compose -f docker-compose.prod.yml down
echo ""

# 3. 重新构建镜像（不缓存）
echo "3️⃣  重新构建镜像..."
echo "   这可能需要几分钟..."
docker-compose -f docker-compose.prod.yml build --no-cache
echo ""

# 4. 启动服务
echo "4️⃣  启动服务..."
docker-compose -f docker-compose.prod.yml up -d
echo ""

# 5. 等待服务启动
echo "5️⃣  等待服务启动..."
sleep 30
echo ""

# 6. 检查服务状态
echo "6️⃣  检查服务状态..."
docker-compose -f docker-compose.prod.yml ps
echo ""

echo "=========================================="
echo "✅ 更新完成！"
echo "=========================================="
echo ""
echo "💡 如果前端仍显示旧版本，请："
echo "   1. 清除浏览器缓存 (Ctrl+Shift+Delete)"
echo "   2. 或使用无痕模式访问"
echo "   3. 或强制刷新 (Ctrl+F5)"
echo ""


