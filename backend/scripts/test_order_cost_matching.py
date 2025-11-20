#!/usr/bin/env python3
"""测试订单与商品SKU匹配及成本利润计算"""
import sys
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.models.order import Order
from app.models.product import Product, ProductCost
from sqlalchemy import func, distinct


def test_order_cost_matching(shop_name: str = None):
    """
    测试订单成本匹配
    
    Args:
        shop_name: 店铺名称，如果为None则显示所有店铺
    """
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("订单成本匹配测试")
        print("=" * 80)
        
        # 查询店铺
        if shop_name:
            shops = db.query(Shop).filter(Shop.shop_name == shop_name).all()
            if not shops:
                print(f"❌ 未找到店铺: {shop_name}")
                return
        else:
            shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        print(f"\n找到 {len(shops)} 个店铺\n")
        
        for shop in shops:
            print("=" * 80)
            print(f"🏪 店铺: {shop.shop_name} (ID: {shop.id})")
            print("=" * 80)
            
            # 统计订单
            total_orders = db.query(Order).filter(Order.shop_id == shop.id).count()
            orders_with_cost = db.query(Order).filter(
                Order.shop_id == shop.id,
                Order.total_cost.isnot(None)
            ).count()
            orders_without_cost = total_orders - orders_with_cost
            
            print(f"\n📊 订单统计:")
            print(f"   总订单数: {total_orders}")
            print(f"   有成本信息: {orders_with_cost} ({orders_with_cost/total_orders*100:.1f}%)" if total_orders > 0 else "   有成本信息: 0 (0%)")
            print(f"   缺少成本信息: {orders_without_cost}")
            
            # 统计商品
            total_products = db.query(Product).filter(Product.shop_id == shop.id).count()
            products_with_cost = db.query(Product).join(ProductCost).filter(
                Product.shop_id == shop.id,
                ProductCost.effective_to.is_(None)
            ).count()
            
            print(f"\n📦 商品统计:")
            print(f"   总商品数（SKU级别）: {total_products}")
            print(f"   有成本价的商品: {products_with_cost} ({products_with_cost/total_products*100:.1f}%)" if total_products > 0 else "   有成本价的商品: 0 (0%)")
            
            # 财务统计（只统计有成本信息的订单）
            if orders_with_cost > 0:
                orders = db.query(Order).filter(
                    Order.shop_id == shop.id,
                    Order.total_cost.isnot(None)
                ).all()
                
                total_gmv = sum(order.total_price for order in orders)
                total_cost = sum(order.total_cost for order in orders)
                total_profit = sum(order.profit for order in orders if order.profit)
                
                if total_gmv > 0:
                    profit_margin = (total_profit / total_gmv) * 100
                else:
                    profit_margin = 0
                
                print(f"\n💰 财务统计（基于 {orders_with_cost} 个订单）:")
                print(f"   GMV（营业额）: {total_gmv:.2f}")
                print(f"   总成本: {total_cost:.2f}")
                print(f"   总利润: {total_profit:.2f}")
                print(f"   利润率: {profit_margin:.2f}%")
            
            # 显示订单明细（前10个）
            print(f"\n📋 订单明细（前10个）:")
            orders = db.query(Order).filter(
                Order.shop_id == shop.id
            ).order_by(Order.order_time.desc()).limit(10).all()
            
            if orders:
                print(f"{'订单号':<20} {'SKU':<15} {'数量':<5} {'总价':<10} {'成本':<10} {'利润':<10} {'状态':<10}")
                print("-" * 95)
                for order in orders:
                    order_sn_short = order.order_sn[:18] + ".." if len(order.order_sn) > 20 else order.order_sn
                    sku_short = (order.product_sku[:13] + "..") if order.product_sku and len(order.product_sku) > 15 else (order.product_sku or "N/A")
                    total_price = f"{order.total_price:.2f}" if order.total_price else "N/A"
                    total_cost = f"{order.total_cost:.2f}" if order.total_cost else "未匹配"
                    profit = f"{order.profit:.2f}" if order.profit else "N/A"
                    status = order.status.value if order.status else "N/A"
                    
                    print(f"{order_sn_short:<20} {sku_short:<15} {order.quantity:<5} {total_price:<10} {total_cost:<10} {profit:<10} {status:<10}")
            else:
                print("   没有订单数据")
            
            # SKU匹配分析
            print(f"\n🔍 SKU匹配分析:")
            
            # 查询订单中的唯一SKU
            order_skus = db.query(distinct(Order.product_sku)).filter(
                Order.shop_id == shop.id,
                Order.product_sku.isnot(None),
                Order.product_sku != ''
            ).all()
            order_sku_set = set(sku[0] for sku in order_skus)
            
            # 查询商品中的SKU
            product_skus = db.query(distinct(Product.sku)).filter(
                Product.shop_id == shop.id,
                Product.sku.isnot(None),
                Product.sku != ''
            ).all()
            product_sku_set = set(sku[0] for sku in product_skus)
            
            # 未匹配的SKU
            unmatched_skus = order_sku_set - product_sku_set
            
            print(f"   订单中的唯一SKU数: {len(order_sku_set)}")
            print(f"   商品库中的SKU数: {len(product_sku_set)}")
            print(f"   未匹配的SKU数: {len(unmatched_skus)}")
            
            if unmatched_skus and len(unmatched_skus) <= 10:
                print(f"\n   未匹配的SKU列表:")
                for sku in list(unmatched_skus)[:10]:
                    print(f"      - {sku}")
            elif unmatched_skus:
                print(f"\n   未匹配的SKU列表（前10个）:")
                for sku in list(unmatched_skus)[:10]:
                    print(f"      - {sku}")
                print(f"      ... 还有 {len(unmatched_skus) - 10} 个")
            
            print()
        
        print("=" * 80)
        print("✅ 测试完成")
        print("=" * 80)
        
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
    
    test_order_cost_matching(shop_name)

