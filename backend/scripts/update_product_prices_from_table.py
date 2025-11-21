#!/usr/bin/env python3
"""根据SKU模式表格更新商品价格

根据提供的SKU模式表格，匹配商品并更新供货价和成本价
"""
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.product import Product, ProductCost
from loguru import logger

# SKU模式价格表（从用户提供的表格）
SKU_PRICE_TABLE = {
    # SKU模式: (供货价_CNY, 成本价_CNY)
    'LBB4-A-ALL': (Decimal('2140'), Decimal('1575')),
    'LBB4-B-ALL': (Decimal('2140'), Decimal('1575')),
    'LBB3-ALL': (Decimal('1700'), Decimal('1035')),
    'LBB-MXT': (Decimal('400'), Decimal('345')),
    'LBB-NG': (Decimal('600'), Decimal('406')),
    'LBB1': (Decimal('287'), Decimal('232')),  # 匹配LBB1开头但不包含ALL的
    'LBB2': (Decimal('216'), Decimal('197')),  # 匹配LBB2开头但不包含ALL的
    'LBB3': (Decimal('225'), Decimal('188')),  # 匹配LBB3开头但不包含ALL的
    'LBB4': (Decimal('186'), Decimal('145')),  # 匹配LBB4开头但不包含ALL的
}


def match_sku_pattern(sku: str) -> tuple:
    """
    根据SKU匹配价格模式
    
    Args:
        sku: 商品SKU
        
    Returns:
        (供货价, 成本价) 或 (None, None) 如果不匹配
    """
    if not sku:
        return None, None
    
    # 精确匹配（优先）
    if 'LBB4-A-ALL' in sku:
        return SKU_PRICE_TABLE['LBB4-A-ALL']
    if 'LBB4-B-ALL' in sku:
        return SKU_PRICE_TABLE['LBB4-B-ALL']
    if 'LBB3-ALL' in sku:
        return SKU_PRICE_TABLE['LBB3-ALL']
    if 'LBB-MXT' in sku:
        return SKU_PRICE_TABLE['LBB-MXT']
    if 'LBB-NG' in sku:
        return SKU_PRICE_TABLE['LBB-NG']
    
    # 前缀匹配（排除ALL变体）
    if sku.startswith('LBB1') and 'ALL' not in sku:
        return SKU_PRICE_TABLE['LBB1']
    if sku.startswith('LBB2') and 'ALL' not in sku:
        return SKU_PRICE_TABLE['LBB2']
    if sku.startswith('LBB3') and 'ALL' not in sku:
        return SKU_PRICE_TABLE['LBB3']
    if sku.startswith('LBB4') and 'ALL' not in sku:
        return SKU_PRICE_TABLE['LBB4']
    
    return None, None


def update_product_prices():
    """更新商品价格"""
    db = SessionLocal()
    try:
        # 获取所有商品
        products = db.query(Product).all()
        
        print(f"找到 {len(products)} 个商品\n")
        
        updated_count = 0
        skipped_count = 0
        
        for product in products:
            sku = product.sku
            if not sku:
                skipped_count += 1
                continue
            
            # 匹配SKU模式
            supply_price, cost_price = match_sku_pattern(sku)
            
            if supply_price is None or cost_price is None:
                logger.debug(f"商品 {sku} 不匹配任何价格模式，跳过")
                skipped_count += 1
                continue
            
            # 更新供货价
            old_supply_price = product.current_price or Decimal('0')
            product.current_price = supply_price
            product.currency = 'CNY'  # 设置为CNY
            
            # 更新或创建成本价记录
            cost_record = db.query(ProductCost).filter(
                ProductCost.product_id == product.id,
                ProductCost.effective_to.is_(None)  # 当前有效的成本记录
            ).first()
            
            if cost_record:
                # 如果成本价不同，更新现有记录
                if cost_record.cost_price != cost_price:
                    cost_record.cost_price = cost_price
                    cost_record.currency = 'CNY'
                    logger.info(
                        f"更新商品 {sku} 成本价: {cost_record.cost_price} -> {cost_price} CNY"
                    )
            else:
                # 创建新的成本记录
                cost_record = ProductCost(
                    product_id=product.id,
                    cost_price=cost_price,
                    currency='CNY',
                    effective_from=datetime.utcnow(),
                    notes="从SKU价格表导入"
                )
                db.add(cost_record)
                logger.info(f"创建商品 {sku} 成本记录: {cost_price} CNY")
            
            updated_count += 1
            logger.info(
                f"✅ 更新商品 {sku}: 供货价 {old_supply_price} -> {supply_price} CNY, "
                f"成本价 {cost_price} CNY"
            )
        
        # 提交更改
        db.commit()
        
        print(f"\n✅ 更新完成！")
        print(f"  更新: {updated_count} 个商品")
        print(f"  跳过: {skipped_count} 个商品（不匹配任何模式）")
        
        return updated_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新商品价格失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_product_prices()

