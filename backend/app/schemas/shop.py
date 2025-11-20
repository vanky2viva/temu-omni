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
    # CN 区域配置
    cn_access_token: Optional[str] = None
    cn_app_key: Optional[str] = None
    cn_app_secret: Optional[str] = None
    cn_api_base_url: Optional[str] = None


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
    # CN 区域配置
    cn_access_token: Optional[str] = None
    cn_app_key: Optional[str] = None
    cn_app_secret: Optional[str] = None
    cn_api_base_url: Optional[str] = None


class ShopResponse(ShopBase):
    """店铺响应模式（列表和详情共用）"""
    id: int
    is_active: bool
    has_api_config: bool = False  # 是否已配置API
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # 编辑时需要这些字段（仅在获取单个店铺详情时返回，列表接口不返回）
    access_token: Optional[str] = None
    cn_access_token: Optional[str] = None
    
    class Config:
        from_attributes = True


class ShopDetailResponse(ShopResponse):
    """店铺详情响应模式（包含敏感字段，用于编辑）"""
    # 继承 ShopResponse 的所有字段，并确保敏感字段被包含
    pass

