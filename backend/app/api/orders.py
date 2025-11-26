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
from datetime import timedelta

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
    shop_id: Optional[int] = Query(None, description="店铺ID（单选）"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表（多选）"),
    status_filter: Optional[OrderStatus] = Query(None, description="订单状态（单选）"),
    status_filters: Optional[List[OrderStatus]] = Query(None, description="订单状态列表（多选）"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    search: Optional[str] = Query(None, description="模糊搜索（订单号、商品名称、SKU）"),
    order_sn: Optional[str] = Query(None, description="订单号（精确匹配）"),
    product_name: Optional[str] = Query(None, description="商品名称（模糊匹配）"),
    product_sku: Optional[str] = Query(None, description="SKU（模糊匹配）"),
    delay_risk_level: Optional[str] = Query(None, description="延误风险等级（normal/warning/delayed）"),
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
    # 优先使用多选店铺，如果没有则使用单选
    if shop_ids and len(shop_ids) > 0:
        query = query.filter(Order.shop_id.in_(shop_ids))
    elif shop_id:
        query = query.filter(Order.shop_id == shop_id)
    
    # 优先使用多选状态，如果没有则使用单选
    if status_filters and len(status_filters) > 0:
        query = query.filter(Order.status.in_(status_filters))
    elif status_filter:
        query = query.filter(Order.status == status_filter)
    
    # 延误风险等级筛选（暂时使用简单的逻辑，后续可以优化）
    if delay_risk_level:
        # 这里可以根据实际业务逻辑实现延误风险等级的判断
        # 暂时留空，等待具体需求
        pass
    
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
    shop_id: Optional[int] = Query(None, description="店铺ID（单选）"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表（多选）"),
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
        订单状态统计信息，包括总订单数（只统计有效订单：待发货、已发货、已签收）、未发货、已发货、已送达、延误订单数、延误率
    """
    from datetime import datetime, timedelta
    
    # 构建查询，只统计有效订单（与销量统计保持一致）
    # 统计口径：一个不重复的父订单号记为一单
    # 只统计有效订单状态：PROCESSING（待发货）、SHIPPED（已发货）、DELIVERED（已签收）
    # 排除：PENDING（待支付）、PAID（平台处理中）、CANCELLED（已取消）、REFUNDED（已退款）
    from sqlalchemy import func, and_
    
    filters = [Order.status.in_([
        OrderStatus.PROCESSING,  # 待发货 - 计入统计
        OrderStatus.SHIPPED,     # 已发货 - 计入统计
        OrderStatus.DELIVERED    # 已签收 - 计入统计
    ])]
    
    # 优先使用多选店铺，如果没有则使用单选
    if shop_ids and len(shop_ids) > 0:
        filters.append(Order.shop_id.in_(shop_ids))
    elif shop_id:
        filters.append(Order.shop_id == shop_id)
    
    if start_date:
        filters.append(Order.order_time >= start_date)
    
    if end_date:
        filters.append(Order.order_time <= end_date)
    
    # 按父订单号去重统计总订单数（排除取消订单）
    # 统计口径：一个不重复的父订单号记为一单
    # 如果parent_order_sn存在，使用parent_order_sn；否则使用order_sn
    from sqlalchemy import case
    parent_order_key = case(
        (Order.parent_order_sn.isnot(None), Order.parent_order_sn),
        else_=Order.order_sn
    )
    
    total_orders_result = db.query(
        func.count(func.distinct(parent_order_key)).label("total_orders")
    ).filter(and_(*filters)).first()
    total_orders = total_orders_result.total_orders or 0
    
    # 统计各状态订单数（按父订单号去重）
    processing_result = db.query(
        func.count(func.distinct(parent_order_key)).label("count")
    ).filter(and_(*filters, Order.status == OrderStatus.PROCESSING)).first()
    processing = processing_result.count or 0
    
    shipped_result = db.query(
        func.count(func.distinct(parent_order_key)).label("count")
    ).filter(and_(*filters, Order.status == OrderStatus.SHIPPED)).first()
    shipped = shipped_result.count or 0
    
    delivered_result = db.query(
        func.count(func.distinct(parent_order_key)).label("count")
    ).filter(and_(*filters, Order.status == OrderStatus.DELIVERED)).first()
    delivered = delivered_result.count or 0
    
    # 计算延误订单数（按父订单号去重）
    # 延误判断逻辑：根据订单的送达日期与要求最晚送达日期对比，晚于该日期的订单为延迟
    # 1. 优先从raw_data中获取latestDeliveryTime（要求最晚送达时间）
    # 2. 如果没有latestDeliveryTime，使用expect_ship_latest_time+14天作为估算
    # 3. 只统计已送达的订单（有delivery_time的订单）
    # 4. 对比送达日期（delivery_time）与要求最晚送达日期（latestDeliveryTime）
    # 5. 如果delivery_time > latestDeliveryTime，则为延迟订单
    import json
    
    delayed_parent_orders = set()  # 使用set来去重父订单号
    
    # 获取所有订单记录用于延误判断
    query = db.query(Order).filter(and_(*filters))
    orders = query.all()
    
    for order in orders:
        # 只统计已送达的订单（必须有送达时间）
        if order.status != OrderStatus.DELIVERED or not order.delivery_time:
            continue
        
        latest_delivery_time = None
        
        # 尝试从raw_data中获取latestDeliveryTime（要求最晚送达时间）
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
                            # 转换为datetime（假设是Unix时间戳，单位可能是秒或毫秒）
                            if isinstance(latest_delivery_time_ts, (int, float)):
                                # 如果是很大的数字（>10位数），可能是毫秒，需要除以1000
                                if latest_delivery_time_ts > 1e10:
                                    latest_delivery_time_ts = latest_delivery_time_ts / 1000
                                latest_delivery_time = datetime.utcfromtimestamp(latest_delivery_time_ts)
                            elif isinstance(latest_delivery_time_ts, str):
                                # 尝试解析为时间戳
                                try:
                                    ts_value = float(latest_delivery_time_ts)
                                    if ts_value > 1e10:
                                        ts_value = ts_value / 1000
                                    latest_delivery_time = datetime.utcfromtimestamp(ts_value)
                                except:
                                    pass
                    # 也可能直接在顶层
                    if not latest_delivery_time:
                        latest_delivery_time_ts = raw_data_json.get('latestDeliveryTime')
                        if latest_delivery_time_ts:
                            if isinstance(latest_delivery_time_ts, (int, float)):
                                if latest_delivery_time_ts > 1e10:
                                    latest_delivery_time_ts = latest_delivery_time_ts / 1000
                                latest_delivery_time = datetime.utcfromtimestamp(latest_delivery_time_ts)
                            elif isinstance(latest_delivery_time_ts, str):
                                try:
                                    ts_value = float(latest_delivery_time_ts)
                                    if ts_value > 1e10:
                                        ts_value = ts_value / 1000
                                    latest_delivery_time = datetime.utcfromtimestamp(ts_value)
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
        
        # 判断是否延误：对比送达日期与要求最晚送达日期
        # 如果送达时间晚于要求最晚送达时间，则为延迟订单
        if order.delivery_time and latest_delivery_time:
            if order.delivery_time > latest_delivery_time:
                # 使用父订单号作为key（如果存在），否则使用订单号
                parent_order_key_value = order.parent_order_sn if order.parent_order_sn else order.order_sn
                delayed_parent_orders.add(parent_order_key_value)
    
    delayed_orders = len(delayed_parent_orders)
    
    # 计算延误率：延迟订单数 / 总订单数 * 100
    # 延误判断逻辑：根据订单的送达日期与要求最晚送达日期对比，晚于该日期的订单为延迟
    # 注意：只有已送达的订单才能判断是否延迟（因为有送达日期），但延迟率的分母是总订单数
    # 这样延迟率反映的是整体订单中延迟订单的比例
    delay_rate = (delayed_orders / total_orders * 100) if total_orders > 0 else 0.0
    
    # 计算7日趋势数据（按订单号去重统计）
    trends = {}
    today_changes = {}
    week_changes = {}
    
    if total_orders > 0:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_ago_start = today_start - timedelta(days=7)
        two_weeks_ago_start = week_ago_start - timedelta(days=7)
        
        # 计算7日趋势（每日订单数统计，按订单号去重）
        trend_days = 7
        trends['total'] = []
        trends['processing'] = []
        trends['shipped'] = []
        trends['delivered'] = []
        
        for i in range(trend_days):
            day_start = today_start - timedelta(days=trend_days - 1 - i)
            day_end = day_start + timedelta(days=1)
            
            # 按父订单号去重统计每日订单数
            day_filters = filters + [Order.order_time >= day_start, Order.order_time < day_end]
            day_total = db.query(func.count(func.distinct(parent_order_key))).filter(and_(*day_filters)).scalar() or 0
            trends['total'].append(day_total)
            
            day_processing = db.query(func.count(func.distinct(parent_order_key))).filter(
                and_(*day_filters, Order.status == OrderStatus.PROCESSING)
            ).scalar() or 0
            trends['processing'].append(day_processing)
            
            day_shipped = db.query(func.count(func.distinct(parent_order_key))).filter(
                and_(*day_filters, Order.status == OrderStatus.SHIPPED)
            ).scalar() or 0
            trends['shipped'].append(day_shipped)
            
            day_delivered = db.query(func.count(func.distinct(parent_order_key))).filter(
                and_(*day_filters, Order.status == OrderStatus.DELIVERED)
            ).scalar() or 0
            trends['delivered'].append(day_delivered)
        
        # 计算今日新增（按父订单号去重）
        today_filters = filters + [Order.order_time >= today_start]
        today_changes['total'] = db.query(func.count(func.distinct(parent_order_key))).filter(and_(*today_filters)).scalar() or 0
        today_changes['processing'] = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*today_filters, Order.status == OrderStatus.PROCESSING)
        ).scalar() or 0
        today_changes['shipped'] = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*today_filters, Order.status == OrderStatus.SHIPPED)
        ).scalar() or 0
        today_changes['delivered'] = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*today_filters, Order.status == OrderStatus.DELIVERED)
        ).scalar() or 0
        
        # 计算周对比变化率（按父订单号去重）
        week_filters = filters + [Order.order_time >= week_ago_start, Order.order_time < today_start]
        two_weeks_ago_filters = filters + [Order.order_time >= two_weeks_ago_start, Order.order_time < week_ago_start]
        
        week_total = db.query(func.count(func.distinct(parent_order_key))).filter(and_(*week_filters)).scalar() or 0
        two_weeks_ago_total = db.query(func.count(func.distinct(parent_order_key))).filter(and_(*two_weeks_ago_filters)).scalar() or 0
        
        week_processing = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*week_filters, Order.status == OrderStatus.PROCESSING)
        ).scalar() or 0
        two_weeks_ago_processing = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*two_weeks_ago_filters, Order.status == OrderStatus.PROCESSING)
        ).scalar() or 0
        
        week_shipped = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*week_filters, Order.status == OrderStatus.SHIPPED)
        ).scalar() or 0
        two_weeks_ago_shipped = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*two_weeks_ago_filters, Order.status == OrderStatus.SHIPPED)
        ).scalar() or 0
        
        week_delivered = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*week_filters, Order.status == OrderStatus.DELIVERED)
        ).scalar() or 0
        two_weeks_ago_delivered = db.query(func.count(func.distinct(parent_order_key))).filter(
            and_(*two_weeks_ago_filters, Order.status == OrderStatus.DELIVERED)
        ).scalar() or 0
        
        # 计算变化率（百分比）
        def calc_change_rate(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous * 100)
        
        week_changes['total'] = round(calc_change_rate(week_total, two_weeks_ago_total), 1)
        week_changes['processing'] = round(calc_change_rate(week_processing, two_weeks_ago_processing), 1)
        week_changes['shipped'] = round(calc_change_rate(week_shipped, two_weeks_ago_shipped), 1)
        week_changes['delivered'] = round(calc_change_rate(week_delivered, two_weeks_ago_delivered), 1)
    
    return OrderStatusStatistics(
        total_orders=total_orders,
        processing=processing,
        shipped=shipped,
        delivered=delivered,
        delayed_orders=delayed_orders,
        delay_rate=round(delay_rate, 2),
        trends=trends if trends else None,
        today_changes=today_changes if today_changes else None,
        week_changes=week_changes if week_changes else None
    )


@router.get("/{parent_order_sn}/shipment-document")
async def get_shipment_document(
    parent_order_sn: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单的发货面单信息
    
    根据父订单号获取发货面单（PDF文档或Base64编码的文档）
    
    Args:
        parent_order_sn: 父订单号（如：PO-211-16278814116470363）
        
    Returns:
        发货面单信息（可能包含PDF链接、Base64编码的文档等）
    """
    import asyncio
    from app.models.shop import Shop
    from app.services.temu_service import TemuService
    from loguru import logger
    
    # 根据父订单号查找订单，获取店铺信息
    order = db.query(Order).filter(
        Order.parent_order_sn == parent_order_sn
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到订单号 {parent_order_sn} 的订单"
        )
    
    # 获取店铺信息
    shop = db.query(Shop).filter(Shop.id == order.shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单关联的店铺不存在"
        )
    
    if not shop.access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺未配置访问令牌，无法调用Temu API"
        )
    
    # 创建Temu服务实例
    temu_service = TemuService(shop)
    standard_client = temu_service._get_standard_client()
    
    try:
        # 步骤1：获取发货信息（获取发货单ID）
        shipment_info = await standard_client.get_shipment_info(
            access_token=temu_service.access_token,
            parent_order_sn=parent_order_sn
        )
        
        # 从发货信息中提取发货单ID
        # 注意：根据Temu API文档，发货信息可能包含多个发货单，需要根据实际情况处理
        shipment_id = None
        if isinstance(shipment_info, dict):
            # 尝试多种可能的字段名
            shipment_id = (
                shipment_info.get('shipmentId') or
                shipment_info.get('shipment_id') or
                shipment_info.get('id')
            )
            # 如果发货信息中包含发货单列表，取第一个
            if not shipment_id and 'shipmentList' in shipment_info:
                shipment_list = shipment_info.get('shipmentList', [])
                if shipment_list and len(shipment_list) > 0:
                    shipment_id = (
                        shipment_list[0].get('shipmentId') or
                        shipment_list[0].get('shipment_id') or
                        shipment_list[0].get('id')
                    )
        
        if not shipment_id:
            # 如果无法从发货信息中获取发货单ID，返回发货信息
            return {
                "success": True,
                "message": "已获取发货信息，但未找到发货单ID",
                "shipment_info": shipment_info,
                "note": "可能需要使用其他方式获取发货单ID"
            }
        
        # 步骤2：使用发货单ID获取发货面单
        document_info = await standard_client.get_shipment_document(
            access_token=temu_service.access_token,
            shipment_id=str(shipment_id)
        )
        
        return {
            "success": True,
            "parent_order_sn": parent_order_sn,
            "shipment_id": shipment_id,
            "shipment_info": shipment_info,
            "document": document_info
        }
        
    except Exception as e:
        logger.error(f"获取发货面单失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取发货面单失败: {str(e)}"
        )
    finally:
        # 确保无论成功还是失败都关闭客户端
        await standard_client.close()

