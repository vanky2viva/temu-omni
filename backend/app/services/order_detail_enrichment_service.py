"""订单详情补齐服务 - 异步获取包裹号"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger

from app.models.order_detail_task import OrderDetailTask, TaskStatus
from app.models.order import Order, OrderStatus
from app.models.shop import Shop
from app.services.temu_service import get_temu_service
from app.core.redis_client import RedisClient

# 为了兼容，将RedisClient作为实例使用
def _get_redis():
    """获取Redis客户端"""
    return RedisClient.get_client()


class OrderDetailEnrichmentService:
    """订单详情补齐服务"""
    
    # Redis键前缀
    QUEUE_KEY = "order_detail_tasks:queue"
    TASK_STATUS_KEY_PREFIX = "order_detail_tasks:status:"
    TASK_LOCK_KEY_PREFIX = "order_detail_tasks:lock:"
    
    # 任务锁TTL（秒）
    LOCK_TTL = 300  # 5分钟
    
    # 任务状态TTL（秒）
    STATUS_TTL = 86400  # 24小时
    
    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self._redis = None  # 延迟初始化
    
    @property
    def redis(self):
        """获取Redis客户端（延迟初始化）"""
        if self._redis is None:
            self._redis = _get_redis()
        return self._redis
    
    def create_tasks_for_shipped_orders(
        self, 
        shop_id: int, 
        force: bool = False
    ) -> int:
        """
        为已发货/已签收的订单创建补齐任务（排除已取消和待发货订单）
        
        Args:
            shop_id: 店铺ID
            force: 是否强制重新获取（即使已有包裹号）
            
        Returns:
            创建的任务数量
        """
        try:
            # 查询需要补齐包裹号的订单（仅查询已发货和已签收的订单，排除已取消和待发货）
            query = self.db.query(Order).filter(
                Order.shop_id == shop_id,
                Order.status.in_([OrderStatus.SHIPPED, OrderStatus.DELIVERED]),
                Order.parent_order_sn.isnot(None)
            )
            
            if not force:
                # 只处理没有包裹号的订单
                query = query.filter(
                    (Order.package_sn.is_(None)) | (Order.package_sn == '')
                )
            
            orders = query.all()
            
            if not orders:
                logger.info(f"店铺 {shop_id} 没有需要补齐包裹号的订单")
                return 0
            
            # 按父订单号分组
            parent_order_groups: Dict[str, List[Order]] = {}
            for order in orders:
                parent_sn = order.parent_order_sn
                if parent_sn not in parent_order_groups:
                    parent_order_groups[parent_sn] = []
                parent_order_groups[parent_sn].append(order)
            
            created_count = 0
            
            for parent_order_sn, child_orders in parent_order_groups.items():
                # 检查是否已有待处理或处理中的任务
                existing_task = self.db.query(OrderDetailTask).filter(
                    OrderDetailTask.shop_id == shop_id,
                    OrderDetailTask.parent_order_sn == parent_order_sn,
                    OrderDetailTask.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING])
                ).first()
                
                if existing_task:
                    logger.debug(f"父订单 {parent_order_sn} 已有待处理任务，跳过")
                    continue
                
                # 检查是否已有完成的任务（且包裹号已获取）
                completed_task = self.db.query(OrderDetailTask).filter(
                    OrderDetailTask.shop_id == shop_id,
                    OrderDetailTask.parent_order_sn == parent_order_sn,
                    OrderDetailTask.status == TaskStatus.COMPLETED,
                    OrderDetailTask.package_sn.isnot(None)
                ).first()
                
                if completed_task and not force:
                    logger.debug(f"父订单 {parent_order_sn} 已有完成的任务，跳过")
                    continue
                
                # 创建任务
                order_ids = [order.id for order in child_orders]
                task = OrderDetailTask(
                    shop_id=shop_id,
                    parent_order_sn=parent_order_sn,
                    order_ids=order_ids,
                    status=TaskStatus.PENDING,
                    max_retries=5
                )
                
                self.db.add(task)
                self.db.flush()  # 获取task.id
                
                # 将任务加入Redis队列
                task_data = {
                    "task_id": task.id,
                    "shop_id": shop_id,
                    "parent_order_sn": parent_order_sn,
                    "order_ids": order_ids
                }
                
                try:
                    if self.redis:
                        RedisClient.lpush(self.QUEUE_KEY, json.dumps(task_data, ensure_ascii=False))
                    # 设置任务状态
                    self._set_task_status(task.id, {
                        "status": "pending",
                        "created_at": datetime.utcnow().isoformat()
                    })
                    created_count += 1
                    logger.info(f"✅ 创建补齐任务: 父订单 {parent_order_sn}, 子订单数: {len(order_ids)}")
                except Exception as e:
                    logger.error(f"将任务加入队列失败: {e}")
                    self.db.rollback()
                    continue
            
            self.db.commit()
            logger.info(f"店铺 {shop_id} 共创建 {created_count} 个补齐任务")
            return created_count
            
        except Exception as e:
            logger.error(f"创建补齐任务失败: {e}")
            self.db.rollback()
            raise
    
    async def process_tasks_batch(self, batch_size: int = 50, max_concurrent: int = 5) -> Dict[str, int]:
        """
        批量处理任务（从Redis队列获取）
        
        Args:
            batch_size: 每批处理的父订单数量
            max_concurrent: 最大并发数（同时进行的API调用数，默认5）
            
        Returns:
            处理统计
        """
        stats = {
            "processed": 0,
            "completed": 0,
            "failed": 0,
            "retried": 0
        }
        
        try:
            # 从队列获取任务（批量）
            tasks_data = []
            if not self.redis:
                logger.warning("Redis不可用，无法处理任务队列")
                return stats
            
            for _ in range(batch_size):
                task_json = RedisClient.rpop(self.QUEUE_KEY) if self.redis else None
                if not task_json:
                    break
                try:
                    task_data = json.loads(task_json)
                    tasks_data.append(task_data)
                except json.JSONDecodeError as e:
                    logger.error(f"解析任务数据失败: {e}, 数据: {task_json}")
                    continue
            
            if not tasks_data:
                return stats
            
            logger.info(f"从队列获取到 {len(tasks_data)} 个任务，开始处理（最大并发: {max_concurrent}）...")
            
            # 使用信号量控制并发数，避免瞬间消耗所有API限流令牌
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(task_data):
                """带信号量控制的任务处理"""
                async with semaphore:
                    return await self._process_single_task(task_data)
            
            # 并发处理任务（受信号量控制）
            results = await asyncio.gather(
                *[process_with_semaphore(task_data) for task_data in tasks_data],
                return_exceptions=True
            )
            
            # 统计结果
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"处理任务异常: {result}")
                    stats["failed"] += 1
                    continue
                
                if result:
                    if result.get("status") == "completed":
                        stats["completed"] += 1
                    elif result.get("status") == "failed":
                        stats["failed"] += 1
                    elif result.get("status") == "retried":
                        stats["retried"] += 1
                    stats["processed"] += 1
            
            logger.info(
                f"批量处理完成 - 处理: {stats['processed']}, "
                f"完成: {stats['completed']}, 失败: {stats['failed']}, 重试: {stats['retried']}"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"批量处理任务失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return stats
    
    async def _process_single_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        处理单个任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            处理结果
        """
        task_id = task_data.get("task_id")
        shop_id = task_data.get("shop_id")
        parent_order_sn = task_data.get("parent_order_sn")
        order_ids = task_data.get("order_ids", [])
        
        if not all([task_id, shop_id, parent_order_sn]):
            logger.error(f"任务数据不完整: {task_data}")
            return None
        
        # 获取任务对象
        task = self.db.query(OrderDetailTask).filter(OrderDetailTask.id == task_id).first()
        if not task:
            logger.error(f"任务不存在: task_id={task_id}")
            return None
        
        # 检查任务锁（防止重复处理）
        if not self.redis:
            logger.warning("Redis不可用，跳过任务处理")
            return None
        
        lock_key = f"{self.TASK_LOCK_KEY_PREFIX}{parent_order_sn}"
        if self.redis and RedisClient.exists(lock_key):
            logger.debug(f"父订单 {parent_order_sn} 正在处理中，跳过")
            # 将任务重新放回队列
            RedisClient.lpush(self.QUEUE_KEY, json.dumps(task_data, ensure_ascii=False))
            return None
        
        try:
            # 设置任务锁
            if self.redis:
                RedisClient.setex(lock_key, self.LOCK_TTL, str(task_id))
            
            # 更新任务状态为处理中
            task.status = TaskStatus.PROCESSING
            self.db.commit()
            
            # 获取店铺信息
            shop = self.db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                raise ValueError(f"店铺不存在: shop_id={shop_id}")
            
            # 调用详情接口获取包裹号
            temu_service = get_temu_service(shop)
            try:
                order_detail = await temu_service.get_order_detail(parent_order_sn)
                
                # 从详情中提取包裹号
                package_sn = None
                order_list = order_detail.get('orderList', [])
                if order_list:
                    first_order = order_list[0]
                    package_sn_info = first_order.get('packageSnInfo')
                    if package_sn_info:
                        if isinstance(package_sn_info, list) and len(package_sn_info) > 0:
                            package_sn = package_sn_info[0].get('packageSn') if isinstance(package_sn_info[0], dict) else None
                        elif isinstance(package_sn_info, dict):
                            package_sn = package_sn_info.get('packageSn')
                
                if package_sn:
                    # 更新订单的包裹号
                    orders = self.db.query(Order).filter(Order.id.in_(order_ids)).all()
                    for order in orders:
                        order.package_sn = package_sn
                    
                    # 标记任务为完成
                    task.mark_completed(package_sn)
                    self.db.commit()
                    
                    # 更新任务状态
                    self._set_task_status(task_id, {
                        "status": "completed",
                        "package_sn": package_sn,
                        "completed_at": datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"✅ 任务完成: 父订单 {parent_order_sn}, 包裹号: {package_sn}")
                    return {"status": "completed", "package_sn": package_sn}
                else:
                    # 成功获取了订单详情，但详情中没有包裹号
                    # 这种情况直接标记为完成（不重试，不计入失败）
                    # 可能原因：订单确实没有包裹号（如已取消但未发货的订单）
                    task.mark_completed(None)  # package_sn 为 None
                    task.error_message = "订单详情中未包含包裹号信息（订单可能未发货或已取消）"
                    self.db.commit()
                    
                    # 更新任务状态
                    self._set_task_status(task_id, {
                        "status": "completed",
                        "package_sn": None,
                        "note": "订单详情中未包含包裹号信息",
                        "completed_at": datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"✅ 任务完成（无包裹号）: 父订单 {parent_order_sn}, 详情已获取但无包裹号")
                    return {"status": "completed", "package_sn": None, "note": "订单详情中未包含包裹号信息"}
                
            finally:
                await temu_service.close()
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"处理任务失败: 父订单 {parent_order_sn}, 错误: {error_msg}")
            
            if task.can_retry():
                task.increment_retry()
                task.status = TaskStatus.PENDING
                task.error_message = error_msg
                self.db.commit()
                # 重新加入队列（延迟重试）
                if self.redis:
                    self.redis.lpush(self.QUEUE_KEY, json.dumps(task_data, ensure_ascii=False))
                logger.warning(f"⚠️ 任务重试: 父订单 {parent_order_sn}, 重试次数: {task.retry_count}")
                return {"status": "retried", "retry_count": task.retry_count}
            else:
                task.mark_failed(error_msg)
                self.db.commit()
                logger.error(f"❌ 任务失败（超过最大重试次数）: 父订单 {parent_order_sn}")
                return {"status": "failed", "error": error_msg}
        
        finally:
            # 释放任务锁
            try:
                if self.redis:
                    RedisClient.delete(lock_key)
            except Exception:
                pass
    
    def _set_task_status(self, task_id: int, status_data: Dict[str, Any]):
        """设置任务状态到Redis"""
        try:
            if not self.redis:
                return
            key = f"{self.TASK_STATUS_KEY_PREFIX}{task_id}"
            RedisClient.setex(
                key,
                self.STATUS_TTL,
                json.dumps(status_data, ensure_ascii=False, default=str)
            )
        except Exception as e:
            logger.error(f"设置任务状态失败: {e}")
    
    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """从Redis获取任务状态"""
        try:
            if not self.redis:
                return None
            key = f"{self.TASK_STATUS_KEY_PREFIX}{task_id}"
            data = RedisClient.get(key)
            if data:
                return json.loads(data) if isinstance(data, str) else data
            return None
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return None
    
    def get_queue_length(self) -> int:
        """获取队列长度"""
        try:
            if not self.redis:
                return 0
            return RedisClient.llen(self.QUEUE_KEY)
        except Exception:
            return 0
    
    def get_task_stats(self, shop_id: Optional[int] = None) -> Dict[str, int]:
        """获取任务统计"""
        try:
            query = self.db.query(OrderDetailTask)
            if shop_id:
                query = query.filter(OrderDetailTask.shop_id == shop_id)
            
            total = query.count()
            pending = query.filter(OrderDetailTask.status == TaskStatus.PENDING).count()
            processing = query.filter(OrderDetailTask.status == TaskStatus.PROCESSING).count()
            completed = query.filter(OrderDetailTask.status == TaskStatus.COMPLETED).count()
            failed = query.filter(OrderDetailTask.status == TaskStatus.FAILED).count()
            
            return {
                "total": total,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "queue_length": self.get_queue_length()
            }
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {
                "total": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "queue_length": 0
            }
