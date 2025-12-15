"""订单详情补齐任务模型"""
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ARRAY, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from datetime import datetime
from app.core.database import Base
import enum


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败（超过最大重试次数）


class OrderDetailTask(Base):
    """订单详情补齐任务表"""
    __tablename__ = "order_detail_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联店铺
    shop_id = Column(Integer, nullable=False, index=True, comment="店铺ID")
    
    # 订单信息
    parent_order_sn = Column(String(100), nullable=False, index=True, comment="父订单号")
    order_ids = Column(PG_ARRAY(Integer), nullable=False, comment="该父订单下的所有子订单ID列表")
    
    # 任务状态
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True, comment="任务状态")
    package_sn = Column(String(200), nullable=True, comment="获取到的包裹号")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 重试信息
    retry_count = Column(Integer, default=0, nullable=False, comment="重试次数")
    max_retries = Column(Integer, default=5, nullable=False, comment="最大重试次数")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    def __repr__(self):
        return f"<OrderDetailTask {self.parent_order_sn} ({self.status})>"
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries and self.status != TaskStatus.COMPLETED
    
    def mark_failed(self, error_message: str):
        """标记任务为失败"""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, package_sn: Optional[str] = None):
        """标记任务为完成
        
        Args:
            package_sn: 包裹号，如果为None表示成功获取详情但订单无包裹号
        """
        self.status = TaskStatus.COMPLETED
        self.package_sn = package_sn
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_retry(self):
        """增加重试次数"""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
