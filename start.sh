#!/bin/bash

# Temu-Omni Docker快速启动脚本

set -e

echo "🚀 Temu-Omni 启动脚本"
echo "===================="
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：未检测到Docker，请先安装Docker Desktop"
    echo "下载地址：https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误：未检测到Docker Compose"
    exit 1
fi

echo "✅ Docker环境检查通过"
echo ""

# 检查环境变量文件
if [ ! -f .env.docker ]; then
    echo "📝 未找到 .env.docker 文件，正在创建..."
    cp env.docker.template .env.docker
    echo "⚠️  请编辑 .env.docker 文件，填入您的Temu API密钥"
    echo ""
    echo "TEMU_APP_KEY 和 TEMU_APP_SECRET 必须填写！"
    echo ""
    read -p "是否现在编辑配置文件？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-vim} .env.docker
    else
        echo "请稍后手动编辑 .env.docker 文件"
        exit 0
    fi
fi

echo "✅ 环境变量配置文件已就绪"
echo ""

# 启动Docker服务
echo "🐳 启动Docker服务..."
docker-compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态："
docker-compose ps

echo ""
read -p "是否初始化数据库？(建议首次运行时执行) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗄️  初始化数据库..."
    docker-compose exec -T backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
    echo "✅ 数据库初始化完成"
fi

echo ""
echo "🎉 启动完成！"
echo ""
echo "访问地址："
echo "  前端界面: http://localhost:5173"
echo "  API文档:  http://localhost:8000/docs"
echo "  后端API:  http://localhost:8000"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  或使用:   make dev-logs / make dev-down / make dev-restart"
echo ""
echo "💡 提示：代码修改会自动热更新，无需重启服务"
echo ""

