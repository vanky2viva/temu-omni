#!/bin/bash

# 更新代理服务器代码并重启

set -e

# 配置
PROXY_HOST="172.236.231.45"
PROXY_USER="root"
CONTAINER_NAME="temu-api-proxy"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================="
echo "🔄 更新代理服务器代码"
echo "==========================================${NC}"
echo ""

# 读取修改后的代码
echo -e "${GREEN}读取修改后的代码...${NC}"
UPDATED_CODE=$(cat << 'PYTHON_EOF'
        # 合并所有参数
        all_params = {**common_params}
        if request.request_data:
            # 根据官方文档，某些API的参数应该直接放在顶层，而不是在request对象中
            # 例如：bg.order.detail.v2.get 的 parentOrderSn 应该直接放在顶层
            # 检查是否是这些特殊API
            apis_with_top_level_params = [
                "bg.order.detail.v2.get",
                # 可以在这里添加其他需要顶层参数的API
            ]
            
            if request.api_type in apis_with_top_level_params:
                # 对于这些API，将参数直接放在顶层
                all_params.update(request.request_data)
            else:
                # 其他API，业务参数放在 request 字段中
                all_params["request"] = request.request_data
PYTHON_EOF
)

# 在服务器上更新代码
echo -e "${GREEN}在服务器上更新代码...${NC}"
ssh ${PROXY_USER}@${PROXY_HOST} << EOF
set -e

# 检查容器是否存在
if ! docker ps -a | grep -q ${CONTAINER_NAME}; then
    echo "❌ 容器 ${CONTAINER_NAME} 不存在"
    exit 1
fi

# 将代码写入容器
echo "更新容器中的代码..."
docker exec ${CONTAINER_NAME} python3 << 'PYTHON_UPDATE'
import os
import re

# 读取文件
file_path = "/app/app/main.py"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并替换代码段
old_pattern = r'        # 合并所有参数\s+all_params = \{.*?common_params\}\s+if request\.request_data:.*?# 业务参数放在 request 字段中\s+all_params\["request"\] = request\.request_data'

new_code = '''        # 合并所有参数
        all_params = {**common_params}
        if request.request_data:
            # 根据官方文档，某些API的参数应该直接放在顶层，而不是在request对象中
            # 例如：bg.order.detail.v2.get 的 parentOrderSn 应该直接放在顶层
            # 检查是否是这些特殊API
            apis_with_top_level_params = [
                "bg.order.detail.v2.get",
                # 可以在这里添加其他需要顶层参数的API
            ]
            
            if request.api_type in apis_with_top_level_params:
                # 对于这些API，将参数直接放在顶层
                all_params.update(request.request_data)
            else:
                # 其他API，业务参数放在 request 字段中
                all_params["request"] = request.request_data'''

# 替换
if re.search(old_pattern, content, re.DOTALL):
    content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 代码更新成功")
else:
    print("⚠️  未找到匹配的代码段，可能已经更新过了")
    # 检查是否已经包含新代码
    if 'apis_with_top_level_params' in content:
        print("✅ 代码已经是最新的")
    else:
        print("❌ 代码格式可能不同，需要手动更新")
PYTHON_UPDATE

# 重启容器使更改生效
echo "重启容器..."
docker restart ${CONTAINER_NAME}

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查服务状态
if docker ps | grep -q ${CONTAINER_NAME}; then
    echo "✅ 代理服务器已成功更新并重启"
    echo ""
    echo "容器状态:"
    docker ps | grep ${CONTAINER_NAME}
else
    echo "❌ 代理服务器重启失败"
    docker logs --tail=50 ${CONTAINER_NAME}
    exit 1
fi

EOF

echo ""
echo -e "${GREEN}=========================================="
echo "✅ 更新完成！"
echo "==========================================${NC}"
echo ""

