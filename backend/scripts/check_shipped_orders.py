#!/usr/bin/env python3
"""检查已发货订单中的包裹号信息"""
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.temu_orders_raw import TemuOrdersRaw
from app.models.order import Order

def check_shipped_orders():
    db = SessionLocal()
    try:
        # 查找已发货的订单
        shipped_orders = db.query(Order).filter(
            Order.status.in_(['SHIPPED', 'DELIVERED'])
        ).limit(10).all()
        
        print(f"找到 {len(shipped_orders)} 个已发货订单\n")
        
        for order in shipped_orders:
            print(f"=== 订单: {order.order_sn} (状态: {order.status}) ===")
            
            # 查找对应的原始数据
            raw_order = db.query(TemuOrdersRaw).filter(
                TemuOrdersRaw.external_order_id == order.order_sn,
                TemuOrdersRaw.shop_id == order.shop_id
            ).first()
            
            if raw_order:
                data = raw_order.raw_json
                
                # 检查orderItem中的packageSnInfo
                order_item = data.get('orderItem', {})
                package_sn_info_item = order_item.get('packageSnInfo')
                print(f"orderItem.packageSnInfo: {package_sn_info_item}")
                
                # 检查parentOrderMap中的packageSnInfo
                parent_order = data.get('parentOrderMap', {})
                package_sn_info_parent = parent_order.get('packageSnInfo')
                print(f"parentOrderMap.packageSnInfo: {package_sn_info_parent}")
                
                # 检查fullOrderData中的packageSnInfo
                full_order_data = data.get('fullOrderData', {})
                if full_order_data:
                    order_list = full_order_data.get('orderList', [])
                    for idx, o in enumerate(order_list):
                        if o.get('orderSn') == order.order_sn:
                            package_sn_info = o.get('packageSnInfo')
                            print(f"fullOrderData.orderList[{idx}].packageSnInfo: {package_sn_info}")
                            if package_sn_info:
                                print(f"  详细内容: {json.dumps(package_sn_info, indent=2, ensure_ascii=False)}")
                            break
                
                print(f"数据库中保存的包裹号: {order.package_sn}")
            else:
                print("未找到对应的原始数据")
            
            print("\n" + "="*50 + "\n")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_shipped_orders()


