#!/usr/bin/env python3
"""从数据库查询订单并展示字段"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.order import Order
from sqlalchemy import or_

def print_order_fields(order):
    """打印订单的所有字段"""
    print("=" * 80)
    print("订单字段列表")
    print("=" * 80)
    
    # 获取订单的所有属性
    order_dict = {}
    for column in Order.__table__.columns:
        value = getattr(order, column.name, None)
        order_dict[column.name] = {
            "type": str(column.type),
            "value": value,
            "comment": column.comment
        }
    
    # 按字段名排序
    sorted_fields = sorted(order_dict.items())
    
    print("\n字段名 | 类型 | 值 | 说明")
    print("-" * 80)
    for field_name, field_info in sorted_fields:
        value_str = str(field_info["value"]) if field_info["value"] is not None else "None"
        if len(value_str) > 50:
            value_str = value_str[:50] + "..."
        comment = field_info["comment"] or ""
        print(f"{field_name:30} | {field_info['type']:20} | {value_str:30} | {comment}")

def main():
    db = SessionLocal()
    try:
        order_sn = "PO-211-01096246467191000"
        
        print(f"查询订单: {order_sn}\n")
        
        # 先按父订单号查找
        orders = db.query(Order).filter(
            or_(
                Order.parent_order_sn == order_sn,
                Order.order_sn == order_sn
            )
        ).all()
        
        if not orders:
            print(f"❌ 未找到订单 {order_sn}")
            print("\n尝试查找包含该订单号的订单...")
            # 尝试模糊匹配
            orders = db.query(Order).filter(
                or_(
                    Order.parent_order_sn.like(f"%{order_sn}%"),
                    Order.order_sn.like(f"%{order_sn}%")
                )
            ).limit(5).all()
            
            if orders:
                print(f"找到 {len(orders)} 个相关订单:")
                for order in orders:
                    print(f"  - 父订单号: {order.parent_order_sn}, 子订单号: {order.order_sn}")
                print("\n显示第一个订单的字段:")
                print_order_fields(orders[0])
            else:
                print("❌ 未找到任何相关订单")
                print("\n显示订单表结构:")
                print_order_fields(Order())  # 显示空订单的结构
        else:
            print(f"✅ 找到 {len(orders)} 个订单\n")
            
            # 显示第一个订单的详细信息
            order = orders[0]
            print_order_fields(order)
            
            # 如果有多个订单，显示汇总信息
            if len(orders) > 1:
                print("\n" + "=" * 80)
                print(f"共找到 {len(orders)} 个子订单，汇总信息:")
                print("=" * 80)
                total_amount = sum(float(order.total_price or 0) for order in orders)
                print(f"  子订单数量: {len(orders)}")
                print(f"  总金额: {total_amount}")
                print(f"  父订单号: {order.parent_order_sn}")
                print(f"  订单状态: {order.status}")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()


