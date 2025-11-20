#!/bin/bash
# 从Git历史中移除敏感信息的脚本
# 警告：此脚本会重写Git历史，请谨慎使用

set -e

echo "⚠️  警告：此脚本将从Git历史中移除敏感信息"
echo "⚠️  这会重写Git历史，需要强制推送"
echo ""
read -p "是否继续？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 0
fi

# 需要移除的敏感字符串
SENSITIVE_STRINGS=(
    "798478197604e93f6f2ce4c2e833041u"
    "776a96163c56c53e237f5456d4e14765301aa8aa"
    "af5bcf5d4bd5a492fa09c2ee302d75b9"
    "e4f229bb9c4db21daa999e73c8683d42ba0a7094"
    "172.236.231.45"
)

echo ""
echo "正在检查Git历史中的敏感信息..."

# 检查是否有敏感信息
for str in "${SENSITIVE_STRINGS[@]}"; do
    if git log --all --source --full-history -S "$str" | grep -q .; then
        echo "❌ 发现敏感信息: $str"
    fi
done

echo ""
echo "建议使用以下工具从Git历史中移除敏感信息："
echo ""
echo "1. 使用 git-filter-repo (推荐):"
echo "   pip install git-filter-repo"
echo "   git filter-repo --replace-text <(echo '798478197604e93f6f2ce4c2e833041u==>REMOVED')"
echo ""
echo "2. 使用 BFG Repo-Cleaner:"
echo "   java -jar bfg.jar --replace-text passwords.txt"
echo ""
echo "3. 手动重写历史（不推荐，复杂且容易出错）"
echo ""
echo "⚠️  重要："
echo "1. 在清理历史之前，请先轮换所有泄露的凭据"
echo "2. 清理后需要强制推送: git push origin --force --all"
echo "3. 通知所有协作者重新克隆仓库"

