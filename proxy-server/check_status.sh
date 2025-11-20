#!/bin/bash

# 检查代理服务器状态的脚本
# 在远程服务器上运行此脚本来排查问题

set -e

echo "=========================================="
echo "🔍 检查代理服务器状态"
echo "=========================================="

# 检查 Docker 是否运行
echo ""
echo "1. 检查 Docker 服务状态..."
if systemctl is-active --quiet docker; then
    echo "✅ Docker 服务正在运行"
else
    echo "❌ Docker 服务未运行"
    echo "   启动命令: sudo systemctl start docker"
    exit 1
fi

# 检查容器状态
echo ""
echo "2. 检查容器状态..."
if docker ps -a | grep -q temu-api-proxy; then
    echo "容器存在，详细信息："
    docker ps -a | grep temu-api-proxy
    echo ""
    
    # 检查容器是否运行
    if docker ps | grep -q temu-api-proxy; then
        echo "✅ 容器正在运行"
    else
        echo "❌ 容器未运行"
        echo ""
        echo "查看容器日志："
        docker logs temu-api-proxy --tail 50
        echo ""
        echo "启动容器："
        echo "  docker start temu-api-proxy"
        exit 1
    fi
else
    echo "❌ 容器不存在"
    echo "   请先部署代理服务器"
    exit 1
fi

# 检查端口监听
echo ""
echo "3. 检查端口 8001 监听状态..."
if netstat -tlnp 2>/dev/null | grep -q ":8001" || ss -tlnp 2>/dev/null | grep -q ":8001"; then
    echo "✅ 端口 8001 正在监听"
    netstat -tlnp 2>/dev/null | grep ":8001" || ss -tlnp 2>/dev/null | grep ":8001"
else
    echo "❌ 端口 8001 未监听"
    echo "   检查容器端口映射配置"
fi

# 检查容器日志
echo ""
echo "4. 查看容器最近日志（最后 30 行）..."
docker logs temu-api-proxy --tail 30

# 检查容器内部服务
echo ""
echo "5. 检查容器内部服务状态..."
if docker exec temu-api-proxy curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ 容器内部服务正常响应"
    echo "   响应内容："
    docker exec temu-api-proxy curl -s http://localhost:8001/health
else
    echo "❌ 容器内部服务无响应"
    echo "   检查应用是否正常启动"
fi

# 检查防火墙
echo ""
echo "6. 检查防火墙状态..."
if command -v firewall-cmd &> /dev/null; then
    if firewall-cmd --list-ports 2>/dev/null | grep -q "8001"; then
        echo "✅ 防火墙已开放端口 8001"
    else
        echo "⚠️  防火墙可能未开放端口 8001"
        echo "   开放命令: sudo firewall-cmd --add-port=8001/tcp --permanent && sudo firewall-cmd --reload"
    fi
elif command -v ufw &> /dev/null; then
    if ufw status | grep -q "8001"; then
        echo "✅ 防火墙已开放端口 8001"
    else
        echo "⚠️  防火墙可能未开放端口 8001"
        echo "   开放命令: sudo ufw allow 8001/tcp"
    fi
else
    echo "ℹ️  未检测到防火墙管理工具"
fi

# 测试本地连接
echo ""
echo "7. 测试本地连接..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ 本地连接成功"
    curl -s http://localhost:8001/health
else
    echo "❌ 本地连接失败"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="



