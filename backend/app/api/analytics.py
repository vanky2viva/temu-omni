"""高级分析API - GMV表格、SKU销量、爆单榜、销量统计"""
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract, case
from decimal import Decimal

from app.core.database import get_db
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.shop import Shop

# 香港时区 (UTC+8)
HK_TIMEZONE = timezone(timedelta(hours=8))

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/gmv-table")
def get_gmv_table(
    shop_ids: Optional[List[int]] = Query(None),
    period_type: str = Query("month", regex="^(day|week|month)$"),
    periods: int = Query(12),
    db: Session = Depends(get_db)
):
    """
    获取GMV表格数据
    
    Args:
        shop_ids: 店铺ID列表
        period_type: 周期类型 (day/week/month)
        periods: 周期数量
    
    Returns:
        GMV表格数据
    """
    # 计算时间范围
    end_date = datetime.now()
    if period_type == "day":
        start_date = end_date - timedelta(days=periods)
    elif period_type == "week":
        start_date = end_date - timedelta(weeks=periods)
    else:  # month
        start_date = end_date - timedelta(days=periods * 30)
    
    # 构建查询条件
    filters = [
        Order.order_time >= start_date,
        Order.order_time <= end_date
    ]
    
    if shop_ids:
        filters.append(Order.shop_id.in_(shop_ids))
    
    # 根据周期类型分组
    if period_type == "day":
        group_by = func.date(Order.order_time)
        results = db.query(
            func.date(Order.order_time).label("period"),
            Shop.shop_name,
            func.count(Order.id).label("orders"),
            func.sum(Order.total_price).label("gmv"),
            func.sum(Order.total_cost).label("cost"),
            func.sum(Order.profit).label("profit"),
        ).join(Shop, Shop.id == Order.shop_id).filter(
            and_(*filters)
        ).group_by(
            func.date(Order.order_time), Shop.shop_name
        ).order_by(
            func.date(Order.order_time).desc()
        ).all()
        
    elif period_type == "week":
        results = db.query(
            extract('year', Order.order_time).label("year"),
            extract('week', Order.order_time).label("week"),
            Shop.shop_name,
            func.count(Order.id).label("orders"),
            func.sum(Order.total_price).label("gmv"),
            func.sum(Order.total_cost).label("cost"),
            func.sum(Order.profit).label("profit"),
        ).join(Shop, Shop.id == Order.shop_id).filter(
            and_(*filters)
        ).group_by(
            extract('year', Order.order_time),
            extract('week', Order.order_time),
            Shop.shop_name
        ).order_by(
            extract('year', Order.order_time).desc(),
            extract('week', Order.order_time).desc()
        ).all()
        
    else:  # month
        results = db.query(
            extract('year', Order.order_time).label("year"),
            extract('month', Order.order_time).label("month"),
            Shop.shop_name,
            func.count(Order.id).label("orders"),
            func.sum(Order.total_price).label("gmv"),
            func.sum(Order.total_cost).label("cost"),
            func.sum(Order.profit).label("profit"),
        ).join(Shop, Shop.id == Order.shop_id).filter(
            and_(*filters)
        ).group_by(
            extract('year', Order.order_time),
            extract('month', Order.order_time),
            Shop.shop_name
        ).order_by(
            extract('year', Order.order_time).desc(),
            extract('month', Order.order_time).desc()
        ).all()
    
    # 格式化结果
    table_data = []
    for row in results:
        if period_type == "day":
            period_str = row.period.strftime("%Y-%m-%d")
        elif period_type == "week":
            period_str = f"{int(row.year)}-W{int(row.week):02d}"
        else:
            period_str = f"{int(row.year)}-{int(row.month):02d}"
        
        table_data.append({
            "period": period_str,
            "shop": row.shop_name,
            "orders": row.orders or 0,
            "gmv": float(row.gmv or 0),
            "cost": float(row.cost or 0),
            "profit": float(row.profit or 0),
            "profit_margin": round((float(row.profit or 0) / float(row.gmv or 1)) * 100, 2) if row.gmv else 0
        })
    
    return {
        "period_type": period_type,
        "data": table_data
    }


@router.get("/sku-sales")
def get_sku_sales(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(20),
    db: Session = Depends(get_db)
):
    """
    获取SKU销量对比
    
    Args:
        shop_ids: 店铺ID列表
        start_date: 开始日期
        end_date: 结束日期
        limit: 返回数量
    
    Returns:
        SKU销量排行
    """
    # 默认查询最近30天
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # 构建查询条件
    filters = [
        Order.order_time >= start_date,
        Order.order_time <= end_date
    ]
    
    if shop_ids:
        filters.append(Order.shop_id.in_(shop_ids))
    
    # 按SKU分组统计
    results = db.query(
        Order.product_sku,
        Order.product_name,
        Shop.shop_name,
        func.sum(Order.quantity).label("total_quantity"),  # SKU销量：quantity之和
        func.count(func.distinct(Order.order_sn)).label("order_count"),  # 订单数：按订单号去重
        func.sum(Order.total_price).label("total_gmv"),
        func.sum(Order.profit).label("total_profit"),
    ).join(Shop, Shop.id == Order.shop_id).filter(
        and_(*filters),
        Order.product_sku.isnot(None)
    ).group_by(
        Order.product_sku, Order.product_name, Shop.shop_name
    ).order_by(
        func.sum(Order.quantity).desc()
    ).limit(limit).all()
    
    # 格式化结果
    sku_data = []
    for row in results:
        sku_data.append({
            "sku": row.product_sku,
            "product_name": row.product_name,
            "shop": row.shop_name,
            "quantity": int(row.total_quantity or 0),
            "orders": int(row.order_count or 0),
            "gmv": float(row.total_gmv or 0),
            "profit": float(row.total_profit or 0),
        })
    
    return sku_data


@router.get("/hot-seller-ranking")
def get_hot_seller_ranking(
    year: int = Query(None),
    month: int = Query(None),
    shop_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    获取爆单榜 - 负责人销量排行
    
    Args:
        year: 年份（默认当前年）
        month: 月份（默认当前月）
        shop_ids: 店铺ID列表
    
    Returns:
        负责人销量排行
    """
    # 默认为当前月
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month
    
    # 计算月份的开始和结束日期
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # 构建查询条件
    filters = [
        Order.order_time >= start_date,
        Order.order_time < end_date
    ]
    
    if shop_ids:
        filters.append(Order.shop_id.in_(shop_ids))
    
    # 按负责人分组统计
    results = db.query(
        Product.manager,
        Shop.shop_name,
        func.sum(Order.quantity).label("total_quantity"),  # SKU销量：quantity之和
        func.count(func.distinct(Order.order_sn)).label("order_count"),  # 订单数：按订单号去重
        func.sum(Order.total_price).label("total_gmv"),
        func.sum(Order.profit).label("total_profit"),
    ).join(
        Product, Product.id == Order.product_id
    ).join(
        Shop, Shop.id == Order.shop_id
    ).filter(
        and_(*filters),
        Product.manager.isnot(None)
    ).group_by(
        Product.manager, Shop.shop_name
    ).order_by(
        func.sum(Order.total_price).desc()
    ).all()
    
    # 格式化结果
    ranking_data = []
    rank = 1
    for row in results:
        ranking_data.append({
            "rank": rank,
            "manager": row.manager,
            "shop": row.shop_name,
            "quantity": int(row.total_quantity or 0),
            "orders": int(row.order_count or 0),
            "gmv": float(row.total_gmv or 0),
            "profit": float(row.total_profit or 0),
            "avg_order_value": round(float(row.total_gmv or 0) / max(int(row.order_count or 1), 1), 2)
        })
        rank += 1
    
    return {
        "year": year,
        "month": month,
        "ranking": ranking_data
    }


@router.get("/manager-sku-details")
def get_manager_sku_details(
    manager: str = Query(...),
    year: int = Query(None),
    month: int = Query(None),
    shop_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    获取负责人的SKU销售详情
    
    Args:
        manager: 负责人姓名
        year: 年份
        month: 月份
        shop_ids: 店铺ID列表
    
    Returns:
        该负责人负责的所有SKU的销售数据
    """
    # 默认为当前月
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month
    
    # 计算月份的开始和结束日期
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # 构建查询条件
    filters = [
        Order.order_time >= start_date,
        Order.order_time < end_date,
        Product.manager == manager
    ]
    
    if shop_ids:
        filters.append(Order.shop_id.in_(shop_ids))
    
    # 按SKU分组统计
    results = db.query(
        Product.sku,
        Product.product_name,
        Shop.shop_name,
        func.sum(Order.quantity).label("total_quantity"),  # SKU销量：quantity之和
        func.count(func.distinct(Order.order_sn)).label("order_count"),  # 订单数：按订单号去重
        func.sum(Order.total_price).label("total_gmv"),
        func.sum(Order.profit).label("total_profit"),
    ).join(
        Product, Product.id == Order.product_id
    ).join(
        Shop, Shop.id == Order.shop_id
    ).filter(
        and_(*filters)
    ).group_by(
        Product.sku, Product.product_name, Shop.shop_name
    ).order_by(
        func.sum(Order.total_price).desc()
    ).all()
    
    # 格式化结果
    sku_details = []
    for row in results:
        sku_details.append({
            "sku": row.sku,
            "product_name": row.product_name,
            "shop": row.shop_name,
            "quantity": int(row.total_quantity or 0),
            "orders": int(row.order_count or 0),
            "gmv": float(row.total_gmv or 0),
            "profit": float(row.total_profit or 0),
        })
    
    return sku_details


# ==================== 销量统计 API ====================

def get_hk_now() -> datetime:
    """获取香港当前时间"""
    return datetime.now(HK_TIMEZONE)


def build_sales_filters(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    shop_ids: Optional[List[int]] = None,
    manager: Optional[str] = None,
    region: Optional[str] = None,
    sku_search: Optional[str] = None,
):
    """构建销量统计的查询条件
    
    统计规则：
    - 有效订单：只统计状态为'已发货'（SHIPPED）、'待发货'（PROCESSING）、'已签收'（DELIVERED）的订单
    - 注意：'平台处理中'（映射为PAID）不计入销量统计
    - 订单量口径：每个不同的订单号为一单
    - SKU销量：每一行乘以应履约件数（quantity）为SKU的销量
    """
    filters = []
    
    # 订单状态筛选：只统计有效订单（已发货、待发货、已签收）
    # 排除：平台处理中（PAID）、待支付（PENDING）、已取消（CANCELLED）、已退款（REFUNDED）等
    filters.append(Order.status.in_([
        OrderStatus.PROCESSING,  # 待发货 - 计入统计
        OrderStatus.SHIPPED,     # 已发货 - 计入统计
        OrderStatus.DELIVERED    # 已签收 - 计入统计
    ]))
    
    # 时间筛选
    if start_date:
        filters.append(Order.order_time >= start_date)
    if end_date:
        filters.append(Order.order_time <= end_date)
    
    # 店铺筛选
    if shop_ids:
        filters.append(Order.shop_id.in_(shop_ids))
    
    # 负责人筛选（通过 product_sku 关联）
    if manager:
        # 先找到该负责人的所有商品SKU
        product_skus = db.query(Product.sku).filter(
            Product.manager == manager,
            Product.sku.isnot(None)
        ).distinct().all()
        sku_list = [sku[0] for sku in product_skus if sku[0]]
        if sku_list:
            filters.append(Order.product_sku.in_(sku_list))
        else:
            # 如果没有找到商品，返回空结果
            filters.append(Order.id == -1)
    
    # 地区筛选（通过店铺的 region）
    if region:
        shop_ids_by_region = db.query(Shop.id).filter(
            Shop.region == region
        ).all()
        region_shop_ids = [sid[0] for sid in shop_ids_by_region]
        if region_shop_ids:
            filters.append(Order.shop_id.in_(region_shop_ids))
        else:
            filters.append(Order.id == -1)
    
    # SKU搜索
    if sku_search:
        filters.append(Order.product_sku.like(f"%{sku_search}%"))
    
    return filters


@router.get("/sales-overview")
def get_sales_overview(
    days: int = Query(30, description="统计天数，默认30天"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    manager: Optional[str] = Query(None, description="负责人"),
    region: Optional[str] = Query(None, description="地区"),
    sku_search: Optional[str] = Query(None, description="SKU搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取销量统计总览
    
    Returns:
        - 总销量（件数）
        - 总订单数
        - GMV（预留，暂无数据）
        - 利润（预留）
        - 按天的趋势数据
        - 按店铺分组的趋势数据
    """
    # 计算时间范围（香港时区）
    end_date = get_hk_now()
    start_date = end_date - timedelta(days=days)
    
    # 构建查询条件
    filters = build_sales_filters(
        db, start_date, end_date, shop_ids, manager, region, sku_search
    )
    
    # 总销量和总订单数
    # 总销量：所有行的quantity之和
    # 总订单数：不同的订单号数量（每个订单号为一单）
    total_stats = db.query(
        func.sum(Order.quantity).label("total_quantity"),
        func.count(func.distinct(Order.order_sn)).label("total_orders"),  # 按订单号去重统计
    ).filter(and_(*filters)).first()
    
    # 按天统计趋势
    # 销量：quantity之和
    # 订单数：不同的订单号数量（按订单号去重）
    daily_trends = db.query(
        func.date(Order.order_time).label("date"),
        func.sum(Order.quantity).label("quantity"),
        func.count(func.distinct(Order.order_sn)).label("orders"),  # 按订单号去重统计
    ).filter(and_(*filters)).group_by(
        func.date(Order.order_time)
    ).order_by(
        func.date(Order.order_time)
    ).all()
    
    # 按店铺统计趋势
    # 销量：quantity之和
    # 订单数：不同的订单号数量（按订单号去重）
    shop_trends = db.query(
        func.date(Order.order_time).label("date"),
        Shop.shop_name.label("shop_name"),
        func.sum(Order.quantity).label("quantity"),
        func.count(func.distinct(Order.order_sn)).label("orders"),  # 按订单号去重统计
    ).join(
        Shop, Shop.id == Order.shop_id
    ).filter(and_(*filters)).group_by(
        func.date(Order.order_time), Shop.shop_name
    ).order_by(
        func.date(Order.order_time), Shop.shop_name
    ).all()
    
    # 格式化返回数据
    daily_data = [
        {
            "date": str(trend.date),
            "quantity": int(trend.quantity or 0),
            "orders": int(trend.orders or 0),
        }
        for trend in daily_trends
    ]
    
    # 按店铺分组日趋势数据
    shop_daily_data = {}
    for trend in shop_trends:
        date_str = str(trend.date)
        shop_name = trend.shop_name
        if shop_name not in shop_daily_data:
            shop_daily_data[shop_name] = []
        shop_daily_data[shop_name].append({
            "date": date_str,
            "quantity": int(trend.quantity or 0),
            "orders": int(trend.orders or 0),
        })
    
    return {
        "total_quantity": int(total_stats.total_quantity or 0),
        "total_orders": int(total_stats.total_orders or 0),
        "total_gmv": None,  # 预留，暂无数据
        "total_profit": None,  # 预留，暂无数据
        "daily_trends": daily_data,
        "shop_trends": shop_daily_data,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        }
    }


@router.get("/sku-sales-ranking")
def get_sku_sales_ranking(
    days: int = Query(30, description="统计天数，默认30天"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    manager: Optional[str] = Query(None, description="负责人"),
    region: Optional[str] = Query(None, description="地区"),
    sku_search: Optional[str] = Query(None, description="SKU搜索关键词"),
    limit: int = Query(100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取SKU销量排行
    
    通过 product_sku 关联订单和商品表
    """
    # 计算时间范围（香港时区）
    end_date = get_hk_now()
    start_date = end_date - timedelta(days=days)
    
    # 构建查询条件
    filters = build_sales_filters(
        db, start_date, end_date, shop_ids, manager, region, sku_search
    )
    
    # SKU销量统计逻辑：
    # 1. 直接从订单表按product_sku分组统计（避免关联商品表导致重复计算）
    # 2. 然后关联商品表获取商品信息（商品名称、负责人），使用DISTINCT避免重复计算
    # SKU销量 = quantity之和
    
    # 先统计有product_sku的订单（直接从订单表统计，不关联商品表）
    sku_stats = db.query(
        Order.product_sku.label("sku"),
        func.max(Order.product_name).label("product_name_from_order"),
        func.sum(Order.quantity).label("total_quantity"),
        func.count(func.distinct(Order.order_sn)).label("order_count"),
    ).filter(
        and_(*filters),
        Order.product_sku.isnot(None),
        Order.product_sku != ''
    ).group_by(
        Order.product_sku
    ).subquery()
    
    # 获取商品信息（通过product_name和shop_id关联，每个SKU可能对应多个商品记录，取其中一个）
    # 使用DISTINCT去重，只取每个SKU的一条商品信息
    product_info = db.query(
        Order.product_sku,
        func.max(Product.product_name).label("product_name"),
        func.max(Product.manager).label("manager"),
        # func.max(Product.spu_id).label("spu_id"),  # 等数据库迁移后再启用
    ).outerjoin(
        Product, and_(
            Order.product_name == Product.product_name,
            Order.shop_id == Product.shop_id
        )
    ).filter(
        and_(*filters),
        Order.product_sku.isnot(None),
        Order.product_sku != ''
    ).group_by(
        Order.product_sku
    ).subquery()
    
    # 合并统计数据
    results = db.query(
        sku_stats.c.sku.label("sku"),
        func.max(sku_stats.c.product_name_from_order).label("product_name_from_order"),
        func.max(product_info.c.product_name).label("product_name"),
        func.max(product_info.c.manager).label("manager"),
        sku_stats.c.total_quantity.label("total_quantity"),
        sku_stats.c.order_count.label("order_count"),
    ).outerjoin(
        product_info, sku_stats.c.sku == product_info.c.product_sku
    ).group_by(
        sku_stats.c.sku,
        sku_stats.c.total_quantity,
        sku_stats.c.order_count
    ).order_by(
        sku_stats.c.total_quantity.desc()
    ).limit(limit).all()
    
    # 格式化结果
    ranking = []
    for idx, row in enumerate(results, 1):
        # 优先使用从商品表获取的商品名称，如果没有则使用订单中的商品名称
        product_name = row.product_name or row.product_name_from_order or '-'
        ranking.append({
            "rank": idx,
            "sku": row.sku,
            "product_name": product_name,
            "manager": row.manager or '-',
            "spu_id": None,  # 等数据库迁移后再启用
            "quantity": int(row.total_quantity or 0),
            "orders": int(row.order_count or 0),
            "gmv": None,  # 预留
            "profit": None,  # 预留
        })
    
    return {
        "ranking": ranking,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        }
    }


@router.get("/spu-sales-ranking")
def get_spu_sales_ranking(
    days: int = Query(30, description="统计天数，默认30天"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    manager: Optional[str] = Query(None, description="负责人"),
    region: Optional[str] = Query(None, description="地区"),
    sku_search: Optional[str] = Query(None, description="SKU搜索关键词"),
    limit: int = Query(100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取SPU销量排行（汇总所有相关SKU的销量）
    """
    # 计算时间范围（香港时区）
    end_date = get_hk_now()
    start_date = end_date - timedelta(days=days)
    
    # 构建查询条件
    filters = build_sales_filters(
        db, start_date, end_date, shop_ids, manager, region, sku_search
    )
    
    # SPU销量统计逻辑：
    # 1. 如果订单表有spu_id，直接使用订单表的spu_id分组统计（避免关联商品表导致重复计算）
    # 2. 如果订单表没有spu_id，通过商品表关联获取spu_id，但需要去重避免重复计算
    # SPU销量 = 该SPU下所有SKU的quantity之和
    
    # 先统计有spu_id的订单（直接从订单表统计，不关联商品表）
    orders_with_spu = db.query(
        Order.spu_id.label("spu_id"),
        func.sum(Order.quantity).label("total_quantity"),
        func.count(func.distinct(Order.order_sn)).label("order_count"),
        func.count(func.distinct(Order.product_sku)).label("sku_count"),
    ).filter(
        and_(*filters),
        Order.spu_id.isnot(None),
        Order.spu_id != ''
    ).group_by(
        Order.spu_id
    ).subquery()
    
    # 获取商品信息（通过spu_id关联）
    product_info = db.query(
        Product.spu_id,
        func.max(Product.product_name).label("product_name"),
        func.max(Product.manager).label("manager"),
    ).filter(
        Product.spu_id.isnot(None),
        Product.spu_id != ''
    ).group_by(
        Product.spu_id
    ).subquery()
    
    # 合并统计数据（有spu_id的订单）
    # 注意：orders_with_spu已经是按spu_id分组后的结果
    # 但SQL要求在SELECT中使用非聚合字段时必须GROUP BY
    results = db.query(
        orders_with_spu.c.spu_id.label("spu_id"),
        func.max(product_info.c.product_name).label("product_name"),
        func.max(product_info.c.manager).label("manager"),
        func.max(orders_with_spu.c.total_quantity).label("total_quantity"),  # 使用MAX避免GROUP BY错误
        func.max(orders_with_spu.c.order_count).label("order_count"),  # 使用MAX避免GROUP BY错误
        func.max(orders_with_spu.c.sku_count).label("sku_count"),  # 使用MAX避免GROUP BY错误
    ).outerjoin(
        product_info, orders_with_spu.c.spu_id == product_info.c.spu_id
    ).group_by(
        orders_with_spu.c.spu_id  # 必须GROUP BY才能使用非聚合字段
    ).order_by(
        func.max(orders_with_spu.c.total_quantity).desc()
    ).limit(limit).all()
    
    # 格式化结果
    ranking = []
    for idx, row in enumerate(results, 1):
        ranking.append({
            "rank": idx,
            "spu_id": row.spu_id,
            "product_name": row.product_name or '-',
            "manager": row.manager or '-',
            "sku_count": int(row.sku_count or 0),
            "quantity": int(row.total_quantity or 0),
            "orders": int(row.order_count or 0),
            "gmv": None,  # 预留
            "profit": None,  # 预留
        })
    
    return {
        "ranking": ranking,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        }
    }


@router.get("/manager-sales")
def get_manager_sales(
    days: int = Query(30, description="统计天数，默认30天"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    manager: Optional[str] = Query(None, description="指定负责人（不指定则返回所有负责人）"),
    region: Optional[str] = Query(None, description="地区"),
    db: Session = Depends(get_db)
):
    """
    获取负责人销量统计
    
    包含：
    - 订单数
    - 总销量
    - GMV（预留）
    - 利润（预留）
    - 按天的趋势数据
    """
    # 计算时间范围（香港时区）
    end_date = get_hk_now()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询条件（不含负责人筛选）
    base_filters = build_sales_filters(
        db, start_date, end_date, shop_ids, None, region, None
    )
    
    # 负责人销量统计逻辑：
    # 1. 先从订单表统计每个订单的负责人（通过product_name和shop_id关联商品表获取负责人）
    # 2. 按负责人分组统计总销量和订单数，避免关联商品表导致重复计算
    # 注意：一个订单可能对应多个商品记录（商品名称相似），需要去重避免重复计算
    
    # 先统计订单数据（按订单号+商品名称+店铺分组，获取每个订单的销量和负责人）
    order_stats = db.query(
        Order.order_sn,
        Order.product_name,
        Order.shop_id,
        Order.quantity,
        func.max(Product.manager).label("manager"),  # 取一个负责人（如果有多个匹配的商品记录）
    ).outerjoin(
        Product, and_(
            Order.product_name == Product.product_name,
            Order.shop_id == Product.shop_id
        )
    ).filter(
        and_(*base_filters),
        or_(
            Product.manager.isnot(None),
            Product.manager != ''
        )
    ).group_by(
        Order.order_sn,
        Order.product_name,
        Order.shop_id,
        Order.quantity
    ).subquery()
    
    # 如果指定了负责人，添加筛选
    if manager:
        order_stats = db.query(
            order_stats.c.order_sn,
            order_stats.c.product_name,
            order_stats.c.shop_id,
            order_stats.c.quantity,
            order_stats.c.manager,
        ).filter(
            order_stats.c.manager == manager
        ).subquery()
    
    # 按负责人分组统计
    results = db.query(
        order_stats.c.manager.label("manager"),
        func.sum(order_stats.c.quantity).label("total_quantity"),  # 总销量
        func.count(func.distinct(order_stats.c.order_sn)).label("order_count"),  # 订单数：按订单号去重
    ).filter(
        order_stats.c.manager.isnot(None),
        order_stats.c.manager != ''
    ).group_by(
        order_stats.c.manager
    ).order_by(
        func.sum(order_stats.c.quantity).desc()
    ).all()
    
    # 按天统计趋势（每个负责人每日的订单量曲线）
    # 使用order_stats子查询避免重复计算
    daily_trends_data = {}
    if manager:
        # 如果指定了负责人，只统计该负责人的日趋势
        daily_trends = db.query(
            func.date(Order.order_time).label("date"),
            func.count(func.distinct(Order.order_sn)).label("orders"),  # 每日订单数（去重）
        ).outerjoin(
            Product, and_(
                Order.product_name == Product.product_name,
                Order.shop_id == Product.shop_id
            )
        ).filter(
            and_(*base_filters),
            Product.manager == manager,
            or_(
                Product.manager.isnot(None),
                Product.manager != ''
            )
        ).group_by(
            func.date(Order.order_time)
        ).order_by(
            func.date(Order.order_time)
        ).all()
        
        daily_trends_data = {
            manager: [
                {
                    "date": str(trend.date),
                    "orders": int(trend.orders or 0),
                }
                for trend in daily_trends
            ]
        }
    else:
        # 如果没指定负责人，统计所有负责人的日趋势（每日订单数）
        all_managers = [r.manager for r in results]
        for mgr in all_managers:
            daily_trends = db.query(
                func.date(Order.order_time).label("date"),
                func.count(func.distinct(Order.order_sn)).label("orders"),  # 每日订单数（去重）
            ).outerjoin(
                Product, and_(
                    Order.product_name == Product.product_name,
                    Order.shop_id == Product.shop_id
                )
            ).filter(
                and_(*base_filters),
                Product.manager == mgr,
                or_(
                    Product.manager.isnot(None),
                    Product.manager != ''
                )
            ).group_by(
                func.date(Order.order_time)
            ).order_by(
                func.date(Order.order_time)
            ).all()
            
            daily_trends_data[mgr] = [
                {
                    "date": str(trend.date),
                    "orders": int(trend.orders or 0),
                }
                for trend in daily_trends
            ]
    
    # 格式化结果
    manager_data = []
    for row in results:
        manager_data.append({
            "manager": row.manager,
            "total_quantity": int(row.total_quantity or 0),
            "order_count": int(row.order_count or 0),
            "total_gmv": None,  # 预留
            "total_profit": None,  # 预留
            "daily_trends": daily_trends_data.get(row.manager, [])
        })
    
    return {
        "managers": manager_data,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        }
    }
