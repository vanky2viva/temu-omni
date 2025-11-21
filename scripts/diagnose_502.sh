#!/bin/bash
# 502错误快速诊断脚本

echo "=========================================="
echo "🔍 502 Bad Gateway 错误诊断"
echo "=========================================="
echo ""

# 检查是否在项目目录
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 1. 检查容器状态
echo "1️⃣  检查容器状态..."
echo "----------------------------------------"
docker-compose -f docker-compose.prod.yml ps
echo ""

# 检查是否有容器未运行
NOT_RUNNING=$(docker-compose -f docker-compose.prod.yml ps | grep -v "Up" | grep -v "NAME" | grep -v "---" | wc -l)
if [ "$NOT_RUNNING" -gt 0 ]; then
    echo "⚠️  警告: 有容器未运行！"
    echo "尝试启动所有服务..."
    docker-compose -f docker-compose.prod.yml up -d
    sleep 10
    echo ""
fi

# 2. 检查后端服务
echo "2️⃣  检查后端服务..."
echo "----------------------------------------"
if docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-backend.*Up"; then
    echo "✅ 后端容器运行中"
    
    # 测试后端健康检查
    BACKEND_HEALTH=$(docker-compose -f docker-compose.prod.yml exec -T backend curl -s http://localhost:8000/health 2>&1)
    if [ $? -eq 0 ]; then
        echo "✅ 后端服务正常响应: $BACKEND_HEALTH"
    else
        echo "❌ 后端服务无法访问"
        echo "后端日志（最后10行）:"
        docker-compose -f docker-compose.prod.yml logs --tail=10 backend
    fi
else
    echo "❌ 后端容器未运行"
fi
echo ""

# 3. 检查前端服务
echo "3️⃣  检查前端服务..."
echo "----------------------------------------"
if docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-frontend.*Up"; then
    echo "✅ 前端容器运行中"
    
    # 测试前端
    FRONTEND_RESPONSE=$(docker-compose -f docker-compose.prod.yml exec -T frontend curl -s -o /dev/null -w "%{http_code}" http://localhost:80 2>&1)
    if [ "$FRONTEND_RESPONSE" = "200" ] || [ "$FRONTEND_RESPONSE" = "304" ]; then
        echo "✅ 前端服务正常响应 (HTTP $FRONTEND_RESPONSE)"
    else
        echo "❌ 前端服务无法访问 (HTTP $FRONTEND_RESPONSE)"
        echo "前端日志（最后10行）:"
        docker-compose -f docker-compose.prod.yml logs --tail=10 frontend
    fi
else
    echo "❌ 前端容器未运行"
fi
echo ""

# 4. 检查Nginx连接
echo "4️⃣  检查Nginx到后端的连接..."
echo "----------------------------------------"
if docker-compose -f docker-compose.prod.yml ps | grep -q "temu-omni-nginx.*Up"; then
    echo "✅ Nginx容器运行中"
    
    # 测试Nginx到后端的连接
    NGINX_TO_BACKEND=$(docker-compose -f docker-compose.prod.yml exec -T nginx wget -qO- --timeout=5 http://backend:8000/health 2>&1)
    if [ $? -eq 0 ]; then
        echo "✅ Nginx可以连接到后端: $NGINX_TO_BACKEND"
    else
        echo "❌ Nginx无法连接到后端"
        echo "   这可能是502错误的原因！"
    fi
    
    # 测试Nginx到前端的连接
    echo ""
    echo "检查Nginx到前端的连接..."
    NGINX_TO_FRONTEND=$(docker-compose -f docker-compose.prod.yml exec -T nginx wget -qO- --timeout=5 http://frontend:80 2>&1 | head -1)
    if [ $? -eq 0 ]; then
        echo "✅ Nginx可以连接到前端"
    else
        echo "❌ Nginx无法连接到前端"
        echo "   这可能是502错误的原因！"
    fi
else
    echo "❌ Nginx容器未运行"
fi
echo ""

# 5. 检查Nginx配置
echo "5️⃣  检查Nginx配置..."
echo "----------------------------------------"
NGINX_TEST=$(docker-compose -f docker-compose.prod.yml exec -T nginx nginx -t 2>&1)
if echo "$NGINX_TEST" | grep -q "successful"; then
    echo "✅ Nginx配置正确"
else
    echo "❌ Nginx配置有错误:"
    echo "$NGINX_TEST"
fi
echo ""

# 6. 检查端口
echo "6️⃣  检查端口占用..."
echo "----------------------------------------"
PORT_80=$(sudo netstat -tlnp 2>/dev/null | grep :80 | head -1 || sudo ss -tlnp 2>/dev/null | grep :80 | head -1)
if [ -n "$PORT_80" ]; then
    echo "端口80监听情况:"
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

# 7. 查看错误日志
echo "7️⃣  查看最近的错误日志..."
echo "----------------------------------------"
echo "Nginx错误日志（最后5行）:"
docker-compose -f docker-compose.prod.yml logs --tail=5 nginx 2>&1 | grep -i error || echo "  无错误日志"
echo ""

echo "后端错误日志（最后5行）:"
docker-compose -f docker-compose.prod.yml logs --tail=5 backend 2>&1 | grep -i error || echo "  无错误日志"
echo ""

# 8. 总结和建议
echo "=========================================="
echo "📋 诊断总结"
echo "=========================================="
echo ""

# 检查关键问题
ISSUES=0

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

if [ $ISSUES -eq 0 ]; then
    echo "✅ 所有容器都在运行"
    echo ""
    echo "💡 如果仍然出现502错误，请尝试:"
    echo "   1. 重启所有服务: docker-compose -f docker-compose.prod.yml restart"
    echo "   2. 检查防火墙: sudo ufw status"
    echo "   3. 检查云服务器安全组配置"
    echo "   4. 查看详细日志: docker-compose -f docker-compose.prod.yml logs"
else
    echo ""
    echo "⚠️  发现 $ISSUES 个问题，请先解决这些问题"
fi

echo ""
echo "=========================================="


