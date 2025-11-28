"""统计分析服务"""
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, case
from decimal import Decimal
import pandas as pd
import json
from loguru import logger

from app.models.order import Order, OrderStatus
from app.models.shop import Shop
from app.utils.currency import CurrencyConverter
from app.core.redis_client import RedisClient
from sqlalchemy import and_


class StatisticsService:
    """统计分析服务类"""
    
    @staticmethod
    def get_order_statistics_cached(
        db: Session,
        shop_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[OrderStatus] = None,
        cache_ttl: int = 300  # 默认5分钟缓存
    ) -> Dict[str, Any]:
        """
        获取订单统计数据（带缓存）
        
        Args:
            db: 数据库会话
            shop_ids: 店铺ID列表，None表示所有店铺
            start_date: 开始日期
            end_date: 结束日期
            status: 订单状态筛选
            cache_ttl: 缓存过期时间（秒），默认5分钟
            
        Returns:
            统计数据字典
        """
        # 生成缓存键
        shop_ids_str = ','.join(map(str, sorted(shop_ids or [])))
        start_str = start_date.isoformat() if start_date else 'none'
        end_str = end_date.isoformat() if end_date else 'none'
        status_str = status.value if status else 'none'
        
        cache_key = f"stats:order:shops:{shop_ids_str}:start:{start_str}:end:{end_str}:status:{status_str}"
        
        # 尝试从缓存获取
        cached = RedisClient.get(cache_key)
        if cached:
            logger.debug(f"从缓存获取统计数据: {cache_key}")
            return cached
        
        # 计算统计数据
        stats = StatisticsService.get_order_statistics(
            db, shop_ids, start_date, end_date, status
        )
        
        # 存入缓存
        RedisClient.set(cache_key, stats, ttl=cache_ttl)
        logger.debug(f"统计数据已缓存: {cache_key}, TTL={cache_ttl}秒")
        
        return stats
    
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
        
        使用 UnifiedStatisticsService 确保统计口径一致
        
        Args:
            db: 数据库会话
            shop_ids: 店铺ID列表，None表示所有店铺
            start_date: 开始日期
            end_date: 结束日期
            status: 订单状态筛选（如果指定，会覆盖默认的有效状态过滤）
            
        Returns:
            统计数据字典
        """
        from app.services.unified_statistics import UnifiedStatisticsService
        
        # 构建查询条件
        # 如果没有指定status，使用统一的过滤规则（PROCESSING, SHIPPED, DELIVERED）
        # 如果指定了status，使用指定的status（但需要确保它符合有效状态）
        filters = []
        
        if shop_ids:
            filters.append(Order.shop_id.in_(shop_ids))
        
        if start_date:
            filters.append(Order.order_time >= start_date)
        
        if end_date:
            filters.append(Order.order_time <= end_date)
        
        # 订单状态筛选
        if status:
            # 如果指定了状态，使用指定的状态
            filters.append(Order.status == status)
        else:
            # 如果没有指定状态，使用统一的有效订单状态过滤
            filters.append(Order.status.in_(UnifiedStatisticsService.get_valid_order_statuses()))
        
        # 计算统计数据（使用统一服务）
        stats = UnifiedStatisticsService.calculate_order_statistics(db, filters)
        
        # 计算平均订单价值和利润率（需要额外的查询）
        parent_order_key = UnifiedStatisticsService.get_parent_order_key()
        parent_order_stats = db.query(
            parent_order_key.label('parent_key'),
            func.sum(Order.total_price).label('parent_gmv'),
        ).filter(and_(*filters)).group_by(parent_order_key).subquery()
        
        avg_result = db.query(
            func.avg(parent_order_stats.c.parent_gmv).label("avg_order_value"),
        ).first()
        
        avg_order_value = float(avg_result.avg_order_value or 0) if avg_result else 0.0
        profit_margin = (stats['total_profit'] / stats['total_gmv'] * 100) if stats['total_gmv'] > 0 else 0
        
        return {
            "total_orders": stats['order_count'],
            "total_gmv": round(stats['total_gmv'], 2),
            "total_cost": round(stats['total_cost'], 2),
            "total_profit": round(stats['total_profit'], 2),
            "avg_order_value": round(avg_order_value, 2),
            "profit_margin": round(profit_margin, 2),
        }
    
    @staticmethod
    def get_daily_statistics(
        db: Session,
        shop_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: Optional[int] = 30
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
        # 如果days为None，不限制日期范围（获取全部历史数据）
        if days is None:
            start_date = None
            end_date = None
        else:
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=days)
        
        # 构建查询条件 - 使用统一服务确保数据一致性
        from app.services.unified_statistics import UnifiedStatisticsService
        
        # 使用统一服务构建基础过滤条件
        filters = UnifiedStatisticsService.build_base_filters(
            db, start_date, end_date, shop_ids, None, None, None
        )
        
        # 按日期分组统计
        # 注意：订单数按订单号去重统计（一个订单号可能对应多条记录，每个订单号为一单）
        # 统一转换为CNY
        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
        results = db.query(
            func.date(Order.order_time).label("date"),
            func.count(func.distinct(Order.order_sn)).label("orders"),  # 按订单号去重统计订单数
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_price * usd_rate),
                    (Order.currency == 'CNY', Order.total_price),
                    else_=Order.total_price * usd_rate
                )
            ).label("gmv"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_cost * usd_rate),
                    (Order.currency == 'CNY', Order.total_cost),
                    else_=Order.total_cost * usd_rate
                )
            ).label("cost"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.profit * usd_rate),
                    (Order.currency == 'CNY', Order.profit),
                    else_=Order.profit * usd_rate
                )
            ).label("profit"),
        ).filter(and_(*filters)).group_by(
            func.date(Order.order_time)
        ).order_by(func.date(Order.order_time)).all()
        
        # 格式化结果，并计算每日延迟到货率
        daily_stats = []
        for row in results:
            # 计算该日期的延迟到货率
            # 延迟到货：发货时间 > 预期最晚发货时间
            date_str = row.date.strftime("%Y-%m-%d")
            date_start = datetime.strptime(date_str, "%Y-%m-%d")
            date_end = date_start + timedelta(days=1)
            
            # 查询该日期下单的订单中，延迟发货的数量
            delay_filters = filters + [
                func.date(Order.order_time) == row.date,
                Order.shipping_time.isnot(None),
                Order.expect_ship_latest_time.isnot(None),
                Order.shipping_time > Order.expect_ship_latest_time
            ]
            delay_count = db.query(
                func.count(func.distinct(Order.order_sn))
            ).filter(and_(*delay_filters)).scalar() or 0
            
            total_orders = row.orders or 0
            delay_rate = (delay_count / total_orders * 100) if total_orders > 0 else 0.0
            
            daily_stats.append({
                "date": date_str,
                "order_count": total_orders,  # 使用 order_count 保持一致性
                "orders": total_orders,  # 保留兼容性
                "gmv": float(row.gmv or 0),
                "cost": float(row.cost or 0),
                "profit": float(row.profit or 0),
                "delay_rate": float(delay_rate),
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
        
        # 排除已取消和已退款的订单（这些订单不应计入销售统计）
        filters.append(Order.status != OrderStatus.CANCELLED)
        filters.append(Order.status != OrderStatus.REFUNDED)
        
        # 只统计有有效金额的订单（total_price > 0）
        filters.append(Order.total_price > 0)
        
        # 按周分组统计，统一转换为CNY
        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
        results = db.query(
            extract('year', Order.order_time).label("year"),
            extract('week', Order.order_time).label("week"),
            func.count(Order.id).label("orders"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_price * usd_rate),
                    (Order.currency == 'CNY', Order.total_price),
                    else_=Order.total_price * usd_rate
                )
            ).label("gmv"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_cost * usd_rate),
                    (Order.currency == 'CNY', Order.total_cost),
                    else_=Order.total_cost * usd_rate
                )
            ).label("cost"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.profit * usd_rate),
                    (Order.currency == 'CNY', Order.profit),
                    else_=Order.profit * usd_rate
                )
            ).label("profit"),
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
        
        # 排除已取消和已退款的订单（这些订单不应计入销售统计）
        filters.append(Order.status != OrderStatus.CANCELLED)
        filters.append(Order.status != OrderStatus.REFUNDED)
        
        # 只统计有有效金额的订单（total_price > 0）
        filters.append(Order.total_price > 0)
        
        # 按月分组统计，统一转换为CNY
        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
        results = db.query(
            extract('year', Order.order_time).label("year"),
            extract('month', Order.order_time).label("month"),
            func.count(Order.id).label("orders"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_price * usd_rate),
                    (Order.currency == 'CNY', Order.total_price),
                    else_=Order.total_price * usd_rate
                )
            ).label("gmv"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_cost * usd_rate),
                    (Order.currency == 'CNY', Order.total_cost),
                    else_=Order.total_cost * usd_rate
                )
            ).label("cost"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.profit * usd_rate),
                    (Order.currency == 'CNY', Order.profit),
                    else_=Order.profit * usd_rate
                )
            ).label("profit"),
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
        
        # 排除已取消和已退款的订单（这些订单不应计入销售统计）
        filters.append(Order.status != OrderStatus.CANCELLED)
        filters.append(Order.status != OrderStatus.REFUNDED)
        
        # 只统计有有效金额的订单（total_price > 0）
        filters.append(Order.total_price > 0)
        
        # 按店铺分组统计，统一转换为CNY
        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
        results = db.query(
            Shop.id,
            Shop.shop_name,
            Shop.region,
            func.count(Order.id).label("orders"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_price * usd_rate),
                    (Order.currency == 'CNY', Order.total_price),
                    else_=Order.total_price * usd_rate
                )
            ).label("gmv"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_cost * usd_rate),
                    (Order.currency == 'CNY', Order.total_cost),
                    else_=Order.total_cost * usd_rate
                )
            ).label("cost"),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.profit * usd_rate),
                    (Order.currency == 'CNY', Order.profit),
                    else_=Order.profit * usd_rate
                )
            ).label("profit"),
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

