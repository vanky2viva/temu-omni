#!/usr/bin/env python3
"""测试查询订单金额接口"""
import sys
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService

async def test_order_amount():
    """测试查询订单金额"""
    db = SessionLocal()
    try:
        # 获取活跃店铺
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 测试店铺: {shop.shop_name}\n")
        
        temu_service = TemuService(shop)
        
        # 先获取一个订单号（从订单列表中获取）
        print("=" * 80)
        print("步骤1: 获取订单列表")
        print("=" * 80)
        try:
            from datetime import datetime, timedelta
            end_time = int(datetime.now().timestamp())
            begin_time = int((datetime.now() - timedelta(days=7)).timestamp())
            
            orders_result = await temu_service.get_orders(
                begin_time=begin_time,
                end_time=end_time,
                page_number=1,
                page_size=5
            )
            
            total_items = orders_result.get('totalItemNum', 0)
            page_items = orders_result.get('pageItems', [])
            
            print(f"订单总数: {total_items}")
            print(f"当前页订单数: {len(page_items) if isinstance(page_items, list) else 0}\n")
            
            if not page_items or len(page_items) == 0:
                print("⚠️  没有找到订单，无法测试订单金额查询")
                return
            
            # 获取第一个订单的订单号
            first_order = page_items[0]
            parent_order = first_order.get('parentOrderMap', {})
            order_list = first_order.get('orderList', [])
            
            if not parent_order or not order_list:
                print("⚠️  订单数据格式不完整")
                return
            
            parent_order_sn = parent_order.get('parentOrderSn')
            first_child_order_sn = order_list[0].get('orderSn') if order_list else None
            
            print(f"父订单号: {parent_order_sn}")
            if first_child_order_sn:
                print(f"子订单号: {first_child_order_sn}")
            print()
            
        except Exception as e:
            print(f"❌ 获取订单列表失败: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 测试查询订单金额（使用父订单号）
        print("=" * 80)
        print("步骤2: 查询订单金额（使用父订单号）")
        print("=" * 80)
        try:
            if parent_order_sn:
                amount_result = await temu_service.get_order_amount(parent_order_sn)
                print(f"✅ 查询成功")
                print(f"响应数据:")
                print(json.dumps(amount_result, ensure_ascii=False, indent=2))
            else:
                print("⚠️  没有父订单号，跳过测试")
        except Exception as e:
            print(f"❌ 查询订单金额失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试查询订单金额（使用子订单号）
        if first_child_order_sn:
            print("\n" + "=" * 80)
            print("步骤3: 查询订单金额（使用子订单号）")
            print("=" * 80)
            try:
                amount_result = await temu_service.get_order_amount(first_child_order_sn)
                print(f"✅ 查询成功")
                print(f"响应数据:")
                print(json.dumps(amount_result, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"❌ 查询订单金额失败: {e}")
                import traceback
                traceback.print_exc()
        
        await temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_order_amount())


