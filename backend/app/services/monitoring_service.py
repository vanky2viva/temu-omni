"""监控和告警服务"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger

from app.models.shop import Shop
from app.models.order_detail_task import OrderDetailTask, TaskStatus
from app.services.order_detail_enrichment_service import OrderDetailEnrichmentService
from app.services.order_detail_worker import get_worker


class MonitoringService:
    """监控和告警服务"""
    
    # 告警阈值配置
    QUEUE_BACKLOG_THRESHOLD = 1000  # 队列积压超过1000个任务
    TASK_FAILURE_RATE_THRESHOLD = 0.1  # 任务失败率超过10%
    SYNC_DURATION_THRESHOLD = 3600  # 同步任务执行时间超过1小时（秒）
    API_FAILURE_RATE_THRESHOLD = 0.05  # API调用失败率超过5%
    
    def __init__(self, db: Session):
        """
        初始化监控服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def check_queue_backlog(self) -> Optional[Dict[str, Any]]:
        """
        检查任务队列积压
        
        Returns:
            如果超过阈值，返回告警信息；否则返回None
        """
        try:
            service = OrderDetailEnrichmentService(self.db)
            queue_length = service.get_queue_length()
            
            if queue_length > self.QUEUE_BACKLOG_THRESHOLD:
                return {
                    "type": "queue_backlog",
                    "severity": "warning",
                    "message": f"任务队列积压严重: {queue_length} 个任务待处理",
                    "queue_length": queue_length,
                    "threshold": self.QUEUE_BACKLOG_THRESHOLD,
                    "timestamp": datetime.now().isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"检查队列积压失败: {e}")
            return None
    
    def check_task_failure_rate(self, hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        检查任务失败率
        
        Args:
            hours: 检查最近N小时的任务
            
        Returns:
            如果超过阈值，返回告警信息；否则返回None
        """
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 查询最近的任务
            recent_tasks = self.db.query(OrderDetailTask).filter(
                OrderDetailTask.created_at >= since_time
            ).all()
            
            if not recent_tasks:
                return None
            
            total = len(recent_tasks)
            failed = len([t for t in recent_tasks if t.status == TaskStatus.FAILED])
            failure_rate = failed / total if total > 0 else 0
            
            if failure_rate > self.TASK_FAILURE_RATE_THRESHOLD:
                return {
                    "type": "task_failure_rate",
                    "severity": "error",
                    "message": f"任务失败率过高: {failure_rate:.1%} ({failed}/{total})",
                    "failure_rate": failure_rate,
                    "failed_count": failed,
                    "total_count": total,
                    "threshold": self.TASK_FAILURE_RATE_THRESHOLD,
                    "hours": hours,
                    "timestamp": datetime.now().isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"检查任务失败率失败: {e}")
            return None
    
    def check_sync_status(self) -> List[Dict[str, Any]]:
        """
        检查同步状态
        
        Returns:
            告警列表
        """
        alerts = []
        
        try:
            # 检查所有店铺的同步状态
            shops = self.db.query(Shop).filter(Shop.is_active == True).all()
            
            for shop in shops:
                # 检查订单同步状态
                if shop.sync_status == "error":
                    alerts.append({
                        "type": "sync_error",
                        "severity": "error",
                        "message": f"店铺 {shop.shop_name} 订单同步失败",
                        "shop_id": shop.id,
                        "shop_name": shop.shop_name,
                        "sync_type": "orders",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 检查商品同步状态
                if shop.product_sync_status == "error":
                    alerts.append({
                        "type": "sync_error",
                        "severity": "error",
                        "message": f"店铺 {shop.shop_name} 商品同步失败",
                        "shop_id": shop.id,
                        "shop_name": shop.shop_name,
                        "sync_type": "products",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 检查同步时间（如果超过24小时未同步，发出警告）
                if shop.last_sync_at:
                    hours_since_sync = (datetime.utcnow() - shop.last_sync_at).total_seconds() / 3600
                    if hours_since_sync > 24:
                        alerts.append({
                            "type": "sync_stale",
                            "severity": "warning",
                            "message": f"店铺 {shop.shop_name} 订单超过24小时未同步",
                            "shop_id": shop.id,
                            "shop_name": shop.shop_name,
                            "hours_since_sync": hours_since_sync,
                            "last_sync_at": shop.last_sync_at.isoformat() if shop.last_sync_at else None,
                            "timestamp": datetime.now().isoformat()
                        })
                
                if shop.last_product_sync_at:
                    hours_since_sync = (datetime.utcnow() - shop.last_product_sync_at).total_seconds() / 3600
                    if hours_since_sync > 24:
                        alerts.append({
                            "type": "sync_stale",
                            "severity": "warning",
                            "message": f"店铺 {shop.shop_name} 商品超过24小时未同步",
                            "shop_id": shop.id,
                            "shop_name": shop.shop_name,
                            "hours_since_sync": hours_since_sync,
                            "last_sync_at": shop.last_product_sync_at.isoformat() if shop.last_product_sync_at else None,
                            "timestamp": datetime.now().isoformat()
                        })
            
            return alerts
        except Exception as e:
            logger.error(f"检查同步状态失败: {e}")
            return []
    
    def check_worker_status(self) -> Optional[Dict[str, Any]]:
        """
        检查工作线程状态
        
        Returns:
            如果工作线程未运行，返回告警信息；否则返回None
        """
        try:
            worker = get_worker()
            if not worker or not worker.is_running():
                return {
                    "type": "worker_down",
                    "severity": "error",
                    "message": "订单详情补齐工作线程未运行",
                    "timestamp": datetime.now().isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"检查工作线程状态失败: {e}")
            return {
                "type": "worker_check_failed",
                "severity": "warning",
                "message": f"检查工作线程状态失败: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_all_alerts(self) -> Dict[str, Any]:
        """
        获取所有告警
        
        Returns:
            告警汇总
        """
        alerts = []
        
        # 检查队列积压
        queue_alert = self.check_queue_backlog()
        if queue_alert:
            alerts.append(queue_alert)
        
        # 检查任务失败率
        failure_alert = self.check_task_failure_rate()
        if failure_alert:
            alerts.append(failure_alert)
        
        # 检查同步状态
        sync_alerts = self.check_sync_status()
        alerts.extend(sync_alerts)
        
        # 检查工作线程状态
        worker_alert = self.check_worker_status()
        if worker_alert:
            alerts.append(worker_alert)
        
        # 按严重程度分类
        error_alerts = [a for a in alerts if a.get("severity") == "error"]
        warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
        
        return {
            "total": len(alerts),
            "errors": len(error_alerts),
            "warnings": len(warning_alerts),
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        
        Returns:
            健康状态汇总
        """
        try:
            service = OrderDetailEnrichmentService(self.db)
            task_stats = service.get_task_stats()
            
            # 检查工作线程
            worker = get_worker()
            worker_running = worker is not None and worker.is_running()
            
            # 检查店铺同步状态
            shops = self.db.query(Shop).filter(Shop.is_active == True).all()
            shops_with_errors = len([
                s for s in shops 
                if s.sync_status == "error" or s.product_sync_status == "error"
            ])
            
            # 计算健康分数（0-100）
            health_score = 100
            if not worker_running:
                health_score -= 30
            if task_stats.get("queue_length", 0) > self.QUEUE_BACKLOG_THRESHOLD:
                health_score -= 20
            if shops_with_errors > 0:
                health_score -= 20
            if task_stats.get("failed", 0) > 0:
                health_score -= 10
            
            health_score = max(0, health_score)
            
            return {
                "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy",
                "health_score": health_score,
                "worker_running": worker_running,
                "task_stats": task_stats,
                "shops_total": len(shops),
                "shops_with_errors": shops_with_errors,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取健康状态失败: {e}")
            return {
                "status": "unknown",
                "health_score": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
