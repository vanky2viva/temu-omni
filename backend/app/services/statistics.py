"""统计分析服务"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from decimal import Decimal
import pandas as pd

from app.models.order import Order, OrderStatus
from app.models.shop import Shop


class StatisticsService:
    """统计分析服务类"""
    
    @staticmethod
    def get_order_statistics(
        db: Session,
        shop_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[OrderStatus] = None
    ) -> Dict[str, Any]:
        """
        获取订单统计数据
        
        Args:
            db: 数据库会话
            shop_ids: 店铺ID列表，None表示所有店铺
            start_date: 开始日期
            end_date: 结束日期
            status: 订单状态筛选
            
        Returns:
            统计数据字典
        """
        # 构建查询条件
        filters = []
        
        if shop_ids:
            filters.append(Order.shop_id.in_(shop_ids))
        
        if start_date:
            filters.append(Order.order_time >= start_date)
        
        if end_date:
            filters.append(Order.order_time <= end_date)
        
        if status:
            filters.append(Order.status == status)
        
        # 执行统计查询
        result = db.query(
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total_price).label("total_gmv"),
            func.sum(Order.total_cost).label("total_cost"),
            func.sum(Order.profit).label("total_profit"),
            func.avg(Order.total_price).label("avg_order_value"),
        ).filter(and_(*filters)).first()
        
        total_orders = result.total_orders or 0
        total_gmv = float(result.total_gmv or 0)
        total_cost = float(result.total_cost or 0)
        total_profit = float(result.total_profit or 0)
        avg_order_value = float(result.avg_order_value or 0)
        
        # 计算利润率
        profit_margin = (total_profit / total_gmv * 100) if total_gmv > 0 else 0
        
        return {
            "total_orders": total_orders,
            "total_gmv": round(total_gmv, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "avg_order_value": round(avg_order_value, 2),
            "profit_margin": round(profit_margin, 2),
        }
    
    @staticmethod
    def get_daily_statistics(
        db: Session,
        shop_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取每日统计数据
        
        Args:
            db: 数据库会话
            shop_ids: 店铺ID列表
            start_date: 开始日期
            end_date: 结束日期
            days: 天数（当未指定日期时使用）
            
        Returns:
            每日统计数据列表
        """
        # 确定日期范围
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=days)
        
        # 构建查询条件
        filters = [
            Order.order_time >= start_date,
            Order.order_time <= end_date
        ]
        
        if shop_ids:
            filters.append(Order.shop_id.in_(shop_ids))
        
        # 按日期分组统计
        results = db.query(
            func.date(Order.order_time).label("date"),
            func.count(Order.id).label("orders"),
            func.sum(Order.total_price).label("gmv"),
            func.sum(Order.total_cost).label("cost"),
            func.sum(Order.profit).label("profit"),
        ).filter(and_(*filters)).group_by(
            func.date(Order.order_time)
        ).order_by(func.date(Order.order_time)).all()
        
        # 格式化结果
        daily_stats = []
        for row in results:
            daily_stats.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "orders": row.orders or 0,
                "gmv": float(row.gmv or 0),
                "cost": float(row.cost or 0),
                "profit": float(row.profit or 0),
            })
        
        return daily_stats
    
    @staticmethod
    def get_weekly_statistics(
        db: Session,
        shop_ids: Optional[List[int]] = None,
        weeks: int = 12
    ) -> List[Dict[str, Any]]:
        """
        获取每周统计数据
        
        Args:
            db: 数据库会话
            shop_ids: 店铺ID列表
            weeks: 周数
            
        Returns:
            每周统计数据列表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        # 构建查询条件
        filters = [
            Order.order_time >= start_date,
            Order.order_time <= end_date
        ]
        
        if shop_ids:
            filters.append(Order.shop_id.in_(shop_ids))
        
        # 按周分组统计
        results = db.query(
            extract('year', Order.order_time).label("year"),
            extract('week', Order.order_time).label("week"),
            func.count(Order.id).label("orders"),
            func.sum(Order.total_price).label("gmv"),
            func.sum(Order.total_cost).label("cost"),
            func.sum(Order.profit).label("profit"),
        ).filter(and_(*filters)).group_by(
            extract('year', Order.order_time),
            extract('week', Order.order_time)
        ).order_by(
            extract('year', Order.order_time),
            extract('week', Order.order_time)
        ).all()
        
        # 格式化结果
        weekly_stats = []
        for row in results:
            weekly_stats.append({
                "year": int(row.year),
                "week": int(row.week),
                "period": f"{int(row.year)}-W{int(row.week):02d}",
                "orders": row.orders or 0,
                "gmv": float(row.gmv or 0),
                "cost": float(row.cost or 0),
                "profit": float(row.profit or 0),
            })
        
        return weekly_stats
    
    @staticmethod
    def get_monthly_statistics(
        db: Session,
        shop_ids: Optional[List[int]] = None,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """
        获取每月统计数据
        
        Args:
            db: 数据库会话
            shop_ids: 店铺ID列表
            months: 月数
            
        Returns:
            每月统计数据列表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # 构建查询条件
        filters = [
            Order.order_time >= start_date,
            Order.order_time <= end_date
        ]
        
        if shop_ids:
            filters.append(Order.shop_id.in_(shop_ids))
        
        # 按月分组统计
        results = db.query(
            extract('year', Order.order_time).label("year"),
            extract('month', Order.order_time).label("month"),
            func.count(Order.id).label("orders"),
            func.sum(Order.total_price).label("gmv"),
            func.sum(Order.total_cost).label("cost"),
            func.sum(Order.profit).label("profit"),
        ).filter(and_(*filters)).group_by(
            extract('year', Order.order_time),
            extract('month', Order.order_time)
        ).order_by(
            extract('year', Order.order_time),
            extract('month', Order.order_time)
        ).all()
        
        # 格式化结果
        monthly_stats = []
        for row in results:
            monthly_stats.append({
                "year": int(row.year),
                "month": int(row.month),
                "period": f"{int(row.year)}-{int(row.month):02d}",
                "orders": row.orders or 0,
                "gmv": float(row.gmv or 0),
                "cost": float(row.cost or 0),
                "profit": float(row.profit or 0),
            })
        
        return monthly_stats
    
    @staticmethod
    def get_shop_comparison(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取店铺对比数据
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            店铺对比数据列表
        """
        # 构建查询条件
        filters = []
        
        if start_date:
            filters.append(Order.order_time >= start_date)
        
        if end_date:
            filters.append(Order.order_time <= end_date)
        
        # 按店铺分组统计
        results = db.query(
            Shop.id,
            Shop.shop_name,
            Shop.region,
            func.count(Order.id).label("orders"),
            func.sum(Order.total_price).label("gmv"),
            func.sum(Order.total_cost).label("cost"),
            func.sum(Order.profit).label("profit"),
        ).join(Order, Shop.id == Order.shop_id).filter(
            and_(*filters)
        ).group_by(
            Shop.id, Shop.shop_name, Shop.region
        ).all()
        
        # 格式化结果
        shop_stats = []
        for row in results:
            gmv = float(row.gmv or 0)
            profit = float(row.profit or 0)
            shop_stats.append({
                "shop_id": row.id,
                "shop_name": row.shop_name,
                "region": row.region,
                "orders": row.orders or 0,
                "gmv": gmv,
                "cost": float(row.cost or 0),
                "profit": profit,
                "profit_margin": round((profit / gmv * 100) if gmv > 0 else 0, 2),
            })
        
        return shop_stats
    
    @staticmethod
    def get_sales_trend(
        db: Session,
        shop_ids: Optional[List[int]] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取销量趋势数据
        
        Args:
            db: 数据库会话
            shop_ids: 店铺ID列表
            days: 天数
            
        Returns:
            趋势数据字典
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取每日数据
        daily_data = StatisticsService.get_daily_statistics(
            db, shop_ids, start_date, end_date
        )
        
        if not daily_data:
            return {
                "trend": [],
                "growth_rate": 0,
                "prediction": None
            }
        
        # 使用pandas进行趋势分析
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # 计算移动平均
        df['gmv_ma7'] = df['gmv'].rolling(window=7, min_periods=1).mean()
        
        # 计算增长率
        if len(df) >= 2:
            first_week_avg = df['gmv'].iloc[:7].mean()
            last_week_avg = df['gmv'].iloc[-7:].mean()
            growth_rate = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
        else:
            growth_rate = 0
        
        # 格式化趋势数据
        trend_data = []
        for idx, row in df.iterrows():
            trend_data.append({
                "date": idx.strftime("%Y-%m-%d"),
                "orders": int(row['orders']),
                "gmv": float(row['gmv']),
                "gmv_ma7": float(row['gmv_ma7']),
            })
        
        return {
            "trend": trend_data,
            "growth_rate": round(growth_rate, 2),
        }

