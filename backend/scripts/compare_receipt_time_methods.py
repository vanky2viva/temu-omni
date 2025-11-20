#!/usr/bin/env python3
"""对比两种方式获取签收时间"""
import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 临时设置代理URL
if not os.getenv('TEMU_API_PROXY_URL'):
    os.environ['TEMU_API_PROXY_URL'] = 'http://172.236.231.45:8001'

from app.core.database import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.shop import Shop
from app.services.temu_service import TemuService
from sqlalchemy import or_

def format_timestamp(ts):
    """格式化时间戳"""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return None

async def compare_receipt_time_methods():
    """对比两种方式获取签收时间"""
    db = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 测试店铺: {shop.shop_name}\n")
        
        temu_service = TemuService(shop)
        
        # 查找已签收的订单
        print("=" * 80)
        print("查找已签收的订单")
        print("=" * 80)
        
        delivered_orders = db.query(Order).filter(
            Order.status.in_([OrderStatus.DELIVERED, OrderStatus.COMPLETED])
        ).limit(10).all()
        
        if not delivered_orders:
            print("❌ 未找到已签收的订单")
            return
        
        print(f"✅ 找到 {len(delivered_orders)} 个已签收订单\n")
        
        # 对比每个订单的两种时间
        results = []
        
        for order in delivered_orders:
            if not order.raw_data:
                continue
            
            try:
                raw_data = json.loads(order.raw_data)
                parent_order = raw_data.get('parentOrderMap', {})
                
                # 方式1: 使用 latestDeliveryTime（最晚送达时间）
                latest_delivery_time_ts = parent_order.get('latestDeliveryTime')
                method1_time = format_timestamp(latest_delivery_time_ts) if latest_delivery_time_ts else None
                
                # 方式2: 使用 updateTime（当状态为已收货时，视为签收时间）
                update_time_ts = parent_order.get('updateTime')
                method2_time = format_timestamp(update_time_ts) if update_time_ts else None
                
                # 订单状态
                parent_order_status = parent_order.get('parentOrderStatus')
                status_text = {
                    1: "PENDING",
                    2: "UN_SHIPPING",
                    3: "CANCELED",
                    4: "SHIPPED",
                    5: "RECEIPTED",
                    41: "部分发货",
                    51: "部分收货"
                }.get(parent_order_status, f"未知({parent_order_status})")
                
                # 数据库中的送达时间
                db_delivery_time = order.delivery_time.strftime('%Y-%m-%d %H:%M:%S') if order.delivery_time else None
                
                results.append({
                    'parent_order_sn': order.parent_order_sn,
                    'order_sn': order.order_sn,
                    'status': status_text,
                    'parent_order_status': parent_order_status,
                    'method1_latestDeliveryTime': method1_time,
                    'method1_timestamp': latest_delivery_time_ts,
                    'method2_updateTime': method2_time,
                    'method2_timestamp': update_time_ts,
                    'db_delivery_time': db_delivery_time,
                    'order_time': order.order_time.strftime('%Y-%m-%d %H:%M:%S') if order.order_time else None,
                    'shipping_time': order.shipping_time.strftime('%Y-%m-%d %H:%M:%S') if order.shipping_time else None,
                })
                
            except Exception as e:
                print(f"⚠️  处理订单 {order.parent_order_sn} 时出错: {e}")
                continue
        
        # 显示对比结果
        print("=" * 80)
        print("签收时间对比结果")
        print("=" * 80)
        print(f"\n{'订单号':<30} {'状态':<12} {'方式1(latestDeliveryTime)':<25} {'方式2(updateTime)':<25} {'数据库delivery_time':<25}")
        print("-" * 120)
        
        for result in results:
            print(f"{result['parent_order_sn']:<30} {result['status']:<12} {str(result['method1_latestDeliveryTime']):<25} {str(result['method2_updateTime']):<25} {str(result['db_delivery_time']):<25}")
        
        # 详细对比
        print("\n" + "=" * 80)
        print("详细对比（前5个订单）")
        print("=" * 80)
        
        for idx, result in enumerate(results[:5], 1):
            print(f"\n订单 {idx}: {result['parent_order_sn']}")
            print(f"  子订单号: {result['order_sn']}")
            print(f"  订单状态: {result['status']} ({result['parent_order_status']})")
            print(f"  下单时间: {result['order_time']}")
            print(f"  发货时间: {result['shipping_time']}")
            print(f"  方式1 - latestDeliveryTime（最晚送达时间）: {result['method1_latestDeliveryTime']} (时间戳: {result['method1_timestamp']})")
            print(f"  方式2 - updateTime（更新时间，状态变更时）: {result['method2_updateTime']} (时间戳: {result['method2_timestamp']})")
            print(f"  数据库 - delivery_time: {result['db_delivery_time']}")
            
            # 计算时间差
            if result['method1_timestamp'] and result['method2_timestamp']:
                time_diff = abs(result['method1_timestamp'] - result['method2_timestamp'])
                days_diff = time_diff / 86400
                print(f"  时间差: {days_diff:.2f} 天 ({time_diff} 秒)")
            
            # 判断哪个更准确
            if result['parent_order_status'] == 5:  # RECEIPTED
                print(f"  💡 建议: 订单状态为已收货，方式2(updateTime)可能更准确（状态变更时间）")
            else:
                print(f"  💡 建议: 订单状态不是已收货，两种时间仅供参考")
        
        # 统计
        print("\n" + "=" * 80)
        print("统计信息")
        print("=" * 80)
        
        method1_count = sum(1 for r in results if r['method1_latestDeliveryTime'])
        method2_count = sum(1 for r in results if r['method2_updateTime'])
        status_5_count = sum(1 for r in results if r['parent_order_status'] == 5)
        
        print(f"  总订单数: {len(results)}")
        print(f"  方式1(latestDeliveryTime)有值: {method1_count}")
        print(f"  方式2(updateTime)有值: {method2_count}")
        print(f"  状态为已收货(status=5): {status_5_count}")
        
        # 对于状态为5的订单，对比两种时间
        if status_5_count > 0:
            print(f"\n  对于已收货订单的对比:")
            status_5_orders = [r for r in results if r['parent_order_status'] == 5]
            for r in status_5_orders[:3]:
                print(f"    订单 {r['parent_order_sn']}:")
                print(f"      latestDeliveryTime: {r['method1_latestDeliveryTime']}")
                print(f"      updateTime: {r['method2_updateTime']}")
                if r['method1_timestamp'] and r['method2_timestamp']:
                    diff = abs(r['method1_timestamp'] - r['method2_timestamp'])
                    print(f"      时间差: {diff/86400:.2f} 天")
        
        await temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(compare_receipt_time_methods())

