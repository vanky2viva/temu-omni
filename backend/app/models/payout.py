"""回款计划模型"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.core.database import Base
import enum


class PayoutStatus(str, enum.Enum):
    """回款状态枚举"""
    PENDING = "pending"  # 待回款
    PAID = "paid"  # 已回款


class Payout(Base):
    """回款计划表
    
    存储订单的回款计划信息，基于订单签收时间计算回款日期。
    """
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键")
    
    # 关联店铺
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True, comment="店铺ID")
    
    # 关联订单
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True, comment="订单ID")
    
    # Temu结算单号（可选，如果Temu API提供）
    external_payout_id = Column(String(100), index=True, comment="Temu结算单号")
    
    # 回款信息
    payout_date = Column(Date, nullable=False, index=True, comment="回款日期")
    payout_amount = Column(Numeric(12, 2), nullable=False, comment="回款金额")
    currency = Column(String(10), default="USD", comment="货币")
    status = Column(Enum(PayoutStatus), default=PayoutStatus.PENDING, index=True, comment="回款状态")
    
    # 关联原始数据（可选）
    raw_data_id = Column(Integer, ForeignKey("temu_orders_raw.id", ondelete="SET NULL"), comment="关联原始数据ID")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    shop = relationship("Shop", backref="payouts")
    order = relationship("Order", backref="payouts")
    raw_data = relationship("TemuOrdersRaw", foreign_keys=[raw_data_id])
    
    # 索引
    __table_args__ = (
        Index('idx_payouts_shop_date', 'shop_id', 'payout_date'),
        {'comment': '回款计划表，基于订单签收时间计算回款日期'}
    )
    
    def __repr__(self):
        return f"<Payout {self.payout_amount} @ {self.payout_date}>"

