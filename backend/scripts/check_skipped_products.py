#!/usr/bin/env python3
"""检查被跳过的商品状态"""
import asyncio
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService


async def check_skipped_products():
    """检查被跳过的商品"""
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
        
        # 这些是日志中显示被跳过的商品ID
        skipped_ids = ['4092947745', '5812665577', '2758743275', '6454420873', '4587047792', '4969842909']
        
        print("🔍 检查被跳过的商品状态...")
        print("=" * 80)
        
        # 遍历所有页面查找这些商品
        found_count = 0
        page_number = 1
        
        while page_number <= 20 and found_count < len(skipped_ids):
            result = await temu_service.get_products(page_number=page_number, page_size=100)
            product_list = result.get('data') or []
            
            if not product_list:
                break
            
            for product in product_list:
                product_id = str(product.get('productId') or product.get('goodsId') or '')
                
                if product_id in skipped_ids:
                    found_count += 1
                    product_name = (product.get('productName') or product.get('goodsName') or '未知')[:60]
                    
                    print(f"\n📦 商品ID: {product_id}")
                    print(f"   名称: {product_name}")
                    
                    # 检查状态字段
                    skc_site_status = product.get('skcSiteStatus')
                    goods_status = product.get('goodsStatus')
                    status = product.get('status')
                    
                    print(f"   状态字段:")
                    print(f"     skcSiteStatus: {skc_site_status} (类型: {type(skc_site_status).__name__})")
                    print(f"     goodsStatus: {goods_status} (类型: {type(goods_status).__name__})")
                    print(f"     status: {status} (类型: {type(status).__name__})")
                    
                    # 检查SKU信息
                    sku_list = product.get('productSkuSummaries') or product.get('skuInfoList') or []
                    print(f"   SKU数量: {len(sku_list)}")
                    if sku_list:
                        for sku_idx, sku in enumerate(sku_list[:2], 1):
                            print(f"   SKU {sku_idx}:")
                            print(f"     extCode: '{sku.get('extCode')}'")
                            print(f"     productSkuId: {sku.get('productSkuId')}")
                            print(f"     skcSiteStatus: {sku.get('skcSiteStatus')}")
                    
                    # 判断是否应该在售
                    is_active = False
                    if skc_site_status is not None:
                        if isinstance(skc_site_status, int):
                            is_active = skc_site_status == 1
                        elif isinstance(skc_site_status, str):
                            is_active = skc_site_status.lower() in ['1', 'active', 'on_sale', 'onsale', 'published']
                    
                    print(f"   判断结果: {'应该在售' if is_active else '应该跳过'}")
                    print("-" * 80)
            
            if len(product_list) < 100:
                break
            
            page_number += 1
        
        await temu_service.close()
        
        print(f"\n✅ 检查完成，找到 {found_count}/{len(skipped_ids)} 个被跳过的商品")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(check_skipped_products())

