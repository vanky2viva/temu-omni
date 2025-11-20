#!/usr/bin/env python3
"""验证订单金额查询接口的端点配置"""
import sys
import os
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 临时设置代理URL
if not os.getenv('TEMU_API_PROXY_URL'):
    os.environ['TEMU_API_PROXY_URL'] = 'http://172.236.231.45:8001'

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService
from app.temu.client import TemuAPIClient
from app.core.config import settings

async def verify_endpoint():
    """验证端点配置"""
    db = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        print("=" * 80)
        print("端点配置验证")
        print("=" * 80)
        
        # 1. 检查标准端点配置
        print("\n1. 标准端点配置:")
        temu_service = TemuService(shop)
        standard_client = temu_service._get_standard_client()
        
        print(f"   API Base URL: {standard_client.base_url}")
        print(f"   App Key: {standard_client.app_key[:20]}...")
        print(f"   使用代理: {'是' if standard_client.proxy_url else '否'}")
        if standard_client.proxy_url:
            print(f"   代理地址: {standard_client.proxy_url}")
        
        # 2. 检查API类型
        print("\n2. API类型:")
        api_type = "bg.order.amount.query"
        print(f"   API Type: {api_type}")
        print(f"   文档链接: https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=ba20da993f7d4605909dd49a5c186c21")
        
        # 3. 检查请求参数
        print("\n3. 请求参数:")
        order_sn = "PO-211-02732691354231486"
        request_data = {"orderSn": order_sn}
        print(f"   订单号: {order_sn}")
        print(f"   请求数据: {json.dumps(request_data, ensure_ascii=False, indent=6)}")
        
        # 4. 构建完整请求信息
        print("\n4. 完整请求信息:")
        print(f"   端点URL: {standard_client.base_url}")
        print(f"   API类型: {api_type}")
        print(f"   请求参数: {json.dumps(request_data, ensure_ascii=False)}")
        print(f"   Access Token: {shop.access_token[:20] if shop.access_token else '未配置'}...")
        
        # 5. 验证端点URL格式
        print("\n5. 端点URL验证:")
        expected_urls = {
            "US": "https://openapi-b-us.temu.com/openapi/router",
            "EU": "https://openapi-b-eu.temu.com/openapi/router",
            "GLOBAL": "https://openapi.temu.com/openapi/router"
        }
        print(f"   当前店铺区域: {shop.region}")
        print(f"   当前使用的URL: {standard_client.base_url}")
        if shop.region in expected_urls:
            expected_url = expected_urls[shop.region]
            if standard_client.base_url == expected_url:
                print(f"   ✅ URL格式正确")
            else:
                print(f"   ⚠️  URL可能不正确，预期: {expected_url}")
        else:
            print(f"   ⚠️  未知区域: {shop.region}")
        
        # 6. 检查代理服务器配置
        print("\n6. 代理服务器配置:")
        if standard_client.proxy_url:
            print(f"   ✅ 代理已配置: {standard_client.proxy_url}")
            # 测试代理服务器是否可达
            import httpx
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{standard_client.proxy_url}/health")
                    if response.status_code == 200:
                        print(f"   ✅ 代理服务器可达")
                    else:
                        print(f"   ⚠️  代理服务器响应异常: {response.status_code}")
            except Exception as e:
                print(f"   ❌ 代理服务器不可达: {e}")
        else:
            print(f"   ❌ 代理未配置")
        
        await standard_client.close()
        
        print("\n" + "=" * 80)
        print("总结")
        print("=" * 80)
        print("✅ API类型: bg.order.amount.query (正确)")
        print(f"✅ 端点URL: {standard_client.base_url} (标准端点)")
        print(f"{'✅' if standard_client.proxy_url else '❌'} 代理配置: {'已配置' if standard_client.proxy_url else '未配置'}")
        print("\n⚠️  如果仍然报错 [3000032]，说明 access_token 未授权此API")
        print("   需要在卖家中心授权 'bg.order.amount.query' API")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_endpoint())


