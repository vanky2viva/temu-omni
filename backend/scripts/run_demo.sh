#!/bin/bash

# 演示数据生成脚本

echo "🎬 Temu-Omni 演示数据生成"
echo "=========================="
echo ""

# 检查是否在Docker容器中
if [ -f /.dockerenv ]; then
    echo "✅ 在Docker容器中运行"
    python /app/scripts/generate_demo_data.py
else
    echo "📍 在本地环境运行"
    
    # 检查是否在backend目录
    if [ ! -f "app/main.py" ]; then
        echo "❌ 错误：请在backend目录下运行此脚本"
        echo "   cd backend && ./scripts/run_demo.sh"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "⚠️  警告：未检测到虚拟环境，尝试激活..."
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        elif [ -f "../venv/bin/activate" ]; then
            source ../venv/bin/activate
        else
            echo "❌ 未找到虚拟环境，请先创建并激活"
            exit 1
        fi
    fi
    
    python scripts/generate_demo_data.py
fi

echo ""
echo "✨ 完成！现在可以访问系统查看演示数据"
echo ""

