#!/usr/bin/env python3
"""检查原始数据中的包裹号信息"""
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.temu_orders_raw import TemuOrdersRaw

def check_package_sn():
    db = SessionLocal()
    try:
        # 获取前5条原始订单数据
        raw_orders = db.query(TemuOrdersRaw).filter(
            TemuOrdersRaw.raw_json.isnot(None)
        ).limit(5).all()
        
        print(f"检查 {len(raw_orders)} 条原始订单数据...\n")
        
        for i, raw in enumerate(raw_orders, 1):
            print(f"=== 订单 {i}: {raw.external_order_id} ===")
            data = raw.raw_json
            
            # 检查orderItem中的packageSnInfo
            order_item = data.get('orderItem', {})
            package_sn_info_item = order_item.get('packageSnInfo')
            print(f"orderItem.packageSnInfo: {package_sn_info_item}")
            print(f"  类型: {type(package_sn_info_item)}")
            
            # 检查parentOrderMap中的packageSnInfo
            parent_order = data.get('parentOrderMap', {})
            package_sn_info_parent = parent_order.get('packageSnInfo')
            print(f"parentOrderMap.packageSnInfo: {package_sn_info_parent}")
            print(f"  类型: {type(package_sn_info_parent)}")
            
            # 检查fullOrderData中的packageSnInfo
            full_order_data = data.get('fullOrderData', {})
            if full_order_data:
                order_list = full_order_data.get('orderList', [])
                if order_list:
                    first_order = order_list[0]
                    package_sn_info_full = first_order.get('packageSnInfo')
                    print(f"fullOrderData.orderList[0].packageSnInfo: {package_sn_info_full}")
                    print(f"  类型: {type(package_sn_info_full)}")
            
            # 打印完整的orderItem结构（只显示前500字符）
            order_item_str = json.dumps(order_item, indent=2, ensure_ascii=False)
            if len(order_item_str) > 500:
                order_item_str = order_item_str[:500] + "..."
            print(f"\norderItem 完整结构（前500字符）:\n{order_item_str}")
            
            print("\n" + "="*50 + "\n")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_package_sn()


