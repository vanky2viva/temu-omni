#!/usr/bin/env python3
"""展示订单详情的完整响应数据"""
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

def extract_all_fields(obj, path="", fields_list=None):
    """提取所有字段路径"""
    if fields_list is None:
        fields_list = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            fields_list.append({
                "path": current_path,
                "type": type(value).__name__,
                "value": value if not isinstance(value, (dict, list)) else None
            })
            if isinstance(value, (dict, list)):
                extract_all_fields(value, current_path, fields_list)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            current_path = f"{path}[{idx}]" if path else f"[{idx}]"
            if isinstance(item, (dict, list)):
                extract_all_fields(item, current_path, fields_list)
            else:
                fields_list.append({
                    "path": current_path,
                    "type": type(item).__name__,
                    "value": item
                })
    
    return fields_list

async def show_order_detail():
    """展示订单详情"""
    db = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        temu_service = TemuService(shop)
        
        # 先从订单列表中获取一个订单
        from datetime import datetime, timedelta
        end_time = int(datetime.now().timestamp())
        begin_time = int((datetime.now() - timedelta(days=30)).timestamp())
        
        print("步骤1: 从订单列表中获取订单...")
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
        
        first_order = page_items[0]
        parent_order = first_order.get('parentOrderMap', {})
        parent_order_sn = parent_order.get('parentOrderSn')
        
        if not parent_order_sn:
            print("❌ 未找到父订单号")
            return
        
        print(f"✅ 找到订单: {parent_order_sn}\n")
        
        print("=" * 80)
        print(f"步骤2: 查询订单详情 - 父订单号: {parent_order_sn}")
        print("=" * 80)
        
        try:
            detail_result = await temu_service.get_order_detail(parent_order_sn)
            
            print("\n✅ 查询成功\n")
            
            # 1. 完整JSON输出
            print("=" * 80)
            print("1. 完整JSON响应")
            print("=" * 80)
            print(json.dumps(detail_result, ensure_ascii=False, indent=2))
            
            # 2. 提取所有字段
            print("\n" + "=" * 80)
            print("2. 所有字段路径列表")
            print("=" * 80)
            
            all_fields = extract_all_fields(detail_result)
            all_fields.sort(key=lambda x: x["path"])
            
            for field in all_fields:
                value_str = ""
                if field["value"] is not None:
                    value_str = str(field["value"])
                    if len(value_str) > 60:
                        value_str = value_str[:60] + "..."
                    value_str = f" = {value_str}"
                print(f"  {field['path']}: {field['type']}{value_str}")
            
            # 3. 搜索所有可能包含签收时间的字段
            print("\n" + "=" * 80)
            print("3. 签收时间相关字段（搜索 receipt, delivery, time, str）")
            print("=" * 80)
            
            keywords = ['receipt', 'delivery', 'time', 'str', 'date', '签收']
            relevant_fields = []
            
            for field in all_fields:
                field_lower = field["path"].lower()
                if any(keyword in field_lower for keyword in keywords):
                    relevant_fields.append(field)
            
            if relevant_fields:
                for field in relevant_fields:
                    value_str = ""
                    if field["value"] is not None:
                        value_str = f" = {field['value']}"
                    print(f"  🔍 {field['path']}: {field['type']}{value_str}")
            else:
                print("  ❌ 未找到相关字段")
            
            # 4. 特别搜索 parentReceiptTimeStr
            print("\n" + "=" * 80)
            print("4. 搜索 parentReceiptTimeStr 字段")
            print("=" * 80)
            
            receipt_time_str_fields = [f for f in all_fields if 'parentreceipttimestr' in f['path'].lower()]
            if receipt_time_str_fields:
                for field in receipt_time_str_fields:
                    print(f"  ✅ 找到: {field['path']}: {field['type']} = {field['value']}")
            else:
                print("  ❌ 未找到 parentReceiptTimeStr 字段")
                print("\n  可能的原因:")
                print("  1. 该字段可能不在订单详情API的响应中")
                print("  2. 该字段可能只在特定条件下返回（如订单已签收）")
                print("  3. 该字段可能在其他API中（如物流跟踪API）")
        
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
        
        await temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(show_order_detail())

