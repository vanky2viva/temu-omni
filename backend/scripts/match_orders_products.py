#!/usr/bin/env python3
"""检查订单和商品的ID匹配关系"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order
from app.models.product import Product


def match_orders_products():
    """检查订单和商品的ID匹配关系"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("检查订单和商品ID匹配关系")
        print("=" * 80)
        
        # 获取一个示例订单
        order = db.query(Order).first()
        
        if not order:
            print("没有订单数据")
            return
        
        print(f"\n示例订单:")
        print(f"  订单号: {order.order_sn}")
        print(f"  product_sku: {order.product_sku}")
        print(f"  spu_id: {order.spu_id}")
        print(f"  notes: {order.notes}")
        
        # 从notes中提取goods_id
        if order.notes:
            import re
            match = re.search(r'GoodsID: (\w+)', order.notes)
            if match:
                goods_id = match.group(1)
                print(f"  goods_id (从notes提取): {goods_id}")
        
        # 获取一个示例商品
        product = db.query(Product).filter(Product.shop_id == order.shop_id).first()
        
        if not product:
            print("\n没有商品数据")
            return
        
        print(f"\n示例商品 (同一店铺):")
        print(f"  product_id: {product.product_id}")
        print(f"  sku: {product.sku}")
        print(f"  spu_id: {product.spu_id}")
        print(f"  skc_id: {product.skc_id}")
        print(f"  product_name: {product.product_name[:50]}")
        
        # 尝试通过SPU匹配
        print(f"\n尝试通过SPU匹配:")
        orders_with_spu = db.query(Order).filter(
            Order.shop_id == order.shop_id,
            Order.spu_id.isnot(None),
            Order.spu_id != ''
        ).limit(5).all()
        
        if orders_with_spu:
            print(f"找到 {len(orders_with_spu)} 个有SPU的订单")
            for o in orders_with_spu:
                print(f"\n  订单: {o.order_sn}")
                print(f"    spu_id: {o.spu_id}")
                print(f"    product_sku: {o.product_sku}")
                
                # 尝试匹配商品
                matched_product = db.query(Product).filter(
                    Product.shop_id == o.shop_id,
                    Product.spu_id == o.spu_id
                ).first()
                
                if matched_product:
                    print(f"    ✅ 匹配到商品: {matched_product.sku} - {matched_product.product_name[:40]}")
                else:
                    print(f"    ❌ 未匹配到商品")
        else:
            print("没有包含SPU的订单")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    match_orders_products()

