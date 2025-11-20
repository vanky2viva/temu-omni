#!/usr/bin/env python3
"""同步前2个店铺的商品数据"""
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


async def sync_two_shops():
    """同步前2个店铺的商品数据"""
    db = SessionLocal()
    
    try:
        # 查询所有启用的店铺
        shops = db.query(Shop).filter(Shop.is_active == True).limit(2).all()
        
        if not shops:
            print("❌ 没有找到启用的店铺")
            return
        
        print(f"✅ 找到 {len(shops)} 个启用的店铺")
        print("=" * 80)
        
        total_results = []
        
        for idx, shop in enumerate(shops, 1):
            print(f"\n{'='*80}")
            print(f"【{idx}/{len(shops)}】同步店铺: {shop.shop_name}")
            print(f"{'='*80}")
            print(f"店铺ID: {shop.id}")
            print(f"区域: {shop.region}")
            print(f"环境: {shop.environment}")
            print("-" * 80)
            
            # 统计旧数据
            old_product_count = db.query(Product).filter(
                Product.shop_id == shop.id
            ).count()
            old_active_count = db.query(Product).filter(
                Product.shop_id == shop.id,
                Product.is_active == True
            ).count()
            
            print(f"📊 同步前数据:")
            print(f"   总商品数: {old_product_count}")
            print(f"   在售商品数: {old_active_count}")
            
            # 清理旧数据
            if old_product_count > 0:
                try:
                    print(f"\n🗑️  清理旧数据...")
                    deleted = db.query(Product).filter(
                        Product.shop_id == shop.id
                    ).delete()
                    db.commit()
                    print(f"   ✅ 已清理 {deleted} 条旧商品数据")
                except Exception as e:
                    db.rollback()
                    print(f"   ⚠️  清理失败: {e}")
            
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
                
                # 统计不同SPU
                from sqlalchemy import func, distinct
                spu_count = db.query(func.count(distinct(Product.spu_id))).filter(
                    Product.shop_id == shop.id,
                    Product.spu_id.isnot(None)
                ).scalar()
                
                print(f"\n📊 同步后数据:")
                print(f"   总商品数（SKU级别）: {new_product_count}")
                print(f"   在售商品数: {new_active_count}")
                print(f"   有SKU商品: {new_with_sku}")
                print(f"   不同SPU数（商品种类）: {spu_count}")
                
                # 保存结果
                total_results.append({
                    'shop_name': shop.shop_name,
                    'shop_id': shop.id,
                    'new': result.get('new', 0),
                    'updated': result.get('updated', 0),
                    'failed': result.get('failed', 0),
                    'total_sku': new_product_count,
                    'active': new_active_count,
                    'with_sku': new_with_sku,
                    'spu_count': spu_count
                })
                
                # 显示部分商品信息
                products = db.query(Product).filter(
                    Product.shop_id == shop.id,
                    Product.is_active == True
                ).limit(5).all()
                
                if products:
                    print(f"\n📦 部分商品信息（前5个）:")
                    for i, product in enumerate(products, 1):
                        print(f"   {i}. {product.product_name[:50]}")
                        print(f"      SKU: {product.sku}, SPU: {product.spu_id}")
                
            except Exception as e:
                print(f"❌ 同步失败: {e}")
                import traceback
                traceback.print_exc()
                
                total_results.append({
                    'shop_name': shop.shop_name,
                    'shop_id': shop.id,
                    'error': str(e)
                })
                continue
        
        # 最终汇总
        print("\n" + "=" * 80)
        print("📊 同步汇总")
        print("=" * 80)
        
        for idx, result in enumerate(total_results, 1):
            print(f"\n{idx}. {result['shop_name']} (ID: {result['shop_id']})")
            if 'error' in result:
                print(f"   ❌ 失败: {result['error']}")
            else:
                print(f"   ✅ 成功")
                print(f"   新增: {result['new']}, 更新: {result['updated']}, 失败: {result['failed']}")
                print(f"   SKU总数: {result['total_sku']}, 在售: {result['active']}, SPU数: {result['spu_count']}")
        
        # 全局统计
        total_sku = sum(r.get('total_sku', 0) for r in total_results if 'error' not in r)
        total_active = sum(r.get('active', 0) for r in total_results if 'error' not in r)
        total_spu = sum(r.get('spu_count', 0) for r in total_results if 'error' not in r)
        success_count = sum(1 for r in total_results if 'error' not in r)
        
        print(f"\n{'='*80}")
        print(f"✅ 成功同步 {success_count}/{len(shops)} 个店铺")
        print(f"📦 总计: {total_sku} 个SKU, {total_active} 个在售, {total_spu} 个不同商品（SPU）")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(sync_two_shops())

