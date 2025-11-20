#!/usr/bin/env python3
"""检查订单详情API是否返回 parentReceiptTimeStr 字段"""
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

def search_field_in_data(data, search_key, path=""):
    """递归搜索字段"""
    results = []
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            # 检查键名是否包含搜索关键词
            if search_key.lower() in key.lower():
                results.append({
                    "path": current_path,
                    "value": value,
                    "type": type(value).__name__
                })
            # 递归搜索
            if isinstance(value, (dict, list)):
                results.extend(search_field_in_data(value, search_key, current_path))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            current_path = f"{path}[{idx}]" if path else f"[{idx}]"
            if isinstance(item, (dict, list)):
                results.extend(search_field_in_data(item, search_key, current_path))
    return results

async def check_receipt_time():
    """检查签收时间相关字段"""
    db = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 测试店铺: {shop.shop_name}\n")
        
        temu_service = TemuService(shop)
        
        # 从订单列表中获取一个订单
        from datetime import datetime, timedelta
        end_time = int(datetime.now().timestamp())
        begin_time = int((datetime.now() - timedelta(days=30)).timestamp())
        
        print("步骤1: 获取订单列表...")
        orders_result = await temu_service.get_orders(
            begin_time=begin_time,
            end_time=end_time,
            page_number=1,
            page_size=5
        )
        
        page_items = orders_result.get('pageItems', [])
        if not page_items:
            print("❌ 未找到订单")
            return
        
        # 使用第一个订单
        first_order = page_items[0]
        parent_order = first_order.get('parentOrderMap', {})
        order_list = first_order.get('orderList', [])
        
        if not parent_order or not order_list:
            print("❌ 订单数据不完整")
            return
        
        parent_order_sn = parent_order.get('parentOrderSn')
        child_order_sn = order_list[0].get('orderSn')
        
        print(f"✅ 找到订单:")
        print(f"   父订单号: {parent_order_sn}")
        print(f"   子订单号: {child_order_sn}\n")
        
        # 检查订单列表API返回的数据
        print("=" * 80)
        print("1. 订单列表API返回的数据中搜索 receipt 相关字段")
        print("=" * 80)
        
        receipt_fields = search_field_in_data(first_order, "receipt")
        if receipt_fields:
            for field in receipt_fields:
                print(f"  ✅ {field['path']}: {field['type']} = {field['value']}")
        else:
            print("  ❌ 未找到 receipt 相关字段")
        
        # 尝试查询订单详情
        print("\n" + "=" * 80)
        print("2. 查询订单详情API，检查是否返回 parentReceiptTimeStr")
        print("=" * 80)
        
        try:
            # 使用父订单号查询详情（订单详情API需要父订单号）
            detail_result = await temu_service.get_order_detail(parent_order_sn)
            
            print("✅ 订单详情查询成功\n")
            
            # 搜索 receipt 相关字段
            receipt_fields_detail = search_field_in_data(detail_result, "receipt")
            time_str_fields = search_field_in_data(detail_result, "TimeStr")
            parent_receipt_fields = search_field_in_data(detail_result, "parentReceipt")
            
            print("搜索 receipt 相关字段:")
            if receipt_fields_detail:
                for field in receipt_fields_detail:
                    print(f"  ✅ {field['path']}: {field['type']} = {field['value']}")
            else:
                print("  ❌ 未找到 receipt 相关字段")
            
            print("\n搜索 TimeStr 相关字段:")
            if time_str_fields:
                for field in time_str_fields:
                    print(f"  ✅ {field['path']}: {field['type']} = {field['value']}")
            else:
                print("  ❌ 未找到 TimeStr 相关字段")
            
            print("\n搜索 parentReceipt 相关字段:")
            if parent_receipt_fields:
                for field in parent_receipt_fields:
                    print(f"  ✅ {field['path']}: {field['type']} = {field['value']}")
            else:
                print("  ❌ 未找到 parentReceipt 相关字段")
            
            # 显示完整响应（用于查找）
            print("\n" + "=" * 80)
            print("3. 完整订单详情响应（前500字符）")
            print("=" * 80)
            print(json.dumps(detail_result, ensure_ascii=False, indent=2)[:500])
            print("...")
            
        except Exception as e:
            print(f"❌ 查询订单详情失败: {e}")
            print("\n⚠️  可能的原因:")
            print("  1. 订单详情API需要父订单号，但可能返回错误")
            print("  2. 或者该字段不在订单详情API中")
        
        await temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_receipt_time())


