#!/usr/bin/env python3
"""测试同步festival finds店铺的商品"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.models.product import Product
from app.services.sync_service import SyncService


async def test_sync_products():
    """测试同步商品"""
    db = SessionLocal()
    
    try:
        # 查找festival finds店铺
        shop = db.query(Shop).filter(Shop.shop_name == "festival finds").first()
        if not shop:
            print("❌ 未找到festival finds店铺")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name} (ID: {shop.id})")
        print(f"   启用状态: {shop.is_active}")
        print(f"   环境: {shop.environment.value}")
        print()
        
        # 查看同步前的商品数量
        before_count = db.query(Product).filter(
            Product.shop_id == shop.id,
            Product.is_active == True
        ).count()
        print(f"📊 同步前在售商品数量: {before_count}")
        print()
        
        # 创建同步服务
        sync_service = SyncService(db, shop)
        
        # 同步商品
        print("🔄 开始同步商品...")
        print("-" * 60)
        result = await sync_service.sync_products(full_sync=True)
        await sync_service.temu_service.close()
        
        print("-" * 60)
        print(f"✅ 同步完成!")
        print(f"   新增: {result.get('new', 0)}")
        print(f"   更新: {result.get('updated', 0)}")
        print(f"   总数: {result.get('total', 0)}")
        print(f"   失败: {result.get('failed', 0)}")
        print()
        
        # 查看同步后的商品
        products = db.query(Product).filter(
            Product.shop_id == shop.id,
            Product.is_active == True
        ).order_by(Product.id).all()
        
        print(f"📦 同步后在售商品数量: {len(products)}")
        print()
        
        if products:
            print("=" * 80)
            print("商品列表:")
            print("=" * 80)
            for idx, product in enumerate(products, 1):
                print(f"\n{idx}. 商品ID: {product.product_id}")
                print(f"   商品名称: {product.product_name}")
                print(f"   SKU货号: {product.sku if product.sku else '(无)'}")
                print(f"   SPU ID: {product.spu_id if product.spu_id else '(无)'}")
                print(f"   SKC ID: {product.skc_id if product.skc_id else '(无)'}")
                print(f"   供货价: {product.current_price} {product.currency}")
                print(f"   库存: {product.stock_quantity}")
                print(f"   状态: {'在售中' if product.is_active else '未发布'}")
                if product.category:
                    print(f"   分类: {product.category}")
        else:
            print("⚠️  没有找到在售商品")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_sync_products())

