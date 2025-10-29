"""高级分析API - GMV表格、SKU销量、爆单榜"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from decimal import Decimal

from app.core.database import get_db
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.shop import Shop

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
        func.sum(Order.quantity).label("total_quantity"),
        func.count(Order.id).label("order_count"),
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
        func.sum(Order.quantity).label("total_quantity"),
        func.count(Order.id).label("order_count"),
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
        func.sum(Order.quantity).label("total_quantity"),
        func.count(Order.id).label("order_count"),
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
