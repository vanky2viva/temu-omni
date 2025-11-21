"""定时任务调度器"""
import asyncio
from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from app.core.database import SessionLocal
from app.core.config import settings
from app.services.order_cost_service import OrderCostCalculationService
from app.services.sync_service import SyncService
from app.services.payout_service import PayoutService
from app.services.report_service import ReportService
from app.models.shop import Shop


def update_order_costs_job():
    """定时任务：自动更新订单成本"""
    logger.info("开始执行定时任务：更新订单成本...")
    db = SessionLocal()
    try:
        service = OrderCostCalculationService(db)
        result = service.calculate_order_costs(force_recalculate=False)
        logger.info(
            f"订单成本更新完成 - "
            f"总计: {result['total']}, "
            f"成功: {result['success']}, "
            f"失败: {result['failed']}, "
            f"跳过: {result['skipped']}"
        )
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}")
    finally:
        db.close()


def sync_orders_job():
    """定时任务：同步订单数据（增量同步）"""
    logger.info("开始执行定时任务：同步订单数据...")
    db = SessionLocal()
    try:
        # 获取所有启用的店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            logger.info("没有启用的店铺，跳过订单同步")
            return
        
        total_new = 0
        total_updated = 0
        total_failed = 0
        
        for shop in shops:
            try:
                logger.info(f"开始同步店铺订单 - 店铺: {shop.shop_name} (ID: {shop.id})")
                sync_service = SyncService(db, shop)
                
                # 使用增量同步（从最后同步时间开始）
                # 注意：这里需要运行异步函数，使用 asyncio.run
                result = asyncio.run(sync_service.sync_orders(full_sync=False))
                
                total_new += result.get('new', 0)
                total_updated += result.get('updated', 0)
                total_failed += result.get('failed', 0)
                
                logger.info(
                    f"店铺订单同步完成 - 店铺: {shop.shop_name}, "
                    f"新增: {result.get('new', 0)}, 更新: {result.get('updated', 0)}, "
                    f"失败: {result.get('failed', 0)}"
                )
                
                # 关闭服务连接
                asyncio.run(sync_service.temu_service.close())
                
            except Exception as e:
                logger.error(f"店铺订单同步失败 - 店铺: {shop.shop_name}, 错误: {e}")
                total_failed += 1
                continue
        
        logger.info(
            f"订单同步任务完成 - "
            f"总新增: {total_new}, 总更新: {total_updated}, 总失败: {total_failed}"
        )
    except Exception as e:
        logger.error(f"订单同步任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


def sync_products_job():
    """定时任务：同步商品数据（增量同步）"""
    logger.info("开始执行定时任务：同步商品数据...")
    db = SessionLocal()
    try:
        # 获取所有启用的店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            logger.info("没有启用的店铺，跳过商品同步")
            return
        
        total_new = 0
        total_updated = 0
        total_failed = 0
        
        for shop in shops:
            try:
                logger.info(f"开始同步店铺商品 - 店铺: {shop.shop_name} (ID: {shop.id})")
                sync_service = SyncService(db, shop)
                
                # 使用增量同步（只同步新增和更新的商品）
                result = asyncio.run(sync_service.sync_products(full_sync=False))
                
                total_new += result.get('new', 0)
                total_updated += result.get('updated', 0)
                total_failed += result.get('failed', 0)
                
                logger.info(
                    f"店铺商品同步完成 - 店铺: {shop.shop_name}, "
                    f"新增: {result.get('new', 0)}, 更新: {result.get('updated', 0)}, "
                    f"失败: {result.get('failed', 0)}"
                )
                
                # 关闭服务连接
                asyncio.run(sync_service.temu_service.close())
                
            except Exception as e:
                logger.error(f"店铺商品同步失败 - 店铺: {shop.shop_name}, 错误: {e}")
                total_failed += 1
                continue
        
        logger.info(
            f"商品同步任务完成 - "
            f"总新增: {total_new}, 总更新: {total_updated}, 总失败: {total_failed}"
        )
    except Exception as e:
        logger.error(f"商品同步任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler:
    """创建并配置调度器"""
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    
    # 每30分钟执行一次订单成本更新（只更新没有成本的订单）
    scheduler.add_job(
        update_order_costs_job,
        trigger=IntervalTrigger(minutes=30),
        id='update_order_costs',
        name='更新订单成本',
        replace_existing=True,
        max_instances=1,  # 确保同一时间只有一个任务实例在运行
    )
    
    # 如果启用了自动同步，添加订单和商品同步任务
    if settings.AUTO_SYNC_ENABLED:
        sync_interval = settings.SYNC_INTERVAL_MINUTES
        
        # 订单同步任务（增量同步）
        scheduler.add_job(
            sync_orders_job,
            trigger=IntervalTrigger(minutes=sync_interval),
            id='sync_orders',
            name='同步订单数据（增量）',
            replace_existing=True,
            max_instances=1,
        )
        
        # 商品同步任务（增量同步）- 频率可以比订单低一些，每小时一次
        scheduler.add_job(
            sync_products_job,
            trigger=IntervalTrigger(minutes=60),  # 每小时同步一次商品
            id='sync_products',
            name='同步商品数据（增量）',
            replace_existing=True,
            max_instances=1,
        )
        
        logger.info(
            f"已启用自动同步 - 订单同步间隔: {sync_interval}分钟, "
            f"商品同步间隔: 60分钟"
        )
    else:
        logger.info("自动同步已禁用，如需启用请在配置中设置 AUTO_SYNC_ENABLED=True")
    
        # 每日00:05 - 生成回款计划（为昨日签收的订单创建回款计划）
        scheduler.add_job(
            create_payouts_job,
            trigger=CronTrigger(hour=0, minute=5, timezone='Asia/Shanghai'),
            id='create_payouts',
            name='生成回款计划',
            replace_existing=True,
            max_instances=1,
        )
        
        # 每日00:15 - 生成运营日报（生成前一日报表）
        scheduler.add_job(
            generate_daily_reports_job,
            trigger=CronTrigger(hour=0, minute=15, timezone='Asia/Shanghai'),
            id='generate_daily_reports',
            name='生成运营日报',
            replace_existing=True,
            max_instances=1,
        )
        
        # 每周一00:30 - 生成运营周报（生成上周报表）
        scheduler.add_job(
            generate_weekly_reports_job,
            trigger=CronTrigger(day_of_week='mon', hour=0, minute=30, timezone='Asia/Shanghai'),
            id='generate_weekly_reports',
            name='生成运营周报',
            replace_existing=True,
            max_instances=1,
        )
        
        # 每月1日01:00 - 生成运营月报（生成上月报表）
        scheduler.add_job(
            generate_monthly_reports_job,
            trigger=CronTrigger(day=1, hour=1, minute=0, timezone='Asia/Shanghai'),
            id='generate_monthly_reports',
            name='生成运营月报',
            replace_existing=True,
            max_instances=1,
        )
        
        # 每10分钟 - 更新未完成订单状态
        scheduler.add_job(
            update_order_status_job,
            trigger=IntervalTrigger(minutes=10),
            id='update_order_status',
            name='更新订单状态',
            replace_existing=True,
            max_instances=1,
        )
        
        logger.info("定时任务调度器已创建")
    return scheduler


def create_payouts_job():
    """定时任务：为昨日签收的订单创建回款计划"""
    logger.info("开始执行定时任务：生成回款计划...")
    db = SessionLocal()
    try:
        service = PayoutService(db)
        yesterday = date.today() - timedelta(days=1)
        
        # 为所有店铺昨日签收的订单创建回款计划
        result = service.create_payouts_for_delivered_orders(delivery_date=yesterday)
        
        logger.info(
            f"回款计划创建完成 - "
            f"总计: {result['total']}, "
            f"创建: {result['created']}, "
            f"跳过: {result['skipped']}"
        )
    except Exception as e:
        logger.error(f"回款计划创建任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


def generate_daily_reports_job():
    """定时任务：生成运营日报（前一日）"""
    logger.info("开始执行定时任务：生成运营日报...")
    db = SessionLocal()
    try:
        # 获取所有启用的店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            logger.info("没有启用的店铺，跳过报表生成")
            return
        
        report_service = ReportService(db)
        yesterday = date.today() - timedelta(days=1)
        
        total_generated = 0
        total_failed = 0
        
        for shop in shops:
            try:
                logger.info(f"为店铺 {shop.shop_name} 生成日报 - 日期: {yesterday}")
                
                # 生成指标
                metrics = report_service.generate_daily_metrics(shop.id, yesterday)
                
                # 保存报表快照
                report_service.save_daily_report(shop.id, yesterday, metrics)
                db.commit()
                
                total_generated += 1
                logger.info(
                    f"店铺 {shop.shop_name} 日报生成完成 - "
                    f"订单数: {metrics.get('total_orders', 0)}, "
                    f"GMV: {metrics.get('gmv', 0)}"
                )
            except Exception as e:
                logger.error(f"店铺 {shop.shop_name} 日报生成失败: {e}")
                db.rollback()
                total_failed += 1
                continue
        
        logger.info(
            f"运营日报生成完成 - "
            f"成功: {total_generated}, "
            f"失败: {total_failed}"
        )
    except Exception as e:
        logger.error(f"运营日报生成任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


def generate_weekly_reports_job():
    """定时任务：生成运营周报（上周）"""
    logger.info("开始执行定时任务：生成运营周报...")
    db = SessionLocal()
    try:
        # 获取所有启用的店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            logger.info("没有启用的店铺，跳过周报生成")
            return
        
        report_service = ReportService(db)
        
        # 计算上周的日期范围（周一到周日）
        today = date.today()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + timedelta(days=6)
        
        total_generated = 0
        total_failed = 0
        
        for shop in shops:
            try:
                logger.info(
                    f"为店铺 {shop.shop_name} 生成周报 - "
                    f"日期范围: {last_monday} 至 {last_sunday}"
                )
                
                # 生成指标
                metrics = report_service.generate_weekly_metrics(
                    shop.id, last_monday, last_sunday
                )
                
                # 保存报表快照
                report_service.save_weekly_report(shop.id, last_monday, metrics)
                db.commit()
                
                total_generated += 1
                logger.info(
                    f"店铺 {shop.shop_name} 周报生成完成 - "
                    f"订单数: {metrics.get('total_orders', 0)}, "
                    f"GMV: {metrics.get('gmv', 0)}"
                )
            except Exception as e:
                logger.error(f"店铺 {shop.shop_name} 周报生成失败: {e}")
                db.rollback()
                total_failed += 1
                continue
        
        logger.info(
            f"运营周报生成完成 - "
            f"成功: {total_generated}, "
            f"失败: {total_failed}"
        )
    except Exception as e:
        logger.error(f"运营周报生成任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


def generate_monthly_reports_job():
    """定时任务：生成运营月报（上月）"""
    logger.info("开始执行定时任务：生成运营月报...")
    db = SessionLocal()
    try:
        # 获取所有启用的店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            logger.info("没有启用的店铺，跳过月报生成")
            return
        
        report_service = ReportService(db)
        
        # 计算上月的日期范围
        today = date.today()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        
        total_generated = 0
        total_failed = 0
        
        for shop in shops:
            try:
                logger.info(
                    f"为店铺 {shop.shop_name} 生成月报 - "
                    f"日期范围: {first_day_last_month} 至 {last_day_last_month}"
                )
                
                # 生成指标
                metrics = report_service.generate_monthly_metrics(
                    shop.id, first_day_last_month, last_day_last_month
                )
                
                # 保存报表快照
                report_service.save_monthly_report(shop.id, first_day_last_month, metrics)
                db.commit()
                
                total_generated += 1
                logger.info(
                    f"店铺 {shop.shop_name} 月报生成完成 - "
                    f"订单数: {metrics.get('total_orders', 0)}, "
                    f"GMV: {metrics.get('gmv', 0)}"
                )
            except Exception as e:
                logger.error(f"店铺 {shop.shop_name} 月报生成失败: {e}")
                db.rollback()
                total_failed += 1
                continue
        
        logger.info(
            f"运营月报生成完成 - "
            f"成功: {total_generated}, "
            f"失败: {total_failed}"
        )
    except Exception as e:
        logger.error(f"运营月报生成任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


def update_order_status_job():
    """定时任务：更新未完成订单状态"""
    logger.info("开始执行定时任务：更新订单状态...")
    db = SessionLocal()
    try:
        # 获取所有启用的店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            logger.info("没有启用的店铺，跳过订单状态更新")
            return
        
        from app.models.order import Order, OrderStatus
        
        total_updated = 0
        total_failed = 0
        
        for shop in shops:
            try:
                logger.info(f"更新店铺 {shop.shop_name} 的订单状态")
                
                # 查询未完成的订单（待支付、处理中、已发货）
                incomplete_statuses = [
                    OrderStatus.PENDING,
                    OrderStatus.PAID,
                    OrderStatus.PROCESSING,
                    OrderStatus.SHIPPED
                ]
                
                incomplete_orders = db.query(Order).filter(
                    Order.shop_id == shop.id,
                    Order.status.in_(incomplete_statuses)
                ).limit(100).all()  # 每次最多处理100个订单，避免超时
                
                if not incomplete_orders:
                    logger.debug(f"店铺 {shop.shop_name} 没有未完成的订单")
                    continue
                
                # 使用同步服务更新订单状态
                sync_service = SyncService(db, shop)
                
                # 获取订单的最新状态（这里可以调用API获取最新状态）
                # 注意：由于Temu API的限制，这里暂时只记录日志
                # 实际的状态更新会在下次同步时自动完成
                logger.info(
                    f"店铺 {shop.shop_name} 有 {len(incomplete_orders)} 个未完成订单，"
                    f"将在下次同步时更新状态"
                )
                
                total_updated += len(incomplete_orders)
                
                # 关闭服务连接
                asyncio.run(sync_service.temu_service.close())
                
            except Exception as e:
                logger.error(f"店铺 {shop.shop_name} 订单状态更新失败: {e}")
                total_failed += 1
                continue
        
        logger.info(
            f"订单状态更新任务完成 - "
            f"检查订单数: {total_updated}, "
            f"失败: {total_failed}"
        )
    except Exception as e:
        logger.error(f"订单状态更新任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


# 全局调度器实例
scheduler = None


def start_scheduler():
    """启动调度器"""
    global scheduler
    if scheduler is None:
        scheduler = create_scheduler()
        scheduler.start()
        logger.info("定时任务调度器已启动")
    else:
        logger.warning("调度器已经在运行中")


def stop_scheduler():
    """停止调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        scheduler = None
        logger.info("定时任务调度器已停止")
    else:
        logger.warning("调度器未运行")

