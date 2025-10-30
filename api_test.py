"""
Temu Open API 测试脚本（基于官方文档标准）
支持沙盒环境和生产环境测试
参考: https://partner-us.temu.com/documentation
"""
import os
import time
import hashlib
import json
import requests


def api_sign_method(app_secret, request_params):
    """
    Temu官方MD5签名算法
    
    签名规则：
    1. 将所有参数（除sign外）按key字母顺序排序
    2. 拼接成 key1value1key2value2... 格式
    3. 在前后各加上 app_secret
    4. 对整个字符串进行MD5加密并转大写
    """
    temp = []
    request_params = sorted(request_params.items())
    for k, v in request_params:
        # 如果值是字典或列表，转换为JSON字符串
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
        # 去除字符串两端的引号
        temp.append(str(k) + str(v).strip('\"'))
    
    un_sign = ''.join(temp)
    un_sign = str(app_secret) + un_sign + str(app_secret)
    sign = hashlib.md5(un_sign.encode('utf-8')).hexdigest().upper()
    return sign


def test_api(env="sandbox", api_type="bg.local.goods.cats.get", request_data=None):
    """
    测试Temu API
    
    Args:
        env: 环境类型 "sandbox"(沙盒) 或 "production"(生产)
        api_type: API接口类型
        request_data: 请求数据
    """
    print("="*80)
    print(f"🧪 测试环境: {'沙盒环境 (Sandbox)' if env == 'sandbox' else '生产环境 (Production)'}")
    print(f"🔧 API类型: {api_type}")
    print("="*80)
    
    # 根据环境选择配置
    if env == "sandbox":
        # 沙盒环境配置（通常文档会提供测试凭据）
        # 注意：Temu可能使用相同的URL，但使用测试凭据来区分环境
        app_key = os.getenv("TEMU_SANDBOX_APP_KEY", "798478197604e93f6f2ce4c2e833041u")
        app_secret = os.getenv("TEMU_SANDBOX_APP_SECRET", "776a96163c56c53e237f5456d4e14765301aa8aa")
        access_token = os.getenv("TEMU_SANDBOX_ACCESS_TOKEN", "")
        # 尝试多个可能的沙盒URL
        base_url = os.getenv("TEMU_SANDBOX_BASE_URL", "https://openapi-b-us.temu.com/openapi/router")
    else:
        # 生产环境配置
        app_key = os.getenv("TEMU_APP_KEY", "")
        app_secret = os.getenv("TEMU_APP_SECRET", "")
        access_token = os.getenv("TEMU_ACCESS_TOKEN", "")
        base_url = "https://openapi-b-us.temu.com/openapi/router"  # 美区生产地址
    
    print(f"\n📋 配置信息:")
    print(f"  App Key: {app_key}")
    print(f"  App Secret: {app_secret[:10]}..." if app_secret else "  App Secret: (未设置)")
    print(f"  Access Token: {access_token[:20]}..." if access_token else "  Access Token: (未设置)")
    print(f"  Base URL: {base_url}")
    
    if not app_key or not app_secret:
        print("\n❌ 错误：缺少 App Key 或 App Secret")
        return None
    
    # 通用参数（Common Params）
    timestamp = int(time.time())
    common_params = {
        "app_key": app_key,
        "data_type": "JSON",
        "timestamp": timestamp,
        "type": api_type,
        "version": "V1"
    }
    
    # 如果有access_token，添加到参数中
    if access_token:
        common_params["access_token"] = access_token
    
    # 业务参数（Request Params）
    if request_data is None:
        # 默认测试参数
        if api_type == "bg.local.goods.cats.get":
            request_data = {"parentCatId": 0}  # 查询根分类
        elif api_type == "bg.open.accesstoken.info.get":
            request_data = {}  # 查询token信息
        else:
            request_data = {}
    
    # 合并所有参数用于签名
    all_params = {**common_params}
    if request_data:
        # 将request_data作为单独的request字段
        all_params["request"] = request_data
    
    # 生成签名
    sign = api_sign_method(app_secret, all_params)
    
    # 最终请求体
    request_payload = {**all_params, "sign": sign}
    
    # 打印请求信息
    print("\n📤 请求信息:")
    print(f"  URL: {base_url}")
    print(f"  请求体:")
    print(json.dumps(request_payload, ensure_ascii=False, indent=4))
    print("="*80)
    
    # 发送请求
    headers = {"Content-Type": "application/json"}
    try:
        print("\n🚀 发送请求中...")
        response = requests.post(
            base_url, 
            headers=headers, 
            data=json.dumps(request_payload),
            timeout=30
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        try:
            response_json = response.json()
            print("\n✅ 响应内容:")
            formatted_json = json.dumps(response_json, indent=4, ensure_ascii=False)
            print(formatted_json)
            
            # 分析响应
            if response_json.get("success"):
                print("\n🎉 请求成功！")
                return response_json
            else:
                error_code = response_json.get("errorCode", "未知")
                error_msg = response_json.get("errorMsg", "未知错误")
                print(f"\n⚠️  业务错误:")
                print(f"  错误码: {error_code}")
                print(f"  错误信息: {error_msg}")
                return None
                
        except json.JSONDecodeError:
            print("\n❌ 响应内容不是JSON格式:")
            print(response.text)
            return None
            
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求失败: {e}")
        return None
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        return None


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("🎯 Temu Open API 测试工具")
    print("="*80)
    
    # 测试1: 沙盒环境 - 查询商品分类
    print("\n\n" + "🔹"*40)
    print("测试 1: 沙盒环境 - 查询商品分类")
    print("🔹"*40)
    result1 = test_api(
        env="sandbox",
        api_type="bg.local.goods.cats.get",
        request_data={"parentCatId": 0}
    )
    
    # 测试2: 沙盒环境 - 查询Token信息（如果有token）
    if os.getenv("TEMU_SANDBOX_ACCESS_TOKEN"):
        print("\n\n" + "🔹"*40)
        print("测试 2: 沙盒环境 - 查询Token信息")
        print("🔹"*40)
        result2 = test_api(
            env="sandbox",
            api_type="bg.open.accesstoken.info.get",
            request_data={}
        )
    
    print("\n\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    print("\n💡 提示:")
    print("  1. 如果遇到签名错误，请检查 App Key 和 App Secret 是否正确")
    print("  2. 如果需要 access_token，请先完成授权流程")
    print("  3. 沙盒环境通常不需要真实的 access_token")
    print("  4. 可以通过环境变量设置配置:")
    print("     - TEMU_SANDBOX_APP_KEY")
    print("     - TEMU_SANDBOX_APP_SECRET")
    print("     - TEMU_SANDBOX_ACCESS_TOKEN")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()


