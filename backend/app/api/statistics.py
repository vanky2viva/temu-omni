"""统计分析API"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.statistics import StatisticsService
from app.models.order import OrderStatus
from app.models.user import User

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview/")
def get_overview_statistics(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)"),
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单总览统计
    
    返回订单总数、GMV、成本、利润等核心指标
    """
    # 解析日期字符串
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            # 如果是日期格式，添加时间部分
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            # 如果是日期格式，添加时间部分
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    return StatisticsService.get_order_statistics(
        db=db,
        shop_ids=shop_ids,
        start_date=start_dt,
        end_date=end_dt,
        status=status
    )


@router.get("/daily/")
def get_daily_statistics(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取每日统计数据
    
    返回指定时间范围内的每日订单、GMV、利润等数据
    """
    # 解析日期字符串
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    return StatisticsService.get_daily_statistics(
        db=db,
        shop_ids=shop_ids,
        start_date=start_dt,
        end_date=end_dt,
        days=days
    )


@router.get("/weekly/")
def get_weekly_statistics(
    shop_ids: Optional[List[int]] = Query(None),
    weeks: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取店铺对比数据
    
    返回各店铺的订单、GMV、利润等数据，用于店铺间对比分析
    """
    # 解析日期字符串
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    return StatisticsService.get_shop_comparison(
        db=db,
        start_date=start_dt,
        end_date=end_dt
    )


@router.get("/trend/")
def get_sales_trend(
    shop_ids: Optional[List[int]] = Query(None),
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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

