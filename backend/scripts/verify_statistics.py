#!/usr/bin/env python3
"""
验证销量统计准确性脚本
检查统计逻辑、时间处理、订单状态过滤等
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, engine
from app.core.config import settings
from app.models.order import Order, OrderStatus
from app.models.shop import Shop
from app.services.unified_statistics import UnifiedStatisticsService
from sqlalchemy import func, and_, text
from loguru import logger

# 北京时间时区
BEIJING_TIMEZONE = pytz.timezone(getattr(settings, 'TIMEZONE', 'Asia/Shanghai'))

def verify_statistics():
    """验证销量统计准确性"""
    print("=" * 60)
    print("销量统计准确性验证")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. 检查数据库时区设置
        print("\n1. 检查数据库时区设置...")
        try:
            result = db.execute(text("SHOW timezone"))
            db_timezone = result.scalar()
            print(f"   数据库时区: {db_timezone}")
            if 'UTC' in db_timezone or db_timezone != 'Asia/Shanghai':
                print(f"   ⚠ 警告: 数据库时区不是 Asia/Shanghai，可能影响日期统计准确性")
            else:
                print(f"   ✓ 数据库时区正确")
        except Exception as e:
            print(f"   ⚠ 无法检查数据库时区: {e}")
        
        # 2. 检查订单时间范围
        print("\n2. 检查订单时间范围...")
        try:
            min_order = db.query(func.min(Order.order_time)).scalar()
            max_order = db.query(func.max(Order.order_time)).scalar()
            if min_order and max_order:
                print(f"   最早订单时间: {min_order}")
                print(f"   最新订单时间: {max_order}")
                
                # 检查时区
                if min_order.tzinfo is None:
                    print(f"   ⚠ 订单时间为 naive datetime（无时区信息）")
                    print(f"   假设这些时间表示北京时间（UTC+8）")
                else:
                    print(f"   订单时间时区: {min_order.tzinfo}")
        except Exception as e:
            print(f"   ✗ 检查订单时间失败: {e}")
        
        # 3. 验证统计规则
        print("\n3. 验证统计规则...")
        
        # 检查有效订单状态
        valid_statuses = UnifiedStatisticsService.get_valid_order_statuses()
        print(f"   有效订单状态: {[s.value for s in valid_statuses]}")
        
        # 统计各状态的订单数
        status_counts = {}
        for status in OrderStatus:
            count = db.query(func.count(Order.id)).filter(Order.status == status).scalar()
            status_counts[status.value] = count
            is_valid = status in valid_statuses
            marker = "✓" if is_valid else "✗"
            print(f"   {marker} {status.value}: {count} 单")
        
        # 4. 验证父订单去重逻辑
        print("\n4. 验证父订单去重逻辑...")
        try:
            # 统计总订单数（不去重）
            total_orders = db.query(func.count(Order.id)).scalar()
            
            # 统计父订单数（去重）
            parent_order_key = UnifiedStatisticsService.get_parent_order_key()
            parent_order_count = db.query(
                func.count(func.distinct(parent_order_key))
            ).scalar()
            
            print(f"   总订单记录数（不去重）: {total_orders}")
            print(f"   父订单数（去重后）: {parent_order_count}")
            print(f"   子订单数: {total_orders - parent_order_count}")
        except Exception as e:
            print(f"   ✗ 验证父订单去重失败: {e}")
        
        # 5. 验证日期统计（最近7天）
        print("\n5. 验证日期统计（最近7天）...")
        try:
            end_dt = datetime.now(BEIJING_TIMEZONE)
            start_dt = end_dt - timedelta(days=7)
            
            # 构建过滤条件
            filters = UnifiedStatisticsService.build_base_filters(
                db, start_dt, end_dt, None, None, None, None
            )
            
            # 计算统计
            stats = UnifiedStatisticsService.calculate_order_statistics(db, filters)
            
            print(f"   时间范围: {start_dt.date()} 至 {end_dt.date()}")
            print(f"   总订单数: {stats['order_count']}")
            print(f"   总销量: {stats['total_quantity']} 件")
            print(f"   总GMV: ¥{stats['total_gmv']:,.2f}")
            print(f"   总利润: ¥{stats['total_profit']:,.2f}")
            
            # 按天统计
            date_expr = func.date(Order.order_time)
            daily_stats = db.query(
                date_expr.label("date"),
                func.count(func.distinct(parent_order_key)).label("orders"),
                func.sum(Order.quantity).label("quantity"),
            ).filter(and_(*filters)).group_by(
                date_expr
            ).order_by(date_expr).all()
            
            print(f"\n   每日统计:")
            total_daily_orders = 0
            total_daily_quantity = 0
            for day_stat in daily_stats:
                print(f"     {day_stat.date}: {day_stat.orders} 单, {day_stat.quantity} 件")
                total_daily_orders += day_stat.orders or 0
                total_daily_quantity += day_stat.quantity or 0
            
            # 验证汇总是否一致
            print(f"\n   验证汇总一致性:")
            print(f"     按天汇总订单数: {total_daily_orders} (应与总订单数 {stats['order_count']} 一致)")
            print(f"     按天汇总销量: {total_daily_quantity} (应与总销量 {stats['total_quantity']} 一致)")
            
            if total_daily_orders == stats['order_count']:
                print(f"     ✓ 订单数汇总一致")
            else:
                print(f"     ✗ 订单数汇总不一致！差异: {abs(total_daily_orders - stats['order_count'])}")
            
            if total_daily_quantity == stats['total_quantity']:
                print(f"     ✓ 销量汇总一致")
            else:
                print(f"     ✗ 销量汇总不一致！差异: {abs(total_daily_quantity - stats['total_quantity'])}")
                
        except Exception as e:
            print(f"   ✗ 验证日期统计失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. 检查时间边界情况
        print("\n6. 检查时间边界情况...")
        try:
            # 检查跨日期的订单（北京时间 23:00-01:00）
            beijing_now = datetime.now(BEIJING_TIMEZONE)
            today_start = beijing_now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # 转换为 naive datetime（因为数据库存储的是 naive）
            today_start_naive = today_start.replace(tzinfo=None)
            today_end_naive = today_end.replace(tzinfo=None)
            
            today_orders = db.query(func.count(func.distinct(parent_order_key))).filter(
                and_(*UnifiedStatisticsService.build_base_filters(
                    db, today_start_naive, today_end_naive, None, None, None, None
                ))
            ).scalar()
            
            print(f"   今日订单数（北京时间）: {today_orders}")
            print(f"   今日开始时间: {today_start}")
            print(f"   今日结束时间: {today_end}")
            
        except Exception as e:
            print(f"   ✗ 检查时间边界失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("验证完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_statistics()



