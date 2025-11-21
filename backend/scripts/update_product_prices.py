#!/usr/bin/env python3
"""批量更新商品价格脚本"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.product import Product, ProductCost
from sqlalchemy import and_

def update_product_prices():
    """批量更新商品价格"""
    db = SessionLocal()
    
    try:
        # 定义价格规则（按优先级从高到低排序，先匹配更具体的模式）
        price_rules = [
            # 最具体的规则先匹配
            {'pattern': 'LBB4-A-ALL', 'supply_price': 2140, 'cost_price': 1575},
            {'pattern': 'LBB4-B-ALL', 'supply_price': 2140, 'cost_price': 1575},
            {'pattern': 'LBB3-ALL', 'supply_price': 1700, 'cost_price': 1035},
            {'pattern': 'LBB-MXT', 'supply_price': 400, 'cost_price': 345},
            {'pattern': 'LBB-NG', 'supply_price': 600, 'cost_price': 406},
            # 然后是通用规则
            {'pattern': 'LBB1', 'supply_price': 287, 'cost_price': 232},
            {'pattern': 'LBB2', 'supply_price': 216, 'cost_price': 197},
            {'pattern': 'LBB3', 'supply_price': 225, 'cost_price': 188},
            {'pattern': 'LBB4', 'supply_price': 186, 'cost_price': 145},
        ]
        
        print("=" * 80)
        print("开始批量更新商品价格...")
        print("=" * 80)
        
        # 获取所有商品
        all_products = db.query(Product).all()
        print(f"\n📦 总共 {len(all_products)} 个商品")
        
        # 记录已处理的商品ID
        processed_product_ids = set()
        total_updated = 0
        
        for rule in price_rules:
            pattern = rule['pattern']
            supply_price = rule['supply_price']
            cost_price = rule['cost_price']
            
            # 查找匹配的商品（排除已处理的）
            products = [p for p in all_products 
                       if pattern in (p.sku or '') and p.id not in processed_product_ids]
            
            if not products:
                print(f"\n❌ 未找到包含 '{pattern}' 的商品（或已被处理）")
                continue
            
            print(f"\n✅ 找到 {len(products)} 个包含 '{pattern}' 的商品")
            
            updated_count = 0
            for product in products:
                # 更新供货价
                old_supply_price = product.current_price
                product.current_price = supply_price
                product.currency = 'CNY'
                
                # 获取当前有效的成本价格
                current_cost = db.query(ProductCost).filter(
                    ProductCost.product_id == product.id,
                    ProductCost.effective_to.is_(None)
                ).first()
                
                old_cost_price = current_cost.cost_price if current_cost else None
                
                # 如果已有成本价格，将其设为过期
                if current_cost:
                    current_cost.effective_to = datetime.utcnow()
                
                # 创建新的成本价格记录
                new_cost = ProductCost(
                    product_id=product.id,
                    cost_price=cost_price,
                    currency='CNY',
                    effective_from=datetime.utcnow(),
                    notes=f'批量更新：根据SKU模式 {pattern} 自动设置'
                )
                db.add(new_cost)
                
                print(f"   ✓ {product.sku}: 供货价 {old_supply_price} → {supply_price} CNY, "
                      f"成本价 {old_cost_price} → {cost_price} CNY")
                
                # 标记为已处理
                processed_product_ids.add(product.id)
                updated_count += 1
            
            if updated_count > 0:
                db.commit()
                print(f"   📊 已更新 {updated_count} 个商品")
                total_updated += updated_count
        
        print("\n" + "=" * 80)
        print(f"✅ 批量更新完成！共更新 {total_updated} 个商品的价格")
        print(f"📊 未处理的商品: {len(all_products) - total_updated} 个")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    update_product_prices()

