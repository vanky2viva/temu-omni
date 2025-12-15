"""订单详情补齐工作线程"""
import asyncio
import threading
import time
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger
from app.core.database import SessionLocal
from app.services.order_detail_enrichment_service import OrderDetailEnrichmentService


class OrderDetailWorker:
    """订单详情补齐工作线程"""
    
    def __init__(self, batch_size: int = 15, poll_interval: int = 5, max_concurrent: int = 5):
        """
        初始化工作线程
        
        Args:
            batch_size: 每批处理的父订单数量（默认15，避免API限流）
            poll_interval: 轮询间隔（秒）
            max_concurrent: 最大并发数（同时进行的API调用数，默认5）
        """
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_concurrent = max_concurrent
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
    
    def start(self):
        """启动工作线程"""
        if self.running:
            logger.warning("工作线程已在运行中")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"订单详情补齐工作线程已启动 (批量大小: {self.batch_size}, 最大并发: {self.max_concurrent}, 轮询间隔: {self.poll_interval}秒)")
    
    def stop(self):
        """停止工作线程"""
        if not self.running:
            return
        
        logger.info("正在停止订单详情补齐工作线程...")
        self.running = False
        
        if self.loop and self.loop.is_running():
            # 停止事件循环
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        
        logger.info("订单详情补齐工作线程已停止")
    
    def _run(self):
        """工作线程主循环"""
        # 创建新的事件循环（每个线程需要自己的事件循环）
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._worker_loop())
        except Exception as e:
            logger.error(f"工作线程异常退出: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.loop.close()
    
    async def _worker_loop(self):
        """工作循环（异步）"""
        logger.info("工作线程循环开始")
        
        consecutive_empty_polls = 0  # 连续空轮询次数
        max_empty_polls = 10  # 最大连续空轮询次数（超过后增加轮询间隔）
        
        while self.running:
            try:
                # 创建数据库会话
                db = SessionLocal()
                try:
                    # 创建服务实例
                    service = OrderDetailEnrichmentService(db)
                    
                    # 批量处理任务（传入并发控制参数）
                    stats = await service.process_tasks_batch(
                        batch_size=self.batch_size,
                        max_concurrent=self.max_concurrent
                    )
                    
                    if stats["processed"] > 0:
                        consecutive_empty_polls = 0
                        logger.debug(
                            f"处理任务统计 - 处理: {stats['processed']}, "
                            f"完成: {stats['completed']}, 失败: {stats['failed']}, 重试: {stats['retried']}"
                        )
                    else:
                        consecutive_empty_polls += 1
                        if consecutive_empty_polls >= max_empty_polls:
                            # 如果连续多次空轮询，增加轮询间隔（避免频繁查询）
                            actual_interval = self.poll_interval * 2
                            logger.debug(f"队列为空，增加轮询间隔至 {actual_interval} 秒")
                        else:
                            actual_interval = self.poll_interval
                        
                        # 等待轮询间隔
                        await asyncio.sleep(actual_interval)
                        continue
                    
                except Exception as e:
                    logger.error(f"处理任务批次失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                finally:
                    db.close()
                
                # 等待轮询间隔
                await asyncio.sleep(self.poll_interval)
                
            except asyncio.CancelledError:
                logger.info("工作线程收到取消信号")
                break
            except Exception as e:
                logger.error(f"工作线程循环异常: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 发生异常时等待一段时间再继续
                await asyncio.sleep(self.poll_interval * 2)
        
        logger.info("工作线程循环结束")
    
    def is_running(self) -> bool:
        """检查工作线程是否在运行"""
        return self.running and self.thread is not None and self.thread.is_alive()


# 全局工作线程实例
_worker: Optional[OrderDetailWorker] = None


def start_order_detail_worker(batch_size: int = 15, poll_interval: int = 5, max_concurrent: int = 5):
    """
    启动订单详情补齐工作线程
    
    Args:
        batch_size: 每批处理的父订单数量（默认15）
        poll_interval: 轮询间隔（秒，默认5）
        max_concurrent: 最大并发数（同时进行的API调用数，默认5）
    """
    global _worker
    if _worker is None:
        _worker = OrderDetailWorker(
            batch_size=batch_size,
            poll_interval=poll_interval,
            max_concurrent=max_concurrent
        )
        _worker.start()
    else:
        logger.warning("工作线程已在运行中")


def stop_order_detail_worker():
    """停止订单详情补齐工作线程"""
    global _worker
    if _worker is not None:
        _worker.stop()
        _worker = None


def get_worker() -> Optional[OrderDetailWorker]:
    """获取工作线程实例"""
    return _worker
