#!/usr/bin/env python3
"""调试商品状态字段"""
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


async def debug_status_fields():
    """调试商品状态字段"""
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
        
        print("🔍 检查前3页商品的状态字段...")
        print("=" * 80)
        
        # 检查前3页
        for page in range(1, 4):
            result = await temu_service.get_products(page_number=page, page_size=10)
            product_list = result.get('data') or []
            
            if not product_list:
                break
            
            print(f"\n📄 第 {page} 页:")
            print("-" * 80)
            
            for idx, product in enumerate(product_list[:3], 1):  # 只显示前3个
                product_id = product.get('productId') or product.get('goodsId') or '未知'
                product_name = (product.get('productName') or product.get('goodsName') or '未知')[:50]
                
                print(f"\n商品 {idx}: {product_name}")
                print(f"  商品ID: {product_id}")
                
                # 检查所有可能的状态字段
                status_fields = {
                    'skcSiteStatus': product.get('skcSiteStatus'),
                    'goodsStatus': product.get('goodsStatus'),
                    'status': product.get('status'),
                    'siteStatus': product.get('siteStatus'),
                    'saleStatus': product.get('saleStatus'),
                    'onSale': product.get('onSale'),
                    'isActive': product.get('isActive'),
                }
                
                print("  状态字段:")
                for field, value in status_fields.items():
                    if value is not None:
                        print(f"    {field}: {value} (类型: {type(value).__name__})")
                
                # 检查SKU列表中的状态
                sku_list = product.get('productSkuSummaries') or product.get('skuInfoList') or []
                if sku_list:
                    print(f"  SKU数量: {len(sku_list)}")
                    for sku_idx, sku in enumerate(sku_list[:2], 1):  # 只显示前2个SKU
                        print(f"  SKU {sku_idx}:")
                        sku_status_fields = {
                            'skcSiteStatus': sku.get('skcSiteStatus'),
                            'siteStatus': sku.get('siteStatus'),
                            'status': sku.get('status'),
                            'saleStatus': sku.get('saleStatus'),
                        }
                        for field, value in sku_status_fields.items():
                            if value is not None:
                                print(f"    {field}: {value}")
                        print(f"    extCode: {sku.get('extCode')}")
                        print(f"    productSkuId: {sku.get('productSkuId')}")
        
        await temu_service.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(debug_status_fields())

