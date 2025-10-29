"""统计分析API"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.statistics import StatisticsService
from app.models.order import OrderStatus

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview/")
def get_overview_statistics(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db)
):
    """
    获取订单总览统计
    
    返回订单总数、GMV、成本、利润等核心指标
    """
    return StatisticsService.get_order_statistics(
        db=db,
        shop_ids=shop_ids,
        start_date=start_date,
        end_date=end_date,
        status=status
    )


@router.get("/daily/")
def get_daily_statistics(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    获取每日统计数据
    
    返回指定时间范围内的每日订单、GMV、利润等数据
    """
    return StatisticsService.get_daily_statistics(
        db=db,
        shop_ids=shop_ids,
        start_date=start_date,
        end_date=end_date,
        days=days
    )


@router.get("/weekly/")
def get_weekly_statistics(
    shop_ids: Optional[List[int]] = Query(None),
    weeks: int = 12,
    db: Session = Depends(get_db)
):
    """
    获取每周统计数据
    
    返回最近N周的订单、GMV、利润等数据
    """
    return StatisticsService.get_weekly_statistics(
        db=db,
        shop_ids=shop_ids,
        weeks=weeks
    )


@router.get("/monthly/")
def get_monthly_statistics(
    shop_ids: Optional[List[int]] = Query(None),
    months: int = 12,
    db: Session = Depends(get_db)
):
    """
    获取每月统计数据
    
    返回最近N个月的订单、GMV、利润等数据
    """
    return StatisticsService.get_monthly_statistics(
        db=db,
        shop_ids=shop_ids,
        months=months
    )


@router.get("/shops/comparison/")
def get_shop_comparison(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    获取店铺对比数据
    
    返回各店铺的订单、GMV、利润等数据，用于店铺间对比分析
    """
    return StatisticsService.get_shop_comparison(
        db=db,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/trend/")
def get_sales_trend(
    shop_ids: Optional[List[int]] = Query(None),
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    获取销量趋势数据
    
    返回销量趋势图表数据，包含移动平均线和增长率
    """
    return StatisticsService.get_sales_trend(
        db=db,
        shop_ids=shop_ids,
        days=days
    )

