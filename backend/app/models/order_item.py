"""订单明细模型"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class OrderItem(Base):
    """订单明细表
    
    存储订单中的商品明细信息，一个订单可以包含多个商品。
    """
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键")
    
    # 关联订单
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True, comment="订单ID")
    
    # 商品信息
    sku_id = Column(String(200), index=True, comment="SKU ID")
    product_name = Column(String(500), comment="商品名称")
    product_sku = Column(String(200), index=True, comment="商品SKU")
    spu_id = Column(String(100), index=True, comment="SPU ID")
    
    # 数量和价格
    quantity = Column(Integer, default=1, nullable=False, comment="数量")
    price = Column(Numeric(10, 2), nullable=False, comment="单价")
    total_price = Column(Numeric(10, 2), nullable=False, comment="总价")
    currency = Column(String(10), default="USD", comment="货币")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    order = relationship("Order", backref="order_items")
    
    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"

