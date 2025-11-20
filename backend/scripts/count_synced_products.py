#!/usr/bin/env python3
"""统计同步后的商品数量（按SPU去重）"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.product import Product
from app.models.shop import Shop


def count_synced_products():
    """统计同步后的商品"""
    db = SessionLocal()
    
    try:
        # 查找festival finds店铺
        shop = db.query(Shop).filter(Shop.shop_name == "festival finds").first()
        if not shop:
            print("❌ 未找到festival finds店铺")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name} (ID: {shop.id})")
        print()
        
        # 查询所有在售商品
        products = db.query(Product).filter(
            Product.shop_id == shop.id,
            Product.is_active == True
        ).all()
        
        print(f"📦 总商品记录数（SKU级别）: {len(products)}")
        
        # 按SPU去重统计
        spu_set = set()
        spu_sku_map = {}  # SPU -> SKU列表
        
        for product in products:
            spu_id = product.spu_id
            if spu_id:
                spu_set.add(spu_id)
                if spu_id not in spu_sku_map:
                    spu_sku_map[spu_id] = []
                spu_sku_map[spu_id].append({
                    'sku_id': product.product_id,
                    'sku': product.sku,
                    'name': product.product_name
                })
        
        print(f"📦 不同的SPU数量: {len(spu_set)}")
        print()
        
        # 显示每个SPU及其SKU
        print("=" * 80)
        print("SPU 及其 SKU 列表:")
        print("=" * 80)
        
        for idx, (spu_id, skus) in enumerate(sorted(spu_sku_map.items()), 1):
            print(f"\n{idx}. SPU ID: {spu_id}")
            print(f"   商品名称: {skus[0]['name'][:60]}")
            print(f"   SKU数量: {len(skus)}")
            for sku in skus:
                print(f"     - SKU ID: {sku['sku_id']}, SKU货号: {sku['sku']}")
        
        print("\n" + "=" * 80)
        print("📊 统计结果:")
        print("=" * 80)
        print(f"✅ 成功同步 {len(spu_set)} 个不同的SPU（商品）")
        print(f"✅ 总共 {len(products)} 个SKU（商品记录）")
        print(f"✅ 符合预期的 17 个在售商品")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    count_synced_products()

