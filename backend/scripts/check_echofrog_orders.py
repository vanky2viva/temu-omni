#!/usr/bin/env python3
"""
诊断脚本：检查 echofrog 店铺 2025-11-27 的订单统计
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, distinct

from app.core.database import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.shop import Shop
from app.api.analytics import build_sales_filters, BEIJING_TIMEZONE, get_beijing_now

def get_date_in_beijing_timezone(column):
    """获取日期部分（北京时间）"""
    return func.date(column)

def check_echofrog_orders():
    """检查 echofrog 店铺的订单数据"""
    db: Session = SessionLocal()
    
    try:
        # 查找 echofrog 店铺
        shop = db.query(Shop).filter(Shop.shop_name.ilike('%echofrog%')).first()
        if not shop:
            print("❌ 未找到 echofrog 店铺")
            # 列出所有店铺
            shops = db.query(Shop).all()
            print(f"\n可用店铺列表：")
            for s in shops:
                print(f"  - ID: {s.id}, 名称: {s.shop_name}")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name} (ID: {shop.id})")
        
        # 设置日期范围：2025-11-27（北京时间）
        beijing_tz = pytz.timezone('Asia/Shanghai')
        start_date = beijing_tz.localize(datetime(2025, 11, 27, 0, 0, 0))
        end_date = beijing_tz.localize(datetime(2025, 11, 27, 23, 59, 59))
        
        # 转换为 naive datetime（数据库存储格式）
        start_date_naive = start_date.replace(tzinfo=None)
        end_date_naive = end_date.replace(tzinfo=None)
        
        print(f"\n📅 查询日期范围（北京时间）:")
        print(f"  开始: {start_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  结束: {end_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  数据库查询范围: {start_date_naive} ~ {end_date_naive}")
        
        # 1. 检查所有订单（不区分状态）
        all_orders = db.query(Order).filter(
            Order.shop_id == shop.id,
            Order.order_time >= start_date_naive,
            Order.order_time <= end_date_naive
        ).all()
        
        print(f"\n📊 订单统计（所有状态）:")
        print(f"  总订单记录数: {len(all_orders)}")
        
        # 按状态分组统计
        status_counts = {}
        for order in all_orders:
            status = order.status.value if order.status else 'UNKNOWN'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"  按状态分组:")
        for status, count in sorted(status_counts.items()):
            print(f"    {status}: {count}")
        
        # 2. 检查有效订单（PROCESSING, SHIPPED, DELIVERED）
        valid_orders = db.query(Order).filter(
            Order.shop_id == shop.id,
            Order.order_time >= start_date_naive,
            Order.order_time <= end_date_naive,
            Order.status.in_([
                OrderStatus.PROCESSING,  # 待发货
                OrderStatus.SHIPPED,     # 已发货
                OrderStatus.DELIVERED    # 已签收
            ])
        ).all()
        
        print(f"\n✅ 有效订单统计（PROCESSING, SHIPPED, DELIVERED）:")
        print(f"  有效订单记录数: {len(valid_orders)}")
        
        # 按状态分组统计有效订单
        valid_status_counts = {}
        for order in valid_orders:
            status = order.status.value if order.status else 'UNKNOWN'
            valid_status_counts[status] = valid_status_counts.get(status, 0) + 1
        
        print(f"  按状态分组:")
        for status, count in sorted(valid_status_counts.items()):
            print(f"    {status}: {count}")
        
        # 3. 检查父订单去重后的数量
        parent_order_key = case(
            (Order.parent_order_sn.isnot(None), Order.parent_order_sn),
            else_=Order.order_sn
        )
        
        # 统计不重复的父订单数
        distinct_parent_orders = db.query(
            distinct(parent_order_key).label('parent_key')
        ).filter(
            Order.shop_id == shop.id,
            Order.order_time >= start_date_naive,
            Order.order_time <= end_date_naive,
            Order.status.in_([
                OrderStatus.PROCESSING,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED
            ])
        ).all()
        
        parent_order_count = len(distinct_parent_orders)
        print(f"\n🔢 父订单去重统计:")
        print(f"  不重复的父订单数: {parent_order_count}")
        
        # 4. 检查 PROCESSING 状态的订单（用户说的 101 个）
        processing_orders = db.query(Order).filter(
            Order.shop_id == shop.id,
            Order.order_time >= start_date_naive,
            Order.order_time <= end_date_naive,
            Order.status == OrderStatus.PROCESSING
        ).all()
        
        print(f"\n📦 PROCESSING（待发货）订单:")
        print(f"  订单记录数: {len(processing_orders)}")
        
        # PROCESSING 状态的父订单去重
        distinct_processing_parent_orders = db.query(
            distinct(parent_order_key).label('parent_key')
        ).filter(
            Order.shop_id == shop.id,
            Order.order_time >= start_date_naive,
            Order.order_time <= end_date_naive,
            Order.status == OrderStatus.PROCESSING
        ).all()
        
        processing_parent_count = len(distinct_processing_parent_orders)
        print(f"  不重复的父订单数: {processing_parent_count}")
        
        # 5. 检查日期边界情况
        print(f"\n🔍 日期边界检查:")
        
        # 检查 11-26 23:00 到 11-27 01:00 的订单（跨天边界）
        boundary_start = beijing_tz.localize(datetime(2025, 11, 26, 23, 0, 0))
        boundary_end = beijing_tz.localize(datetime(2025, 11, 27, 1, 0, 0))
        boundary_start_naive = boundary_start.replace(tzinfo=None)
        boundary_end_naive = boundary_end.replace(tzinfo=None)
        
        boundary_orders = db.query(Order).filter(
            Order.shop_id == shop.id,
            Order.order_time >= boundary_start_naive,
            Order.order_time <= boundary_end_naive,
            Order.status == OrderStatus.PROCESSING
        ).all()
        
        print(f"  11-26 23:00 ~ 11-27 01:00 的 PROCESSING 订单数: {len(boundary_orders)}")
        for order in boundary_orders[:5]:  # 只显示前5个
            print(f"    - {order.order_sn}: {order.order_time} (状态: {order.status.value})")
        
        # 6. 使用 build_sales_filters 检查统计逻辑
        print(f"\n🔧 使用 build_sales_filters 检查:")
        filters = build_sales_filters(
            db=db,
            start_date=start_date_naive,
            end_date=end_date_naive,
            shop_ids=[shop.id]
        )
        
        # 使用这些过滤器查询
        filtered_orders = db.query(Order).filter(and_(*filters)).all()
        print(f"  使用 build_sales_filters 的订单记录数: {len(filtered_orders)}")
        
        # 父订单去重
        filtered_distinct_parent = db.query(
            distinct(parent_order_key).label('parent_key')
        ).filter(and_(*filters)).all()
        
        filtered_parent_count = len(filtered_distinct_parent)
        print(f"  使用 build_sales_filters 的父订单数: {filtered_parent_count}")
        
        # 7. 检查是否有更多订单（扩大日期范围）
        print(f"\n🔍 扩大日期范围检查（11-26 ~ 11-28）:")
        extended_start = beijing_tz.localize(datetime(2025, 11, 26, 0, 0, 0))
        extended_end = beijing_tz.localize(datetime(2025, 11, 28, 23, 59, 59))
        extended_start_naive = extended_start.replace(tzinfo=None)
        extended_end_naive = extended_end.replace(tzinfo=None)
        
        extended_processing = db.query(
            distinct(parent_order_key).label('parent_key')
        ).filter(
            Order.shop_id == shop.id,
            Order.order_time >= extended_start_naive,
            Order.order_time <= extended_end_naive,
            Order.status == OrderStatus.PROCESSING
        ).all()
        
        extended_count = len(extended_processing)
        print(f"  11-26 ~ 11-28 的 PROCESSING 父订单数: {extended_count}")
        
        # 8. 检查所有 PROCESSING 订单（不限制日期）
        all_time_processing = db.query(
            distinct(parent_order_key).label('parent_key')
        ).filter(
            Order.shop_id == shop.id,
            Order.status == OrderStatus.PROCESSING
        ).all()
        
        all_time_count = len(all_time_processing)
        print(f"  所有时间的 PROCESSING 父订单数: {all_time_count}")
        
        # 9. 检查订单时间分布
        print(f"\n📅 订单时间分布（11-27 的 PROCESSING 订单）:")
        time_distribution = db.query(
            func.date(Order.order_time).label('date'),
            func.count(distinct(parent_order_key)).label('count')
        ).filter(
            Order.shop_id == shop.id,
            Order.status == OrderStatus.PROCESSING,
            Order.order_time >= extended_start_naive,
            Order.order_time <= extended_end_naive
        ).group_by(func.date(Order.order_time)).order_by(func.date(Order.order_time)).all()
        
        for row in time_distribution:
            print(f"  {row.date}: {row.count} 个父订单")
        
        # 10. 检查是否有订单的 order_time 不在 11-27 范围内
        print(f"\n🔍 检查订单时间范围问题:")
        # 查找所有 PROCESSING 订单，看看它们的 order_time
        all_processing_orders = db.query(Order).filter(
            Order.shop_id == shop.id,
            Order.status == OrderStatus.PROCESSING
        ).order_by(Order.order_time.desc()).limit(200).all()
        
        # 统计 11-27 前后的订单
        before_27 = 0
        on_27 = 0
        after_27 = 0
        
        for order in all_processing_orders:
            order_date = order.order_time.date()
            if order_date < datetime(2025, 11, 27).date():
                before_27 += 1
            elif order_date == datetime(2025, 11, 27).date():
                on_27 += 1
            elif order_date > datetime(2025, 11, 27).date():
                after_27 += 1
        
        print(f"  11-27 之前的 PROCESSING 订单: {before_27}")
        print(f"  11-27 当天的 PROCESSING 订单: {on_27}")
        print(f"  11-27 之后的 PROCESSING 订单: {after_27}")
        
        # 11. 对比结果
        print(f"\n📈 对比分析:")
        print(f"  平台显示: 101 个有效订单（待发货）")
        print(f"  系统统计 - 11-27 PROCESSING 父订单数: {processing_parent_count}")
        print(f"  系统统计 - 11-26~11-28 PROCESSING 父订单数: {extended_count}")
        print(f"  系统统计 - 所有时间 PROCESSING 父订单数: {all_time_count}")
        print(f"  系统统计 - 使用 build_sales_filters: {filtered_parent_count}")
        
        if processing_parent_count != 101:
            print(f"\n⚠️  差异: {abs(processing_parent_count - 101)} 个订单")
            print(f"  可能原因:")
            if extended_count >= 101:
                print(f"    ✅ 扩大日期范围后找到 {extended_count} 个订单，可能是日期范围问题")
            else:
                print(f"    ❌ 扩大日期范围后仍只有 {extended_count} 个订单，可能是订单同步不完整")
            print(f"    1. 日期范围处理问题（时区转换）")
            print(f"    2. 订单状态映射问题")
            print(f"    3. 父订单去重逻辑问题")
            print(f"    4. 订单同步不完整（缺少 {101 - processing_parent_count} 个订单）")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    check_echofrog_orders()

