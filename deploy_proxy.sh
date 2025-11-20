#!/bin/bash

# Temu API 代理服务器部署脚本
# 用于在白名单 IP 服务器上部署代理服务

set -e

echo "=========================================="
echo "🚀 部署 Temu API 代理服务器"
echo "=========================================="

# 配置
PROXY_HOST="172.236.231.45"
PROXY_PORT="8001"
PROXY_USER="root"
PROXY_DIR="/opt/temu-api-proxy"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}目标服务器: ${PROXY_USER}@${PROXY_HOST}${NC}"
echo -e "${YELLOW}部署目录: ${PROXY_DIR}${NC}"
echo ""

# 检查本地 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ 错误: Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 构建代理服务器镜像（指定平台为 linux/amd64）
echo -e "${GREEN}📦 构建代理服务器 Docker 镜像（linux/amd64）...${NC}"
cd "$(dirname "$0")/proxy-server"
docker build --platform linux/amd64 -t temu-api-proxy:latest .

# 保存镜像为 tar 文件
echo -e "${GREEN}💾 保存镜像为 tar 文件...${NC}"
docker save temu-api-proxy:latest | gzip > /tmp/temu-api-proxy.tar.gz

# 上传到服务器
echo -e "${GREEN}📤 上传镜像到服务器...${NC}"
scp /tmp/temu-api-proxy.tar.gz ${PROXY_USER}@${PROXY_HOST}:/tmp/

# 在服务器上部署
echo -e "${GREEN}🔧 在服务器上部署...${NC}"
ssh ${PROXY_USER}@${PROXY_HOST} << EOF
set -e

# 创建部署目录
mkdir -p ${PROXY_DIR}

# 加载镜像
echo "加载 Docker 镜像..."
docker load < /tmp/temu-api-proxy.tar.gz

# 停止并删除旧容器（如果存在）
if docker ps -a | grep -q temu-api-proxy; then
    echo "停止旧容器..."
    docker stop temu-api-proxy || true
    docker rm temu-api-proxy || true
fi

# 启动新容器
echo "启动代理服务器容器..."
docker run -d \\
    --name temu-api-proxy \\
    --restart unless-stopped \\
    -p ${PROXY_PORT}:8001 \\
    -e TEMU_APP_KEY=${TEMU_APP_KEY:-798478197604e93f6f2ce4c2e833041u} \\
    -e TEMU_APP_SECRET=${TEMU_APP_SECRET:-776a96163c56c53e237f5456d4e14765301aa8aa} \\
    temu-api-proxy:latest

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查服务状态
if docker ps | grep -q temu-api-proxy; then
    echo "✅ 代理服务器已成功启动"
    docker ps | grep temu-api-proxy
else
    echo "❌ 代理服务器启动失败"
    docker logs temu-api-proxy
    exit 1
fi

# 清理临时文件
rm -f /tmp/temu-api-proxy.tar.gz

EOF

# 清理本地临时文件
rm -f /tmp/temu-api-proxy.tar.gz

echo ""
echo -e "${GREEN}=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo -e "代理服务器地址: http://${PROXY_HOST}:${PROXY_PORT}${NC}"
echo -e "${YELLOW}测试命令:${NC}"
echo "  python test_proxy.py --mode proxy"
echo ""

