#!/usr/bin/env python3
"""统计实际在售商品数量（去重后）"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService


async def count_real_active_products():
    """统计实际在售商品数量（去重）"""
    db = SessionLocal()
    
    try:
        # 查找festival finds店铺
        shop = db.query(Shop).filter(Shop.shop_name == "festival finds").first()
        if not shop:
            print("❌ 未找到festival finds店铺")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name} (ID: {shop.id})")
        print()
        
        # 创建Temu服务
        temu_service = TemuService(shop)
        
        print("🔍 统计实际在售商品（去重）...")
        print("=" * 80)
        
        # 使用集合去重
        active_products = set()  # 使用productId去重
        all_products = set()
        page_number = 1
        page_size = 100
        
        while page_number <= 20:
            result = await temu_service.get_products(
                page_number=page_number,
                page_size=page_size
            )
            
            product_list = result.get('data') or []
            total = result.get('totalCount') or result.get('total') or 0
            
            if not product_list:
                break
            
            print(f"\n📄 第 {page_number} 页:")
            print(f"   API返回总数: {total}")
            print(f"   当前页商品数: {len(product_list)}")
            
            page_active = 0
            for product in product_list:
                product_id = str(product.get('productId') or product.get('goodsId') or '')
                skc_site_status = product.get('skcSiteStatus')
                
                all_products.add(product_id)
                
                if skc_site_status == 1:
                    active_products.add(product_id)
                    page_active += 1
                    product_name = (product.get('productName') or product.get('goodsName') or '未知')[:50]
                    print(f"   ✅ 在售: {product_id} - {product_name}")
            
            print(f"   当前页在售商品数: {page_active}")
            print(f"   累计去重后总数: {len(all_products)}, 在售: {len(active_products)}")
            
            # 检查是否还有更多页
            if total > 0:
                if len(all_products) >= total:
                    break
            else:
                if len(product_list) < page_size:
                    break
            
            page_number += 1
        
        await temu_service.close()
        
        print("\n" + "=" * 80)
        print(f"📊 最终统计结果（去重后）:")
        print(f"   总商品数（去重）: {len(all_products)}")
        print(f"   在售商品数（去重）: {len(active_products)}")
        print(f"   不在售商品数: {len(all_products) - len(active_products)}")
        print()
        print(f"   预期应该有 17 个在售商品")
        print()
        if len(active_products) > 0:
            print("   在售商品列表:")
            for product_id in sorted(active_products):
                print(f"     - {product_id}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(count_real_active_products())

