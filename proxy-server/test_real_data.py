#!/usr/bin/env python3
"""测试代理服务器获取真实数据"""
import requests
import json
import sys
from datetime import datetime, timedelta

# 配置
PROXY_URL = "http://172.236.231.45:8001"
ACCESS_TOKEN = "upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k"

def test_api(api_type, request_data=None, description=""):
    """测试 API 调用"""
    print(f"\n{'='*80}")
    print(f"测试: {description or api_type}")
    print(f"{'='*80}")
    
    payload = {
        "api_type": api_type,
        "access_token": ACCESS_TOKEN
    }
    
    if request_data:
        payload["request_data"] = request_data
    
    print(f"请求 URL: {PROXY_URL}/api/proxy")
    print(f"请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(
            f"{PROXY_URL}/api/proxy",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"HTTP 状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print()
        
        try:
            result = response.json()
            print(f"响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if response.status_code == 200:
                if result.get("success"):
                    print(f"\n✅ 成功: {description or api_type}")
                    return True, result
                else:
                    error_code = result.get("error_code", "未知")
                    error_msg = result.get("error_msg", "未知错误")
                    print(f"\n❌ 业务错误: [{error_code}] {error_msg}")
                    return False, result
            else:
                print(f"\n❌ HTTP 错误: {response.status_code}")
                return False, result
                
        except json.JSONDecodeError:
            print(f"响应内容（非 JSON）:")
            print(response.text)
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False, None


def main():
    print("="*80)
    print("🧪 测试代理服务器获取真实 Temu API 数据")
    print("="*80)
    print(f"代理服务器: {PROXY_URL}")
    print(f"Access Token: {ACCESS_TOKEN[:20]}...")
    print()
    
    # 测试 1: 获取 Token 信息（最简单的 API）
    success1, result1 = test_api(
        "bg.open.accesstoken.info.get",
        description="获取 Token 信息"
    )
    
    # 测试 2: 获取商品分类
    success2, result2 = test_api(
        "bg.local.goods.cats.get",
        request_data={"parentCatId": 0},
        description="获取商品分类（根分类）"
    )
    
    # 测试 3: 获取商品列表
    success3, result3 = test_api(
        "bg.local.goods.list.query",
        request_data={
            "pageNumber": 1,
            "pageSize": 10
        },
        description="获取商品列表（第一页，10条）"
    )
    
    # 测试 4: 获取订单列表（最近7天）
    end_time = int(datetime.now().timestamp())
    begin_time = int((datetime.now() - timedelta(days=7)).timestamp())
    
    success4, result4 = test_api(
        "bg.order.list.v2.get",
        request_data={
            "beginTime": begin_time,
            "endTime": end_time,
            "pageNumber": 1,
            "pageSize": 10
        },
        description="获取订单列表（最近7天）"
    )
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"1. 获取 Token 信息: {'✅ 成功' if success1 else '❌ 失败'}")
    print(f"2. 获取商品分类: {'✅ 成功' if success2 else '❌ 失败'}")
    print(f"3. 获取商品列表: {'✅ 成功' if success3 else '❌ 失败'}")
    print(f"4. 获取订单列表: {'✅ 成功' if success4 else '❌ 失败'}")
    
    total = sum([success1, success2, success3, success4])
    print(f"\n总计: {total}/4 个测试通过")
    
    if total == 4:
        print("\n🎉 所有测试通过！代理服务器可以正常获取真实数据")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查：")
        print("   1. IP 白名单是否已生效")
        print("   2. API 凭证是否正确")
        print("   3. Access Token 是否有效")
        print("   4. 查看代理服务器日志: docker logs temu-api-proxy -f")
        return 1


if __name__ == "__main__":
    sys.exit(main())



