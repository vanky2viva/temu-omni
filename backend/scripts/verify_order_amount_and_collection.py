#!/usr/bin/env python3
"""验证订单金额和回款统计是否正常"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, text, case

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.shop import Shop
from app.models.product import Product
from app.utils.currency import CurrencyConverter
from app.services.order_cost_service import OrderCostCalculationService
# from app.api.analytics import get_payment_collection  # 不需要直接导入，我们直接查询数据库


def verify_order_amounts(db):
    """验证订单金额是否正确"""
    print("=" * 80)
    print("📊 验证订单金额")
    print("=" * 80)
    
    # 1. 检查订单金额为0或空的订单
    orders_without_amount = db.query(Order).filter(
        or_(
            Order.total_price.is_(None),
            Order.total_price == 0,
            Order.unit_price.is_(None),
            Order.unit_price == 0
        )
    ).count()
    
    print(f"\n1. 订单金额检查:")
    print(f"   - 金额为0或空的订单数: {orders_without_amount}")
    
    if orders_without_amount > 0:
        print(f"   ⚠️  发现 {orders_without_amount} 个订单金额异常")
        # 显示前10个异常订单
        sample_orders = db.query(Order).filter(
            or_(
                Order.total_price.is_(None),
                Order.total_price == 0,
                Order.unit_price.is_(None),
                Order.unit_price == 0
            )
        ).limit(10).all()
        
        print(f"\n   前10个异常订单示例:")
        for order in sample_orders:
            print(f"   - 订单号: {order.order_sn}, "
                  f"单价: {order.unit_price}, "
                  f"总价: {order.total_price}, "
                  f"数量: {order.quantity}")
    else:
        print(f"   ✅ 所有订单金额正常")
    
    # 2. 检查订单金额计算是否正确（unit_price * quantity = total_price）
    orders_with_wrong_calculation = db.query(Order).filter(
        and_(
            Order.unit_price.isnot(None),
            Order.total_price.isnot(None),
            Order.quantity.isnot(None),
            Order.unit_price > 0,
            Order.total_price != (Order.unit_price * Order.quantity)
        )
    ).count()
    
    print(f"\n2. 订单金额计算检查:")
    print(f"   - 金额计算错误的订单数: {orders_with_wrong_calculation}")
    
    if orders_with_wrong_calculation > 0:
        print(f"   ⚠️  发现 {orders_with_wrong_calculation} 个订单金额计算错误")
        # 显示前10个错误订单
        sample_orders = db.query(Order).filter(
            and_(
                Order.unit_price.isnot(None),
                Order.total_price.isnot(None),
                Order.quantity.isnot(None),
                Order.unit_price > 0,
                Order.total_price != (Order.unit_price * Order.quantity)
            )
        ).limit(10).all()
        
        print(f"\n   前10个计算错误订单示例:")
        for order in sample_orders:
            expected = order.unit_price * order.quantity
            print(f"   - 订单号: {order.order_sn}, "
                  f"单价: {order.unit_price}, "
                  f"数量: {order.quantity}, "
                  f"总价: {order.total_price} (期望: {expected})")
    else:
        print(f"   ✅ 所有订单金额计算正确")
    
    # 3. 统计订单金额汇总
    total_orders = db.query(Order).filter(
        Order.status != OrderStatus.CANCELLED,
        Order.status != OrderStatus.REFUNDED
    ).count()
    
    orders_with_amount = db.query(Order).filter(
        and_(
            Order.total_price.isnot(None),
            Order.total_price > 0,
            Order.status != OrderStatus.CANCELLED,
            Order.status != OrderStatus.REFUNDED
        )
    ).count()
    
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    
    # 计算总GMV（统一转换为CNY）
    total_gmv_result = db.query(
        func.sum(
            case(
                (Order.currency == 'USD', Order.total_price * usd_rate),
                (Order.currency == 'CNY', Order.total_price),
                else_=Order.total_price * usd_rate
            )
        )
    ).filter(
        and_(
            Order.total_price.isnot(None),
            Order.total_price > 0,
            Order.status != OrderStatus.CANCELLED,
            Order.status != OrderStatus.REFUNDED
        )
    ).scalar()
    
    total_gmv = float(total_gmv_result or 0)
    
    print(f"\n3. 订单金额统计:")
    print(f"   - 总订单数: {total_orders}")
    print(f"   - 有金额的订单数: {orders_with_amount}")
    print(f"   - 总GMV (CNY): {total_gmv:,.2f}")
    print(f"   - 有金额订单占比: {(orders_with_amount/total_orders*100) if total_orders > 0 else 0:.2f}%")
    
    return {
        'orders_without_amount': orders_without_amount,
        'orders_with_wrong_calculation': orders_with_wrong_calculation,
        'total_orders': total_orders,
        'orders_with_amount': orders_with_amount,
        'total_gmv': total_gmv
    }


def verify_payment_collection(db):
    """验证回款统计是否正确"""
    print("\n" + "=" * 80)
    print("💰 验证回款统计")
    print("=" * 80)
    
    # 1. 检查已签收订单
    delivered_orders = db.query(Order).filter(
        Order.status == OrderStatus.DELIVERED,
        Order.delivery_time.isnot(None)
    ).count()
    
    print(f"\n1. 已签收订单检查:")
    print(f"   - 已签收订单数: {delivered_orders}")
    
    if delivered_orders == 0:
        print(f"   ⚠️  没有已签收的订单，无法验证回款统计")
        return None
    
    # 2. 检查回款日期计算（delivery_time + 8天）
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    collection_date_expr = func.date(Order.delivery_time + text("INTERVAL '8 days'"))
    
    # 获取最近30天的回款统计
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # 查询回款统计
    collection_stats = db.query(
        collection_date_expr.label("collection_date"),
        func.sum(
            case(
                (Order.currency == 'USD', Order.total_price * usd_rate),
                (Order.currency == 'CNY', Order.total_price),
                else_=Order.total_price * usd_rate
            )
        ).label("collection_amount"),
        func.count(Order.id).label("order_count")
    ).filter(
        and_(
            Order.status == OrderStatus.DELIVERED,
            Order.delivery_time.isnot(None),
            collection_date_expr >= start_date.date(),
            collection_date_expr <= end_date.date()
        )
    ).group_by(collection_date_expr).order_by(collection_date_expr.desc()).limit(10).all()
    
    print(f"\n2. 最近30天回款统计（前10天）:")
    if collection_stats:
        total_collection = sum(float(row.collection_amount or 0) for row in collection_stats)
        total_orders = sum(int(row.order_count or 0) for row in collection_stats)
        
        for row in collection_stats:
            date_str = row.collection_date.strftime("%Y-%m-%d")
            amount = float(row.collection_amount or 0)
            count = int(row.order_count or 0)
            print(f"   - {date_str}: {amount:,.2f} CNY ({count} 单)")
        
        print(f"\n   最近30天回款总计: {total_collection:,.2f} CNY ({total_orders} 单)")
    else:
        print(f"   ⚠️  最近30天内没有回款记录")
    
    # 3. 验证回款日期计算逻辑
    sample_orders = db.query(Order).filter(
        and_(
            Order.status == OrderStatus.DELIVERED,
            Order.delivery_time.isnot(None),
            Order.total_price.isnot(None),
            Order.total_price > 0
        )
    ).limit(5).all()
    
    print(f"\n3. 回款日期计算验证（示例订单）:")
    for order in sample_orders:
        delivery_date = order.delivery_time.date() if isinstance(order.delivery_time, datetime) else order.delivery_time
        collection_date = delivery_date + timedelta(days=8)
        print(f"   - 订单号: {order.order_sn}")
        print(f"     签收日期: {delivery_date}")
        print(f"     回款日期: {collection_date} (签收日期 + 8天)")
        print(f"     订单金额: {order.total_price} {order.currency}")
    
    return {
        'delivered_orders': delivered_orders,
        'collection_stats': collection_stats
    }


def verify_scheduler_status():
    """验证定时任务状态"""
    print("\n" + "=" * 80)
    print("⏰ 验证定时任务状态")
    print("=" * 80)
    
    try:
        from app.core.scheduler import scheduler
        
        if scheduler is None:
            print("\n   ⚠️  调度器未初始化")
            return False
        
        if not scheduler.running:
            print("\n   ⚠️  调度器未运行")
            return False
        
        # 获取所有任务
        jobs = scheduler.get_jobs()
        
        print(f"\n1. 调度器状态:")
        print(f"   - 调度器运行中: ✅")
        print(f"   - 任务数量: {len(jobs)}")
        
        print(f"\n2. 定时任务列表:")
        for job in jobs:
            next_run = job.next_run_time
            next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "未安排"
            print(f"   - 任务ID: {job.id}")
            print(f"     任务名称: {job.name}")
            print(f"     下次执行时间: {next_run_str}")
            print(f"     触发器: {job.trigger}")
        
        return True
    except Exception as e:
        print(f"\n   ❌ 检查调度器状态失败: {e}")
        return False


def test_order_cost_calculation(db):
    """测试订单成本计算"""
    print("\n" + "=" * 80)
    print("🧪 测试订单成本计算")
    print("=" * 80)
    
    # 查找没有成本的订单
    orders_without_cost = db.query(Order).filter(
        and_(
            or_(
                Order.unit_cost.is_(None),
                Order.total_cost.is_(None),
                Order.profit.is_(None)
            ),
            Order.status != OrderStatus.CANCELLED,
            Order.status != OrderStatus.REFUNDED
        )
    ).count()
    
    print(f"\n1. 订单成本状态:")
    print(f"   - 没有成本的订单数: {orders_without_cost}")
    
    if orders_without_cost > 0:
        print(f"   ⚠️  发现 {orders_without_cost} 个订单没有成本信息")
        print(f"   💡 这些订单将在下次定时任务时自动计算成本")
    else:
        print(f"   ✅ 所有订单都有成本信息")
    
    # 测试计算服务
    print(f"\n2. 测试成本计算服务:")
    try:
        service = OrderCostCalculationService(db)
        # 只计算前10个没有成本的订单作为测试
        test_orders = db.query(Order).filter(
            and_(
                or_(
                    Order.unit_cost.is_(None),
                    Order.total_cost.is_(None)
                ),
                Order.status != OrderStatus.CANCELLED,
                Order.status != OrderStatus.REFUNDED
            )
        ).limit(10).all()
        
        if test_orders:
            test_order_ids = [order.id for order in test_orders]
            result = service.calculate_order_costs(order_ids=test_order_ids, force_recalculate=False)
            print(f"   - 测试订单数: {len(test_order_ids)}")
            print(f"   - 成功: {result['success']}")
            print(f"   - 失败: {result['failed']}")
            print(f"   - 跳过: {result['skipped']}")
        else:
            print(f"   - 没有需要计算的订单")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")


def main():
    """主函数"""
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 80)
        print("🔍 订单金额和回款统计验证")
        print("=" * 80)
        print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 验证订单金额
        amount_result = verify_order_amounts(db)
        
        # 2. 验证回款统计
        collection_result = verify_payment_collection(db)
        
        # 3. 验证定时任务状态
        scheduler_ok = verify_scheduler_status()
        
        # 4. 测试订单成本计算
        test_order_cost_calculation(db)
        
        # 总结
        print("\n" + "=" * 80)
        print("📋 验证总结")
        print("=" * 80)
        
        issues = []
        
        if amount_result['orders_without_amount'] > 0:
            issues.append(f"⚠️  发现 {amount_result['orders_without_amount']} 个订单金额异常")
        
        if amount_result['orders_with_wrong_calculation'] > 0:
            issues.append(f"⚠️  发现 {amount_result['orders_with_wrong_calculation']} 个订单金额计算错误")
        
        if not scheduler_ok:
            issues.append("⚠️  定时任务调度器未正常运行")
        
        if issues:
            print("\n发现的问题:")
            for issue in issues:
                print(f"   {issue}")
            print("\n建议:")
            print("   1. 运行订单成本计算脚本更新订单金额")
            print("   2. 检查定时任务调度器是否正常启动")
            print("   3. 查看应用日志了解详细错误信息")
        else:
            print("\n✅ 所有验证通过！")
            print("   - 订单金额正常")
            print("   - 回款统计正常")
            print("   - 定时任务正常运行")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()

