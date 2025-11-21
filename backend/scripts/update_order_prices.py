#!/usr/bin/env python3
"""更新订单价格脚本

从商品表的供货价（current_price）重新计算订单价格
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.order import Order
from app.models.product import Product
from decimal import Decimal
from loguru import logger

def update_order_prices():
    """更新所有订单的价格（从商品表的供货价计算）"""
    db = SessionLocal()
    try:
        # 查找所有价格为0或需要更新的订单
        orders = db.query(Order).filter(
            Order.product_id.isnot(None),
            Order.total_price == 0
        ).all()
        
        print(f"找到 {len(orders)} 个需要更新价格的订单\n")
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for order in orders:
            try:
                # 获取关联的商品
                product = db.query(Product).filter(Product.id == order.product_id).first()
                
                if not product:
                    logger.warning(f"订单 {order.order_sn} 的商品不存在 (product_id={order.product_id})")
                    skipped_count += 1
                    continue
                
                # 获取商品的供货价
                supply_price = product.current_price or Decimal('0')
                
                if supply_price == 0:
                    logger.warning(
                        f"订单 {order.order_sn} 的商品 {product.sku} 供货价为0，跳过"
                    )
                    skipped_count += 1
                    continue
                
                # 计算新价格
                new_unit_price = supply_price
                new_total_price = new_unit_price * Decimal(order.quantity) if order.quantity else Decimal('0')
                
                # 更新订单价格
                order.unit_price = new_unit_price
                order.total_price = new_total_price
                
                # 如果订单有成本，重新计算利润
                if order.unit_cost is not None and order.quantity:
                    order.total_cost = order.unit_cost * Decimal(order.quantity)
                    order.profit = new_total_price - order.total_cost
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    db.commit()
                    logger.info(f"已更新 {updated_count} 个订单...")
                    
            except Exception as e:
                logger.error(f"更新订单 {order.order_sn} 失败: {e}")
                error_count += 1
                continue
        
        # 提交所有更改
        db.commit()
        
        print(f"\n✅ 更新完成！")
        print(f"  更新: {updated_count} 个订单")
        print(f"  跳过: {skipped_count} 个订单（商品不存在或供货价为0）")
        print(f"  错误: {error_count} 个订单")
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新订单价格失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_order_prices()

