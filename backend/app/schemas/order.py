"""订单相关的Pydantic模式"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List
from decimal import Decimal
from app.models.order import OrderStatus


class OrderBase(BaseModel):
    """订单基础模式"""
    order_sn: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal
    total_price: Decimal
    currency: str = "USD"


class OrderCreate(OrderBase):
    """创建订单模式"""
    shop_id: int
    temu_order_id: Optional[str] = None
    product_id: Optional[int] = None
    order_time: datetime
    status: OrderStatus = OrderStatus.PENDING


class OrderUpdate(BaseModel):
    """更新订单模式"""
    status: Optional[OrderStatus] = None
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    payment_time: Optional[datetime] = None
    shipping_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    """订单响应模式"""
    id: int
    shop_id: int
    temu_order_id: Optional[str] = None
    parent_order_sn: Optional[str] = None
    product_id: Optional[int] = None
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    profit: Optional[Decimal] = None
    status: OrderStatus
    order_time: datetime
    payment_time: Optional[datetime] = None
    shipping_time: Optional[datetime] = None
    expect_ship_latest_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    customer_id: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_province: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    notes: Optional[str] = None
    raw_data: Optional[str] = None  # 列表查询时建议排除此字段
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderListResponse(OrderBase):
    """订单列表响应模式（优化版，排除大字段）"""
    id: int
    shop_id: int
    temu_order_id: Optional[str] = None
    parent_order_sn: Optional[str] = None
    product_id: Optional[int] = None
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    profit: Optional[Decimal] = None
    status: OrderStatus
    order_time: datetime
    payment_time: Optional[datetime] = None
    shipping_time: Optional[datetime] = None
    expect_ship_latest_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    customer_id: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_province: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    notes: Optional[str] = None
    # 排除raw_data大字段，提升列表查询性能
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderStatistics(BaseModel):
    """订单统计模式"""
    total_orders: int
    total_gmv: Decimal
    total_cost: Decimal
    total_profit: Decimal
    avg_order_value: Decimal
    profit_margin: float


class OrderStatusStatistics(BaseModel):
    """订单状态统计模式"""
    total_orders: int  # 总订单数（不含已取消）
    processing: int  # 未发货
    shipped: int  # 已发货
    delivered: int  # 已送达
    delayed_orders: int  # 延误订单数
    delay_rate: float  # 延误率（百分比）
    trends: Optional[Dict[str, List[int]]] = None  # 7日趋势数据 {total: [...], processing: [...], shipped: [...], delivered: [...]}
    today_changes: Optional[Dict[str, int]] = None  # 今日新增 {total: ..., processing: ..., shipped: ..., delivered: ...}
    week_changes: Optional[Dict[str, float]] = None  # 周对比变化率（百分比）

