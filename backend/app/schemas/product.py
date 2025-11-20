"""商品相关的Pydantic模式"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class ProductCostBase(BaseModel):
    """商品成本基础模式"""
    cost_price: Decimal
    currency: str = "CNY"
    effective_from: datetime
    notes: Optional[str] = None


class ProductCostCreate(ProductCostBase):
    """创建商品成本模式"""
    product_id: int


class ProductCostUpdate(BaseModel):
    """快速更新商品成本价格模式"""
    cost_price: Decimal
    currency: str = "CNY"


class ProductCostResponse(ProductCostBase):
    """商品成本响应模式"""
    id: int
    product_id: int
    effective_to: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """商品基础模式"""
    product_name: str
    sku: Optional[str] = None
    current_price: Optional[Decimal] = None
    currency: str = "USD"


class ProductCreate(ProductBase):
    """创建商品模式"""
    shop_id: int
    product_id: Optional[str] = None
    stock_quantity: int = 0
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    """更新商品模式"""
    product_name: Optional[str] = None
    current_price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class ProductResponse(ProductBase):
    """商品响应模式"""
    id: int
    shop_id: int
    product_id: Optional[str] = None
    stock_quantity: int
    is_active: bool
    description: Optional[str] = None
    manager: Optional[str] = None
    category: Optional[str] = None
    skc_id: Optional[str] = None
    spu_id: Optional[str] = None
    price_status: Optional[str] = None
    current_cost_price: Optional[Decimal] = None  # 当前成本价格
    cost_currency: Optional[str] = None  # 成本价格货币
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

