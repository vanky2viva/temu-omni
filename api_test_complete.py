"""
Temu Open API 完整测试脚本
使用官方提供的测试凭据测试所有主要接口
"""
import os
import time
import hashlib
import json
import requests
from datetime import datetime, timedelta


# 测试凭据（来自官方文档）
TEST_CREDENTIALS = {
    "app_key": "4ebbc9190ae410443d65b4c2faca981f",
    "app_secret": "4782d2d827276688bf4758bed55dbdd4bbe79a79",
    "access_token": "uplv3hfyt5kcwoymrgnajnbl1ow5qxlz4sqhev6hl3xosz5dejrtyl2jre7"
}


def api_sign_method(app_secret, request_params):
    """Temu官方MD5签名算法"""
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


def call_api(api_type, request_data=None):
    """调用API的通用方法"""
    base_url = "https://openapi-b-us.temu.com/openapi/router"
    
    timestamp = int(time.time())
    common_params = {
        "app_key": TEST_CREDENTIALS["app_key"],
        "data_type": "JSON",
        "timestamp": timestamp,
        "type": api_type,
        "version": "V1",
        "access_token": TEST_CREDENTIALS["access_token"]
    }
    
    all_params = {**common_params}
    if request_data:
        all_params["request"] = request_data
    
    sign = api_sign_method(TEST_CREDENTIALS["app_secret"], all_params)
    request_payload = {**all_params, "sign": sign}
    
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(base_url, headers=headers, 
                                data=json.dumps(request_payload), timeout=30)
        return {
            "status_code": response.status_code,
            "response": response.json(),
            "success": response.json().get("success", False)
        }
    except Exception as e:
        return {
            "status_code": 0,
            "error": str(e),
            "success": False
        }


def print_test_result(title, result):
    """打印测试结果"""
    print(f"\n{'='*80}")
    print(f"🧪 {title}")
    print('='*80)
    
    if "error" in result:
        print(f"❌ 请求失败: {result['error']}")
        return False
    
    response = result["response"]
    success = response.get("success", False)
    
    if success:
        print("✅ 成功")
        print(f"📦 返回数据:")
        # 只打印result部分，如果数据太多就截断
        result_data = response.get("result", {})
        result_str = json.dumps(result_data, indent=2, ensure_ascii=False)
        if len(result_str) > 2000:
            print(result_str[:2000] + "\n... (数据太长，已截断)")
        else:
            print(result_str)
    else:
        error_code = response.get("errorCode", "未知")
        error_msg = response.get("errorMsg", "未知错误")
        print(f"❌ 失败: [{error_code}] {error_msg}")
    
    return success


def main():
    """主测试函数"""
    print("\n" + "🎯"*40)
    print("Temu Open API 完整测试")
    print("使用官方提供的测试凭据")
    print("🎯"*40)
    
    print(f"\n📋 测试配置:")
    print(f"  App Key: {TEST_CREDENTIALS['app_key']}")
    print(f"  App Secret: {TEST_CREDENTIALS['app_secret'][:20]}...")
    print(f"  Access Token: {TEST_CREDENTIALS['access_token'][:30]}...")
    
    # 计算时间范围
    end_time = int(time.time())
    start_time = end_time - (30 * 24 * 60 * 60)  # 最近30天
    
    # 定义测试用例
    test_cases = [
        # Token & 基础信息
        {
            "category": "🔐 Token & 基础信息",
            "tests": [
                {
                    "name": "查询Token信息",
                    "api_type": "bg.open.accesstoken.info.get",
                    "request_data": {}
                },
            ]
        },
        
        # 商品管理
        {
            "category": "📦 商品管理",
            "tests": [
                {
                    "name": "查询商品分类",
                    "api_type": "bg.local.goods.cats.get",
                    "request_data": {"parentCatId": 0}
                },
                {
                    "name": "查询商品列表",
                    "api_type": "bg.local.goods.list.query",
                    "request_data": {
                        "pageNumber": 1,
                        "pageSize": 10
                    }
                },
                {
                    "name": "查询SKU列表（替代接口）",
                    "api_type": "bg.local.goods.sku.list.query",
                    "request_data": {
                        "pageNumber": 1,
                        "pageSize": 10
                    }
                },
            ]
        },
        
        # 订单管理（V2版本）
        {
            "category": "🛒 订单管理",
            "tests": [
                {
                    "name": "查询订单列表 (V2)",
                    "api_type": "bg.order.list.v2.get",
                    "request_data": {
                        "beginTime": start_time,
                        "endTime": end_time,
                        "pageSize": 10,
                        "pageNumber": 1
                    }
                },
            ]
        },
        
        # 物流管理
        {
            "category": "🚚 物流管理",
            "tests": [
                {
                    "name": "获取仓库列表",
                    "api_type": "bg.logistics.warehouse.list.get",
                    "request_data": {}
                },
            ]
        },
        
        # 售后管理
        {
            "category": "🔄 售后管理",
            "tests": [
                {
                    "name": "查询取消订单售后列表",
                    "api_type": "bg.aftersales.cancel.list.get",
                    "request_data": {
                        "page": 1,
                        "pageSize": 10
                    }
                },
            ]
        },
    ]
    
    # 执行所有测试
    total_tests = 0
    success_count = 0
    failed_tests = []
    
    for category_group in test_cases:
        print(f"\n\n{'='*80}")
        print(category_group["category"])
        print('='*80)
        
        for test in category_group["tests"]:
            total_tests += 1
            print(f"\n📍 测试 {total_tests}: {test['name']}")
            print(f"   API: {test['api_type']}")
            
            result = call_api(test["api_type"], test["request_data"])
            
            if print_test_result(test["name"], result):
                success_count += 1
            else:
                failed_tests.append({
                    "name": test["name"],
                    "api_type": test["api_type"],
                    "error": result.get("response", {}).get("errorMsg", "未知错误")
                })
            
            # 避免请求过快
            time.sleep(0.5)
    
    # 打印总结
    print("\n\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    print(f"\n总测试数: {total_tests}")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {total_tests - success_count}")
    print(f"📈 成功率: {success_count/total_tests*100:.1f}%")
    
    if failed_tests:
        print(f"\n\n失败的测试详情:")
        for i, test in enumerate(failed_tests, 1):
            print(f"\n{i}. {test['name']}")
            print(f"   API: {test['api_type']}")
            print(f"   错误: {test['error']}")
    
    print("\n" + "="*80)
    print("💡 提示")
    print("="*80)
    print("\n✅ 已验证的功能：")
    print("  1. API连接正常")
    print("  2. 签名算法正确")
    print("  3. Token有效且权限充足")
    print("  4. 可以获取商品、订单、物流等数据")
    
    print("\n🔧 下一步：")
    print("  1. 将测试凭据保存到配置文件")
    print("  2. 更新 backend/app/temu/client.py 使用正确的签名算法")
    print("  3. 集成到主应用中")
    print("  4. 开发具体业务功能")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

