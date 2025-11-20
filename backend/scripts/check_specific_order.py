#!/usr/bin/env python3
"""检查特定订单与商品的匹配关系"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order
from app.models.product import Product


def check_specific_order():
    """检查特定订单"""
    db = SessionLocal()
    
    try:
        # 用户提供的信息
        target_order_sn = "PO-211-02345811251833312"
        target_product_sku_id = "11385873200"
        
        print("=" * 120)
        print("检查特定订单与商品的匹配")
        print("=" * 120)
        print(f"\n目标订单号: {target_order_sn}")
        print(f"目标商品 SKU ID: {target_product_sku_id}")
        
        # 1. 查找订单
        print(f"\n{'='*120}")
        print("【1】查找订单")
        print(f"{'='*120}")
        
        order = db.query(Order).filter(
            (Order.order_sn == target_order_sn) | 
            (Order.parent_order_sn == target_order_sn) |
            (Order.temu_order_id == target_order_sn)
        ).first()
        
        if not order:
            print(f"❌ 未找到订单: {target_order_sn}")
            print(f"\n尝试模糊搜索...")
            order = db.query(Order).filter(
                Order.order_sn.like(f'%{target_order_sn[-10:]}%')
            ).first()
            
            if order:
                print(f"✅ 找到相似订单: {order.order_sn}")
            else:
                print(f"❌ 仍未找到订单")
                return
        else:
            print(f"✅ 找到订单: {order.order_sn}")
        
        print(f"\n订单信息:")
        print(f"   order_sn: {order.order_sn}")
        print(f"   parent_order_sn: {order.parent_order_sn}")
        print(f"   temu_order_id: {order.temu_order_id}")
        print(f"   product_name: {order.product_name[:60]}")
        print(f"   product_sku (数据库): {order.product_sku}")
        print(f"   spu_id (数据库): {order.spu_id or '空'}")
        print(f"   product_id (关联): {order.product_id}")
        
        # 解析原始数据
        if not order.raw_data:
            print(f"\n⚠️  订单没有原始数据")
            return
        
        print(f"\n{'─'*120}")
        print("【订单原始数据中的所有ID字段】")
        print(f"{'─'*120}")
        
        raw_data = json.loads(order.raw_data)
        
        # 提取所有ID字段
        all_ids = {}
        
        # 从 orderList 提取
        order_list = raw_data.get('orderList', [])
        if order_list:
            order_item = order_list[0]
            
            # 订单级别的ID
            id_fields = ['skuId', 'goodsId', 'productId', 'skcId', 'spuId']
            for field in id_fields:
                if field in order_item:
                    all_ids[f"orderList[].{field}"] = order_item[field]
            
            # productList 中的ID
            product_list = order_item.get('productList', [])
            if product_list:
                product_info = product_list[0]
                product_id_fields = ['productSkuId', 'productId', 'skuId', 'extCode']
                for field in product_id_fields:
                    if field in product_info:
                        all_ids[f"orderList[].productList[].{field}"] = product_info[field]
        
        # 显示所有ID
        print(f"\n提取到的所有ID字段:")
        for path, value in all_ids.items():
            print(f"   {path:<45}: {value}")
        
        # 2. 查找目标商品
        print(f"\n{'='*120}")
        print(f"【2】查找商品 (SKU ID: {target_product_sku_id})")
        print(f"{'='*120}")
        
        # 尝试多种方式查找
        product = None
        match_field = None
        
        # 方式1: 通过 product_id
        product = db.query(Product).filter(
            Product.product_id == target_product_sku_id
        ).first()
        if product:
            match_field = "Product.product_id"
            print(f"✅ 通过 Product.product_id 找到商品")
        
        # 方式2: 如果没找到，尝试其他店铺
        if not product:
            product = db.query(Product).filter(
                Product.product_id == target_product_sku_id
            ).first()
            if product:
                match_field = "Product.product_id (其他店铺)"
        
        if not product:
            print(f"❌ 未找到 product_id = {target_product_sku_id} 的商品")
            print(f"\n尝试查找所有可能的商品...")
            
            # 显示该店铺的所有商品
            shop_products = db.query(Product).filter(
                Product.shop_id == order.shop_id
            ).limit(10).all()
            
            print(f"\n该店铺的商品列表（前10个）:")
            print(f"{'product_id':<20} {'sku':<20} {'product_name':<60}")
            print("-" * 120)
            for p in shop_products:
                print(f"{p.product_id:<20} {p.sku:<20} {p.product_name[:60]}")
        else:
            print(f"\n商品信息:")
            print(f"   Product.id: {product.id}")
            print(f"   Product.product_id: {product.product_id}")
            print(f"   Product.sku: {product.sku}")
            print(f"   Product.skc_id: {product.skc_id}")
            print(f"   Product.spu_id: {product.spu_id}")
            print(f"   Product.product_name: {product.product_name[:60]}")
        
        # 3. 尝试匹配
        print(f"\n{'='*120}")
        print("【3】匹配分析")
        print(f"{'='*120}")
        
        if product:
            # 对比所有ID
            print(f"\n逐一对比所有ID字段:")
            print(f"{'订单字段':<45} {'订单值':<25} {'商品值':<25} {'匹配?'}")
            print("-" * 120)
            
            # 商品的所有ID
            product_ids = {
                'Product.product_id': product.product_id,
                'Product.sku': product.sku,
                'Product.skc_id': product.skc_id,
                'Product.spu_id': product.spu_id,
            }
            
            matches = []
            for order_path, order_value in all_ids.items():
                for product_field, product_value in product_ids.items():
                    if product_value and str(order_value) == str(product_value):
                        matches.append({
                            'order_field': order_path,
                            'order_value': order_value,
                            'product_field': product_field,
                            'product_value': product_value
                        })
                        print(f"{order_path:<45} {str(order_value):<25} {str(product_value):<25} ✅ 匹配!")
            
            if not matches:
                print(f"\n❌ 没有找到任何匹配的ID字段")
                print(f"\n但可以尝试通过 extCode (SKU货号) 匹配:")
                ext_code = all_ids.get('orderList[].productList[].extCode')
                if ext_code:
                    matched_by_sku = db.query(Product).filter(
                        Product.shop_id == order.shop_id,
                        Product.sku == ext_code
                    ).first()
                    if matched_by_sku:
                        print(f"   ✅ 通过 extCode '{ext_code}' 找到商品:")
                        print(f"      Product.id: {matched_by_sku.id}")
                        print(f"      Product.sku: {matched_by_sku.sku}")
                        print(f"      Product.product_name: {matched_by_sku.product_name[:60]}")
            else:
                print(f"\n{'='*120}")
                print(f"✅ 找到 {len(matches)} 个匹配!")
                print(f"{'='*120}")
                for match in matches:
                    print(f"\n匹配字段:")
                    print(f"   订单: {match['order_field']} = {match['order_value']}")
                    print(f"   商品: {match['product_field']} = {match['product_value']}")
        
        print(f"\n{'='*120}")
        print("✅ 检查完成")
        print(f"{'='*120}")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_specific_order()

