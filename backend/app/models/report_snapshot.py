"""报表快照模型"""
from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.core.database import Base
import enum


class ReportType(str, enum.Enum):
    """报表类型枚举"""
    DAILY = "daily"  # 日报
    WEEKLY = "weekly"  # 周报


class ReportSnapshot(Base):
    """报表快照表
    
    存储每日/每周的运营报表快照，包含指标数据和AI生成的总结。
    """
    __tablename__ = "report_snapshots"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键")
    
    # 关联店铺
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True, comment="店铺ID")
    
    # 报表信息
    date = Column(Date, nullable=False, index=True, comment="报表日期")
    type = Column(String(20), nullable=False, default=ReportType.DAILY, comment="报表类型（daily/weekly）")
    
    # 指标数据（JSONB格式，存储结构化指标）
    metrics = Column(JSONB, nullable=False, comment="指标数据（订单数、GMV、退款率等）")
    
    # AI生成的文字总结（可选，后续AI功能实现时使用）
    ai_summary = Column(Text, comment="AI生成的文字总结")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    shop = relationship("Shop", backref="report_snapshots")
    
    # 唯一约束和索引
    __table_args__ = (
        UniqueConstraint('shop_id', 'date', 'type', name='uq_report_shop_date_type'),
        Index('idx_report_snapshots_shop_date', 'shop_id', 'date'),
        {'comment': '报表快照表，存储每日/每周运营报表'}
    )
    
    def __repr__(self):
        return f"<ReportSnapshot {self.shop_id} {self.date} {self.type}>"

