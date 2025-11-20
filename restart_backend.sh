#!/bin/bash
# 重启后端服务以应用代理服务器配置

echo "正在重启后端服务以应用代理服务器配置..."
cd "$(dirname "$0")"

# 检查docker-compose.yml是否存在
if [ ! -f "docker-compose.yml" ]; then
    echo "错误: 未找到 docker-compose.yml 文件"
    exit 1
fi

# 重启后端服务
echo "重启后端容器..."
docker-compose restart backend

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查环境变量
echo ""
echo "检查代理服务器配置..."
docker exec temu-omni-backend env | grep TEMU_API_PROXY_URL || echo "⚠️  未找到 TEMU_API_PROXY_URL 环境变量"

echo ""
echo "✅ 后端服务已重启"
echo ""
echo "如果代理服务器配置仍然未生效，请："
echo "1. 检查 docker-compose.yml 中的 TEMU_API_PROXY_URL 配置"
echo "2. 或者设置环境变量: export TEMU_API_PROXY_URL=http://172.236.231.45:8001"
echo "3. 然后重新启动: docker-compose up -d backend"

