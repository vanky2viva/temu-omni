"""店铺模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Shop(Base):
    """店铺模型"""
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 店铺基本信息
    shop_id = Column(String(100), unique=True, index=True, nullable=False, comment="Temu店铺ID")
    shop_name = Column(String(200), nullable=False, comment="店铺名称")
    region = Column(String(50), nullable=False, comment="店铺地区")
    entity = Column(String(200), comment="经营主体")
    
    # API认证信息
    access_token = Column(Text, comment="访问令牌")
    refresh_token = Column(Text, comment="刷新令牌")
    token_expires_at = Column(DateTime, comment="令牌过期时间")
    
    # 店铺状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_sync_at = Column(DateTime, comment="最后同步时间")
    
    # 备注信息
    description = Column(Text, comment="备注")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    orders = relationship("Order", back_populates="shop", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="shop", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Shop {self.shop_name} ({self.region})>"

