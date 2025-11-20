#!/usr/bin/env python3
"""对比订单和商品的SKU ID"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order
from app.models.product import Product


def compare_sku_ids():
    """对比订单和商品的SKU ID"""
    db = SessionLocal()
    
    try:
        print("=" * 120)
        print("订单与商品 SKU ID 对照")
        print("=" * 120)
        
        # 获取一个有原始数据的订单
        order = db.query(Order).filter(Order.raw_data.isnot(None)).first()
        
        if not order:
            print("没有订单数据")
            return
        
        print(f"\n【订单】{order.order_sn}")
        print(f"商品名称: {order.product_name[:60]}")
        print(f"product_sku (数据库): {order.product_sku}")
        
        # 解析原始数据
        raw_data = json.loads(order.raw_data)
        order_list = raw_data.get('orderList', [])
        
        if order_list:
            order_item = order_list[0]
            
            print(f"\n🔑 订单中的ID字段:")
            print(f"   orderList[].skuId           : {order_item.get('skuId')}")
            print(f"   orderList[].goodsId         : {order_item.get('goodsId')}")
            
            product_list = order_item.get('productList', [])
            if product_list:
                product_info = product_list[0]
                print(f"\n   productList[].productSkuId  : {product_info.get('productSkuId')}")
                print(f"   productList[].productId     : {product_info.get('productId')}")
                print(f"   productList[].extCode       : {product_info.get('extCode')}")  # 真正的SKU货号
        
        # 获取对应店铺的商品
        print(f"\n{'='*120}")
        print(f"【商品列表】店铺ID: {order.shop_id}")
        print(f"{'='*120}")
        
        products = db.query(Product).filter(
            Product.shop_id == order.shop_id
        ).limit(5).all()
        
        print(f"\n找到 {len(products)} 个商品\n")
        
        print(f"{'Product.id':<12} {'Product.product_id':<20} {'Product.sku':<20} {'Product.skc_id':<20} {'Product.spu_id':<20}")
        print("-" * 120)
        
        for product in products:
            print(f"{product.id:<12} {product.product_id:<20} {product.sku:<20} {product.skc_id or 'NULL':<20} {product.spu_id or 'NULL':<20}")
        
        # 匹配分析
        print(f"\n{'='*120}")
        print("🎯 匹配分析")
        print(f"{'='*120}")
        
        if order_list and product_list:
            ext_code = product_list[0].get('extCode')  # 订单的SKU货号
            
            if ext_code:
                # 通过extCode (SKU货号) 匹配
                matched_product = db.query(Product).filter(
                    Product.shop_id == order.shop_id,
                    Product.sku == ext_code
                ).first()
                
                if matched_product:
                    print(f"\n✅ 通过 extCode (SKU货号) 匹配成功:")
                    print(f"   订单 extCode: {ext_code}")
                    print(f"   商品 SKU: {matched_product.sku}")
                    print(f"   商品 product_id: {matched_product.product_id}")
                    print(f"   商品 skc_id: {matched_product.skc_id}")
                    print(f"   商品 spu_id: {matched_product.spu_id}")
                    
                    # 对比订单和商品的ID
                    print(f"\n📊 ID对照:")
                    print(f"   订单 skuId              : {order_item.get('skuId')}")
                    print(f"   订单 productSkuId       : {product_list[0].get('productSkuId')}")
                    print(f"   商品 product_id (数据库) : {matched_product.product_id}")
                    print(f"   商品 skc_id (数据库)     : {matched_product.skc_id}")
                    
                    # 结论
                    print(f"\n💡 结论:")
                    if str(order_item.get('skuId')) == str(matched_product.product_id):
                        print(f"   ✅ 订单的 skuId 与商品的 product_id 匹配！")
                    elif str(product_list[0].get('productSkuId')) == str(matched_product.product_id):
                        print(f"   ✅ 订单的 productSkuId 与商品的 product_id 匹配！")
                    else:
                        print(f"   ⚠️  订单的 skuId 和 productSkuId 都不匹配商品的 product_id")
                        print(f"   ✅ 但可以通过 extCode (SKU货号) 匹配：{ext_code}")
                else:
                    print(f"\n❌ 通过 extCode 未找到匹配的商品")
                    print(f"   订单 extCode: {ext_code}")
        
        print(f"\n{'='*120}")
        print("✅ 对比完成")
        print(f"{'='*120}")
        
        print(f"\n💡 最终建议:")
        print(f"   1. 最可靠的匹配方式：通过 extCode (SKU货号) 匹配")
        print(f"      订单: orderList[].productList[].extCode")
        print(f"      商品: Product.sku")
        print(f"   2. 备选方式：尝试通过 skuId 或 productSkuId 匹配")
        print(f"      需要进一步验证 ID 格式是否一致")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    compare_sku_ids()

