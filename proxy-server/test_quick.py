"""快速测试代理服务器连接"""
import requests
import json
import sys


def test_proxy_health(proxy_url="http://localhost:8001"):
    """测试代理服务器健康状态"""
    try:
        response = requests.get(f"{proxy_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 代理服务器健康检查通过: {response.json()}")
            return True
        else:
            print(f"❌ 代理服务器健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到代理服务器: {e}")
        print(f"   请确保代理服务器正在运行: {proxy_url}")
        return False


def test_proxy_api(proxy_url="http://localhost:8001"):
    """测试代理 API 请求"""
    print("\n测试代理 API 请求...")
    
    # 简化调用方式（推荐）：只需传入 access_token
    # app_key 和 app_secret 从代理服务器环境变量读取
    request_data = {
        "api_type": "bg.open.accesstoken.info.get",
        "access_token": "upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k"
        # app_key 和 app_secret 可选，如果不提供则使用代理服务器环境变量中的配置
    }
    
    try:
        response = requests.post(
            f"{proxy_url}/api/proxy",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 代理 API 请求成功")
                print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"❌ 代理 API 请求失败: {result.get('error_msg', '未知错误')}")
                return False
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False


if __name__ == "__main__":
    proxy_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    
    print("=" * 80)
    print(f"🧪 快速测试代理服务器: {proxy_url}")
    print("=" * 80)
    
    # 测试健康检查
    if not test_proxy_health(proxy_url):
        sys.exit(1)
    
    # 测试 API 请求
    if not test_proxy_api(proxy_url):
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)

