#!/usr/bin/env python3
"""检查订单原始数据，查找真实的SKU字段"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order


def check_order_raw_data(shop_name: str = None):
    """
    检查订单原始数据
    
    Args:
        shop_name: 店铺名称
    """
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("检查订单原始数据")
        print("=" * 80)
        
        # 查询订单
        query = db.query(Order)
        
        if shop_name:
            from app.models.shop import Shop
            shop = db.query(Shop).filter(Shop.shop_name == shop_name).first()
            if not shop:
                print(f"❌ 未找到店铺: {shop_name}")
                return
            query = query.filter(Order.shop_id == shop.id)
        
        # 获取前5个订单
        orders = query.limit(5).all()
        
        for idx, order in enumerate(orders, 1):
            print(f"\n{'='*80}")
            print(f"订单 {idx}: {order.order_sn}")
            print(f"{'='*80}")
            print(f"product_sku字段: {order.product_sku}")
            print(f"spu_id字段: {order.spu_id}")
            
            if order.raw_data:
                try:
                    raw_data = json.loads(order.raw_data)
                    print(f"\n原始数据结构:")
                    
                    # 打印order_item相关字段
                    if 'order_item' in raw_data:
                        order_item = raw_data['order_item']
                        print(f"\n  order_item相关字段:")
                        for key in ['orderSn', 'spec', 'sku', 'productSku', 'outSkuSn', 
                                   'extCode', 'skuSn', 'spuId', 'goodsId', 'goodsName', 
                                   'productName', 'goodsSpec']:
                            if key in order_item:
                                value = order_item[key]
                                if isinstance(value, str) and len(value) > 50:
                                    value = value[:50] + "..."
                                print(f"    {key}: {value}")
                    
                    # 打印parent_order相关字段
                    if 'parent_order' in raw_data:
                        parent_order = raw_data['parent_order']
                        print(f"\n  parent_order相关字段:")
                        for key in ['parentOrderSn', 'productSku', 'sku', 'outSkuSn']:
                            if key in parent_order:
                                print(f"    {key}: {parent_order[key]}")
                    
                except json.JSONDecodeError:
                    print("  ⚠️  无法解析JSON数据")
            else:
                print("  ⚠️  没有原始数据")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    shop_name = None
    if len(sys.argv) > 1:
        shop_name = sys.argv[1]
    
    check_order_raw_data(shop_name)

