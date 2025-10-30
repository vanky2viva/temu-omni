"""导入历史记录模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class ImportType(str, enum.Enum):
    """导入类型枚举"""
    ORDERS = "orders"  # 订单
    PRODUCTS = "products"  # 商品
    ACTIVITIES = "activities"  # 活动


class ImportStatus(str, enum.Enum):
    """导入状态枚举"""
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    PARTIAL = "partial"  # 部分成功


class ImportHistory(Base):
    """导入历史记录模型"""
    __tablename__ = "import_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联店铺
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, comment="店铺ID")
    
    # 导入信息
    import_type = Column(SQLEnum(ImportType), nullable=False, comment="导入类型")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_size = Column(Integer, comment="文件大小(字节)")
    
    # 统计信息
    total_rows = Column(Integer, default=0, comment="总行数")
    success_rows = Column(Integer, default=0, comment="成功行数")
    failed_rows = Column(Integer, default=0, comment="失败行数")
    skipped_rows = Column(Integer, default=0, comment="跳过行数")
    
    # 状态
    status = Column(SQLEnum(ImportStatus), default=ImportStatus.PROCESSING, comment="导入状态")
    
    # 日志信息
    error_log = Column(Text, comment="错误日志(JSON格式)")
    success_log = Column(Text, comment="成功日志(JSON格式)")
    
    # 时间信息
    started_at = Column(DateTime, default=datetime.utcnow, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关联关系
    shop = relationship("Shop", back_populates="import_history")
    
    def __repr__(self):
        return f"<ImportHistory {self.file_name} - {self.status}>"

