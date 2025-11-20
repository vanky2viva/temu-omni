#!/usr/bin/env python3
"""测试使用 skcSiteStatus 参数筛选在售商品"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService


async def test_goods_list_with_status():
    """测试使用skcSiteStatus参数筛选在售商品"""
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
        
        print("🔍 测试1: 获取全部商品（不筛选）...")
        print("=" * 80)
        
        # 测试1: 获取全部商品
        result_all = await temu_service.get_products(
            page_number=1,
            page_size=10
        )
        
        product_list_all = result_all.get('data') or []
        total_all = result_all.get('totalCount') or result_all.get('total') or 0
        
        print(f"全部商品 - 总数: {total_all}, 当前页: {len(product_list_all)}")
        
        # 统计在售商品
        active_count_all = 0
        for product in product_list_all:
            skc_site_status = product.get('skcSiteStatus')
            if skc_site_status == 1:
                active_count_all += 1
                product_id = product.get('productId') or product.get('goodsId') or '未知'
                product_name = (product.get('productName') or product.get('goodsName') or '未知')[:50]
                print(f"   ✅ 在售: {product_id} - {product_name}")
        
        print(f"   当前页在售商品数: {active_count_all}/{len(product_list_all)}")
        print()
        
        print("🔍 测试2: 使用 skcSiteStatus=1 筛选在售商品...")
        print("=" * 80)
        
        # 测试2: 使用skcSiteStatus=1筛选在售商品
        total_active = 0
        page_number = 1
        page_size = 100
        
        while page_number <= 10:
            result = await temu_service.get_products(
                page_number=page_number,
                page_size=page_size,
                skc_site_status=1  # 只获取在售商品
            )
            
            product_list = result.get('data') or []
            total = result.get('totalCount') or result.get('total') or 0
            
            if not product_list:
                break
            
            print(f"\n📄 第 {page_number} 页:")
            print(f"   API返回总数: {total}")
            print(f"   当前页商品数: {len(product_list)}")
            
            for product in product_list:
                total_active += 1
                product_id = product.get('productId') or product.get('goodsId') or '未知'
                product_name = (product.get('productName') or product.get('goodsName') or '未知')[:50]
                skc_site_status = product.get('skcSiteStatus')
                print(f"   ✅ {product_id} - {product_name} (状态: {skc_site_status})")
            
            # 检查是否还有更多页
            if total > 0:
                if total_active >= total:
                    break
            else:
                if len(product_list) < page_size:
                    break
            
            page_number += 1
        
        await temu_service.close()
        
        print("\n" + "=" * 80)
        print(f"📊 统计结果:")
        print(f"   使用 skcSiteStatus=1 筛选后，获取到 {total_active} 个在售商品")
        print(f"   预期应该有 17 个在售商品")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_goods_list_with_status())

