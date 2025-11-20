#!/usr/bin/env python3
"""批量更新商品价格"""
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.product import Product, ProductCost
from sqlalchemy import or_


def batch_update_prices():
    """批量更新商品价格"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("批量更新商品价格")
        print("=" * 80)
        
        # 规则1：SKU包含LBB3的商品
        print("\n🔍 查找SKU包含'LBB3'的商品...")
        lbb3_products = db.query(Product).filter(
            Product.sku.like('%LBB3%')
        ).all()
        
        print(f"   找到 {len(lbb3_products)} 个商品")
        
        # 规则2：SKU包含LBB4的商品
        print("\n🔍 查找SKU包含'LBB4'的商品...")
        lbb4_products = db.query(Product).filter(
            Product.sku.like('%LBB4%')
        ).all()
        
        print(f"   找到 {len(lbb4_products)} 个商品")
        
        if not lbb3_products and not lbb4_products:
            print("\n⚠️  没有找到符合条件的商品")
            return
        
        # 确认更新
        print("\n" + "=" * 80)
        print("📋 更新计划:")
        print("=" * 80)
        print(f"1. SKU包含'LBB3'的商品（{len(lbb3_products)}个）：")
        print(f"   供货价: 225 CNY")
        print(f"   成本价: 195 CNY")
        print()
        print(f"2. SKU包含'LBB4'的商品（{len(lbb4_products)}个）：")
        print(f"   供货价: 185 CNY")
        print(f"   成本价: 149 CNY")
        print()
        
        # 开始更新
        updated_count = 0
        error_count = 0
        
        # 更新LBB3商品
        if lbb3_products:
            print("\n" + "-" * 80)
            print("🔄 更新SKU包含'LBB3'的商品...")
            print("-" * 80)
            
            for product in lbb3_products:
                try:
                    print(f"\n📦 {product.product_name[:50]}")
                    print(f"   SKU: {product.sku}")
                    print(f"   旧供货价: {product.current_price} {product.currency}")
                    
                    # 更新供货价
                    product.current_price = Decimal('225')
                    product.currency = 'CNY'
                    
                    # 更新成本价
                    # 先将当前生效的成本设置为过期
                    current_costs = db.query(ProductCost).filter(
                        ProductCost.product_id == product.id,
                        ProductCost.effective_to.is_(None)
                    ).all()
                    
                    now = datetime.utcnow()
                    for cost in current_costs:
                        cost.effective_to = now
                    
                    # 创建新的成本记录
                    new_cost = ProductCost(
                        product_id=product.id,
                        cost_price=Decimal('195'),
                        currency='CNY',
                        effective_from=now,
                        effective_to=None,
                        notes='批量更新 - SKU包含LBB3'
                    )
                    db.add(new_cost)
                    
                    print(f"   ✅ 新供货价: 225 CNY")
                    print(f"   ✅ 新成本价: 195 CNY")
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"   ❌ 更新失败: {e}")
                    error_count += 1
                    continue
        
        # 更新LBB4商品
        if lbb4_products:
            print("\n" + "-" * 80)
            print("🔄 更新SKU包含'LBB4'的商品...")
            print("-" * 80)
            
            for product in lbb4_products:
                try:
                    print(f"\n📦 {product.product_name[:50]}")
                    print(f"   SKU: {product.sku}")
                    print(f"   旧供货价: {product.current_price} {product.currency}")
                    
                    # 更新供货价
                    product.current_price = Decimal('185')
                    product.currency = 'CNY'
                    
                    # 更新成本价
                    # 先将当前生效的成本设置为过期
                    current_costs = db.query(ProductCost).filter(
                        ProductCost.product_id == product.id,
                        ProductCost.effective_to.is_(None)
                    ).all()
                    
                    now = datetime.utcnow()
                    for cost in current_costs:
                        cost.effective_to = now
                    
                    # 创建新的成本记录
                    new_cost = ProductCost(
                        product_id=product.id,
                        cost_price=Decimal('149'),
                        currency='CNY',
                        effective_from=now,
                        effective_to=None,
                        notes='批量更新 - SKU包含LBB4'
                    )
                    db.add(new_cost)
                    
                    print(f"   ✅ 新供货价: 185 CNY")
                    print(f"   ✅ 新成本价: 149 CNY")
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"   ❌ 更新失败: {e}")
                    error_count += 1
                    continue
        
        # 提交更改
        print("\n" + "=" * 80)
        print("💾 保存更改...")
        db.commit()
        print("✅ 更改已保存")
        
        # 最终统计
        print("\n" + "=" * 80)
        print("📊 更新结果:")
        print("=" * 80)
        print(f"✅ 成功更新: {updated_count} 个商品")
        if error_count > 0:
            print(f"❌ 失败: {error_count} 个商品")
        
        # 验证更新结果
        print("\n" + "=" * 80)
        print("🔍 验证更新结果:")
        print("=" * 80)
        
        # 验证LBB3
        print("\nSKU包含'LBB3'的商品价格:")
        for product in lbb3_products[:5]:  # 显示前5个
            # 获取当前成本
            current_cost = db.query(ProductCost).filter(
                ProductCost.product_id == product.id,
                ProductCost.effective_to.is_(None)
            ).first()
            
            cost_price = current_cost.cost_price if current_cost else 0
            print(f"  - {product.sku}: 供货价={product.current_price} {product.currency}, 成本价={cost_price} CNY")
        
        if len(lbb3_products) > 5:
            print(f"  ... 还有 {len(lbb3_products) - 5} 个商品")
        
        # 验证LBB4
        print("\nSKU包含'LBB4'的商品价格:")
        for product in lbb4_products[:5]:  # 显示前5个
            # 获取当前成本
            current_cost = db.query(ProductCost).filter(
                ProductCost.product_id == product.id,
                ProductCost.effective_to.is_(None)
            ).first()
            
            cost_price = current_cost.cost_price if current_cost else 0
            print(f"  - {product.sku}: 供货价={product.current_price} {product.currency}, 成本价={cost_price} CNY")
        
        if len(lbb4_products) > 5:
            print(f"  ... 还有 {len(lbb4_products) - 5} 个商品")
        
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
    batch_update_prices()

