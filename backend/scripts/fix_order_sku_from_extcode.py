#!/usr/bin/env python3
"""从订单原始数据中提取extCode并修复product_sku字段"""
import sys
import json
from pathlib import Path
from sqlalchemy import or_

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order


def fix_order_sku_from_extcode(shop_id: int = None, dry_run: bool = True):
    """
    从订单原始数据中提取extCode并修复product_sku字段
    
    Args:
        shop_id: 店铺ID，如果为None则修复所有店铺的订单
        dry_run: 是否为试运行模式（只显示不实际更新）
    """
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("修复订单SKU货号（从extCode提取）")
        print("=" * 80)
        print(f"模式: {'🔍 试运行（只查看不修改）' if dry_run else '✏️  实际修复'}")
        
        # 定义无效的SKU值（这些不是真正的extCode格式）
        invalid_sku_patterns = [
            '1', '1pc', 'Random 1PCS', 'random 1pcs', 
            'RANDOM 1PCS', '1PCS', '1pcs', 'random',
            'Random', 'RANDOM'
        ]
        
        # 查询订单
        query = db.query(Order)
        
        if shop_id:
            query = query.filter(Order.shop_id == shop_id)
            print(f"\n🏪 修复店铺ID: {shop_id} 的订单")
        else:
            print(f"\n🏪 修复所有店铺的订单")
        
        # 查找需要修复的订单：
        # 1. product_sku为空
        # 2. product_sku是无效格式（如"1", "1pc", "Random 1PCS"等）
        # 3. 或者所有有raw_data的订单（检查是否有更好的extCode）
        conditions = [
            Order.product_sku.is_(None),
            Order.product_sku == '',
        ]
        
        # 添加无效SKU模式的条件
        for pattern in invalid_sku_patterns:
            conditions.append(Order.product_sku == pattern)
        
        query = query.filter(or_(*conditions))
        
        # 只查询有raw_data的订单
        query = query.filter(Order.raw_data.isnot(None))
        query = query.filter(Order.raw_data != '')
        
        orders = query.all()
        
        print(f"📊 找到 {len(orders)} 个需要检查的订单")
        
        if not orders:
            print("\n✅ 没有找到需要修复的订单")
            return
        
        # 统计信息
        updated_count = 0
        not_found_count = 0
        already_correct_count = 0
        no_raw_data_count = 0
        
        print("\n" + "=" * 80)
        print("🔄 开始检查和修复订单SKU货号...")
        print("=" * 80)
        
        for idx, order in enumerate(orders, 1):
            if idx % 100 == 0:
                print(f"   处理进度: {idx}/{len(orders)}")
            
            try:
                # 从raw_data中提取extCode
                ext_code = None
                
                if order.raw_data:
                    try:
                        raw_data = json.loads(order.raw_data)
                        
                        # 方式1: 从orderList[].productList[].extCode提取
                        order_list = raw_data.get('orderList', [])
                        if order_list:
                            for order_item in order_list:
                                if order_item.get('orderSn') == order.order_sn:
                                    product_list = order_item.get('productList', [])
                                    if product_list and len(product_list) > 0:
                                        product_info = product_list[0]
                                        ext_code = product_info.get('extCode')
                                        if ext_code:
                                            break
                        
                        # 方式2: 如果方式1没找到，尝试从order_item中提取
                        if not ext_code:
                            order_item = raw_data.get('order_item') or raw_data.get('orderItem')
                            if order_item:
                                product_list = order_item.get('productList', [])
                                if product_list and len(product_list) > 0:
                                    product_info = product_list[0]
                                    ext_code = product_info.get('extCode')
                        
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        no_raw_data_count += 1
                        continue
                
                # 如果找到了extCode且与当前值不同
                if ext_code and ext_code.strip():
                    ext_code = ext_code.strip()
                    current_sku = order.product_sku or ''
                    
                    # 判断是否需要更新
                    should_update = False
                    reason = ''
                    
                    if not current_sku or current_sku == '':
                        should_update = True
                        reason = '当前SKU为空'
                    elif current_sku in invalid_sku_patterns:
                        should_update = True
                        reason = f'当前SKU无效（{current_sku}）'
                    elif current_sku != ext_code:
                        # 检查当前SKU是否是有效的extCode格式（包含字母和数字的组合）
                        if current_sku.isdigit() or current_sku in invalid_sku_patterns:
                            should_update = True
                            reason = f'当前SKU格式无效，使用extCode（{ext_code}）'
                    
                    if should_update:
                        if dry_run:
                            print(f"\n📝 订单 {order.order_sn}:")
                            print(f"   当前SKU: {current_sku}")
                            print(f"   新的SKU: {ext_code}")
                            print(f"   原因: {reason}")
                        else:
                            # 实际更新
                            old_sku = order.product_sku
                            order.product_sku = ext_code
                            db.commit()
                            print(f"\n✅ 更新订单 {order.order_sn}: {old_sku} -> {ext_code}")
                        
                        updated_count += 1
                    else:
                        already_correct_count += 1
                else:
                    not_found_count += 1
                    if idx <= 10:  # 只显示前10个没找到的例子
                        print(f"\n⚠️  订单 {order.order_sn}: 在raw_data中未找到extCode")
                        print(f"   当前SKU: {order.product_sku}")
                
            except Exception as e:
                print(f"\n❌ 处理订单 {order.order_sn} 时出错: {e}")
                db.rollback()
                continue
        
        # 打印统计结果
        print("\n" + "=" * 80)
        print("📊 修复统计")
        print("=" * 80)
        print(f"✅ 已修复/需要修复: {updated_count} 个订单")
        print(f"✅ 已正确（无需修复）: {already_correct_count} 个订单")
        print(f"⚠️  未找到extCode: {not_found_count} 个订单")
        print(f"⚠️  原始数据无效: {no_raw_data_count} 个订单")
        print(f"📊 总计检查: {len(orders)} 个订单")
        
        if dry_run:
            print("\n💡 提示: 这是试运行模式，没有实际修改数据")
            print("   要实际执行修复，请运行: python fix_order_sku_from_extcode.py --execute")
        else:
            print("\n✅ 修复完成！")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='修复订单SKU货号（从extCode提取）')
    parser.add_argument('--shop-id', type=int, help='店铺ID（可选）')
    parser.add_argument('--execute', action='store_true', help='实际执行修复（默认是试运行模式）')
    
    args = parser.parse_args()
    
    fix_order_sku_from_extcode(
        shop_id=args.shop_id,
        dry_run=not args.execute
    )

