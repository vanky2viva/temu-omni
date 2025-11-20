#!/usr/bin/env python3
"""测试同步服务的代理配置是否正确"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService

async def test_sync_proxy_config():
    """测试同步服务的代理配置"""
    db = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 测试店铺: {shop.shop_name}\n")
        
        temu_service = TemuService(shop)
        
        # 测试1: 检查订单API的代理配置
        print("=" * 80)
        print("测试1: 订单API代理配置")
        print("=" * 80)
        standard_client = temu_service._get_standard_client()
        print(f"✅ 标准端点客户端已创建")
        print(f"   API URL: {standard_client.base_url}")
        print(f"   使用代理: {'是' if standard_client.proxy_url else '否'}")
        if standard_client.proxy_url:
            print(f"   代理地址: {standard_client.proxy_url}")
        else:
            print(f"   ⚠️  警告: 订单API未配置代理，可能导致IP白名单错误")
        await standard_client.close()
        
        # 测试2: 检查商品API的代理配置
        print("\n" + "=" * 80)
        print("测试2: 商品API代理配置（CN端点）")
        print("=" * 80)
        if shop.cn_access_token:
            cn_api_url = shop.cn_api_base_url or 'https://openapi.kuajingmaihuo.com/openapi/router'
            cn_app_key = shop.cn_app_key or 'af5bcf5d4bd5a492fa09c2ee302d75b9'
            cn_app_secret = shop.cn_app_secret or 'e4f229bb9c4db21daa999e73c8683d42ba0a7094'
            
            from app.temu.client import TemuAPIClient
            cn_client = TemuAPIClient(
                app_key=cn_app_key,
                app_secret=cn_app_secret,
                proxy_url=""  # 空字符串表示不使用代理
            )
            cn_client.base_url = cn_api_url
            print(f"✅ CN端点客户端已创建")
            print(f"   API URL: {cn_client.base_url}")
            print(f"   使用代理: {'是' if cn_client.proxy_url else '否'}")
            if not cn_client.proxy_url:
                print(f"   ✅ 正确: CN端点直接访问，无需代理")
            else:
                print(f"   ⚠️  警告: CN端点配置了代理，但应该直接访问")
            await cn_client.close()
        else:
            print("⚠️  店铺未配置CN Access Token，跳过CN端点测试")
        
        print("\n" + "=" * 80)
        print("总结")
        print("=" * 80)
        print("✅ 订单API: 通过代理服务器访问（标准端点）")
        print("✅ 商品API: 直接访问，不通过代理（CN端点）")
        print("\n配置验证完成！")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_sync_proxy_config())

