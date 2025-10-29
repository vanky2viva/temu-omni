"""店铺相关的Pydantic模式"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ShopBase(BaseModel):
    """店铺基础模式"""
    shop_id: str
    shop_name: str
    region: str
    entity: Optional[str] = None
    description: Optional[str] = None


class ShopCreate(ShopBase):
    """创建店铺模式"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class ShopUpdate(BaseModel):
    """更新店铺模式"""
    shop_name: Optional[str] = None
    region: Optional[str] = None
    entity: Optional[str] = None
    is_active: Optional[bool] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    description: Optional[str] = None


class ShopResponse(ShopBase):
    """店铺响应模式"""
    id: int
    is_active: bool
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

