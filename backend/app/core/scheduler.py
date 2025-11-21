"""定时任务调度器"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from app.core.database import SessionLocal
from app.services.order_cost_service import OrderCostCalculationService


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

