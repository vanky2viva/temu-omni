"""
Temu Open API 详细测试脚本
测试不同的API接口，包括需要和不需要access_token的接口
"""
import os
import time
import hashlib
import json
import requests


def api_sign_method(app_secret, request_params):
    """
    Temu官方MD5签名算法
    """
    temp = []
    request_params = sorted(request_params.items())
    for k, v in request_params:
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
        temp.append(str(k) + str(v).strip('\"'))
    
    un_sign = ''.join(temp)
    un_sign = str(app_secret) + un_sign + str(app_secret)
    sign = hashlib.md5(un_sign.encode('utf-8')).hexdigest().upper()
    return sign


def call_temu_api(app_key, app_secret, api_type, request_data=None, access_token=None):
    """
    调用Temu API的通用方法
    """
    base_url = "https://openapi-b-us.temu.com/openapi/router"
    
    # 通用参数
    timestamp = int(time.time())
    common_params = {
        "app_key": app_key,
        "data_type": "JSON",
        "timestamp": timestamp,
        "type": api_type,
        "version": "V1"
    }
    
    # 添加access_token（如果提供）
    if access_token:
        common_params["access_token"] = access_token
    
    # 添加请求参数
    all_params = {**common_params}
    if request_data:
        all_params["request"] = request_data
    
    # 生成签名
    sign = api_sign_method(app_secret, all_params)
    
    # 最终请求体
    request_payload = {**all_params, "sign": sign}
    
    # 发送请求
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            base_url,
            headers=headers,
            data=json.dumps(request_payload),
            timeout=30
        )
        return {
            "status_code": response.status_code,
            "response": response.json()
        }
    except Exception as e:
        return {
            "status_code": 0,
            "error": str(e)
        }


def print_result(title, result):
    """
    打印测试结果
    """
    print("\n" + "="*80)
    print(f"📌 {title}")
    print("="*80)
    
    if "error" in result:
        print(f"❌ 请求失败: {result['error']}")
    else:
        print(f"📥 状态码: {result['status_code']}")
        print(f"📄 响应:")
        print(json.dumps(result['response'], indent=4, ensure_ascii=False))
        
        response = result['response']
        if response.get('success'):
            print("\n✅ 请求成功！")
        else:
            error_code = response.get('errorCode', '未知')
            error_msg = response.get('errorMsg', '未知错误')
            print(f"\n⚠️  错误码: {error_code}")
            print(f"⚠️  错误信息: {error_msg}")


def main():
    """
    主测试函数
    """
    print("\n" + "🔬"*40)
    print("Temu Open API 详细测试")
    print("🔬"*40)
    
    # 配置
    app_key = os.getenv("TEMU_APP_KEY", "798478197604e93f6f2ce4c2e833041u")
    app_secret = os.getenv("TEMU_APP_SECRET", "776a96163c56c53e237f5456d4e14765301aa8aa")
    access_token = os.getenv("TEMU_ACCESS_TOKEN", "")
    
    print(f"\n📋 使用配置:")
    print(f"  App Key: {app_key}")
    print(f"  App Secret: {app_secret[:10]}...")
    print(f"  Access Token: {'✅ 已设置' if access_token else '❌ 未设置'}")
    
    # 测试场景
    test_cases = [
        {
            "title": "测试 1: 查询商品分类（需要token）",
            "api_type": "bg.local.goods.cats.get",
            "request_data": {"parentCatId": 0},
            "need_token": True
        },
        {
            "title": "测试 2: 查询Token信息",
            "api_type": "bg.open.accesstoken.info.get",
            "request_data": {},
            "need_token": True
        },
        {
            "title": "测试 3: 获取店铺信息（需要token）",
            "api_type": "bg.shop.info.get",
            "request_data": {},
            "need_token": True
        },
        {
            "title": "测试 4: 订单列表查询（需要token）",
            "api_type": "bg.order.list.get",
            "request_data": {
                "page_no": 1,
                "page_size": 10
            },
            "need_token": True
        },
    ]
    
    # 执行测试
    for i, test_case in enumerate(test_cases, 1):
        if test_case["need_token"] and not access_token:
            print(f"\n\n⏭️  跳过测试 {i}: {test_case['title']} (需要access_token)")
            continue
        
        print(f"\n\n{'='*80}")
        print(f"🧪 执行: {test_case['title']}")
        print(f"   API类型: {test_case['api_type']}")
        print(f"   需要Token: {'是' if test_case['need_token'] else '否'}")
        print('='*80)
        
        result = call_temu_api(
            app_key=app_key,
            app_secret=app_secret,
            api_type=test_case["api_type"],
            request_data=test_case["request_data"],
            access_token=access_token if test_case["need_token"] else None
        )
        
        print_result(test_case["title"], result)
        
        # 如果成功，记录一下
        if result.get("response", {}).get("success"):
            print("\n🎉 这个接口测试成功！")
    
    # 总结
    print("\n\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    if not access_token:
        print("\n⚠️  所有测试都需要 access_token，请设置后再测试：")
        print("\n方法 1: 使用环境变量")
        print("  export TEMU_ACCESS_TOKEN='你的token'")
        print("\n方法 2: 如果文档提供了沙盒token，直接在代码中设置")
        print(f"  access_token = '沙盒token'")
        print("\n方法 3: 通过授权流程获取")
        print("  1. 访问 Temu Seller Center")
        print("  2. 创建应用并授权")
        print("  3. 使用 bg.open.accesstoken.create 接口换取token")
    else:
        print("\n✅ 已配置 access_token，可以测试需要授权的接口")
    
    print("\n💡 根据文档，你可以：")
    print("  1. 查看文档中提供的沙盒token（如果有）")
    print("  2. 在测试环境中使用提供的测试凭据")
    print("  3. 参考文档中的示例请求")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

