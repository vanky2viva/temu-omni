#!/usr/bin/env python3
"""验证代理服务器配置"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_proxy_config():
    """检查代理服务器配置"""
    print("=" * 60)
    print("代理服务器配置验证")
    print("=" * 60)
    
    # 检查环境变量
    proxy_url_env = os.getenv("TEMU_API_PROXY_URL", "")
    print(f"\n1. 环境变量 TEMU_API_PROXY_URL: {proxy_url_env if proxy_url_env else '(未设置)'}")
    
    # 尝试导入配置（需要设置必要的环境变量）
    try:
        # 设置最小必需的环境变量以避免验证错误
        if not os.getenv("SECRET_KEY"):
            os.environ["SECRET_KEY"] = "temp-secret-key-for-check"
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite:///./temp.db"
        
        from app.core.config import settings
        proxy_url_config = settings.TEMU_API_PROXY_URL
        print(f"2. 配置中的 TEMU_API_PROXY_URL: {proxy_url_config if proxy_url_config else '(未设置)'}")
        
        # 检查是否配置
        if not proxy_url_config:
            print("\n❌ 代理服务器未配置！")
            print("\n解决方案：")
            print("1. 设置环境变量 TEMU_API_PROXY_URL")
            print("   例如：export TEMU_API_PROXY_URL=http://172.236.231.45:8001")
            print("\n2. 或者在 .env 文件中添加：")
            print("   TEMU_API_PROXY_URL=http://172.236.231.45:8001")
            print("\n3. 如果使用 Docker，在 docker-compose.yml 中已配置默认值")
            print("   确保重启服务：docker-compose restart backend")
            return False
        else:
            print(f"\n✅ 代理服务器已配置: {proxy_url_config}")
            print("\n订单同步流程：")
            print("1. sync_orders() -> TemuService.get_orders()")
            print("2. get_orders() -> _get_standard_client()")
            print("3. _get_standard_client() -> 创建 TemuAPIClient(proxy_url=proxy_url)")
            print("4. TemuAPIClient._request() -> 检查 proxy_url")
            print("5. 如果 proxy_url 存在 -> _request_via_proxy()")
            print(f"6. _request_via_proxy() -> POST {proxy_url_config}/api/proxy")
            return True
    except Exception as e:
        print(f"\n⚠️ 无法加载配置: {e}")
        print("\n请确保：")
        print("1. 已设置必要的环境变量（SECRET_KEY, DATABASE_URL）")
        print("2. 已安装项目依赖")
        return False

if __name__ == "__main__":
    check_proxy_config()

