"""Temu商品原始数据模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class TemuProductsRaw(Base):
    """Temu商品原始数据表
    
    存储Temu API返回的完整商品数据，不做任何字段裁剪。
    作为原始数据层，方便后续扩展、排查异常和对账。
    """
    __tablename__ = "temu_products_raw"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键")
    
    # 关联店铺
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True, comment="店铺ID")
    
    # 商品标识
    external_product_id = Column(String(100), nullable=False, unique=True, index=True, comment="Temu商品ID")
    
    # 原始数据（JSONB类型，PostgreSQL支持高效查询）
    raw_json = Column(JSONB, nullable=False, comment="Temu接口返回的完整商品记录（JSONB）")
    
    # 时间信息
    fetched_at = Column(DateTime, nullable=False, index=True, comment="数据获取时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关联关系
    shop = relationship("Shop", backref="temu_products_raw")
    
    # 索引
    __table_args__ = (
        Index('idx_temu_products_raw_shop_fetched', 'shop_id', 'fetched_at'),
        {'comment': 'Temu商品原始数据表，完整存储API返回数据'}
    )
    
    def __repr__(self):
        return f"<TemuProductsRaw {self.external_product_id}>"

