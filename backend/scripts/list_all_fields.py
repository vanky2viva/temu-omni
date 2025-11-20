#!/usr/bin/env python3
"""列出商品和订单的所有字段及示例数据"""
import sys
import json
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order
from app.models.product import Product, ProductCost
from sqlalchemy import inspect


def format_value(value, max_length=60):
    """格式化值用于显示"""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    if isinstance(value, str):
        if len(value) > max_length:
            return value[:max_length] + "..."
        return value
    return str(value)[:max_length]


def list_all_fields():
    """列出所有字段"""
    db = SessionLocal()
    
    try:
        print("=" * 120)
        print("商品表和订单表字段对照")
        print("=" * 120)
        
        # ===== 商品表 =====
        print("\n" + "=" * 120)
        print("【1】商品表 (Product) - 数据库字段")
        print("=" * 120)
        
        # 获取Product模型的所有列
        product_columns = inspect(Product).columns
        print(f"\n{'字段名':<30} {'类型':<20} {'说明':<40}")
        print("-" * 120)
        
        for col in product_columns:
            col_name = col.name
            col_type = str(col.type)
            comment = col.comment or ""
            print(f"{col_name:<30} {col_type:<20} {comment:<40}")
        
        # 获取示例商品数据
        sample_products = db.query(Product).limit(3).all()
        
        if sample_products:
            print(f"\n示例数据（前3个商品）:")
            print("=" * 120)
            
            for idx, product in enumerate(sample_products, 1):
                print(f"\n【商品 {idx}】")
                print("-" * 120)
                for col in product_columns:
                    col_name = col.name
                    value = getattr(product, col_name, None)
                    formatted_value = format_value(value)
                    print(f"  {col_name:<28}: {formatted_value}")
        
        # ===== 商品成本表 =====
        print("\n\n" + "=" * 120)
        print("【2】商品成本表 (ProductCost) - 数据库字段")
        print("=" * 120)
        
        cost_columns = inspect(ProductCost).columns
        print(f"\n{'字段名':<30} {'类型':<20} {'说明':<40}")
        print("-" * 120)
        
        for col in cost_columns:
            col_name = col.name
            col_type = str(col.type)
            comment = col.comment or ""
            print(f"{col_name:<30} {col_type:<20} {comment:<40}")
        
        # 获取示例成本数据
        sample_costs = db.query(ProductCost).filter(
            ProductCost.effective_to.is_(None)
        ).limit(3).all()
        
        if sample_costs:
            print(f"\n示例数据（前3个成本记录）:")
            print("=" * 120)
            
            for idx, cost in enumerate(sample_costs, 1):
                print(f"\n【成本记录 {idx}】")
                print("-" * 120)
                for col in cost_columns:
                    col_name = col.name
                    value = getattr(cost, col_name, None)
                    formatted_value = format_value(value)
                    print(f"  {col_name:<28}: {formatted_value}")
        
        # ===== 订单表 =====
        print("\n\n" + "=" * 120)
        print("【3】订单表 (Order) - 数据库字段")
        print("=" * 120)
        
        order_columns = inspect(Order).columns
        print(f"\n{'字段名':<30} {'类型':<20} {'说明':<40}")
        print("-" * 120)
        
        for col in order_columns:
            col_name = col.name
            col_type = str(col.type)
            comment = col.comment or ""
            print(f"{col_name:<30} {col_type:<20} {comment:<40}")
        
        # 获取示例订单数据
        sample_orders = db.query(Order).limit(3).all()
        
        if sample_orders:
            print(f"\n示例数据（前3个订单）:")
            print("=" * 120)
            
            for idx, order in enumerate(sample_orders, 1):
                print(f"\n【订单 {idx}】")
                print("-" * 120)
                for col in order_columns:
                    col_name = col.name
                    value = getattr(order, col_name, None)
                    if col_name == 'raw_data':
                        # raw_data太长，只显示是否有数据
                        formatted_value = f"<JSON数据 {len(value)} 字符>" if value else "NULL"
                    else:
                        formatted_value = format_value(value)
                    print(f"  {col_name:<28}: {formatted_value}")
        
        # ===== 订单原始数据字段分析 =====
        print("\n\n" + "=" * 120)
        print("【4】订单原始数据 (raw_data) - API返回字段")
        print("=" * 120)
        
        if sample_orders and sample_orders[0].raw_data:
            print("\n分析第一个订单的原始数据结构...")
            
            try:
                raw_data = json.loads(sample_orders[0].raw_data)
                
                # order_item字段
                if 'order_item' in raw_data:
                    print("\n【order_item 字段】（子订单数据）")
                    print("-" * 120)
                    order_item = raw_data['order_item']
                    
                    # 按字母顺序排序显示
                    sorted_keys = sorted(order_item.keys())
                    for key in sorted_keys:
                        value = order_item[key]
                        formatted_value = format_value(value, 80)
                        print(f"  {key:<30}: {formatted_value}")
                
                # parent_order字段
                if 'parent_order' in raw_data:
                    print("\n【parent_order 字段】（父订单数据）")
                    print("-" * 120)
                    parent_order = raw_data['parent_order']
                    
                    # 按字母顺序排序显示
                    sorted_keys = sorted(parent_order.keys())
                    for key in sorted_keys:
                        value = parent_order[key]
                        # 跳过嵌套对象，只显示简单值
                        if isinstance(value, (dict, list)):
                            formatted_value = f"<{type(value).__name__}>"
                        else:
                            formatted_value = format_value(value, 80)
                        print(f"  {key:<30}: {formatted_value}")
                
            except json.JSONDecodeError as e:
                print(f"  ⚠️  无法解析JSON: {e}")
        
        # ===== 关键字段对照表 =====
        print("\n\n" + "=" * 120)
        print("【5】关键匹配字段对照表")
        print("=" * 120)
        
        print("\n可用于匹配的字段组合:")
        print("-" * 120)
        print("\n1️⃣  通过 product_id (商品ID) 匹配:")
        print("   商品表: Product.product_id")
        print("   订单表: Order.notes 中的 'GoodsID: xxx'")
        print("   匹配度: ⭐⭐⭐ (goods_id 格式可能不同)")
        
        print("\n2️⃣  通过 spu_id (SPU ID) 匹配:")
        print("   商品表: Product.spu_id")
        print("   订单表: Order.spu_id (目前为空)")
        print("   匹配度: ⭐⭐⭐⭐⭐ (最准确，但订单中缺失)")
        
        print("\n3️⃣  通过 sku (SKU货号) 匹配:")
        print("   商品表: Product.sku (如: LBB3-1-US)")
        print("   订单表: Order.product_sku (实际是规格描述，如: 1pc, Random 1PCS)")
        print("   匹配度: ⭐ (字段内容不匹配)")
        
        print("\n4️⃣  通过 skc_id 匹配:")
        print("   商品表: Product.skc_id")
        print("   订单表: 未保存")
        print("   匹配度: ⭐⭐⭐⭐ (准确但订单中缺失)")
        
        # 统计匹配情况
        print("\n\n" + "=" * 120)
        print("【6】当前匹配统计")
        print("=" * 120)
        
        total_orders = db.query(Order).count()
        orders_with_cost = db.query(Order).filter(Order.total_cost.isnot(None)).count()
        orders_with_product_id = db.query(Order).filter(Order.product_id.isnot(None)).count()
        orders_with_spu = db.query(Order).filter(
            Order.spu_id.isnot(None),
            Order.spu_id != ''
        ).count()
        
        print(f"\n总订单数: {total_orders}")
        print(f"已关联商品 (product_id不为空): {orders_with_product_id} ({orders_with_product_id/total_orders*100:.1f}%)" if total_orders > 0 else "已关联商品: 0")
        print(f"有SPU ID的订单: {orders_with_spu} ({orders_with_spu/total_orders*100:.1f}%)" if total_orders > 0 else "有SPU ID的订单: 0")
        print(f"有成本信息的订单: {orders_with_cost} ({orders_with_cost/total_orders*100:.1f}%)" if total_orders > 0 else "有成本信息的订单: 0")
        
        total_products = db.query(Product).count()
        products_with_cost = db.query(Product).join(ProductCost).filter(
            ProductCost.effective_to.is_(None)
        ).count()
        
        print(f"\n总商品数 (SKU级别): {total_products}")
        print(f"有成本价的商品: {products_with_cost} ({products_with_cost/total_products*100:.1f}%)" if total_products > 0 else "有成本价的商品: 0")
        
        print("\n" + "=" * 120)
        print("✅ 字段列表完成")
        print("=" * 120)
        
        print("\n💡 建议:")
        print("   1. 订单同步时需要正确提取并保存 spu_id 字段")
        print("   2. 可以尝试通过原始数据中的其他ID字段进行匹配")
        print("   3. 如果API返回的ID格式不同，可能需要建立映射关系")
        print()
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    list_all_fields()

