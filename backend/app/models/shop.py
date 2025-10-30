"""店铺模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class ShopEnvironment(str, enum.Enum):
    """店铺环境枚举"""
    SANDBOX = "sandbox"  # 沙盒环境（测试数据）
    PRODUCTION = "production"  # 生产环境（真实数据）


class ShopRegion(str, enum.Enum):
    """店铺区域枚举"""
    US = "us"  # 美国
    EU = "eu"  # 欧洲
    GLOBAL = "global"  # 全球


class Shop(Base):
    """店铺模型"""
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 店铺基本信息
    shop_id = Column(String(100), unique=True, index=True, nullable=False, comment="Temu店铺ID/Mall ID")
    shop_name = Column(String(200), nullable=False, comment="店铺名称")
    region = Column(Enum(ShopRegion), nullable=False, default=ShopRegion.US, comment="店铺地区")
    entity = Column(String(200), comment="经营主体")
    default_manager = Column(String(100), comment="默认负责人")
    
    # 环境标识
    environment = Column(
        Enum(ShopEnvironment), 
        nullable=False, 
        default=ShopEnvironment.SANDBOX, 
        comment="环境类型：sandbox=沙盒数据，production=真实数据"
    )
    
    # API认证信息
    app_key = Column(String(200), comment="Temu App Key")
    app_secret = Column(Text, comment="Temu App Secret")
    access_token = Column(Text, comment="访问令牌（每个店铺独立的token）")
    refresh_token = Column(Text, comment="刷新令牌")
    token_expires_at = Column(DateTime, comment="令牌过期时间")
    
    # API基础URL（根据区域不同）
    api_base_url = Column(String(200), comment="API基础URL")
    
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
    import_history = relationship("ImportHistory", back_populates="shop", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Shop {self.shop_name} ({self.region})>"

