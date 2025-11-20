#!/usr/bin/env python3
"""展示订单的原始数据字段"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.order import Order
from sqlalchemy import or_

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

def main():
    db = SessionLocal()
    try:
        order_sn = "PO-211-01096246467191000"
        
        print(f"查询订单: {order_sn}\n")
        
        # 查找订单
        orders = db.query(Order).filter(
            or_(
                Order.parent_order_sn == order_sn,
                Order.order_sn == order_sn
            )
        ).all()
        
        if not orders:
            print(f"❌ 未找到订单 {order_sn}")
            return
        
        order = orders[0]
        print(f"✅ 找到订单: {order.order_sn}")
        print(f"   父订单号: {order.parent_order_sn}")
        print(f"   商品名称: {order.product_name}")
        print(f"   当前金额: {order.total_price}\n")
        
        # 解析原始数据
        if order.raw_data:
            try:
                raw_data = json.loads(order.raw_data)
                
                print("=" * 80)
                print("1. 完整原始数据JSON")
                print("=" * 80)
                print(json.dumps(raw_data, ensure_ascii=False, indent=2))
                
                # 提取所有字段
                print("\n" + "=" * 80)
                print("2. 所有字段路径列表")
                print("=" * 80)
                
                all_fields = extract_fields(raw_data)
                all_fields.sort(key=lambda x: x["path"])
                
                for field in all_fields:
                    value_str = ""
                    if field["value"] is not None:
                        value_str = str(field["value"])
                        if len(value_str) > 60:
                            value_str = value_str[:60] + "..."
                        value_str = f" = {value_str}"
                    print(f"  {field['path']}: {field['type']}{value_str}")
                
                # 金额相关字段
                print("\n" + "=" * 80)
                print("3. 金额相关字段（重点）")
                print("=" * 80)
                
                amount_keywords = ['amount', 'price', 'total', 'cost', 'fee', 'money', 'value', 'sum', 'paid', 'settlement', 'transaction', 'goodsPrice', 'goodsTotalPrice', 'unitPrice', 'unit_price']
                
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
                        print(f"  💰 {field['path']}: {field['type']}{value_str}")
                else:
                    print("  ⚠️  未找到明显的金额字段")
                
                # 订单号相关字段
                print("\n" + "=" * 80)
                print("4. 订单号相关字段")
                print("=" * 80)
                
                order_keywords = ['order', 'sn', 'id']
                
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
                
            except json.JSONDecodeError as e:
                print(f"❌ 解析原始数据失败: {e}")
        else:
            print("⚠️  订单没有原始数据")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()


