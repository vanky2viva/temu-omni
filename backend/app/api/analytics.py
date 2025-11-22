"""高级分析API - GMV表格、SKU销量、爆单榜、销量统计"""
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract, case, text
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.shop import Shop
from app.models.user import User
from app.utils.currency import CurrencyConverter

# 香港时区 (UTC+8)
HK_TIMEZONE = timezone(timedelta(hours=8))

router = APIRouter(prefix="/analytics", tags=["analytics"])

# 汇率转换辅助函数
def _convert_to_cny(column, usd_rate=None):
    """将金额列转换为CNY"""
    if usd_rate is None:
        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    return case(
        (Order.currency == 'USD', column * usd_rate),
        (Order.currency == 'CNY', column),
        else_=column * usd_rate
    )


@router.get("/gmv-table")
def get_gmv_table(
    shop_ids: Optional[List[int]] = Query(None),
    period_type: str = Query("month", regex="^(day|week|month)$"),
    periods: int = Query(12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    
    # 根据周期类型分组，统一转换为CNY
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    if period_type == "day":
        group_by = func.date(Order.order_time)
        results = db.query(
            func.date(Order.order_time).label("period"),
            Shop.shop_name,
            func.count(Order.id).label("orders"),
            func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("gmv"),
            func.sum(_convert_to_cny(Order.total_cost, usd_rate)).label("cost"),
            func.sum(_convert_to_cny(Order.profit, usd_rate)).label("profit"),
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
            func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("gmv"),
            func.sum(_convert_to_cny(Order.total_cost, usd_rate)).label("cost"),
            func.sum(_convert_to_cny(Order.profit, usd_rate)).label("profit"),
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
            func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("gmv"),
            func.sum(_convert_to_cny(Order.total_cost, usd_rate)).label("cost"),
            func.sum(_convert_to_cny(Order.profit, usd_rate)).label("profit"),
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    # 统一转换为CNY
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    results = db.query(
        Order.product_sku,
        Order.product_name,
        Shop.shop_name,
        func.sum(Order.quantity).label("total_quantity"),  # SKU销量：quantity之和
        func.count(func.distinct(Order.order_sn)).label("order_count"),  # 订单数：按订单号去重
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("total_gmv"),
        func.sum(_convert_to_cny(Order.profit, usd_rate)).label("total_profit"),
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    
    # 按负责人分组统计，统一转换为CNY
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    results = db.query(
        Product.manager,
        Shop.shop_name,
        func.sum(Order.quantity).label("total_quantity"),  # SKU销量：quantity之和
        func.count(func.distinct(Order.order_sn)).label("order_count"),  # 订单数：按订单号去重
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("total_gmv"),
        func.sum(_convert_to_cny(Order.profit, usd_rate)).label("total_profit"),
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
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).desc()
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    
    # 按SKU分组统计，统一转换为CNY
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    results = db.query(
        Product.sku,
        Product.product_name,
        Shop.shop_name,
        func.sum(Order.quantity).label("total_quantity"),  # SKU销量：quantity之和
        func.count(func.distinct(Order.order_sn)).label("order_count"),  # 订单数：按订单号去重
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("total_gmv"),
        func.sum(_convert_to_cny(Order.profit, usd_rate)).label("total_profit"),
    ).join(
        Product, Product.id == Order.product_id
    ).join(
        Shop, Shop.id == Order.shop_id
    ).filter(
        and_(*filters)
    ).group_by(
        Product.sku, Product.product_name, Shop.shop_name
    ).order_by(
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).desc()
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
    - 订单量口径：一个不重复的父订单号记为一单（如果parent_order_sn存在，使用parent_order_sn；否则使用order_sn）
    - 销售件数：子订单内商品数量累计（quantity之和）
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
    days: Optional[int] = Query(None, description="统计天数（如果未提供start_date和end_date则使用此参数，默认30天）"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    manager: Optional[str] = Query(None, description="负责人"),
    region: Optional[str] = Query(None, description="地区"),
    sku_search: Optional[str] = Query(None, description="SKU搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取销量统计总览
    
    统计口径：
    - 订单数：一个不重复的父订单号记为一单（如果parent_order_sn存在，使用parent_order_sn；否则使用order_sn）
    - 销售件数：子订单内商品数量累计（quantity之和）
    - 只统计有效订单（PROCESSING、SHIPPED、DELIVERED）
    - 如果没有提供日期范围，统计所有时间的订单（与订单列表页面保持一致）
    
    Returns:
        - 总销量（件数）：子订单内商品数量累计
        - 总订单数（按父订单号去重，只统计有效订单）
        - GMV（收入）：统一转换为CNY
        - 利润：统一转换为CNY
        - 按天的趋势数据
        - 按店铺分组的趋势数据
    """
    # 解析日期字符串
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            # 如果是日期格式，添加时间部分（设置为当天的开始时间）
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        # 转换为香港时区
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=HK_TIMEZONE)
        else:
            start_dt = start_dt.astimezone(HK_TIMEZONE)
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            # 如果是日期格式，添加时间部分（设置为当天的结束时间）
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # 设置为当天的23:59:59
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        # 转换为香港时区
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=HK_TIMEZONE)
        else:
            end_dt = end_dt.astimezone(HK_TIMEZONE)
    
    # 计算时间范围（香港时区）
    # 如果没有提供日期范围，不应用时间筛选（统计所有时间的订单）
    # 这样与订单列表页面的行为保持一致
    if start_dt and end_dt:
        # 如果提供了start_date和end_date，使用它们
        start_date = start_dt
        end_date = end_dt
    else:
        # 如果没有提供日期范围，不应用时间筛选（统计所有时间）
        # 注意：这里不设置start_date和end_date，让build_sales_filters不应用时间筛选
        start_date = None
        end_date = None
    
    # 构建查询条件
    filters = build_sales_filters(
        db, start_date, end_date, shop_ids, manager, region, sku_search
    )
    
    # 总销量、总订单数、GMV和利润
    # 总销量：所有行的quantity之和（子订单内商品数量累计）
    # 总订单数：按父订单号去重统计（一个不重复的父订单号记为一单）
    #   如果parent_order_sn存在，使用parent_order_sn；否则使用order_sn
    # GMV和利润：统一转换为CNY
    from sqlalchemy import case
    parent_order_key = case(
        (Order.parent_order_sn.isnot(None), Order.parent_order_sn),
        else_=Order.order_sn
    )
    
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    total_stats = db.query(
        func.sum(Order.quantity).label("total_quantity"),  # 销售件数：子订单内商品数量累计
        func.count(func.distinct(parent_order_key)).label("total_orders"),  # 按父订单号去重统计
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("total_gmv"),
        func.sum(_convert_to_cny(Order.profit, usd_rate)).label("total_profit"),
    ).filter(and_(*filters)).first()
    
    # 按天统计趋势
    # 销量：quantity之和（子订单内商品数量累计）
    # 订单数：按父订单号去重统计
    daily_trends = db.query(
        func.date(Order.order_time).label("date"),
        func.sum(Order.quantity).label("quantity"),
        func.count(func.distinct(parent_order_key)).label("orders"),  # 按父订单号去重统计
    ).filter(and_(*filters)).group_by(
        func.date(Order.order_time)
    ).order_by(
        func.date(Order.order_time)
    ).all()
    
    # 按店铺统计趋势
    # 销量：quantity之和（子订单内商品数量累计）
    # 订单数：按父订单号去重统计
    shop_trends = db.query(
        func.date(Order.order_time).label("date"),
        Shop.shop_name.label("shop_name"),
        func.sum(Order.quantity).label("quantity"),
        func.count(func.distinct(parent_order_key)).label("orders"),  # 按父订单号去重统计
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
    
    # 计算实际使用的天数（用于返回）
    if start_date and end_date:
        actual_days = (end_date - start_date).days + 1
        period_info = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": actual_days
        }
    else:
        # 如果没有日期范围，返回None表示统计所有时间
        period_info = {
            "start_date": None,
            "end_date": None,
            "days": None
        }
    
    return {
        "total_quantity": int(total_stats.total_quantity or 0),
        "total_orders": int(total_stats.total_orders or 0),  # 按父订单号去重，只统计有效订单
        "total_gmv": float(total_stats.total_gmv or 0),  # GMV（收入），统一转换为CNY
        "total_profit": float(total_stats.total_profit or 0),  # 利润，统一转换为CNY
        "daily_trends": daily_data,
        "shop_trends": shop_daily_data,
        "period": period_info
    }


@router.get("/sku-sales-ranking")
def get_sku_sales_ranking(
    days: Optional[int] = Query(None, description="统计天数（如果未提供start_date和end_date则使用此参数，默认30天）"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    manager: Optional[str] = Query(None, description="负责人"),
    region: Optional[str] = Query(None, description="地区"),
    sku_search: Optional[str] = Query(None, description="SKU搜索关键词"),
    limit: int = Query(100, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取SKU销量排行
    
    通过 product_sku 关联订单和商品表
    """
    # 计算时间范围（香港时区）
    if start_date and end_date:
        # 如果提供了start_date和end_date，使用它们
        start_date = start_date.replace(tzinfo=HK_TIMEZONE) if start_date.tzinfo is None else start_date
        end_date = end_date.replace(tzinfo=HK_TIMEZONE) if end_date.tzinfo is None else end_date
    else:
        # 否则使用days参数
        end_date = get_hk_now()
        days = days or 30
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
    # 统一转换为CNY
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    sku_stats = db.query(
        Order.product_sku.label("sku"),
        func.max(Order.product_name).label("product_name_from_order"),
        func.sum(Order.quantity).label("total_quantity"),
        func.count(func.distinct(Order.order_sn)).label("order_count"),
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("total_gmv"),
        func.sum(_convert_to_cny(Order.profit, usd_rate)).label("total_profit"),
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
        sku_stats.c.total_gmv.label("total_gmv"),
        sku_stats.c.total_profit.label("total_profit"),
    ).outerjoin(
        product_info, sku_stats.c.sku == product_info.c.product_sku
    ).group_by(
        sku_stats.c.sku,
        sku_stats.c.total_quantity,
        sku_stats.c.order_count,
        sku_stats.c.total_gmv,
        sku_stats.c.total_profit
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
            "gmv": float(row.total_gmv or 0),
            "profit": float(row.total_profit or 0),
        })
    
    # 计算实际使用的天数（用于返回）
    actual_days = (end_date - start_date).days + 1
    
    return {
        "ranking": ranking,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": actual_days
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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


@router.get("/payment-collection")
def get_payment_collection(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取回款统计数据
    
    回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额
    
    Args:
        shop_ids: 店铺ID列表，None表示所有店铺
        start_date: 开始日期（回款日期范围）
        end_date: 结束日期（回款日期范围）
        days: 天数（当未指定日期时使用，默认30天）
    
    Returns:
        回款统计数据，包含每日回款金额（按店铺分组）和总计
    """
    # 统一转换为CNY的汇率
    usd_rate = CurrencyConverter.USD_TO_CNY_RATE
    
    # 回款日期 = delivery_time + 8天
    collection_date_expr = func.date(Order.delivery_time + text("INTERVAL '8 days'"))
    
    # 确定日期范围（回款日期范围）
    # 如果未指定end_date，则查询到未来7天（基于最新的签收日期）
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
            # 最新签收日期 + 8天 + 7天（未来7天）= 最新签收日期 + 15天
            latest_delivery_date = latest_delivery.date() if isinstance(latest_delivery, datetime) else latest_delivery
            end_date = datetime.combine(latest_delivery_date + timedelta(days=15), datetime.min.time())
        else:
            end_date = datetime.now() + timedelta(days=7)  # 如果没有签收记录，显示未来7天
    
    if not start_date:
        start_date = end_date - timedelta(days=days)
    
    # 构建查询条件
    # 筛选已签收的订单，且回款日期在指定范围内
    filters = [
        Order.status == OrderStatus.DELIVERED,
        Order.delivery_time.isnot(None),
        # 回款日期 = delivery_time + 8天
        collection_date_expr >= start_date.date(),
        collection_date_expr <= end_date.date()
    ]
    
    if shop_ids:
        filters.append(Order.shop_id.in_(shop_ids))
    
    # 按店铺和回款日期分组统计
    
    results = db.query(
        Shop.id.label("shop_id"),
        Shop.shop_name,
        collection_date_expr.label("collection_date"),
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("collection_amount"),
        func.count(Order.id).label("order_count")
    ).join(
        Shop, Shop.id == Order.shop_id
    ).filter(
        and_(*filters)
    ).group_by(
        Shop.id,
        Shop.shop_name,
        collection_date_expr
    ).order_by(
        collection_date_expr,
        Shop.shop_name
    ).all()
    
    # 计算总计
    total_collection = db.query(
        func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("total_amount"),
        func.count(Order.id).label("total_orders")
    ).join(
        Shop, Shop.id == Order.shop_id
    ).filter(
        and_(*filters)
    ).first()
    
    # 格式化结果：按日期和店铺组织数据
    daily_data: dict = {}  # {date: {shop_name: amount, ...}}
    shop_list = set()
    
    for row in results:
        date_str = row.collection_date.strftime("%Y-%m-%d")
        shop_name = row.shop_name
        amount = float(row.collection_amount or 0)
        
        shop_list.add(shop_name)
        
        if date_str not in daily_data:
            daily_data[date_str] = {}
        daily_data[date_str][shop_name] = amount
    
    # 只使用有回款数据的日期（不填充缺失的日期）
    date_list = sorted(daily_data.keys())  # 按日期排序
    
    # 生成表格数据：只显示有回款金额的日期，按日期倒序排序
    table_data = []
    for date_str in reversed(date_list):  # 倒序排列
        date_amounts = daily_data.get(date_str, {})
        total = sum(date_amounts.values())
        
        # 只添加有回款金额的日期（total > 0）
        if total > 0:
            row_data: dict = {
                "date": date_str,
                "total": total
            }
            for shop_name in sorted(shop_list):
                amount = date_amounts.get(shop_name, 0.0)
                row_data[shop_name] = amount
            table_data.append(row_data)
    
    # 生成图表数据：每个店铺的折线图数据
    chart_series = []
    for shop_name in sorted(shop_list):
        series_data = []
        for date_str in date_list:
            amount = daily_data.get(date_str, {}).get(shop_name, 0.0)
            series_data.append(round(amount, 2))
        chart_series.append({
            "name": shop_name,
            "data": series_data
        })
    
    # 总计折线图数据
    total_series_data = []
    for date_str in date_list:
        total = sum(daily_data.get(date_str, {}).values())
        total_series_data.append(round(total, 2))
    chart_series.append({
        "name": "总计",
        "data": total_series_data
    })
    
    return {
        "table_data": table_data,
        "chart_data": {
            "dates": date_list,
            "series": chart_series
        },
        "summary": {
            "total_amount": float(total_collection.total_amount or 0),
            "total_orders": int(total_collection.total_orders or 0),
            "shops": sorted(list(shop_list))
        },
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        }
    }
