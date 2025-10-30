"""
修复失败的API测试
针对三个失败的接口尝试不同的参数组合
"""
import os
import time
import hashlib
import json
import requests
from datetime import datetime, timedelta


# 测试凭据
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


def test_sku_list():
    """测试SKU列表查询 - 尝试多种参数格式"""
    print("\n" + "="*80)
    print("🧪 测试 1: 查询SKU列表")
    print("="*80)
    
    # 尝试不同的参数组合
    test_cases = [
        {
            "name": "尝试 1: 只传分页参数",
            "params": {
                "page": 1,
                "pageSize": 10
            }
        },
        {
            "name": "尝试 2: 使用驼峰命名",
            "params": {
                "pageNumber": 1,
                "pageSize": 10
            }
        },
        {
            "name": "尝试 3: 添加状态筛选",
            "params": {
                "pageNumber": 1,
                "pageSize": 10,
                "skuStatus": 1
            }
        },
        {
            "name": "尝试 4: 空参数",
            "params": {}
        }
    ]
    
    for test in test_cases:
        print(f"\n📍 {test['name']}")
        print(f"   参数: {json.dumps(test['params'], ensure_ascii=False)}")
        
        result = call_api("temu.local.sku.list.retrieve", test["params"])
        
        if result.get("success"):
            print("   ✅ 成功！")
            print(f"   响应: {json.dumps(result['response']['result'], indent=2, ensure_ascii=False)[:200]}...")
            return True
        else:
            error = result.get("response", {})
            print(f"   ❌ 失败: [{error.get('errorCode')}] {error.get('errorMsg')}")
    
    return False


def test_logistics_companies():
    """测试物流公司列表 - 尝试多种参数格式"""
    print("\n" + "="*80)
    print("🧪 测试 2: 获取物流公司列表")
    print("="*80)
    
    # 尝试不同的参数组合
    test_cases = [
        {
            "name": "尝试 1: 空参数",
            "params": {}
        },
        {
            "name": "尝试 2: 指定区域",
            "params": {
                "regionId": 211
            }
        },
        {
            "name": "尝试 3: 指定仓库",
            "params": {
                "warehouseId": "WH-04851008798852414"
            }
        },
        {
            "name": "尝试 4: 指定物流类型",
            "params": {
                "shippingType": 1
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n📍 {test['name']}")
        print(f"   参数: {json.dumps(test['params'], ensure_ascii=False)}")
        
        result = call_api("bg.logistics.companies.get", test["params"])
        
        if result.get("success"):
            print("   ✅ 成功！")
            print(f"   响应: {json.dumps(result['response']['result'], indent=2, ensure_ascii=False)[:200]}...")
            return True
        else:
            error = result.get("response", {})
            print(f"   ❌ 失败: [{error.get('errorCode')}] {error.get('errorMsg')}")
    
    return False


def test_aftersales_list():
    """测试售后列表 - 尝试多种参数格式"""
    print("\n" + "="*80)
    print("🧪 测试 3: 查询售后列表")
    print("="*80)
    
    # 计算时间范围
    end_time = int(time.time())
    start_time = end_time - (30 * 24 * 60 * 60)  # 最近30天
    
    # 尝试不同的参数组合
    test_cases = [
        {
            "name": "尝试 1: 基础分页参数",
            "params": {
                "page": 1,
                "pageSize": 10
            }
        },
        {
            "name": "尝试 2: 添加时间范围",
            "params": {
                "page": 1,
                "pageSize": 10,
                "startTime": start_time,
                "endTime": end_time
            }
        },
        {
            "name": "尝试 3: 使用驼峰命名 + 时间",
            "params": {
                "pageNumber": 1,
                "pageSize": 10,
                "beginTime": start_time,
                "endTime": end_time
            }
        },
        {
            "name": "尝试 4: 添加售后状态",
            "params": {
                "pageNumber": 1,
                "pageSize": 10,
                "beginTime": start_time,
                "endTime": end_time,
                "aftersalesStatus": 1
            }
        },
        {
            "name": "尝试 5: 查询类型",
            "params": {
                "pageNumber": 1,
                "pageSize": 10,
                "queryType": 1,
                "beginTime": start_time,
                "endTime": end_time
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n📍 {test['name']}")
        print(f"   参数: {json.dumps(test['params'], ensure_ascii=False)}")
        
        result = call_api("bg.aftersales.aftersales.list.get", test["params"])
        
        if result.get("success"):
            print("   ✅ 成功！")
            print(f"   响应: {json.dumps(result['response']['result'], indent=2, ensure_ascii=False)[:200]}...")
            return True
        else:
            error = result.get("response", {})
            print(f"   ❌ 失败: [{error.get('errorCode')}] {error.get('errorMsg')}")
    
    return False


def test_alternative_apis():
    """测试替代的API接口"""
    print("\n" + "="*80)
    print("🔍 尝试相关的替代API")
    print("="*80)
    
    alternatives = [
        {
            "name": "物流服务列表（替代物流公司）",
            "api": "bg.logistics.shippingservices.get",
            "params": {}
        },
        {
            "name": "商品SKU列表（替代SKU查询）",
            "api": "bg.local.goods.sku.list.query",
            "params": {
                "pageNumber": 1,
                "pageSize": 10
            }
        },
        {
            "name": "取消订单售后列表",
            "api": "bg.aftersales.cancel.list.get",
            "params": {
                "page": 1,
                "pageSize": 10
            }
        }
    ]
    
    success_count = 0
    for alt in alternatives:
        print(f"\n📍 {alt['name']}")
        print(f"   API: {alt['api']}")
        
        result = call_api(alt["api"], alt["params"])
        
        if result.get("success"):
            print("   ✅ 成功！")
            success_count += 1
        else:
            error = result.get("response", {})
            print(f"   ❌ 失败: [{error.get('errorCode')}] {error.get('errorMsg')}")
    
    return success_count


def main():
    """主测试函数"""
    print("\n" + "🔧"*40)
    print("Temu API - 修复失败的测试")
    print("🔧"*40)
    
    print(f"\n📋 测试配置:")
    print(f"  App Key: {TEST_CREDENTIALS['app_key']}")
    print(f"  Base URL: https://openapi-b-us.temu.com/openapi/router")
    
    results = {
        "sku_list": False,
        "logistics_companies": False,
        "aftersales_list": False
    }
    
    # 测试失败的三个接口
    print("\n\n" + "🎯"*40)
    print("修复原有失败的接口")
    print("🎯"*40)
    
    results["sku_list"] = test_sku_list()
    time.sleep(1)
    
    results["logistics_companies"] = test_logistics_companies()
    time.sleep(1)
    
    results["aftersales_list"] = test_aftersales_list()
    time.sleep(1)
    
    # 测试替代API
    print("\n\n" + "🔄"*40)
    print("测试替代API")
    print("🔄"*40)
    
    alternative_success = test_alternative_apis()
    
    # 总结
    print("\n\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    fixed_count = sum(1 for v in results.values() if v)
    
    print(f"\n原有失败接口:")
    print(f"  ✅ 修复成功: {fixed_count}/3")
    print(f"  ❌ 仍然失败: {3 - fixed_count}/3")
    
    print(f"\n各接口状态:")
    print(f"  SKU列表查询: {'✅ 成功' if results['sku_list'] else '❌ 失败'}")
    print(f"  物流公司列表: {'✅ 成功' if results['logistics_companies'] else '❌ 失败'}")
    print(f"  售后列表查询: {'✅ 成功' if results['aftersales_list'] else '❌ 失败'}")
    
    print(f"\n替代API:")
    print(f"  ✅ 成功: {alternative_success}/3")
    
    print("\n" + "="*80)
    print("💡 建议")
    print("="*80)
    
    if fixed_count == 0:
        print("\n⚠️  所有失败接口都无法修复")
        print("\n可能的原因:")
        print("  1. 这些接口需要特定的业务数据（如已有的SKU、售后记录等）")
        print("  2. 测试账号没有相应的权限或数据")
        print("  3. 接口参数需要从其他接口获取（如需要先有商品ID）")
        print("  4. 某些接口可能在测试环境不可用")
        
        print("\n✅ 好消息:")
        print("  - 核心接口（订单、商品分类、仓库）都工作正常")
        print("  - 已经有6,019个订单数据可以使用")
        print("  - 可以正常开发主要业务功能")
        
        if alternative_success > 0:
            print(f"\n  - 找到了 {alternative_success} 个替代API可以使用")
    else:
        print(f"\n🎉 成功修复了 {fixed_count} 个接口！")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

