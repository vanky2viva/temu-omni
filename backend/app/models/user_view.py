"""用户视图模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class UserView(Base):
    """用户视图表"""
    __tablename__ = "user_views"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 视图基本信息
    name = Column(String(100), nullable=False, comment="视图名称")
    view_type = Column(String(50), default="order_list", comment="视图类型")
    description = Column(Text, comment="视图描述")
    
    # 视图配置（JSON格式存储）
    filters = Column(JSON, nullable=False, default=dict, comment="筛选条件")
    visible_columns = Column(ARRAY(String), nullable=False, default=[], comment="可见列列表")
    column_order = Column(ARRAY(String), nullable=False, default=[], comment="列顺序")
    column_widths = Column(JSON, default=dict, comment="列宽度配置")
    group_by = Column(String(50), comment="分组方式")
    
    # 视图设置
    is_default = Column(Boolean, default=False, comment="是否默认视图")
    is_public = Column(Boolean, default=False, comment="是否公开（其他用户可见）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    user = relationship("User", backref="views")
    
    def __repr__(self):
        return f"<UserView {self.name}>"

