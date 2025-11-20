#!/usr/bin/env python3
"""显示订单原始数据中的所有字段"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order


def show_raw_data_fields():
    """显示订单原始数据字段"""
    db = SessionLocal()
    
    try:
        print("=" * 120)
        print("订单原始数据 (raw_data) 详细字段")
        print("=" * 120)
        
        # 获取前2个有原始数据的订单
        orders = db.query(Order).filter(Order.raw_data.isnot(None)).limit(2).all()
        
        if not orders:
            print("没有包含原始数据的订单")
            return
        
        for idx, order in enumerate(orders, 1):
            print(f"\n{'='*120}")
            print(f"【订单 {idx}】{order.order_sn}")
            print(f"{'='*120}")
            print(f"商品名称: {order.product_name[:60]}")
            print(f"product_sku (数据库): {order.product_sku}")
            print(f"spu_id (数据库): {order.spu_id or '空'}")
            print(f"notes: {order.notes}")
            
            try:
                raw_data = json.loads(order.raw_data)
                
                # order_item 字段
                if 'order_item' in raw_data:
                    print(f"\n{'─'*120}")
                    print("【A】order_item 字段（子订单数据）")
                    print(f"{'─'*120}")
                    order_item = raw_data['order_item']
                    
                    # 重点字段
                    important_fields = [
                        'orderSn', 'goodsId', 'spuId', 'skuId', 'skcId',
                        'spec', 'sku', 'productSku', 'goodsSku',
                        'extCode', 'outSkuSn', 'skuSn',
                        'goodsName', 'productName',
                        'goodsPrice', 'goodsTotalPrice', 'goodsNumber'
                    ]
                    
                    print("\n  🔑 重点ID/SKU字段:")
                    for field in important_fields:
                        if field in order_item:
                            value = order_item[field]
                            if isinstance(value, str) and len(value) > 80:
                                value = value[:80] + "..."
                            print(f"    {field:<25}: {value}")
                    
                    print(f"\n  📋 所有字段 (按字母顺序):")
                    sorted_keys = sorted(order_item.keys())
                    for key in sorted_keys:
                        value = order_item[key]
                        if isinstance(value, str) and len(value) > 80:
                            value = value[:80] + "..."
                        elif isinstance(value, (dict, list)):
                            value = f"<{type(value).__name__} with {len(value)} items>"
                        print(f"    {key:<25}: {value}")
                
                # parent_order 字段
                if 'parent_order' in raw_data:
                    print(f"\n{'─'*120}")
                    print("【B】parent_order 字段（父订单数据）")
                    print(f"{'─'*120}")
                    parent_order = raw_data['parent_order']
                    
                    # 重点字段
                    important_fields = [
                        'parentOrderSn', 'parentOrderStatus',
                        'parentOrderTime', 'parentShippingTime',
                        'customerId', 'buyerId'
                    ]
                    
                    print("\n  🔑 重点字段:")
                    for field in important_fields:
                        if field in parent_order:
                            value = parent_order[field]
                            if isinstance(value, (dict, list)):
                                value = f"<{type(value).__name__}>"
                            print(f"    {field:<25}: {value}")
                    
                    print(f"\n  📋 所有字段 (按字母顺序):")
                    sorted_keys = sorted(parent_order.keys())
                    for key in sorted_keys:
                        value = parent_order[key]
                        if isinstance(value, str) and len(value) > 80:
                            value = value[:80] + "..."
                        elif isinstance(value, (dict, list)):
                            value = f"<{type(value).__name__} with {len(value)} items>"
                        print(f"    {key:<25}: {value}")
                
            except json.JSONDecodeError as e:
                print(f"\n⚠️  无法解析JSON: {e}")
        
        print(f"\n{'='*120}")
        print("✅ 原始数据字段显示完成")
        print(f"{'='*120}")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    show_raw_data_fields()

