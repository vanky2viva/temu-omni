"""店铺相关的Pydantic模式"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ShopBase(BaseModel):
    """店铺基础模式"""
    shop_id: Optional[str] = None
    shop_name: str
    region: str
    entity: Optional[str] = None
    default_manager: Optional[str] = None
    description: Optional[str] = None


class ShopCreate(ShopBase):
    """创建店铺模式"""
    access_token: Optional[str] = None  # 可选，改为非必填


class ShopUpdate(BaseModel):
    """更新店铺模式"""
    shop_name: Optional[str] = None
    region: Optional[str] = None
    entity: Optional[str] = None
    default_manager: Optional[str] = None
    is_active: Optional[bool] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    description: Optional[str] = None


class ShopResponse(ShopBase):
    """店铺响应模式"""
    id: int
    is_active: bool
    has_api_config: bool = False  # 是否已配置API
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, obj):
        """从ORM对象创建响应"""
        data = super().from_orm(obj)
        # 判断是否已配置Token
        data.has_api_config = bool(obj.access_token)
        return data

