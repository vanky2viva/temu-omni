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


async def debug_product_status():
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
        
        # 获取第一页商品
        print("🔄 获取第一页商品数据...")
        result = await temu_service.get_products(page_number=1, page_size=10)
        await temu_service.close()
        
        # 解析商品列表
        product_list = result.get('data') or []
        
        print(f"📦 获取到 {len(product_list)} 个商品")
        print()
        
        # 分析每个商品的状态字段
        for idx, product in enumerate(product_list[:5], 1):  # 只分析前5个
            print(f"=" * 80)
            print(f"商品 {idx}:")
            print(f"  商品ID: {product.get('productId')}")
            print(f"  商品名称: {product.get('productName', 'N/A')[:50]}...")
            print()
            print("  状态相关字段:")
            print(f"    skcSiteStatus: {product.get('skcSiteStatus')}")
            print(f"    goodsStatus: {product.get('goodsStatus')}")
            print(f"    status: {product.get('status')}")
            print()
            print("  SKU信息:")
            sku_list = product.get('productSkuSummaries') or []
            if sku_list:
                for sku_idx, sku in enumerate(sku_list[:2], 1):  # 只显示前2个SKU
                    print(f"    SKU {sku_idx}:")
                    print(f"      productSkuId: {sku.get('productSkuId')}")
                    print(f"      extCode: {sku.get('extCode')}")
                    print(f"      skcSiteStatus: {sku.get('skcSiteStatus')}")
                    print(f"      status: {sku.get('status')}")
            else:
                print("    无SKU列表")
            print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(debug_product_status())

