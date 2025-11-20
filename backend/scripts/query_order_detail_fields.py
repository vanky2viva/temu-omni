#!/usr/bin/env python3
"""查询订单详情并展示所有返回字段"""
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

def print_dict_structure(data, prefix="", max_depth=10, current_depth=0):
    """递归打印字典结构"""
    if current_depth >= max_depth:
        print(f"{prefix}... (达到最大深度)")
        return
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}: {{")
                print_dict_structure(value, prefix + "  ", max_depth, current_depth + 1)
                print(f"{prefix}}}")
            elif isinstance(value, list):
                print(f"{prefix}{key}: [")
                if len(value) > 0:
                    print(f"{prefix}  [0]: {type(value[0]).__name__}")
                    if isinstance(value[0], dict):
                        print_dict_structure(value[0], prefix + "    ", max_depth, current_depth + 1)
                    elif len(value) > 1:
                        print(f"{prefix}  ... (共 {len(value)} 项)")
                else:
                    print(f"{prefix}  (空列表)")
                print(f"{prefix}]")
            else:
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"{prefix}{key}: {type(value).__name__} = {value_str}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            print(f"{prefix}[{idx}]:")
            print_dict_structure(item, prefix + "  ", max_depth, current_depth + 1)
    else:
        value_str = str(data)
        if len(value_str) > 100:
            value_str = value_str[:100] + "..."
        print(f"{prefix}{type(data).__name__}: {value_str}")

def extract_fields(obj, path="", fields_list=None):
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
                extract_fields(value, current_path, fields_list)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            current_path = f"{path}[{idx}]" if path else f"[{idx}]"
            if isinstance(item, (dict, list)):
                extract_fields(item, current_path, fields_list)
            else:
                fields_list.append({
                    "path": current_path,
                    "type": type(item).__name__,
                    "value": item
                })
    
    return fields_list

async def query_order_detail():
    """查询订单详情并展示字段"""
    db = SessionLocal()
    try:
        # 获取活跃店铺
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 测试店铺: {shop.shop_name}")
        print(f"✅ 代理服务器: {os.getenv('TEMU_API_PROXY_URL')}\n")
        
        temu_service = TemuService(shop)
        
        # 要查询的订单号（先尝试父订单号，如果失败再尝试子订单号）
        parent_order_sn = "PO-211-01096246467191000"
        
        print("=" * 80)
        print(f"查询订单详情 - 父订单号: {parent_order_sn}")
        print("=" * 80)
        
        try:
            # 先获取订单列表，找到对应的子订单号
            from datetime import datetime, timedelta
            end_time = int(datetime.now().timestamp())
            begin_time = int((datetime.now() - timedelta(days=30)).timestamp())
            
            print("\n步骤1: 从订单列表中查找该订单...")
            orders_result = await temu_service.get_orders(
                begin_time=begin_time,
                end_time=end_time,
                page_number=1,
                page_size=100
            )
            
            page_items = orders_result.get('pageItems', [])
            target_order = None
            child_order_sn = None
            
            for item in page_items:
                parent_order = item.get('parentOrderMap', {})
                if parent_order.get('parentOrderSn') == parent_order_sn:
                    target_order = item
                    order_list = item.get('orderList', [])
                    if order_list:
                        child_order_sn = order_list[0].get('orderSn')
                    break
            
            if not target_order:
                print(f"⚠️  未在订单列表中找到订单 {parent_order_sn}")
                print("尝试直接使用父订单号查询详情...")
                child_order_sn = parent_order_sn
            
            if child_order_sn:
                print(f"✅ 找到子订单号: {child_order_sn}\n")
                
                print("步骤2: 查询订单详情...")
                detail_result = await temu_service.get_order_detail(child_order_sn)
                
                print(f"\n✅ 查询成功\n")
                
                # 1. 完整JSON输出
                print("=" * 80)
                print("1. 完整JSON响应")
                print("=" * 80)
                print(json.dumps(detail_result, ensure_ascii=False, indent=2))
                
                # 2. 字段结构分析
                print("\n" + "=" * 80)
                print("2. 字段结构分析")
                print("=" * 80)
                print_dict_structure(detail_result)
                
                # 3. 提取所有字段路径
                print("\n" + "=" * 80)
                print("3. 所有字段路径列表")
                print("=" * 80)
                
                all_fields = extract_fields(detail_result)
                all_fields.sort(key=lambda x: x["path"])
                
                for field in all_fields:
                    value_str = ""
                    if field["value"] is not None:
                        value_str = str(field["value"])
                        if len(value_str) > 50:
                            value_str = value_str[:50] + "..."
                        value_str = f" = {value_str}"
                    print(f"  {field['path']}: {field['type']}{value_str}")
                
                # 4. 金额相关字段（重点）
                print("\n" + "=" * 80)
                print("4. 金额相关字段（重点）")
                print("=" * 80)
                
                amount_keywords = ['amount', 'price', 'total', 'cost', 'fee', 'money', 'value', 'sum', 'paid', 'settlement', 'transaction', 'goodsPrice', 'goodsTotalPrice']
                
                amount_fields = []
                for field in all_fields:
                    field_lower = field["path"].lower()
                    if any(keyword in field_lower for keyword in amount_keywords):
                        amount_fields.append(field)
                
                if amount_fields:
                    for field in amount_fields:
                        value_str = ""
                        if field["value"] is not None:
                            value_str = f" = {field['value']}"
                        print(f"  ✅ {field['path']}: {field['type']}{value_str}")
                else:
                    print("  ⚠️  未找到明显的金额字段")
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
        
        await temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(query_order_detail())


