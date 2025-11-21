"""定时任务调度器"""
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from app.core.database import SessionLocal
from app.core.config import settings
from app.services.order_cost_service import OrderCostCalculationService
from app.services.sync_service import SyncService
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
    
    logger.info("定时任务调度器已创建")
    return scheduler


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

