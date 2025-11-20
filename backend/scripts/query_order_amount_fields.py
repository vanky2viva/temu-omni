#!/usr/bin/env python3
"""查询订单金额并展示所有返回字段"""
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

async def query_order_amount():
    """查询订单金额并展示字段"""
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
        
        # 要查询的订单号
        order_sn = "PO-211-01096246467191000"
        
        print("=" * 80)
        print(f"查询订单金额 - 订单号: {order_sn}")
        print("=" * 80)
        
        try:
            amount_result = await temu_service.get_order_amount(order_sn)
            
            print(f"\n✅ 查询成功\n")
            
            # 1. 完整JSON输出
            print("=" * 80)
            print("1. 完整JSON响应")
            print("=" * 80)
            print(json.dumps(amount_result, ensure_ascii=False, indent=2))
            
            # 2. 字段结构分析
            print("\n" + "=" * 80)
            print("2. 字段结构分析")
            print("=" * 80)
            print_dict_structure(amount_result)
            
            # 3. 提取所有字段路径
            print("\n" + "=" * 80)
            print("3. 所有字段路径列表")
            print("=" * 80)
            
            def extract_fields(obj, path="", fields_list=None):
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
            
            all_fields = extract_fields(amount_result)
            
            # 按路径排序
            all_fields.sort(key=lambda x: x["path"])
            
            # 打印字段列表
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
            
            amount_keywords = ['amount', 'price', 'total', 'cost', 'fee', 'money', 'value', 'sum', 'paid', 'settlement', 'transaction']
            
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
                print("  ⚠️  未找到明显的金额字段，请查看完整响应")
            
            # 5. 订单相关信息
            print("\n" + "=" * 80)
            print("5. 订单相关信息")
            print("=" * 80)
            
            order_keywords = ['order', 'sn', 'id', 'status', 'time', 'date', 'currency']
            
            order_fields = []
            for field in all_fields:
                field_lower = field["path"].lower()
                if any(keyword in field_lower for keyword in order_keywords):
                    order_fields.append(field)
            
            if order_fields:
                for field in order_fields:
                    value_str = ""
                    if field["value"] is not None:
                        value_str = f" = {field['value']}"
                    print(f"  📦 {field['path']}: {field['type']}{value_str}")
            else:
                print("  ⚠️  未找到订单相关字段")
        
        except Exception as e:
            print(f"❌ 查询订单金额失败: {e}")
            import traceback
            traceback.print_exc()
        
        await temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(query_order_amount())


