#!/usr/bin/env python3
"""检查商品API返回的SKU ID字段"""
import asyncio
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.models.product import Product
from app.services.temu_service import get_temu_service


async def check_product_sku_id():
    """检查商品API返回的SKU ID"""
    db = SessionLocal()
    
    try:
        print("=" * 100)
        print("检查商品API返回的SKU ID")
        print("=" * 100)
        
        # 获取第一个启用的店铺
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        
        if not shop:
            print("❌ 没有找到启用的店铺")
            return
        
        print(f"\n🏪 店铺: {shop.shop_name} (ID: {shop.id})")
        print(f"   区域: {shop.region}")
        print(f"   环境: {shop.environment.value}")
        
        # 获取一个示例商品
        sample_product = db.query(Product).filter(
            Product.shop_id == shop.id
        ).first()
        
        if sample_product:
            print(f"\n📦 数据库中的商品示例:")
            print(f"   product_id: {sample_product.product_id}")
            print(f"   sku: {sample_product.sku}")
            print(f"   spu_id: {sample_product.spu_id}")
            print(f"   skc_id: {sample_product.skc_id}")
            print(f"   product_name: {sample_product.product_name[:50]}...")
        
        # 通过API获取商品列表
        print(f"\n{'='*100}")
        print("🔍 通过API获取商品列表...")
        print(f"{'='*100}")
        
        temu_service = get_temu_service(shop)
        
        try:
            # 获取第一页商品（只获取在售商品）
            result = await temu_service.get_products(
                page_number=1,
                page_size=1,  # 只获取1个商品
                skc_site_status=1  # 只获取在售商品
            )
            
            print(f"\n✅ API调用成功")
            print(f"   返回数据键: {list(result.keys())}")
            
            # 检查商品列表
            product_list = result.get('data') or result.get('list') or result.get('productList') or []
            
            if not product_list:
                print(f"\n⚠️  没有返回商品数据")
                print(f"\n完整响应 (前2000字符):")
                print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
                return
            
            print(f"\n📦 获取到 {len(product_list)} 个商品")
            
            # 分析第一个商品的字段
            for idx, product_data in enumerate(product_list[:1], 1):
                print(f"\n{'─'*100}")
                print(f"【商品 {idx}】详细字段分析")
                print(f"{'─'*100}")
                
                # 重点ID字段
                print(f"\n🔑 关键ID字段:")
                id_fields = [
                    'productId', 'product_id', 'goodsId', 'goods_id',
                    'skuId', 'sku_id', 'productSkuId', 'product_sku_id',
                    'skcId', 'skc_id', 'skcCode',
                    'spuId', 'spu_id',
                    'extCode', 'sku', 'productSku', 'goodsSku', 'outSkuSn'
                ]
                
                for field in id_fields:
                    if field in product_data:
                        value = product_data[field]
                        print(f"   {field:<25}: {value}")
                
                # SKU相关字段（嵌套）
                print(f"\n📋 SKU信息列表:")
                sku_list_fields = [
                    'productSkuSummaries', 'skuInfoList', 'skuList', 
                    'productSkuList', 'sku_info_list'
                ]
                
                for field in sku_list_fields:
                    if field in product_data:
                        sku_list = product_data[field]
                        if isinstance(sku_list, list) and sku_list:
                            print(f"\n   {field} ({len(sku_list)} 个SKU):")
                            for sku_idx, sku_item in enumerate(sku_list[:2], 1):  # 只显示前2个
                                print(f"\n     SKU {sku_idx}:")
                                # 显示SKU的所有字段
                                for key, value in sku_item.items():
                                    if isinstance(value, (dict, list)):
                                        value = f"<{type(value).__name__}>"
                                    print(f"       {key:<23}: {value}")
                
                # 所有字段
                print(f"\n📋 所有字段 (按字母顺序):")
                sorted_keys = sorted(product_data.keys())
                for key in sorted_keys:
                    value = product_data[key]
                    if isinstance(value, str) and len(value) > 80:
                        value = value[:80] + "..."
                    elif isinstance(value, (dict, list)):
                        value = f"<{type(value).__name__} with {len(value)} items>"
                    print(f"   {key:<30}: {value}")
            
        except Exception as e:
            print(f"\n❌ API调用失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await temu_service.close()
        
        print(f"\n{'='*100}")
        print("✅ 检查完成")
        print(f"{'='*100}")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(check_product_sku_id())

