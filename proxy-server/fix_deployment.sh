#!/bin/bash

# 修复已部署的代理服务器（添加环境变量并重启）

set -e

echo "=========================================="
echo "🔧 修复代理服务器部署"
echo "=========================================="

# 配置
PROXY_HOST="${PROXY_HOST:-172.236.231.45}"
PROXY_USER="${PROXY_USER:-root}"

echo "目标服务器: ${PROXY_USER}@${PROXY_HOST}"
echo ""

# 在服务器上执行修复
ssh ${PROXY_USER}@${PROXY_HOST} << 'EOF'
set -e

echo "1. 停止并删除旧容器..."
if docker ps -a | grep -q temu-api-proxy; then
    docker stop temu-api-proxy || true
    docker rm temu-api-proxy || true
    echo "✅ 旧容器已删除"
else
    echo "ℹ️  未找到旧容器"
fi

echo ""
echo "2. 检查镜像是否存在..."
if ! docker images | grep -q temu-api-proxy; then
    echo "❌ 镜像不存在，需要先构建或加载镜像"
    echo "   请在本地执行: ./deploy_proxy.sh"
    exit 1
fi

echo ""
echo "3. 启动新容器（带环境变量）..."
docker run -d \
    --name temu-api-proxy \
    --restart unless-stopped \
    --platform linux/amd64 \
    -p 8001:8001 \
    -e TEMU_APP_KEY=798478197604e93f6f2ce4c2e833041u \
    -e TEMU_APP_SECRET=776a96163c56c53e237f5456d4e14765301aa8aa \
    temu-api-proxy:latest

echo ""
echo "4. 等待服务启动..."
sleep 5

echo ""
echo "5. 检查容器状态..."
if docker ps | grep -q temu-api-proxy; then
    echo "✅ 容器正在运行"
    docker ps | grep temu-api-proxy
else
    echo "❌ 容器启动失败"
    echo "查看日志："
    docker logs temu-api-proxy --tail 50
    exit 1
fi

echo ""
echo "6. 检查服务响应..."
sleep 3
if docker exec temu-api-proxy curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ 服务正常响应"
    echo "健康检查响应："
    docker exec temu-api-proxy curl -s http://localhost:8001/health
else
    echo "❌ 服务无响应"
    echo "查看日志："
    docker logs temu-api-proxy --tail 30
    exit 1
fi

echo ""
echo "7. 检查端口监听..."
if netstat -tlnp 2>/dev/null | grep -q ":8001" || ss -tlnp 2>/dev/null | grep -q ":8001"; then
    echo "✅ 端口 8001 正在监听"
else
    echo "⚠️  端口 8001 未监听，检查端口映射"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo "测试命令："
echo "  curl http://172.236.231.45:8001/health"
echo ""

EOF

echo ""
echo "✅ 修复脚本执行完成"
echo ""
echo "现在可以测试："
echo "  curl http://${PROXY_HOST}:8001/health"
echo ""

