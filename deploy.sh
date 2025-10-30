#!/bin/bash

# Temu-Omni 生产环境部署脚本
# 用于部署到 echofrog.net

set -e

echo "======================================"
echo "  Temu-Omni 生产环境部署"
echo "  域名: echofrog.net"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否在正确的目录
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ 错误: 找不到 docker-compose.prod.yml 文件${NC}"
    echo "请在项目根目录运行此脚本"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️  警告: 未找到 .env.production 文件${NC}"
    echo "正在从模板创建..."
    cp env.production.example .env.production
    echo -e "${YELLOW}⚠️  请编辑 .env.production 文件，设置安全的密码和密钥！${NC}"
    echo "编辑完成后，重新运行此脚本"
    exit 1
fi

# 生成随机密钥（如果需要）
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

echo -e "${GREEN}✅ 环境检查完成${NC}"
echo ""

# 询问是否继续
read -p "是否继续部署? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo "步骤 1/6: 停止现有容器..."
docker-compose -f docker-compose.prod.yml down || true

echo ""
echo "步骤 2/6: 拉取最新镜像..."
docker-compose -f docker-compose.prod.yml pull || true

echo ""
echo "步骤 3/6: 构建新镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo ""
echo "步骤 4/6: 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "步骤 5/6: 等待服务启动..."
sleep 10

echo ""
echo "步骤 6/6: 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "======================================"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "======================================"
echo ""
echo "访问地址："
echo "  前端: http://echofrog.net"
echo "  后端API: http://echofrog.net/api"
echo "  API文档: http://echofrog.net/docs"
echo ""
echo "健康检查："
echo "  curl http://echofrog.net/health"
echo ""
echo "查看日志："
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "停止服务："
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""

# 可选：测试健康检查
echo "正在测试健康检查..."
sleep 5
if curl -s http://localhost/health > /dev/null; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  健康检查失败，请检查日志${NC}"
fi

echo ""
echo -e "${GREEN}部署成功！${NC}"
echo ""

