#!/usr/bin/env python3
"""检查商品的product_id格式"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.product import Product


def check_product_ids():
    """检查商品的product_id格式"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("检查商品product_id")
        print("=" * 80)
        
        # 获取前20个商品
        products = db.query(Product).limit(20).all()
        
        print(f"\n找到 {len(products)} 个商品\n")
        
        print(f"{'Product ID':<25} {'SKU':<20} {'Shop ID':<10} {'Product Name':<50}")
        print("-" * 110)
        
        for product in products:
            product_id_str = str(product.product_id) if product.product_id else "NULL"
            sku_str = str(product.sku) if product.sku else "NULL"
            name_str = product.product_name[:47] + "..." if len(product.product_name) > 50 else product.product_name
            
            print(f"{product_id_str:<25} {sku_str:<20} {product.shop_id:<10} {name_str:<50}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_product_ids()

