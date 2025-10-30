"""订单模型"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class OrderStatus(str, enum.Enum):
    """订单状态枚举"""
    PENDING = "PENDING"  # 待支付
    PAID = "PAID"  # 已支付
    PROCESSING = "PROCESSING"  # 处理中
    SHIPPED = "SHIPPED"  # 已发货
    DELIVERED = "DELIVERED"  # 已送达
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消
    REFUNDED = "REFUNDED"  # 已退款


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联店铺
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 订单基本信息
    order_sn = Column(String(100), unique=True, index=True, nullable=False, comment="订单编号")
    temu_order_id = Column(String(100), unique=True, index=True, comment="Temu订单ID")
    
    # 商品信息
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), index=True)
    product_name = Column(String(500), comment="商品名称")
    product_sku = Column(String(200), comment="商品SKU")
    quantity = Column(Integer, default=1, comment="购买数量")
    
    # 价格信息
    unit_price = Column(Numeric(10, 2), nullable=False, comment="单价")
    total_price = Column(Numeric(10, 2), nullable=False, comment="订单总价")
    currency = Column(String(10), default="USD", comment="货币")
    
    # 成本和利润
    unit_cost = Column(Numeric(10, 2), comment="单位成本")
    total_cost = Column(Numeric(10, 2), comment="总成本")
    profit = Column(Numeric(10, 2), comment="利润")
    
    # 订单状态
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True, comment="订单状态")
    
    # 时间信息
    order_time = Column(DateTime, nullable=False, index=True, comment="下单时间")
    payment_time = Column(DateTime, comment="支付时间")
    shipping_time = Column(DateTime, comment="发货时间")
    delivery_time = Column(DateTime, comment="送达时间")
    
    # 客户信息（可选）
    customer_id = Column(String(100), comment="客户ID")
    shipping_country = Column(String(50), comment="收货国家")
    
    # 其他信息
    notes = Column(Text, comment="备注")
    raw_data = Column(Text, comment="原始数据JSON")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    shop = relationship("Shop", back_populates="orders")
    product = relationship("Product", back_populates="orders")
    
    def __repr__(self):
        return f"<Order {self.order_sn}>"
    
    def calculate_profit(self):
        """计算利润"""
        if self.total_cost and self.total_price:
            self.profit = self.total_price - self.total_cost
        return self.profit

