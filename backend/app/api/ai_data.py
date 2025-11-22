"""
AI模块数据访问API - 为AI模块提供统一、全面的数据访问接口

本模块提供专门为AI模块设计的数据访问接口，确保AI能获取到正确、全面的数据。
所有接口都遵循统一的统计规则（见 API_STATISTICS_STANDARD.md）。
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text, or_
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductCost
from app.models.shop import Shop
from app.models.payout import Payout
from app.services.unified_statistics import UnifiedStatisticsService
from app.utils.currency import CurrencyConverter

router = APIRouter(prefix="/ai-data", tags=["AI Data"])


class SalesOverviewResponse(BaseModel):
    """销量总览响应"""
    total_orders: int
    total_quantity: int
    total_gmv: float
    total_cost: float
    total_profit: float
    profit_margin: float
    period: Dict[str, Any]


class SKUStatisticsResponse(BaseModel):
    """SKU统计响应"""
    sku: str
    product_name: str
    manager: Optional[str]
    total_quantity: int
    order_count: int
    total_gmv: float
    total_profit: float


class ManagerStatisticsResponse(BaseModel):
    """负责人统计响应"""
    manager: str
    total_quantity: int
    order_count: int
    total_gmv: float
    total_profit: float


@router.get("/sales-overview", response_model=SalesOverviewResponse)
def get_ai_sales_overview(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: Optional[int] = Query(None, description="最近N天（如果未提供日期范围）"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    manager: Optional[str] = Query(None, description="负责人"),
    region: Optional[str] = Query(None, description="地区"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取销量总览数据（AI模块专用）
    
    遵循统一的统计规则：
    - 订单状态：只统计 PROCESSING, SHIPPED, DELIVERED
    - 订单数：按父订单去重统计
    - 不过滤订单金额
    
    Returns:
        销量总览数据
    """
    # 解析日期范围
    start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
        start_date, end_date, days
    )
    
    # 构建过滤条件
    filters = UnifiedStatisticsService.build_base_filters(
        db, start_dt, end_dt, shop_ids, manager, region, None
    )
    
    # 计算统计数据
    stats = UnifiedStatisticsService.calculate_order_statistics(db, filters)
    
    # 计算实际使用的天数
    if start_dt and end_dt:
        actual_days = (end_dt - start_dt).days + 1
    else:
        actual_days = None
    
    # 计算利润率
    profit_margin = (stats['total_profit'] / stats['total_gmv'] * 100) if stats['total_gmv'] > 0 else 0
    
    return {
        "total_orders": stats['order_count'],
        "total_quantity": stats['total_quantity'],
        "total_gmv": round(stats['total_gmv'], 2),
        "total_cost": round(stats['total_cost'], 2),
        "total_profit": round(stats['total_profit'], 2),
        "profit_margin": round(profit_margin, 2),
        "period": {
            "start_date": start_dt.isoformat() if start_dt else None,
            "end_date": end_dt.isoformat() if end_dt else None,
            "days": actual_days
        }
    }


@router.get("/sku-statistics", response_model=List[SKUStatisticsResponse])
def get_ai_sku_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: Optional[int] = Query(None, description="最近N天"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    manager: Optional[str] = Query(None, description="负责人"),
    region: Optional[str] = Query(None, description="地区"),
    limit: int = Query(100, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取SKU统计数据（AI模块专用）
    
    返回按SKU ID（Product.product_id）分组的统计数据。
    
    Returns:
        SKU统计列表
    """
    # 解析日期范围
    start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
        start_date, end_date, days
    )
    
    # 构建过滤条件
    filters = UnifiedStatisticsService.build_base_filters(
        db, start_dt, end_dt, shop_ids, manager, region, None
    )
    
    # 获取SKU统计
    sku_stats = UnifiedStatisticsService.get_sku_statistics(db, filters, limit)
    
    return sku_stats


@router.get("/manager-statistics", response_model=List[ManagerStatisticsResponse])
def get_ai_manager_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: Optional[int] = Query(None, description="最近N天"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    region: Optional[str] = Query(None, description="地区"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取负责人统计数据（AI模块专用）
    
    返回按负责人分组的统计数据。
    
    Returns:
        负责人统计列表
    """
    # 解析日期范围
    start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
        start_date, end_date, days
    )
    
    # 构建过滤条件（不含负责人筛选）
    filters = UnifiedStatisticsService.build_base_filters(
        db, start_dt, end_dt, shop_ids, None, region, None
    )
    
    # 获取负责人统计
    manager_stats = UnifiedStatisticsService.get_manager_statistics(db, filters)
    
    return manager_stats


@router.get("/data-summary")
def get_ai_data_summary(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: Optional[int] = Query(7, description="最近N天（默认7天）"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据摘要（AI模块专用）
    
    返回全面的数据摘要，包括：
    - 销量总览
    -  top SKU
    -  top 负责人
    - 趋势数据
    
    Returns:
        数据摘要字典
    """
    # 解析日期范围
    start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
        start_date, end_date, days
    )
    
    # 构建过滤条件
    filters = UnifiedStatisticsService.build_base_filters(
        db, start_dt, end_dt, shop_ids, None, None, None
    )
    
    # 获取销量总览
    overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
    
    # 获取top SKU（前10）
    top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
    
    # 获取top 负责人（前10）
    top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
    
    # 计算利润率
    profit_margin = (overview['total_profit'] / overview['total_gmv'] * 100) if overview['total_gmv'] > 0 else 0
    
    return {
        "overview": {
            "total_orders": overview['order_count'],
            "total_quantity": overview['total_quantity'],
            "total_gmv": round(overview['total_gmv'], 2),
            "total_cost": round(overview['total_cost'], 2),
            "total_profit": round(overview['total_profit'], 2),
            "profit_margin": round(profit_margin, 2),
        },
        "top_skus": top_skus,
        "top_managers": top_managers,
        "period": {
            "start_date": start_dt.isoformat() if start_dt else None,
            "end_date": end_dt.isoformat() if end_dt else None,
        }
    }


class CollectionDetailResponse(BaseModel):
    """回款详细数据响应"""
    order_sn: str
    parent_order_sn: Optional[str]
    shop_name: str
    product_name: str
    product_sku: str
    quantity: int
    total_price: float
    delivery_time: Optional[str]
    collection_date: str
    collection_amount: float
    order_status: str


class OrderDetailResponse(BaseModel):
    """订单详细数据响应"""
    id: int
    order_sn: str
    parent_order_sn: Optional[str]
    temu_order_id: Optional[str]
    shop_id: int
    shop_name: Optional[str]
    product_id: Optional[int]
    product_name: Optional[str]
    product_sku: Optional[str]
    spu_id: Optional[str]
    quantity: int
    unit_price: float
    total_price: float
    currency: str
    unit_cost: Optional[float]
    total_cost: Optional[float]
    profit: Optional[float]
    status: str
    order_time: str
    payment_time: Optional[str]
    shipping_time: Optional[str]
    delivery_time: Optional[str]
    expect_ship_latest_time: Optional[str]
    customer_id: Optional[str]
    shipping_country: Optional[str]
    shipping_city: Optional[str]
    shipping_province: Optional[str]
    shipping_postal_code: Optional[str]


class ProductCostDetailResponse(BaseModel):
    """商品成本详细数据响应"""
    product_id: int
    product_name: str
    sku: str
    product_id_temu: Optional[str]
    current_cost: Optional[float]
    current_cost_currency: Optional[str]
    current_cost_effective_from: Optional[str]
    cost_history: List[Dict[str, Any]]


class CollectionStatisticsResponse(BaseModel):
    """回款统计数据响应"""
    summary: Dict[str, Any]
    table_data: List[Dict[str, Any]]
    chart_data: Dict[str, Any]
    period: Dict[str, Any]


@router.get("/collection-details", response_model=List[CollectionDetailResponse])
def get_ai_collection_details(
    start_date: Optional[str] = Query(None, description="开始日期（回款日期范围，YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（回款日期范围，YYYY-MM-DD）"),
    days: Optional[int] = Query(30, description="最近N天（如果未提供日期范围）"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    order_sn: Optional[str] = Query(None, description="订单号（精确匹配）"),
    limit: int = Query(1000, ge=1, le=5000, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取回款详细数据（最小粒度，按订单级别）（AI模块专用）
    
    回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额
    注意：价格已统一存储为CNY，直接使用total_price字段
    
    Returns:
        回款详细数据列表，包含每个订单的回款信息
    """
    # 回款日期 = delivery_time + 8天
    collection_date_expr = func.date(Order.delivery_time + text("INTERVAL '8 days'"))
    
    # 确定日期范围（回款日期范围）
    if not end_date:
        # 查找最新的签收日期
        latest_delivery_query = db.query(func.max(Order.delivery_time)).filter(
            Order.status == OrderStatus.DELIVERED,
            Order.delivery_time.isnot(None)
        )
        if shop_ids:
            latest_delivery_query = latest_delivery_query.filter(Order.shop_id.in_(shop_ids))
        
        latest_delivery = latest_delivery_query.scalar()
        
        if latest_delivery:
            latest_delivery_date = latest_delivery.date() if isinstance(latest_delivery, datetime) else latest_delivery
            end_date_dt = datetime.combine(latest_delivery_date + timedelta(days=15), datetime.min.time())
        else:
            end_date_dt = datetime.now() + timedelta(days=7)
    else:
        try:
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_dt = end_date_dt.replace(hour=23, minute=59, second=59)
        except ValueError:
            end_date_dt = datetime.now() + timedelta(days=7)
    
    if not start_date:
        start_date_dt = end_date_dt - timedelta(days=days or 30)
    else:
        try:
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            start_date_dt = end_date_dt - timedelta(days=days or 30)
    
    # 构建查询条件
    filters = [
        Order.status == OrderStatus.DELIVERED,
        Order.delivery_time.isnot(None),
        collection_date_expr >= start_date_dt.date(),
        collection_date_expr <= end_date_dt.date()
    ]
    
    if shop_ids:
        filters.append(Order.shop_id.in_(shop_ids))
    
    if order_sn:
        filters.append(
            or_(
                Order.order_sn == order_sn,
                Order.parent_order_sn == order_sn
            )
        )
    
    # 查询订单详细数据
    results = db.query(
        Order.order_sn,
        Order.parent_order_sn,
        Shop.shop_name,
        Order.product_name,
        Order.product_sku,
        Order.quantity,
        Order.total_price,
        Order.delivery_time,
        collection_date_expr.label("collection_date"),
        Order.status
    ).join(
        Shop, Shop.id == Order.shop_id
    ).filter(
        and_(*filters)
    ).order_by(
        collection_date_expr.desc(),
        Order.order_time.desc()
    ).limit(limit).all()
    
    # 转换为响应格式
    collection_details = []
    for row in results:
        # 价格已统一存储为CNY，直接使用
        collection_amount = float(row.total_price or 0)
        
        collection_details.append({
            "order_sn": row.order_sn,
            "parent_order_sn": row.parent_order_sn,
            "shop_name": row.shop_name,
            "product_name": row.product_name or '',
            "product_sku": row.product_sku or '',
            "quantity": row.quantity or 0,
            "total_price": float(row.total_price or 0),
            "delivery_time": row.delivery_time.isoformat() if row.delivery_time else None,
            "collection_date": row.collection_date.strftime("%Y-%m-%d") if row.collection_date else '',
            "collection_amount": round(collection_amount, 2),
            "order_status": row.status.value if row.status else ''
        })
    
    return collection_details


@router.get("/order-details", response_model=List[OrderDetailResponse])
def get_ai_order_details(
    start_date: Optional[str] = Query(None, description="开始日期（订单时间，YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（订单时间，YYYY-MM-DD）"),
    days: Optional[int] = Query(None, description="最近N天（如果未提供日期范围）"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    status_filters: Optional[List[OrderStatus]] = Query(None, description="订单状态列表"),
    order_sn: Optional[str] = Query(None, description="订单号（模糊匹配）"),
    product_sku: Optional[str] = Query(None, description="商品SKU（模糊匹配）"),
    product_name: Optional[str] = Query(None, description="商品名称（模糊匹配）"),
    limit: int = Query(500, ge=1, le=2000, description="返回数量限制"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单详细数据（AI模块专用）
    
    返回包含所有订单字段和关联信息的详细数据。
    
    Returns:
        订单详细数据列表
    """
    # 解析日期范围
    start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
        start_date, end_date, days
    )
    
    # 构建查询
    query = db.query(
        Order,
        Shop.shop_name
    ).outerjoin(
        Shop, Shop.id == Order.shop_id
    )
    
    # 应用过滤条件
    filters = []
    
    if start_dt:
        filters.append(Order.order_time >= start_dt)
    
    if end_dt:
        filters.append(Order.order_time <= end_dt)
    
    if shop_ids:
        filters.append(Order.shop_id.in_(shop_ids))
    
    if status_filters:
        filters.append(Order.status.in_(status_filters))
    
    if order_sn:
        filters.append(
            or_(
                Order.order_sn.ilike(f"%{order_sn}%"),
                Order.parent_order_sn.ilike(f"%{order_sn}%")
            )
        )
    
    if product_sku:
        filters.append(Order.product_sku.ilike(f"%{product_sku}%"))
    
    if product_name:
        filters.append(Order.product_name.ilike(f"%{product_name}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # 排序和分页
    orders = query.order_by(Order.order_time.desc()).offset(skip).limit(limit).all()
    
    # 转换为响应格式
    order_details = []
    for order, shop_name in orders:
        order_details.append({
            "id": order.id,
            "order_sn": order.order_sn,
            "parent_order_sn": order.parent_order_sn,
            "temu_order_id": order.temu_order_id,
            "shop_id": order.shop_id,
            "shop_name": shop_name,
            "product_id": order.product_id,
            "product_name": order.product_name,
            "product_sku": order.product_sku,
            "spu_id": order.spu_id,
            "quantity": order.quantity or 0,
            "unit_price": float(order.unit_price or 0),
            "total_price": float(order.total_price or 0),
            "currency": order.currency or 'USD',
            "unit_cost": float(order.unit_cost) if order.unit_cost else None,
            "total_cost": float(order.total_cost) if order.total_cost else None,
            "profit": float(order.profit) if order.profit else None,
            "status": order.status.value if order.status else '',
            "order_time": order.order_time.isoformat() if order.order_time else '',
            "payment_time": order.payment_time.isoformat() if order.payment_time else None,
            "shipping_time": order.shipping_time.isoformat() if order.shipping_time else None,
            "delivery_time": order.delivery_time.isoformat() if order.delivery_time else None,
            "expect_ship_latest_time": order.expect_ship_latest_time.isoformat() if order.expect_ship_latest_time else None,
            "customer_id": order.customer_id,
            "shipping_country": order.shipping_country,
            "shipping_city": order.shipping_city,
            "shipping_province": order.shipping_province,
            "shipping_postal_code": order.shipping_postal_code,
        })
    
    return order_details


@router.get("/product-cost-details", response_model=List[ProductCostDetailResponse])
def get_ai_product_cost_details(
    product_id: Optional[int] = Query(None, description="商品ID（数据库ID）"),
    product_id_temu: Optional[str] = Query(None, description="Temu商品ID（product_id字段）"),
    sku: Optional[str] = Query(None, description="商品SKU（模糊匹配）"),
    product_name: Optional[str] = Query(None, description="商品名称（模糊匹配）"),
    include_history: bool = Query(True, description="是否包含历史成本记录"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取商品成本详细数据（AI模块专用）
    
    返回商品成本信息，包括当前成本和历史成本记录。
    
    Returns:
        商品成本详细数据列表
    """
    # 构建查询
    query = db.query(Product)
    
    # 应用过滤条件
    filters = []
    
    if product_id:
        filters.append(Product.id == product_id)
    
    if product_id_temu:
        filters.append(Product.product_id == product_id_temu)
    
    if sku:
        filters.append(Product.sku.ilike(f"%{sku}%"))
    
    if product_name:
        filters.append(Product.product_name.ilike(f"%{product_name}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # 限制数量
    products = query.limit(limit).all()
    
    # 转换为响应格式
    cost_details = []
    for product in products:
        # 获取当前成本
        current_cost = db.query(ProductCost).filter(
            ProductCost.product_id == product.id,
            ProductCost.effective_to.is_(None)
        ).first()
        
        # 获取历史成本记录
        cost_history = []
        if include_history:
            history_costs = db.query(ProductCost).filter(
                ProductCost.product_id == product.id
            ).order_by(ProductCost.effective_from.desc()).all()
            
            for cost in history_costs:
                cost_history.append({
                    "cost_price": float(cost.cost_price or 0),
                    "currency": cost.currency or 'USD',
                    "effective_from": cost.effective_from.isoformat() if cost.effective_from else None,
                    "effective_to": cost.effective_to.isoformat() if cost.effective_to else None,
                    "notes": cost.notes,
                    "created_at": cost.created_at.isoformat() if cost.created_at else None,
                })
        
        cost_details.append({
            "product_id": product.id,
            "product_name": product.product_name or '',
            "sku": product.sku or '',
            "product_id_temu": product.product_id,
            "current_cost": float(current_cost.cost_price) if current_cost and current_cost.cost_price else None,
            "current_cost_currency": current_cost.currency if current_cost else None,
            "current_cost_effective_from": current_cost.effective_from.isoformat() if current_cost and current_cost.effective_from else None,
            "cost_history": cost_history,
        })
    
    return cost_details


@router.get("/collection-statistics", response_model=CollectionStatisticsResponse)
def get_ai_collection_statistics(
    start_date: Optional[str] = Query(None, description="开始日期（回款日期范围，YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（回款日期范围，YYYY-MM-DD）"),
    days: Optional[int] = Query(30, description="最近N天（如果未提供日期范围）"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取回款统计数据（AI模块专用）
    
    回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额
    返回按日期和店铺分组的回款统计数据，与财务管理页面使用的数据格式一致。
    
    Returns:
        回款统计数据，包含：
        - summary: 汇总信息（总回款金额、总订单数、店铺列表）
        - table_data: 表格数据（按日期和店铺分组的回款金额）
        - chart_data: 图表数据（日期列表和每个店铺的折线图数据）
        - period: 时间范围信息
    """
    from app.api.analytics import get_payment_collection
    from datetime import datetime as dt
    
    # 转换日期参数
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = dt.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = dt.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            pass
    
    # 调用analytics模块的接口（复用逻辑）
    result = get_payment_collection(
        shop_ids=shop_ids,
        start_date=start_dt,
        end_date=end_dt,
        days=days or 30,
        db=db,
        current_user=current_user
    )
    
    return result

