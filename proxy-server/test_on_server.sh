#!/bin/bash

# 在远程服务器上直接测试 API 调用

set -e

echo "=========================================="
echo "🧪 在服务器上测试 Temu API 调用"
echo "=========================================="

# 配置
ACCESS_TOKEN="upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k"
APP_KEY="798478197604e93f6f2ce4c2e833041u"
APP_SECRET="776a96163c56c53e237f5456d4e14765301aa8aa"
API_URL="https://agentpartner.temu.com/api"

echo "API URL: $API_URL"
echo "App Key: $APP_KEY"
echo "Access Token: ${ACCESS_TOKEN:0:20}..."
echo ""

# 检查是否安装了 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，安装中..."
    apt-get update && apt-get install -y python3 python3-pip curl
fi

# 检查是否安装了 requests
if ! python3 -c "import requests" 2>/dev/null; then
    echo "安装 requests 库..."
    pip3 install requests
fi

# 创建测试脚本
cat > /tmp/test_temu_api.py << 'PYTHON_SCRIPT'
import requests
import json
import hashlib
import time
import sys

def generate_sign(app_secret, params):
    """生成签名"""
    temp = []
    sorted_params = sorted(params.items())
    
    for key, value in sorted_params:
        if value is not None:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            temp.append(str(key) + str(value).strip('"'))
    
    un_sign = ''.join(temp)
    un_sign = str(app_secret) + un_sign + str(app_secret)
    sign = hashlib.md5(un_sign.encode('utf-8')).hexdigest().upper()
    return sign

def test_api(api_type, request_data=None, access_token=None):
    """测试 API"""
    app_key = "798478197604e93f6f2ce4c2e833041u"
    app_secret = "776a96163c56c53e237f5456d4e14765301aa8aa"
    api_url = "https://agentpartner.temu.com/api"
    access_token = access_token or "upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k"
    
    timestamp = int(time.time())
    common_params = {
        "app_key": app_key,
        "data_type": "JSON",
        "timestamp": timestamp,
        "type": api_type,
        "version": "V1"
    }
    
    if access_token:
        common_params["access_token"] = access_token
    
    all_params = {**common_params}
    if request_data:
        all_params["request"] = request_data
    
    sign = generate_sign(app_secret, all_params)
    request_payload = {**all_params, "sign": sign}
    
    print(f"\n{'='*80}")
    print(f"测试: {api_type}")
    print(f"{'='*80}")
    print(f"请求参数: {json.dumps(request_payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(
            api_url,
            json=request_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"HTTP 状态码: {response.status_code}")
        print(f"响应内容:")
        
        try:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if response.status_code == 200:
                if result.get("success"):
                    print(f"\n✅ 成功!")
                    return True
                else:
                    error_code = result.get("errorCode", "未知")
                    error_msg = result.get("errorMsg", "未知错误")
                    print(f"\n❌ 业务错误: [{error_code}] {error_msg}")
                    return False
            else:
                print(f"\n❌ HTTP 错误: {response.status_code}")
                return False
        except json.JSONDecodeError:
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*80)
    print("🧪 在服务器上直接测试 Temu API")
    print("="*80)
    
    # 测试 1: 获取 Token 信息
    success1 = test_api("bg.open.accesstoken.info.get")
    
    # 测试 2: 获取商品分类
    success2 = test_api("bg.local.goods.cats.get", {"parentCatId": 0})
    
    # 测试 3: 获取商品列表
    success3 = test_api("bg.local.goods.list.query", {
        "pageNumber": 1,
        "pageSize": 10
    })
    
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"1. 获取 Token 信息: {'✅ 成功' if success1 else '❌ 失败'}")
    print(f"2. 获取商品分类: {'✅ 成功' if success2 else '❌ 失败'}")
    print(f"3. 获取商品列表: {'✅ 成功' if success3 else '❌ 失败'}")
    
    total = sum([success1, success2, success3])
    print(f"\n总计: {total}/3 个测试通过")
    
    sys.exit(0 if total == 3 else 1)
PYTHON_SCRIPT

echo "执行测试脚本..."
python3 /tmp/test_temu_api.py

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="



