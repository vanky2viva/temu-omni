"""商品模型"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Product(Base):
    """商品模型"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联店铺
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 商品基本信息
    product_id = Column(String(100), index=True, comment="Temu商品ID")
    product_name = Column(String(500), nullable=False, comment="商品名称")
    sku = Column(String(200), index=True, comment="商品SKU")
    
    # 价格信息
    current_price = Column(Numeric(10, 2), comment="当前售价")
    currency = Column(String(10), default="USD", comment="货币")
    
    # 库存信息
    stock_quantity = Column(Integer, default=0, comment="库存数量")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否在售")
    
    # 其他信息
    description = Column(Text, comment="商品描述")
    image_url = Column(String(500), comment="商品图片URL")
    category = Column(String(200), comment="商品分类")
    manager = Column(String(100), comment="负责人")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    shop = relationship("Shop", back_populates="products")
    costs = relationship("ProductCost", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="product")
    
    def __repr__(self):
        return f"<Product {self.product_name}>"


class ProductCost(Base):
    """商品成本模型（支持历史成本记录）"""
    __tablename__ = "product_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联商品
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 成本信息
    cost_price = Column(Numeric(10, 2), nullable=False, comment="成本价")
    currency = Column(String(10), default="USD", comment="货币")
    
    # 生效时间
    effective_from = Column(DateTime, nullable=False, index=True, comment="生效开始时间")
    effective_to = Column(DateTime, comment="生效结束时间")
    
    # 备注
    notes = Column(Text, comment="备注")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关联关系
    product = relationship("Product", back_populates="costs")
    
    def __repr__(self):
        return f"<ProductCost {self.cost_price} @ {self.effective_from}>"

