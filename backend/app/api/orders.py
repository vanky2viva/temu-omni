"""订单管理API"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse, OrderStatistics, OrderStatusStatistics

router = APIRouter(prefix="/orders", tags=["orders"])

# 最大查询限制
MAX_LIMIT = 1000
DEFAULT_LIMIT = 20


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[OrderListResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


@router.get("/", response_model=PaginatedResponse)
def get_orders(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="每页数量"),
    shop_id: Optional[int] = Query(None, description="店铺ID"),
    status_filter: Optional[OrderStatus] = Query(None, description="订单状态"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    search: Optional[str] = Query(None, description="模糊搜索（订单号、商品名称、SKU）"),
    order_sn: Optional[str] = Query(None, description="订单号（精确匹配）"),
    product_name: Optional[str] = Query(None, description="商品名称（模糊匹配）"),
    product_sku: Optional[str] = Query(None, description="SKU（模糊匹配）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单列表（优化版）
    
    使用eager loading优化关联查询，排除大字段，支持分页和多种筛选条件
    """
    from sqlalchemy import or_
    
    # 构建基础查询
    # 注意：如果不需要shop和product的详细信息，可以不使用joinedload
    # 因为Order表中已经包含了shop_id和product_id，以及product_name等冗余字段
    query = db.query(Order)
    
    # 应用过滤条件
    if shop_id:
        query = query.filter(Order.shop_id == shop_id)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    if start_date:
        query = query.filter(Order.order_time >= start_date)
    
    if end_date:
        query = query.filter(Order.order_time <= end_date)
    
    # 订单号精确匹配
    if order_sn:
        query = query.filter(
            or_(
                Order.order_sn.ilike(f"%{order_sn}%"),
                Order.parent_order_sn.ilike(f"%{order_sn}%")
            )
        )
    
    # 商品名称模糊匹配
    if product_name:
        query = query.filter(Order.product_name.ilike(f"%{product_name}%"))
    
    # SKU模糊匹配
    if product_sku:
        query = query.filter(Order.product_sku.ilike(f"%{product_sku}%"))
    
    # 综合模糊搜索（搜索订单号、商品名称、SKU）
    if search:
        query = query.filter(
            or_(
                Order.order_sn.ilike(f"%{search}%"),
                Order.parent_order_sn.ilike(f"%{search}%"),
                Order.product_name.ilike(f"%{search}%"),
                Order.product_sku.ilike(f"%{search}%")
            )
        )
    
    # 获取总数（在分页前，使用子查询优化）
    # 使用distinct()避免重复计数（如果有joinedload）
    total = query.distinct().count()
    
    # 应用排序和分页
    # 使用order_time索引优化排序查询
    # 使用distinct()避免joinedload导致的重复记录
    orders = query.distinct().order_by(Order.order_time.desc()).offset(skip).limit(limit).all()
    
    # 直接使用OrderListResponse序列化，Pydantic会自动处理
    # 注意：OrderListResponse不包含raw_data字段，所以会自动排除
    order_list = [OrderListResponse.model_validate(order) for order in orders]
    
    return PaginatedResponse(
        items=order_list,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取订单详情"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    return order


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建订单"""
    # 检查订单编号是否已存在
    existing_order = db.query(Order).filter(Order.order_sn == order.order_sn).first()
    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单编号已存在"
        )
    
    db_order = Order(**order.model_dump())
    
    # 如果有成本信息，计算利润
    if db_order.total_cost:
        db_order.calculate_profit()
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新订单信息"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    # 重新计算利润
    if order.total_cost:
        order.calculate_profit()
    
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除订单"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    db.delete(order)
    db.commit()
    return None


@router.get("/statistics/summary", response_model=OrderStatistics)
def get_order_statistics(
    shop_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单统计信息（GMV、成本、利润等）
    
    Args:
        shop_id: 店铺ID（可选，不指定则统计所有店铺）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    Returns:
        订单统计信息，包括GMV、总成本、总利润、利润率等
    """
    # 构建查询
    query = db.query(Order).filter(
        Order.total_cost.isnot(None),  # 只统计有成本信息的订单
        Order.profit.isnot(None)
    )
    
    if shop_id:
        query = query.filter(Order.shop_id == shop_id)
    
    if start_date:
        query = query.filter(Order.order_time >= start_date)
    
    if end_date:
        query = query.filter(Order.order_time <= end_date)
    
    # 获取订单列表
    orders = query.all()
    
    if not orders:
        # 没有订单数据，返回零值
        return OrderStatistics(
            total_orders=0,
            total_gmv=Decimal('0'),
            total_cost=Decimal('0'),
            total_profit=Decimal('0'),
            avg_order_value=Decimal('0'),
            profit_margin=0.0
        )
    
    # 计算统计数据，统一转换为CNY
    from app.utils.currency import CurrencyConverter
    
    total_orders = len(orders)
    total_gmv = sum(
        CurrencyConverter.convert_to_cny(
            order.total_price or Decimal('0'),
            order.currency or 'USD'
        ) for order in orders
    )
    total_cost = sum(
        CurrencyConverter.convert_to_cny(
            order.total_cost or Decimal('0'),
            order.currency or 'USD'
        ) for order in orders if order.total_cost
    )
    total_profit = sum(
        CurrencyConverter.convert_to_cny(
            order.profit or Decimal('0'),
            order.currency or 'USD'
        ) for order in orders if order.profit
    )
    
    # 平均订单价值
    avg_order_value = total_gmv / Decimal(total_orders) if total_orders > 0 else Decimal('0')
    
    # 利润率
    profit_margin = float(total_profit / total_gmv * 100) if total_gmv > 0 else 0.0
    
    return OrderStatistics(
        total_orders=total_orders,
        total_gmv=total_gmv,
        total_cost=total_cost,
        total_profit=total_profit,
        avg_order_value=avg_order_value,
            profit_margin=profit_margin
        )


@router.get("/statistics/status", response_model=OrderStatusStatistics)
def get_order_status_statistics(
    shop_id: Optional[int] = Query(None, description="店铺ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单状态统计信息
    
    Args:
        shop_id: 店铺ID（可选，不指定则统计所有店铺）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    Returns:
        订单状态统计信息，包括总订单数（不含已取消）、未发货、已发货、已送达、延误订单数、延误率
    """
    from datetime import datetime, timedelta
    
    # 构建查询，排除已取消的订单
    query = db.query(Order).filter(Order.status != OrderStatus.CANCELLED)
    
    if shop_id:
        query = query.filter(Order.shop_id == shop_id)
    
    if start_date:
        query = query.filter(Order.order_time >= start_date)
    
    if end_date:
        query = query.filter(Order.order_time <= end_date)
    
    # 获取所有订单
    orders = query.all()
    
    # 统计各状态订单数
    total_orders = len(orders)
    processing = sum(1 for o in orders if o.status == OrderStatus.PROCESSING)
    shipped = sum(1 for o in orders if o.status == OrderStatus.SHIPPED)
    delivered = sum(1 for o in orders if o.status == OrderStatus.DELIVERED)
    
    # 计算延误订单数
    # 延误判断逻辑：
    # 1. 优先从raw_data中获取latestDeliveryTime（最晚送达时间）
    # 2. 如果没有latestDeliveryTime，使用expect_ship_latest_time+14天作为估算
    # 3. 如果订单状态是DELIVERED，检查delivery_time是否超过latestDeliveryTime
    # 4. 如果订单状态不是DELIVERED，检查当前时间是否超过latestDeliveryTime
    import json
    
    now = datetime.utcnow()
    delayed_orders = 0
    
    for order in orders:
        is_delayed = False
        latest_delivery_time = None
        
        # 尝试从raw_data中获取latestDeliveryTime
        if order.raw_data:
            try:
                raw_data_json = json.loads(order.raw_data)
                # raw_data可能包含parent_order数据，其中包含latestDeliveryTime
                if isinstance(raw_data_json, dict):
                    # 如果是订单项数据，可能在parent_order中
                    parent_order = raw_data_json.get('parent_order') or raw_data_json.get('parentOrderMap')
                    if parent_order:
                        latest_delivery_time_ts = parent_order.get('latestDeliveryTime')
                        if latest_delivery_time_ts:
                            # 转换为datetime（假设是Unix时间戳）
                            if isinstance(latest_delivery_time_ts, (int, float)):
                                latest_delivery_time = datetime.utcfromtimestamp(latest_delivery_time_ts)
                            elif isinstance(latest_delivery_time_ts, str):
                                # 尝试解析为时间戳
                                try:
                                    latest_delivery_time = datetime.utcfromtimestamp(float(latest_delivery_time_ts))
                                except:
                                    pass
                    # 也可能直接在顶层
                    if not latest_delivery_time:
                        latest_delivery_time_ts = raw_data_json.get('latestDeliveryTime')
                        if latest_delivery_time_ts:
                            if isinstance(latest_delivery_time_ts, (int, float)):
                                latest_delivery_time = datetime.utcfromtimestamp(latest_delivery_time_ts)
                            elif isinstance(latest_delivery_time_ts, str):
                                try:
                                    latest_delivery_time = datetime.utcfromtimestamp(float(latest_delivery_time_ts))
                                except:
                                    pass
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # 如果没有从raw_data中获取到，使用expect_ship_latest_time+14天作为估算
        if not latest_delivery_time:
            if order.expect_ship_latest_time:
                latest_delivery_time = order.expect_ship_latest_time + timedelta(days=14)
            else:
                # 如果没有expect_ship_latest_time，使用order_time+21天作为估算
                latest_delivery_time = order.order_time + timedelta(days=21)
        
        # 判断是否延误
        if order.status == OrderStatus.DELIVERED:
            # 已送达：检查送达时间是否超过最晚送达时间
            if order.delivery_time and order.delivery_time > latest_delivery_time:
                is_delayed = True
        else:
            # 未送达：检查当前时间是否已超过最晚送达时间
            if now > latest_delivery_time:
                is_delayed = True
        
        if is_delayed:
            delayed_orders += 1
    
    # 计算延误率
    delay_rate = (delayed_orders / total_orders * 100) if total_orders > 0 else 0.0
    
    return OrderStatusStatistics(
        total_orders=total_orders,
        processing=processing,
        shipped=shipped,
        delivered=delivered,
        delayed_orders=delayed_orders,
        delay_rate=delay_rate
    )

