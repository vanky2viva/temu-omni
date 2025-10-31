#!/bin/bash

# Temu-Omni 生产环境一键部署脚本
# 包括清理虚拟数据和初始化真实数据库

set -e

echo "======================================"
echo "  Temu-Omni 生产环境完整部署"
echo "  包含：部署 + 清理虚拟数据 + 初始化数据库"
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
    echo -e "${RED}⚠️  请编辑 .env.production 文件，设置安全的密码和密钥！${NC}"
    echo "编辑完成后，重新运行此脚本"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查完成${NC}"
echo ""

# 警告提示
echo -e "${RED}⚠️  警告：此部署将${NC}"
echo "   1. 停止并删除现有容器"
echo "   2. 清空数据库中的所有虚拟数据"
echo "   3. 重新初始化数据库（仅表结构，无数据）"
echo ""
read -p "确认要继续吗？(yes/no): " -n 3 -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo "======================================"
echo "  开始部署流程"
echo "======================================"
echo ""

# 步骤 1: 停止现有容器
echo "步骤 1/7: 停止现有容器..."
docker-compose -f docker-compose.prod.yml down || true
echo -e "${GREEN}✓ 完成${NC}"

# 步骤 2: 拉取最新镜像
echo ""
echo "步骤 2/7: 拉取最新镜像..."
docker-compose -f docker-compose.prod.yml pull || true
echo -e "${GREEN}✓ 完成${NC}"

# 步骤 3: 构建新镜像
echo ""
echo "步骤 3/7: 构建新镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache
echo -e "${GREEN}✓ 完成${NC}"

# 步骤 4: 启动服务
echo ""
echo "步骤 4/7: 启动服务..."
docker-compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✓ 完成${NC}"

# 步骤 5: 等待服务启动
echo ""
echo "步骤 5/7: 等待服务启动..."
sleep 30
echo -e "${GREEN}✓ 完成${NC}"

# 步骤 6: 初始化生产数据库（清理虚拟数据）
echo ""
echo "步骤 6/7: 初始化生产数据库（清理虚拟数据）..."
docker-compose -f docker-compose.prod.yml exec -T backend python scripts/init_production_database.py <<EOF
yes
EOF
echo -e "${GREEN}✓ 完成${NC}"

# 步骤 7: 检查服务状态
echo ""
echo "步骤 7/7: 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps
echo -e "${GREEN}✓ 完成${NC}"

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
echo "下一步：导入真实数据"
echo "  1. 通过 API 同步: 访问 http://echofrog.net/shops"
echo "  2. 通过 Excel 导入: 上传本地文件"
echo "  3. 通过在线表格: 导入飞书表格"
echo ""
echo "健康检查："
curl -s http://localhost/health || echo "  请稍候，服务还在启动中..."
echo ""
echo "查看日志："
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "停止服务："
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
echo -e "${GREEN}🎉 生产部署成功！现在可以开始导入真实数据了。${NC}"
echo ""

