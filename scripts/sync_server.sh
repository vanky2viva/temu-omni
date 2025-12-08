#!/bin/bash

# 服务器同步更新脚本
# 用于处理本地更改与远程更新的冲突

set -e

echo "=== 服务器代码同步脚本 ==="
echo ""

# 检查是否有本地更改
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ 工作区干净，直接拉取更新..."
    git pull origin main
    echo "✅ 同步完成！"
    exit 0
fi

echo "⚠️  检测到本地有未提交的更改"
echo ""

# 显示更改的文件
echo "本地更改的文件："
git status --short
echo ""

# 检查是否有冲突文件
CONFLICT_FILE="frontend/src/services/orderCostApi.ts"
if git diff --name-only | grep -q "$CONFLICT_FILE"; then
    echo "⚠️  发现冲突文件: $CONFLICT_FILE"
    echo ""
    
    # 显示本地更改的差异
    echo "本地更改内容："
    git diff "$CONFLICT_FILE" | head -30
    echo ""
    
    # 询问处理方式
    echo "请选择处理方式："
    echo "1. 保留本地更改（暂存后合并，可能需要解决冲突）"
    echo "2. 丢弃本地更改（使用远程版本）"
    echo "3. 查看完整差异后决定"
    echo ""
    read -p "请输入选项 (1/2/3，默认2): " choice
    choice=${choice:-2}
    
    case $choice in
        1)
            echo "📦 暂存本地更改..."
            git stash push -m "本地更改备份 $(date +%Y%m%d_%H%M%S)"
            
            echo "⬇️  拉取远程更新..."
            git pull origin main
            
            echo "🔄 尝试应用本地更改..."
            if git stash pop; then
                echo "✅ 本地更改已成功应用！"
                echo ""
                echo "⚠️  请检查是否有合并冲突，如有冲突请手动解决："
                echo "   git status"
                echo "   # 编辑冲突文件"
                echo "   git add <文件>"
                echo "   git commit -m '解决合并冲突'"
            else
                echo "⚠️  应用本地更改时出现冲突，请手动解决："
                echo "   git status"
                echo "   # 编辑冲突文件"
                echo "   git add <文件>"
                echo "   git stash drop  # 解决冲突后删除stash"
            fi
            ;;
        2)
            echo "🗑️  丢弃本地更改..."
            git checkout -- "$CONFLICT_FILE"
            
            echo "⬇️  拉取远程更新..."
            git pull origin main
            
            echo "✅ 同步完成！本地更改已丢弃。"
            ;;
        3)
            echo "📋 完整差异："
            git diff "$CONFLICT_FILE"
            echo ""
            echo "请手动处理："
            echo "1. 如果需要保留：git stash -> git pull -> git stash pop"
            echo "2. 如果不需要：git checkout -- $CONFLICT_FILE -> git pull"
            exit 0
            ;;
        *)
            echo "❌ 无效选项"
            exit 1
            ;;
    esac
else
    # 有其他文件更改，但不是冲突文件
    echo "📦 暂存所有本地更改..."
    git stash push -m "本地更改备份 $(date +%Y%m%d_%H%M%S)"
    
    echo "⬇️  拉取远程更新..."
    git pull origin main
    
    echo "🔄 恢复本地更改..."
    git stash pop
    
    echo "✅ 同步完成！"
fi

echo ""
echo "=== 同步完成 ==="
echo "当前状态："
git status --short












