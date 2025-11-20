#!/usr/bin/env python3
"""批量更新订单的成本和利润信息"""
import asyncio
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
from sqlalchemy import and_, or_


def update_order_costs(shop_id: int = None):
    """
    批量更新订单的成本和利润信息
    
    Args:
        shop_id: 店铺ID，如果为None则更新所有店铺的订单
    """
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("批量更新订单成本和利润")
        print("=" * 80)
        
        # 查询需要更新的订单（没有成本信息的订单）
        query = db.query(Order)
        
        if shop_id:
            query = query.filter(Order.shop_id == shop_id)
            print(f"\n🏪 更新店铺ID: {shop_id} 的订单")
        else:
            print(f"\n🏪 更新所有店铺的订单")
        
        # 查找没有成本信息的订单
        orders_without_cost = query.filter(
            or_(
                Order.unit_cost.is_(None),
                Order.total_cost.is_(None),
                Order.profit.is_(None)
            )
        ).all()
        
        print(f"📊 找到 {len(orders_without_cost)} 个需要更新成本的订单")
        
        if not orders_without_cost:
            print("\n✅ 所有订单都已有成本信息")
            return
        
        # 统计信息
        updated_count = 0
        failed_count = 0
        no_match_count = 0
        no_cost_count = 0
        
        print("\n" + "=" * 80)
        print("🔄 开始更新订单成本...")
        print("=" * 80)
        
        for idx, order in enumerate(orders_without_cost, 1):
            if idx % 100 == 0:
                print(f"   处理进度: {idx}/{len(orders_without_cost)}")
            
            try:
                # 从raw_data中提取productSkuId和extCode
                product_sku_id = None
                ext_code = None
                spu_id = order.spu_id
                
                if order.raw_data:
                    import json
                    try:
                        raw_data = json.loads(order.raw_data)
                        order_list = raw_data.get('orderList', [])
                        if order_list:
                            order_item = order_list[0]
                            product_list = order_item.get('productList', [])
                            if product_list:
                                product_info = product_list[0]
                                product_sku_id = product_info.get('productSkuId')
                                ext_code = product_info.get('extCode')
                                spu_id = product_info.get('productId') or spu_id
                    except:
                        pass
                
                # 尝试匹配商品：优先通过productSkuId，其次extCode (SKU货号)，最后spu_id
                product = None
                match_method = None
                
                # 优先级1：通过productSkuId匹配
                if product_sku_id:
                    product = db.query(Product).filter(
                        Product.shop_id == order.shop_id,
                        Product.product_id == str(product_sku_id)
                    ).first()
                    if product:
                        match_method = "productSkuId"
                
                # 优先级2：通过extCode (SKU货号) 匹配
                if not product and ext_code:
                    product = db.query(Product).filter(
                        Product.shop_id == order.shop_id,
                        Product.sku == ext_code
                    ).first()
                    if product:
                        match_method = "extCode"
                
                # 优先级3：通过spu_id匹配
                if not product and spu_id:
                    product = db.query(Product).filter(
                        Product.shop_id == order.shop_id,
                        Product.spu_id == spu_id
                    ).first()
                    if product:
                        match_method = "spu_id"
                
                # 优先级4：通过product_sku匹配（最后尝试，因为可能是规格描述）
                if not product and order.product_sku:
                    product = db.query(Product).filter(
                        Product.shop_id == order.shop_id,
                        Product.sku == order.product_sku
                    ).first()
                    if product:
                        match_method = "product_sku"
                
                if not product:
                    no_match_count += 1
                    logger_msg = f"   ⚠️  订单 {order.order_sn} (productSkuId: {product_sku_id}, extCode: {ext_code}, spu_id: {spu_id}) 未找到匹配商品"
                    if idx <= 10:  # 只打印前10个警告
                        print(logger_msg)
                    continue
                
                # 查询在订单时间有效的成本记录
                cost_record = db.query(ProductCost).filter(
                    ProductCost.product_id == product.id,
                    ProductCost.effective_from <= order.order_time,
                    or_(
                        ProductCost.effective_to.is_(None),
                        ProductCost.effective_to > order.order_time
                    )
                ).order_by(ProductCost.effective_from.desc()).first()
                
                if not cost_record:
                    no_cost_count += 1
                    logger_msg = f"   ⚠️  订单 {order.order_sn} SKU {order.product_sku} 未找到成本记录"
                    if idx <= 10:  # 只打印前10个警告
                        print(logger_msg)
                    continue
                
                # 更新成本和利润
                order.product_id = product.id
                order.unit_cost = cost_record.cost_price
                order.total_cost = cost_record.cost_price * Decimal(order.quantity)
                order.profit = order.total_price - order.total_cost
                
                updated_count += 1
                
                # 打印前10个成功更新的订单
                if updated_count <= 10:
                    print(
                        f"   ✅ 订单 {order.order_sn}: "
                        f"SKU={order.product_sku}, "
                        f"数量={order.quantity}, "
                        f"总价={order.total_price}, "
                        f"成本={order.total_cost}, "
                        f"利润={order.profit}"
                    )
                
            except Exception as e:
                failed_count += 1
                print(f"   ❌ 订单 {order.order_sn} 更新失败: {e}")
                continue
        
        # 提交更改
        if updated_count > 0:
            print("\n" + "=" * 80)
            print("💾 保存更改...")
            db.commit()
            print("✅ 更改已保存")
        
        # 统计结果
        print("\n" + "=" * 80)
        print("📊 更新统计:")
        print("=" * 80)
        print(f"✅ 成功更新: {updated_count} 个订单")
        print(f"⚠️  SKU未匹配到商品: {no_match_count} 个订单")
        print(f"⚠️  商品无成本记录: {no_cost_count} 个订单")
        if failed_count > 0:
            print(f"❌ 更新失败: {failed_count} 个订单")
        
        # 计算GMV和利润统计
        if updated_count > 0:
            print("\n" + "=" * 80)
            print("💰 财务统计:")
            print("=" * 80)
            
            # 查询所有有成本信息的订单
            orders_with_cost = query.filter(
                Order.total_cost.isnot(None),
                Order.profit.isnot(None)
            ).all()
            
            total_gmv = sum(order.total_price for order in orders_with_cost)
            total_cost = sum(order.total_cost for order in orders_with_cost)
            total_profit = sum(order.profit for order in orders_with_cost)
            
            if total_gmv > 0:
                profit_margin = (total_profit / total_gmv) * 100
            else:
                profit_margin = 0
            
            print(f"📦 订单数: {len(orders_with_cost)}")
            print(f"💵 GMV（营业额）: {total_gmv:.2f}")
            print(f"💰 总成本: {total_cost:.2f}")
            print(f"📈 总利润: {total_profit:.2f}")
            print(f"📊 利润率: {profit_margin:.2f}%")
        
        print("\n" + "=" * 80)
        print("✅ 批量更新完成！")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # 可以指定店铺ID，或留空更新所有店铺
    shop_id = None
    if len(sys.argv) > 1:
        try:
            shop_id = int(sys.argv[1])
        except ValueError:
            print(f"错误: 无效的店铺ID '{sys.argv[1]}'")
            sys.exit(1)
    
    update_order_costs(shop_id)

