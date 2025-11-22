"""用户视图相关的Pydantic模式"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List, Any


class UserViewBase(BaseModel):
    """用户视图基础模式"""
    name: str
    view_type: str = "order_list"
    description: Optional[str] = None
    filters: Dict[str, Any] = {}
    visible_columns: List[str] = []
    column_order: List[str] = []
    column_widths: Dict[str, int] = {}
    group_by: Optional[str] = None
    is_default: bool = False
    is_public: bool = False


class UserViewCreate(UserViewBase):
    """创建用户视图模式"""
    pass


class UserViewUpdate(BaseModel):
    """更新用户视图模式"""
    name: Optional[str] = None
    description: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    visible_columns: Optional[List[str]] = None
    column_order: Optional[List[str]] = None
    column_widths: Optional[Dict[str, int]] = None
    group_by: Optional[str] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None


class UserViewResponse(UserViewBase):
    """用户视图响应模式"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

