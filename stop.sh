#!/bin/bash

# Temu-Omni Docker停止脚本

set -e

echo "🛑 停止 Temu-Omni 服务"
echo "===================="
echo ""

read -p "是否保留数据？(y保留/n删除所有数据) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "停止服务（保留数据）..."
    docker-compose down
    echo "✅ 服务已停止，数据已保留"
else
    echo "⚠️  警告：这将删除所有数据！"
    read -p "确定要删除所有数据吗？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        echo "✅ 服务已停止，所有数据已删除"
    else
        docker-compose down
        echo "✅ 服务已停止，数据已保留"
    fi
fi

echo ""
echo "如需重新启动，请运行: ./start.sh 或 make dev"
echo ""

