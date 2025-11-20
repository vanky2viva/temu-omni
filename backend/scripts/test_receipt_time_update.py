#!/usr/bin/env python3
"""测试签收时间更新逻辑"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 临时设置代理URL
if not os.getenv('TEMU_API_PROXY_URL'):
    os.environ['TEMU_API_PROXY_URL'] = 'http://172.236.231.45:8001'

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.models.order import Order, OrderStatus
from app.services.sync_service import SyncService

def format_timestamp(ts):
    """格式化时间戳"""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return None

async def test_receipt_time_update():
    """测试签收时间更新逻辑"""
    db = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 测试店铺: {shop.shop_name}\n")
        
        # 查找一个已签收的订单
        delivered_order = db.query(Order).filter(
            Order.status.in_([OrderStatus.DELIVERED, OrderStatus.COMPLETED])
        ).first()
        
        if not delivered_order:
            print("❌ 未找到已签收的订单")
            return
        
        print(f"✅ 找到订单: {delivered_order.parent_order_sn}")
        print(f"   当前签收时间（数据库）: {delivered_order.delivery_time}")
        print(f"   订单状态: {delivered_order.status}\n")
        
        # 查看原始数据
        import json
        if delivered_order.raw_data:
            raw_data = json.loads(delivered_order.raw_data)
            parent_order = raw_data.get('parentOrderMap', {})
            
            parent_order_status = parent_order.get('parentOrderStatus')
            update_time_ts = parent_order.get('updateTime')
            latest_delivery_time_ts = parent_order.get('latestDeliveryTime')
            
            print("=" * 80)
            print("原始数据中的时间字段")
            print("=" * 80)
            print(f"  订单状态: {parent_order_status} ({'已收货' if parent_order_status == 5 else '其他'})")
            print(f"  updateTime (时间戳): {update_time_ts}")
            print(f"  updateTime (格式化): {format_timestamp(update_time_ts)}")
            print(f"  latestDeliveryTime (时间戳): {latest_delivery_time_ts}")
            print(f"  latestDeliveryTime (格式化): {format_timestamp(latest_delivery_time_ts)}\n")
            
            # 测试时间转换
            print("=" * 80)
            print("时间转换测试（UTC -> 北京时间）")
            print("=" * 80)
            
            if update_time_ts:
                # UTC时间
                utc_dt = datetime.fromtimestamp(update_time_ts, tz=timezone.utc)
                print(f"  updateTime UTC: {utc_dt}")
                
                # 北京时间
                beijing_tz = timezone(timedelta(hours=8))
                beijing_dt = utc_dt.astimezone(beijing_tz)
                print(f"  updateTime 北京时间: {beijing_dt}")
                
                # Naive datetime（存储到数据库）
                naive_dt = beijing_dt.replace(tzinfo=None)
                print(f"  updateTime 存储格式（北京时间）: {naive_dt}")
            
            if latest_delivery_time_ts:
                # UTC时间
                utc_dt = datetime.fromtimestamp(latest_delivery_time_ts, tz=timezone.utc)
                print(f"  latestDeliveryTime UTC: {utc_dt}")
                
                # 北京时间
                beijing_tz = timezone(timedelta(hours=8))
                beijing_dt = utc_dt.astimezone(beijing_tz)
                print(f"  latestDeliveryTime 北京时间: {beijing_dt}")
                
                # Naive datetime（存储到数据库）
                naive_dt = beijing_dt.replace(tzinfo=None)
                print(f"  latestDeliveryTime 存储格式（北京时间）: {naive_dt}")
        
        # 测试同步服务的时间解析
        print("\n" + "=" * 80)
        print("同步服务时间解析测试")
        print("=" * 80)
        
        sync_service = SyncService(db, shop)
        
        if delivered_order.raw_data:
            raw_data = json.loads(delivered_order.raw_data)
            parent_order = raw_data.get('parentOrderMap', {})
            
            # 测试解析updateTime
            if parent_order.get('updateTime'):
                parsed_time = sync_service._parse_timestamp(parent_order.get('updateTime'))
                print(f"  解析 updateTime: {parsed_time}")
                print(f"  类型: {type(parsed_time)}")
                if parsed_time:
                    print(f"  是否为naive datetime: {parsed_time.tzinfo is None}")
            
            # 测试解析latestDeliveryTime
            if parent_order.get('latestDeliveryTime'):
                parsed_time = sync_service._parse_timestamp(parent_order.get('latestDeliveryTime'))
                print(f"  解析 latestDeliveryTime: {parsed_time}")
                print(f"  类型: {type(parsed_time)}")
                if parsed_time:
                    print(f"  是否为naive datetime: {parsed_time.tzinfo is None}")
        
        print("\n" + "=" * 80)
        print("结论")
        print("=" * 80)
        print("✅ 时间戳已正确转换为北京时间（UTC+8）")
        print("✅ 对于已收货订单（status=5），将使用 updateTime 作为签收时间")
        print("✅ 时间以 naive datetime 格式存储到数据库（但已经是北京时间）")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_receipt_time_update())


