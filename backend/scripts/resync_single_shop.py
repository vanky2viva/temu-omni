#!/usr/bin/env python3
"""重新同步单个店铺的商品数据"""
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


async def resync_single_shop(shop_name: str, clear_old_data: bool = True):
    """重新同步单个店铺的商品数据"""
    db = SessionLocal()
    
    try:
        # 查找店铺
        shop = db.query(Shop).filter(Shop.shop_name == shop_name).first()
        
        if not shop:
            print(f"❌ 未找到店铺: {shop_name}")
            print("\n可用店铺列表:")
            shops = db.query(Shop).all()
            for s in shops:
                print(f"  - {s.shop_name} (ID: {s.id}, 状态: {'启用' if s.is_active else '禁用'})")
            return
        
        if not shop.is_active:
            print(f"⚠️  店铺已禁用: {shop_name}")
            print("   如需同步，请先启用店铺")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name}")
        print(f"   店铺ID: {shop.id}")
        print(f"   区域: {shop.region}")
        print(f"   环境: {shop.environment}")
        print("=" * 80)
        
        # 统计旧数据
        old_product_count = db.query(Product).filter(
            Product.shop_id == shop.id
        ).count()
        old_active_count = db.query(Product).filter(
            Product.shop_id == shop.id,
            Product.is_active == True
        ).count()
        
        print(f"\n📊 旧数据统计:")
        print(f"   总商品数: {old_product_count}")
        print(f"   在售商品数: {old_active_count}")
        
        # 清理旧数据（可选）
        if clear_old_data and old_product_count > 0:
            print(f"\n🗑️  清理旧数据...")
            try:
                deleted = db.query(Product).filter(
                    Product.shop_id == shop.id
                ).delete()
                db.commit()
                print(f"   ✅ 已清理 {deleted} 条旧商品数据")
            except Exception as e:
                db.rollback()
                print(f"   ❌ 清理失败: {e}")
                return
        
        # 同步商品
        print(f"\n🔄 开始同步商品...")
        print("-" * 80)
        
        try:
            sync_service = SyncService(db, shop)
            result = await sync_service.sync_products()
            await sync_service.temu_service.close()
            
            print("-" * 80)
            print(f"✅ 商品同步完成!")
            print(f"   新增: {result.get('new', 0)}")
            print(f"   更新: {result.get('updated', 0)}")
            print(f"   总数: {result.get('total', 0)}")
            print(f"   失败: {result.get('failed', 0)}")
            
            # 统计新数据
            new_product_count = db.query(Product).filter(
                Product.shop_id == shop.id
            ).count()
            new_active_count = db.query(Product).filter(
                Product.shop_id == shop.id,
                Product.is_active == True
            ).count()
            new_with_sku = db.query(Product).filter(
                Product.shop_id == shop.id,
                Product.sku.isnot(None),
                Product.sku != ''
            ).count()
            
            print(f"\n📊 新数据统计:")
            print(f"   总商品数: {new_product_count}")
            print(f"   在售商品数: {new_active_count}")
            print(f"   有SKU商品: {new_with_sku}")
            
            # 统计不同SPU
            from sqlalchemy import func, distinct
            spu_count = db.query(func.count(distinct(Product.spu_id))).filter(
                Product.shop_id == shop.id,
                Product.spu_id.isnot(None)
            ).scalar()
            
            print(f"   不同SPU数: {spu_count}")
            
        except Exception as e:
            print(f"❌ 同步失败: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python resync_single_shop.py <店铺名称> [--keep-old]")
        print()
        print("示例:")
        print("  python resync_single_shop.py 'festival finds'")
        print("  python resync_single_shop.py 'festival finds' --keep-old")
        sys.exit(1)
    
    shop_name = sys.argv[1]
    clear_old = "--keep-old" not in sys.argv
    
    if clear_old:
        print(f"⚠️  将清理店铺 '{shop_name}' 的旧商品数据后重新同步")
        print("   如需保留旧数据，请使用参数: --keep-old")
    else:
        print(f"ℹ️  保留旧数据，仅更新店铺 '{shop_name}'")
    
    print()
    
    asyncio.run(resync_single_shop(shop_name, clear_old_data=clear_old))

