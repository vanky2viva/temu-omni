#!/usr/bin/env python3
"""检查店铺的access_token是否正确"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 临时设置代理URL
if not os.getenv('TEMU_API_PROXY_URL'):
    os.environ['TEMU_API_PROXY_URL'] = 'http://172.236.231.45:8001'

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService

async def check_shop_token():
    """检查店铺的access_token"""
    db = SessionLocal()
    try:
        # 查找"festival finds"店铺
        shop = db.query(Shop).filter(Shop.shop_name.ilike('%festival finds%')).first()
        
        if not shop:
            print("❌ 未找到 'festival finds' 店铺")
            # 列出所有店铺
            all_shops = db.query(Shop).all()
            print(f"\n当前共有 {len(all_shops)} 个店铺:")
            for s in all_shops:
                print(f"  - {s.shop_name} (ID: {s.id})")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name}")
        print(f"   店铺ID: {shop.id}")
        print(f"   区域: {shop.region}")
        print(f"   是否激活: {shop.is_active}")
        print(f"   最后同步时间: {shop.last_sync_at}")
        print(f"\n📋 配置信息:")
        print(f"   API Base URL: {shop.api_base_url or '使用默认'}")
        print(f"   App Key: {shop.app_key[:20] + '...' if shop.app_key else '未配置'}")
        print(f"   App Secret: {'已配置' if shop.app_secret else '未配置'}")
        print(f"   Access Token: {shop.access_token[:30] + '...' if shop.access_token else '❌ 未配置'}")
        print(f"   CN Access Token: {shop.cn_access_token[:30] + '...' if shop.cn_access_token else '未配置'}")
        
        if not shop.access_token:
            print("\n❌ 错误: Access Token 未配置！")
            return
        
        if not shop.is_active:
            print("\n⚠️  警告: 店铺未激活")
        
        # 测试API调用
        print("\n" + "=" * 80)
        print("测试API调用 - 获取订单列表")
        print("=" * 80)
        
        try:
            temu_service = TemuService(shop)
            
            # 获取最近7天的订单
            end_time = int(datetime.now().timestamp())
            begin_time = int((datetime.now() - timedelta(days=7)).timestamp())
            
            print(f"\n请求参数:")
            print(f"  开始时间: {datetime.fromtimestamp(begin_time)} ({begin_time})")
            print(f"  结束时间: {datetime.fromtimestamp(end_time)} ({end_time})")
            print(f"  使用代理: 是")
            print(f"  API URL: {temu_service._get_standard_client().base_url}")
            
            print("\n正在调用API...")
            orders_result = await temu_service.get_orders(
                begin_time=begin_time,
                end_time=end_time,
                page_number=1,
                page_size=10
            )
            
            print("\n✅ API调用成功！")
            print(f"\n返回结果:")
            print(f"  总订单数: {orders_result.get('totalCount', 0)}")
            print(f"  当前页订单数: {len(orders_result.get('pageItems', []))}")
            
            if orders_result.get('pageItems'):
                first_order = orders_result['pageItems'][0]
                parent_order = first_order.get('parentOrderMap', {})
                print(f"\n示例订单:")
                print(f"  父订单号: {parent_order.get('parentOrderSn')}")
                print(f"  订单状态: {parent_order.get('parentOrderStatus')}")
                print(f"  子订单数: {len(first_order.get('orderList', []))}")
            else:
                print("\n⚠️  当前时间范围内没有订单")
            
            await temu_service.close()
            
        except Exception as e:
            print(f"\n❌ API调用失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 检查常见错误
            error_str = str(e)
            if 'access_token' in error_str.lower() or 'token' in error_str.lower():
                print("\n💡 可能的原因:")
                print("  1. Access Token 已过期")
                print("  2. Access Token 不正确")
                print("  3. Access Token 与 App Key/Secret 不匹配")
                print("  4. 需要在卖家中心重新授权")
            elif 'ip' in error_str.lower() or 'whitelist' in error_str.lower():
                print("\n💡 可能的原因:")
                print("  1. IP地址未在白名单中")
                print("  2. 代理服务器配置不正确")
            elif 'permission' in error_str.lower() or 'authorization' in error_str.lower():
                print("\n💡 可能的原因:")
                print("  1. Access Token 没有相应的API权限")
                print("  2. 需要在卖家中心授权相应的API")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_shop_token())

