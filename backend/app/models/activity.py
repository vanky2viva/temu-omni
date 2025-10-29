"""活动模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class ActivityType(str, enum.Enum):
    """活动类型枚举"""
    DISCOUNT = "discount"  # 折扣活动
    FLASH_SALE = "flash_sale"  # 限时抢购
    COUPON = "coupon"  # 优惠券
    PROMOTION = "promotion"  # 促销活动
    OTHER = "other"  # 其他


class Activity(Base):
    """活动模型"""
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联店铺
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 活动基本信息
    activity_id = Column(String(100), index=True, comment="Temu活动ID")
    activity_name = Column(String(200), nullable=False, comment="活动名称")
    activity_type = Column(Enum(ActivityType), default=ActivityType.PROMOTION, comment="活动类型")
    
    # 活动时间
    start_time = Column(DateTime, nullable=False, index=True, comment="开始时间")
    end_time = Column(DateTime, nullable=False, index=True, comment="结束时间")
    
    # 活动状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 活动描述
    description = Column(Text, comment="活动描述")
    
    # 其他信息
    notes = Column(Text, comment="备注")
    raw_data = Column(Text, comment="原始数据JSON")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    shop = relationship("Shop", back_populates="activities")
    
    def __repr__(self):
        return f"<Activity {self.activity_name}>"

