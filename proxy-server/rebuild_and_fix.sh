#!/bin/bash

# 重新构建并修复代理服务器（解决架构不匹配问题）

set -e

echo "=========================================="
echo "🔧 重新构建并修复代理服务器"
echo "=========================================="

# 配置
PROXY_HOST="${PROXY_HOST:-172.236.231.45}"
PROXY_USER="${PROXY_USER:-root}"

echo "目标服务器: ${PROXY_USER}@${PROXY_HOST}"
echo ""

# 在本地重新构建镜像（指定平台）
echo "1. 在本地重新构建镜像（linux/amd64）..."
cd "$(dirname "$0")"
docker build --platform linux/amd64 -t temu-api-proxy:latest .

# 保存镜像
echo ""
echo "2. 保存镜像..."
docker save temu-api-proxy:latest | gzip > /tmp/temu-api-proxy.tar.gz

# 上传到服务器
echo ""
echo "3. 上传镜像到服务器..."
scp /tmp/temu-api-proxy.tar.gz ${PROXY_USER}@${PROXY_HOST}:/tmp/

# 在服务器上部署
echo ""
echo "4. 在服务器上部署..."
ssh ${PROXY_USER}@${PROXY_HOST} << 'EOF'
set -e

echo "4.1 加载镜像..."
docker load < /tmp/temu-api-proxy.tar.gz

echo ""
echo "4.2 停止并删除旧容器..."
if docker ps -a | grep -q temu-api-proxy; then
    docker stop temu-api-proxy || true
    docker rm temu-api-proxy || true
    echo "✅ 旧容器已删除"
fi

echo ""
echo "4.3 启动新容器（带环境变量）..."
docker run -d \
    --name temu-api-proxy \
    --restart unless-stopped \
    -p 8001:8001 \
    -e TEMU_APP_KEY=798478197604e93f6f2ce4c2e833041u \
    -e TEMU_APP_SECRET=776a96163c56c53e237f5456d4e14765301aa8aa \
    temu-api-proxy:latest

echo ""
echo "4.4 等待服务启动..."
sleep 5

echo ""
echo "4.5 检查容器状态..."
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
echo "4.6 检查服务响应..."
sleep 3
if docker exec temu-api-proxy curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ 服务正常响应"
    echo "健康检查响应："
    docker exec temu-api-proxy curl -s http://localhost:8001/health
else
    echo "⚠️  服务可能还在启动中，查看日志："
    docker logs temu-api-proxy --tail 30
fi

echo ""
echo "4.7 清理临时文件..."
rm -f /tmp/temu-api-proxy.tar.gz

EOF

# 清理本地临时文件
rm -f /tmp/temu-api-proxy.tar.gz

echo ""
echo "=========================================="
echo "✅ 重新构建和部署完成！"
echo "=========================================="
echo "测试命令："
echo "  curl http://${PROXY_HOST}:8001/health"
echo ""




