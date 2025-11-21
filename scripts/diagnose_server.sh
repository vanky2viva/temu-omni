#!/bin/bash
# 服务器问题诊断脚本

echo "=========================================="
echo "🔍 Temu-Omni 服务器诊断"
echo "=========================================="
echo ""

# 检查是否在项目目录
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 1. 检查Docker服务
echo "1️⃣  检查Docker服务..."
echo "----------------------------------------"
if systemctl is-active --quiet docker; then
    echo "✅ Docker服务运行中"
else
    echo "❌ Docker服务未运行"
    echo "   启动命令: sudo systemctl start docker"
fi
echo ""

# 2. 检查容器状态
echo "2️⃣  检查容器状态..."
echo "----------------------------------------"
docker-compose -f docker-compose.prod.yml ps
echo ""

# 检查是否有容器未运行
NOT_RUNNING=$(docker-compose -f docker-compose.prod.yml ps | grep -v "Up" | grep -v "NAME" | grep -v "---" | grep -v "CONTAINER" | wc -l)
if [ "$NOT_RUNNING" -gt 0 ]; then
    echo "⚠️  警告: 有容器未运行！"
    echo ""
fi

# 3. 检查环境变量
echo "3️⃣  检查环境变量配置..."
echo "----------------------------------------"
if [ -f ".env.production" ]; then
    echo "✅ 找到 .env.production 文件"
    
    # 检查关键变量
    if grep -q "^SECRET_KEY=" .env.production && ! grep -q "^SECRET_KEY=请生成" .env.production; then
        echo "✅ SECRET_KEY: 已设置"
    else
        echo "❌ SECRET_KEY: 未设置或使用默认值"
    fi
    
    if grep -q "^TEMU_APP_KEY=" .env.production && ! grep -q "^TEMU_APP_KEY=$" .env.production; then
        echo "✅ TEMU_APP_KEY: 已设置"
    else
        echo "❌ TEMU_APP_KEY: 未设置"
    fi
    
    if grep -q "^TEMU_APP_SECRET=" .env.production && ! grep -q "^TEMU_APP_SECRET=$" .env.production; then
        echo "✅ TEMU_APP_SECRET: 已设置"
    else
        echo "❌ TEMU_APP_SECRET: 未设置"
    fi
else
    echo "❌ 未找到 .env.production 文件"
    echo "   创建命令: cp env.production.example .env.production"
fi
echo ""

# 4. 检查端口占用
echo "4️⃣  检查端口占用..."
echo "----------------------------------------"
echo "端口 80:"
PORT_80=$(sudo netstat -tlnp 2>/dev/null | grep :80 || sudo ss -tlnp 2>/dev/null | grep :80)
if [ -n "$PORT_80" ]; then
    echo "$PORT_80"
    if echo "$PORT_80" | grep -q "nginx\|temu-omni-nginx"; then
        echo "✅ 端口80被Nginx占用（正常）"
    else
        echo "⚠️  警告: 端口80被其他服务占用"
    fi
else
    echo "❌ 端口80未被监听"
fi
echo ""

echo "端口 443:"
PORT_443=$(sudo netstat -tlnp 2>/dev/null | grep :443 || sudo ss -tlnp 2>/dev/null | grep :443)
if [ -n "$PORT_443" ]; then
    echo "$PORT_443"
else
    echo "ℹ️  端口443未被监听（如果不需要HTTPS，这是正常的）"
fi
echo ""

# 5. 检查防火墙
echo "5️⃣  检查防火墙状态..."
echo "----------------------------------------"
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(sudo ufw status | head -1)
    echo "$UFW_STATUS"
    if echo "$UFW_STATUS" | grep -q "active"; then
        echo "检查端口规则:"
        sudo ufw status | grep -E "80|443" || echo "  未找到80/443端口规则"
    fi
else
    echo "ℹ️  ufw未安装或未启用"
fi
echo ""

# 6. 检查后端服务
echo "6️⃣  检查后端服务..."
echo "----------------------------------------"
if docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-backend.*Up"; then
    echo "✅ 后端容器运行中"
    
    # 检查后端健康
    BACKEND_HEALTH=$(docker-compose -f docker-compose.prod.yml exec -T backend curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1)
    if [ "$BACKEND_HEALTH" = "200" ]; then
        echo "✅ 后端服务正常响应 (HTTP $BACKEND_HEALTH)"
    else
        echo "❌ 后端服务无法访问 (HTTP $BACKEND_HEALTH)"
        echo "后端日志（最后10行）:"
        docker-compose -f docker-compose.prod.yml logs --tail=10 backend 2>&1 | tail -5
    fi
else
    echo "❌ 后端容器未运行"
    echo "后端日志（最后20行）:"
    docker-compose -f docker-compose.prod.yml logs --tail=20 backend 2>&1 | tail -10
fi
echo ""

# 7. 检查前端服务
echo "7️⃣  检查前端服务..."
echo "----------------------------------------"
if docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-frontend.*Up"; then
    echo "✅ 前端容器运行中"
    
    # 检查前端响应
    FRONTEND_RESPONSE=$(docker-compose -f docker-compose.prod.yml exec -T frontend curl -s -o /dev/null -w "%{http_code}" http://localhost:80 2>&1)
    if [ "$FRONTEND_RESPONSE" = "200" ] || [ "$FRONTEND_RESPONSE" = "304" ]; then
        echo "✅ 前端服务正常响应 (HTTP $FRONTEND_RESPONSE)"
    else
        echo "❌ 前端服务无法访问 (HTTP $FRONTEND_RESPONSE)"
    fi
else
    echo "❌ 前端容器未运行"
fi
echo ""

# 8. 检查Nginx
echo "8️⃣  检查Nginx服务..."
echo "----------------------------------------"
if docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-nginx.*Up"; then
    echo "✅ Nginx容器运行中"
    
    # 测试Nginx配置
    NGINX_TEST=$(docker-compose -f docker-compose.prod.yml exec -T nginx nginx -t 2>&1)
    if echo "$NGINX_TEST" | grep -q "successful"; then
        echo "✅ Nginx配置正确"
    else
        echo "❌ Nginx配置有错误:"
        echo "$NGINX_TEST" | grep -i error
    fi
    
    # 测试Nginx到后端的连接
    echo ""
    echo "测试Nginx到后端连接:"
    NGINX_TO_BACKEND=$(docker-compose -f docker-compose.prod.yml exec -T nginx wget -qO- --timeout=5 http://backend:8000/health 2>&1)
    if [ $? -eq 0 ] && echo "$NGINX_TO_BACKEND" | grep -q "ok\|healthy"; then
        echo "✅ Nginx可以连接到后端"
    else
        echo "❌ Nginx无法连接到后端"
        echo "   这可能是502错误的原因！"
    fi
    
    # 测试Nginx到前端的连接
    echo ""
    echo "测试Nginx到前端连接:"
    NGINX_TO_FRONTEND=$(docker-compose -f docker-compose.prod.yml exec -T nginx wget -qO- --timeout=5 http://frontend:80 2>&1 | head -1)
    if [ $? -eq 0 ]; then
        echo "✅ Nginx可以连接到前端"
    else
        echo "❌ Nginx无法连接到前端"
    fi
else
    echo "❌ Nginx容器未运行"
fi
echo ""

# 9. 检查数据库
echo "9️⃣  检查数据库服务..."
echo "----------------------------------------"
if docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-postgres.*Up"; then
    echo "✅ PostgreSQL容器运行中"
    
    # 测试数据库连接
    DB_CONNECT=$(docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U temu_user -d temu_omni 2>&1)
    if echo "$DB_CONNECT" | grep -q "accepting connections"; then
        echo "✅ 数据库可以连接"
    else
        echo "❌ 数据库连接失败"
    fi
else
    echo "❌ PostgreSQL容器未运行"
fi
echo ""

# 10. 检查网络连接
echo "🔟 检查Docker网络..."
echo "----------------------------------------"
NETWORK_EXISTS=$(docker network ls | grep -q "temu-omni_temu-network" && echo "yes" || echo "no")
if [ "$NETWORK_EXISTS" = "yes" ]; then
    echo "✅ Docker网络存在"
    
    # 检查容器是否在同一网络
    echo "检查容器网络连接:"
    docker network inspect temu-omni_temu-network 2>/dev/null | grep -E "Name|IPv4Address" | head -10
else
    echo "❌ Docker网络不存在"
fi
echo ""

# 11. 检查错误日志
echo "1️⃣1️⃣  检查最近的错误日志..."
echo "----------------------------------------"
echo "Nginx错误日志（最后5行）:"
docker-compose -f docker-compose.prod.yml logs --tail=50 nginx 2>&1 | grep -i error | tail -5 || echo "  无错误日志"
echo ""

echo "后端错误日志（最后5行）:"
docker-compose -f docker-compose.prod.yml logs --tail=50 backend 2>&1 | grep -i error | tail -5 || echo "  无错误日志"
echo ""

# 12. 测试外部访问
echo "1️⃣2️⃣  测试本地访问..."
echo "----------------------------------------"
echo "测试 http://localhost:"
LOCAL_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>&1)
if [ "$LOCAL_TEST" = "200" ]; then
    echo "✅ 本地访问正常 (HTTP $LOCAL_TEST)"
elif [ "$LOCAL_TEST" = "502" ]; then
    echo "❌ 本地访问返回502错误"
    echo "   这表示Nginx无法连接到后端或前端服务"
else
    echo "⚠️  本地访问返回 HTTP $LOCAL_TEST"
fi
echo ""

echo "测试 http://localhost/api/health:"
API_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health 2>&1)
if [ "$API_TEST" = "200" ]; then
    echo "✅ API访问正常 (HTTP $API_TEST)"
else
    echo "❌ API访问失败 (HTTP $API_TEST)"
fi
echo ""

# 总结
echo "=========================================="
echo "📋 诊断总结"
echo "=========================================="
echo ""

ISSUES=0

# 检查关键问题
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-backend.*Up"; then
    echo "❌ 问题: 后端容器未运行"
    echo "   解决: docker-compose -f docker-compose.prod.yml up -d backend"
    ISSUES=$((ISSUES + 1))
fi

if ! docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-frontend.*Up"; then
    echo "❌ 问题: 前端容器未运行"
    echo "   解决: docker-compose -f docker-compose.prod.yml up -d frontend"
    ISSUES=$((ISSUES + 1))
fi

if ! docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-nginx.*Up"; then
    echo "❌ 问题: Nginx容器未运行"
    echo "   解决: docker-compose -f docker-compose.prod.yml up -d nginx"
    ISSUES=$((ISSUES + 1))
fi

if [ ! -f ".env.production" ]; then
    echo "❌ 问题: 环境变量文件不存在"
    echo "   解决: cp env.production.example .env.production && nano .env.production"
    ISSUES=$((ISSUES + 1))
fi

if [ "$LOCAL_TEST" = "502" ]; then
    echo "❌ 问题: 网站返回502错误"
    echo "   可能原因:"
    echo "   1. 后端服务未启动或无法连接"
    echo "   2. 前端服务未启动或无法连接"
    echo "   3. Nginx配置错误"
    echo "   解决: 查看上面的详细诊断信息"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo "✅ 未发现明显问题"
    echo ""
    echo "💡 如果仍有问题，请检查:"
    echo "   1. 云服务器安全组是否开放80/443端口"
    echo "   2. 域名DNS解析是否正确"
    echo "   3. 查看详细日志: docker-compose -f docker-compose.prod.yml logs"
else
    echo ""
    echo "⚠️  发现 $ISSUES 个问题，请根据上面的建议进行修复"
fi

echo ""
echo "=========================================="
echo "📝 详细日志查看命令:"
echo "=========================================="
echo "查看所有日志: docker-compose -f docker-compose.prod.yml logs"
echo "查看后端日志: docker-compose -f docker-compose.prod.yml logs backend"
echo "查看Nginx日志: docker-compose -f docker-compose.prod.yml logs nginx"
echo "查看前端日志: docker-compose -f docker-compose.prod.yml logs frontend"
echo ""


