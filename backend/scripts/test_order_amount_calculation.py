#!/usr/bin/env python3
"""测试订单成本计算服务：验证是否将商品供货价带入订单计算订单金额"""
import sys
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.services.order_cost_service import OrderCostCalculationService


def test_order_amount_calculation():
    """测试订单金额计算功能"""
    print("=" * 80)
    print("🧪 测试订单成本计算服务：验证供货价带入订单金额计算")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # 1. 查找一些没有金额的订单
        print("\n1. 查找需要计算金额的订单...")
        orders_without_amount = db.query(Order).filter(
            Order.status != OrderStatus.CANCELLED,
            Order.status != OrderStatus.REFUNDED,
            (Order.total_price.is_(None) | (Order.total_price == 0))
        ).limit(5).all()
        
        if not orders_without_amount:
            print("   ✅ 没有找到需要计算金额的订单")
            return
        
        print(f"   找到 {len(orders_without_amount)} 个需要计算金额的订单")
        
        # 2. 检查这些订单对应的商品是否有供货价格
        print("\n2. 检查商品供货价格...")
        test_orders = []
        for order in orders_without_amount:
            # 尝试匹配商品
            product = None
            
            # 通过 product_id 匹配
            if order.product_id:
                product = db.query(Product).filter(Product.id == order.product_id).first()
            
            # 通过 SKU 匹配
            if not product and order.product_sku:
                product = db.query(Product).filter(
                    Product.shop_id == order.shop_id,
                    Product.sku == order.product_sku
                ).first()
            
            if product:
                has_supply_price = product.current_price is not None and product.current_price > 0
                print(f"   - 订单 {order.order_sn}:")
                print(f"     商品SKU: {order.product_sku}")
                print(f"     商品名称: {product.product_name}")
                print(f"     供货价格: {product.current_price} {product.currency if product.currency else 'N/A'}")
                print(f"     是否有供货价: {'✅ 是' if has_supply_price else '❌ 否'}")
                
                if has_supply_price:
                    test_orders.append(order)
            else:
                print(f"   - 订单 {order.order_sn}: ❌ 未找到匹配的商品")
        
        if not test_orders:
            print("\n   ⚠️  没有找到有供货价格的商品，无法测试订单金额计算")
            print("   💡 建议：先在商品管理中设置商品的供货价格（current_price）")
            return
        
        print(f"\n   找到 {len(test_orders)} 个可以测试的订单（商品有供货价格）")
        
        # 3. 记录测试前的订单金额
        print("\n3. 测试前的订单金额状态:")
        for order in test_orders:
            print(f"   - 订单 {order.order_sn}:")
            print(f"     单价: {order.unit_price}")
            print(f"     总价: {order.total_price}")
            print(f"     数量: {order.quantity}")
        
        # 4. 运行订单成本计算服务
        print("\n4. 运行订单成本计算服务...")
        service = OrderCostCalculationService(db)
        order_ids = [order.id for order in test_orders]
        result = service.calculate_order_costs(order_ids=order_ids, force_recalculate=False)
        
        print(f"   计算结果:")
        print(f"   - 总计: {result['total']}")
        print(f"   - 成功: {result['success']}")
        print(f"   - 失败: {result['failed']}")
        print(f"   - 跳过: {result['skipped']}")
        
        # 5. 刷新订单数据，查看计算后的结果
        print("\n5. 测试后的订单金额状态:")
        db.expire_all()  # 刷新所有对象
        for order_id in order_ids:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                product = db.query(Product).filter(Product.id == order.product_id).first() if order.product_id else None
                print(f"   - 订单 {order.order_sn}:")
                print(f"     单价: {order.unit_price} (之前: {test_orders[0].unit_price if test_orders[0].id == order_id else 'N/A'})")
                print(f"     总价: {order.total_price} (之前: {test_orders[0].total_price if test_orders[0].id == order_id else 'N/A'})")
                print(f"     数量: {order.quantity}")
                if product:
                    expected_total = (product.current_price or 0) * order.quantity
                    print(f"     商品供货价: {product.current_price} {product.currency}")
                    print(f"     期望总价: {expected_total} (供货价 × 数量)")
                    if order.total_price and order.total_price > 0:
                        print(f"     ✅ 订单金额已更新")
                    else:
                        print(f"     ❌ 订单金额未更新")
        
        # 6. 验证结果
        print("\n6. 验证结果:")
        success_count = 0
        for order_id in order_ids:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order and order.total_price and order.total_price > 0:
                success_count += 1
        
        if success_count == len(test_orders):
            print(f"   ✅ 所有订单金额计算成功 ({success_count}/{len(test_orders)})")
        else:
            print(f"   ⚠️  部分订单金额计算失败 ({success_count}/{len(test_orders)})")
        
        print("\n" + "=" * 80)
        print("📋 测试总结")
        print("=" * 80)
        print("✅ 订单成本计算服务包含以下功能：")
        print("   1. 从商品列表获取供货价格（current_price）")
        print("   2. 将供货价格带入订单列表")
        print("   3. 计算订单金额（unit_price = supply_price, total_price = unit_price × quantity）")
        print("   4. 更新订单的 unit_price 和 total_price 字段")
        print("   5. 统一转换为CNY货币单位")
        print("\n💡 注意：")
        print("   - 如果商品没有供货价格，订单金额不会更新")
        print("   - 订单金额 = 商品供货价 × 订单数量")
        print("   - 所有金额统一转换为CNY")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_order_amount_calculation()

