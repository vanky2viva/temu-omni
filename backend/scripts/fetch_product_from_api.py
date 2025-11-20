#!/usr/bin/env python3
"""从API获取指定商品信息"""
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


async def fetch_product(product_id: str):
    """从API获取商品信息"""
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
        
        print(f"🔍 正在从API查找商品ID: {product_id}...")
        print("-" * 60)
        
        # 遍历所有页面查找商品
        page_number = 1
        page_size = 100
        found = False
        
        while page_number <= 20:
            result = await temu_service.get_products(page_number=page_number, page_size=page_size)
            product_list = result.get('data') or []
            
            if not product_list:
                break
            
            # 查找匹配的商品
            for product in product_list:
                # 检查各种可能的ID字段
                if (str(product.get('productId', '')) == product_id or
                    str(product.get('goodsId', '')) == product_id or
                    str(product.get('spuId', '')) == product_id or
                    str(product.get('skcId', '')) == product_id):
                    
                    found = True
                    print(f"✅ 找到商品!")
                    print()
                    print("📦 商品详细信息:")
                    print(json.dumps(product, indent=2, ensure_ascii=False))
                    print()
                    
                    # 提取关键信息
                    print("📋 关键信息:")
                    print(f"   商品ID: {product.get('productId')}")
                    print(f"   SPU ID: {product.get('spuId')}")
                    print(f"   SKC ID: {product.get('skcId')}")
                    print(f"   商品名称: {product.get('goodsName') or product.get('productName')}")
                    print(f"   状态 (skcSiteStatus): {product.get('skcSiteStatus')}")
                    print(f"   状态 (goodsStatus): {product.get('goodsStatus')}")
                    
                    # 检查SKU信息
                    sku_list = product.get('productSkuSummaries') or product.get('skuInfoList') or []
                    if sku_list:
                        print(f"   SKU数量: {len(sku_list)}")
                        for idx, sku in enumerate(sku_list[:3], 1):  # 只显示前3个
                            print(f"   SKU {idx}:")
                            print(f"     - extCode: {sku.get('extCode')}")
                            print(f"     - outSkuSn: {sku.get('outSkuSn')}")
                            print(f"     - skuSn: {sku.get('skuSn')}")
                    else:
                        print("   SKU信息: 无")
                    
                    break
            
            if found:
                break
            
            if len(product_list) < page_size:
                break
            
            page_number += 1
        
        await temu_service.close()
        
        if not found:
            print(f"❌ 在API返回的商品中未找到ID为 {product_id} 的商品")
            print(f"   已搜索 {page_number} 页")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python fetch_product_from_api.py <商品ID/SPU_ID/SKC_ID>")
        sys.exit(1)
    
    product_id = sys.argv[1]
    asyncio.run(fetch_product(product_id))

