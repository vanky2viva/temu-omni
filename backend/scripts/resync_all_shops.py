#!/usr/bin/env python3
"""重新同步所有店铺的商品数据"""
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


async def resync_all_shops(clear_old_data: bool = True):
    """重新同步所有店铺的商品数据"""
    db = SessionLocal()
    
    try:
        # 查询所有启用的店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            print("❌ 没有找到启用的店铺")
            return
        
        print(f"✅ 找到 {len(shops)} 个启用的店铺")
        print("=" * 80)
        
        for idx, shop in enumerate(shops, 1):
            print(f"\n【{idx}/{len(shops)}】处理店铺: {shop.shop_name}")
            print(f"   店铺ID: {shop.id}")
            print(f"   区域: {shop.region}")
            print(f"   环境: {shop.environment}")
            print("-" * 80)
            
            # 统计旧数据
            old_product_count = db.query(Product).filter(
                Product.shop_id == shop.id
            ).count()
            old_active_count = db.query(Product).filter(
                Product.shop_id == shop.id,
                Product.is_active == True
            ).count()
            
            print(f"   旧数据统计: 总商品={old_product_count}, 在售={old_active_count}")
            
            # 清理旧数据（可选）
            if clear_old_data and old_product_count > 0:
                try:
                    deleted = db.query(Product).filter(
                        Product.shop_id == shop.id
                    ).delete()
                    db.commit()
                    print(f"   ✅ 已清理 {deleted} 条旧商品数据")
                except Exception as e:
                    db.rollback()
                    print(f"   ⚠️  清理旧数据失败: {e}")
            
            # 同步商品
            try:
                print(f"   🔄 开始同步商品...")
                
                sync_service = SyncService(db, shop)
                result = await sync_service.sync_products()
                await sync_service.temu_service.close()
                
                print(f"   ✅ 商品同步完成!")
                print(f"      新增: {result.get('new', 0)}")
                print(f"      更新: {result.get('updated', 0)}")
                print(f"      失败: {result.get('failed', 0)}")
                
                # 统计新数据
                new_product_count = db.query(Product).filter(
                    Product.shop_id == shop.id
                ).count()
                new_active_count = db.query(Product).filter(
                    Product.shop_id == shop.id,
                    Product.is_active == True
                ).count()
                
                print(f"   📊 新数据统计: 总商品={new_product_count}, 在售={new_active_count}")
                
            except Exception as e:
                print(f"   ❌ 同步失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 80)
        print("🎉 所有店铺同步完成！")
        print("=" * 80)
        
        # 最终统计
        total_products = db.query(Product).count()
        total_active = db.query(Product).filter(Product.is_active == True).count()
        
        print(f"\n📊 总计:")
        print(f"   店铺数量: {len(shops)}")
        print(f"   总商品数: {total_products}")
        print(f"   在售商品数: {total_active}")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # 检查命令行参数
    clear_old = "--keep-old" not in sys.argv
    
    if clear_old:
        print("⚠️  将清理所有旧商品数据后重新同步")
        print("   如需保留旧数据，请使用参数: --keep-old")
    else:
        print("ℹ️  保留旧数据，仅更新")
    
    print()
    
    asyncio.run(resync_all_shops(clear_old_data=clear_old))

