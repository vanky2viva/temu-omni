"""
Temu Open API 交互式测试脚本
允许用户输入access_token并立即测试
"""
import os
import time
import hashlib
import json
import requests


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


def call_api(app_key, app_secret, access_token, api_type, request_data):
    """调用API"""
    base_url = "https://openapi-b-us.temu.com/openapi/router"
    
    timestamp = int(time.time())
    common_params = {
        "app_key": app_key,
        "data_type": "JSON",
        "timestamp": timestamp,
        "type": api_type,
        "version": "V1",
        "access_token": access_token
    }
    
    all_params = {**common_params}
    if request_data:
        all_params["request"] = request_data
    
    sign = api_sign_method(app_secret, all_params)
    request_payload = {**all_params, "sign": sign}
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        base_url,
        headers=headers,
        data=json.dumps(request_payload),
        timeout=30
    )
    
    return response.json()


def test_with_token(access_token, app_key, app_secret):
    """使用提供的token进行测试"""
    print("\n" + "="*80)
    print("🚀 开始测试 Temu API")
    print("="*80)
    
    test_cases = [
        {
            "name": "查询Token信息",
            "api_type": "bg.open.accesstoken.info.get",
            "request_data": {}
        },
        {
            "name": "查询商品分类",
            "api_type": "bg.local.goods.cats.get",
            "request_data": {"parentCatId": 0}
        },
        {
            "name": "获取店铺信息",
            "api_type": "bg.shop.info.get",
            "request_data": {}
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}/{len(test_cases)}: {test['name']}")
        print(f"API: {test['api_type']}")
        print('='*80)
        
        try:
            result = call_api(
                app_key=app_key,
                app_secret=app_secret,
                access_token=access_token,
                api_type=test['api_type'],
                request_data=test['request_data']
            )
            
            print("\n📥 响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('success'):
                print("\n✅ 成功！")
                success_count += 1
            else:
                error_code = result.get('errorCode', '未知')
                error_msg = result.get('errorMsg', '未知错误')
                print(f"\n❌ 失败: [{error_code}] {error_msg}")
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
    
    # 总结
    print("\n\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    print(f"\n成功: {success_count}/{len(test_cases)}")
    
    if success_count > 0:
        print("\n🎉 恭喜！API测试成功！")
        print("\n下一步可以：")
        print("  1. 集成到主应用中")
        print("  2. 测试更多API接口")
        print("  3. 开发业务功能")
    else:
        print("\n⚠️  所有测试都失败了")
        print("\n可能的原因：")
        print("  1. Access Token 无效或过期")
        print("  2. Token 没有相应的权限")
        print("  3. 账号状态异常")
        print("\n建议：")
        print("  1. 检查文档中的token是否正确")
        print("  2. 确认token的有效期")
        print("  3. 联系Temu技术支持")


def main():
    """主函数"""
    print("\n" + "🔧"*40)
    print("Temu Open API 交互式测试工具")
    print("🔧"*40)
    
    # 配置
    app_key = os.getenv("TEMU_APP_KEY", "798478197604e93f6f2ce4c2e833041u")
    app_secret = os.getenv("TEMU_APP_SECRET", "776a96163c56c53e237f5456d4e14765301aa8aa")
    
    print(f"\n📋 当前配置:")
    print(f"  App Key: {app_key}")
    print(f"  App Secret: {app_secret[:10]}...")
    
    # 检查环境变量
    env_token = os.getenv("TEMU_ACCESS_TOKEN", "")
    
    if env_token:
        print(f"\n✅ 检测到环境变量中的 ACCESS_TOKEN")
        print(f"  Token: {env_token[:20]}...")
        
        use_env = input("\n是否使用此token进行测试? (y/n): ").strip().lower()
        
        if use_env == 'y':
            test_with_token(env_token, app_key, app_secret)
            return
    
    # 手动输入token
    print("\n" + "-"*80)
    print("请输入 Access Token:")
    print("(可以从文档中复制，或从授权流程获取)")
    print("-"*80)
    
    access_token = input("\nAccess Token: ").strip()
    
    if not access_token:
        print("\n❌ 未输入 Access Token，退出测试")
        return
    
    print(f"\n✅ 已接收 Token: {access_token[:20]}...")
    
    confirm = input("\n确认开始测试? (y/n): ").strip().lower()
    
    if confirm == 'y':
        test_with_token(access_token, app_key, app_secret)
    else:
        print("\n已取消测试")
    
    print("\n" + "="*80)
    print("💡 提示：你可以设置环境变量来避免每次输入：")
    print(f"  export TEMU_ACCESS_TOKEN='{access_token[:20]}...'")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")

