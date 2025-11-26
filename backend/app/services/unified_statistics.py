"""
统一统计服务 - 确保所有页面和AI模块使用一致的统计逻辑

本服务提供统一的统计函数，所有API接口应使用这些函数来保证数据一致性。
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, or_
from decimal import Decimal

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.shop import Shop
from app.api.analytics import build_sales_filters, HK_TIMEZONE
from datetime import timezone, timedelta

def get_hk_now():
    """获取香港时区的当前时间"""
    return datetime.now(HK_TIMEZONE)


class UnifiedStatisticsService:
    """统一统计服务类"""
    
    # 统一的父订单键定义
    @staticmethod
    def get_parent_order_key():
        """
        获取统一的父订单键表达式
        
        Returns:
            SQLAlchemy case 表达式
        """
        return case(
            (Order.parent_order_sn.isnot(None), Order.parent_order_sn),
            else_=Order.order_sn
        )
    
    @staticmethod
    def get_valid_order_statuses() -> List[OrderStatus]:
        """
        获取有效的订单状态列表（统一规则）
        
        Returns:
            有效订单状态列表
        """
        return [
            OrderStatus.PROCESSING,  # 待发货
            OrderStatus.SHIPPED,     # 已发货
            OrderStatus.DELIVERED    # 已签收
        ]
    
    @staticmethod
    def build_base_filters(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        shop_ids: Optional[List[int]] = None,
        manager: Optional[str] = None,
        region: Optional[str] = None,
        sku_search: Optional[str] = None,
    ) -> List:
        """
        构建基础过滤条件（统一规则）
        
        使用 build_sales_filters 确保所有接口使用相同的过滤逻辑
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            shop_ids: 店铺ID列表
            manager: 负责人
            region: 地区
            sku_search: SKU搜索关键词
            
        Returns:
            过滤条件列表
        """
        return build_sales_filters(
            db, start_date, end_date, shop_ids, manager, region, sku_search
        )
    
    @staticmethod
    def calculate_order_statistics(
        db: Session,
        filters: List,
        group_by_fields: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        计算订单统计数据（统一规则）
        
        Args:
            db: 数据库会话
            filters: 过滤条件列表
            group_by_fields: 分组字段列表（如果为None，返回总计）
            
        Returns:
            统计数据字典，包含：
            - order_count: 订单数（按父订单去重）
            - total_quantity: 销售件数
            - total_gmv: 总GMV（CNY）
            - total_cost: 总成本（CNY）
            - total_profit: 总利润（CNY）
        """
        parent_order_key = UnifiedStatisticsService.get_parent_order_key()
        
        # 先按父订单分组，计算每个父订单的GMV、成本、利润
        parent_order_stats = db.query(
            parent_order_key.label('parent_key'),
            func.sum(Order.quantity).label('parent_quantity'),
            func.sum(Order.total_price).label('parent_gmv'),  # 已经是CNY
            func.sum(Order.total_cost).label('parent_cost'),  # 已经是CNY
            func.sum(Order.profit).label('parent_profit'),  # 已经是CNY
        ).filter(and_(*filters)).group_by(parent_order_key).subquery()
        
        # 如果指定了分组字段，添加分组
        if group_by_fields:
            # 需要从原始查询中获取分组字段
            # 这里返回子查询，由调用者进一步处理
            return {
                'subquery': parent_order_stats,
                'parent_order_key': parent_order_key
            }
        
        # 汇总所有父订单的统计数据
        result = db.query(
            func.count(parent_order_stats.c.parent_key).label("order_count"),
            func.sum(parent_order_stats.c.parent_quantity).label("total_quantity"),
            func.sum(parent_order_stats.c.parent_gmv).label("total_gmv"),
            func.sum(parent_order_stats.c.parent_cost).label("total_cost"),
            func.sum(parent_order_stats.c.parent_profit).label("total_profit"),
        ).first()
        
        return {
            "order_count": int(result.order_count or 0),
            "total_quantity": int(result.total_quantity or 0),
            "total_gmv": float(result.total_gmv or 0),
            "total_cost": float(result.total_cost or 0),
            "total_profit": float(result.total_profit or 0),
        }
    
    @staticmethod
    def get_sku_statistics(
        db: Session,
        filters: List,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取SKU统计数据（统一规则）
        
        Args:
            db: 数据库会话
            filters: 过滤条件列表
            limit: 返回数量限制
            
        Returns:
            SKU统计列表，每个元素包含：
            - sku: SKU ID (Product.product_id)
            - product_name: 商品名称
            - manager: 负责人
            - total_quantity: 销售件数
            - order_count: 订单数
            - total_gmv: GMV
            - total_profit: 利润
        """
        parent_order_key = UnifiedStatisticsService.get_parent_order_key()
        
        # 按Product.product_id（SKU ID）分组统计
        results = db.query(
            func.coalesce(Product.product_id, Order.product_sku).label("sku_id"),
            func.max(func.coalesce(Product.product_name, Order.product_name)).label("product_name"),
            func.max(Product.manager).label("manager"),
            func.sum(Order.quantity).label("total_quantity"),
            func.count(func.distinct(parent_order_key)).label("order_count"),
            func.sum(Order.total_price).label("total_gmv"),
            func.sum(Order.profit).label("total_profit"),
        ).outerjoin(
            Product, Order.product_id == Product.id
        ).filter(
            and_(*filters),
            or_(
                Product.product_id.isnot(None),
                Order.product_sku.isnot(None)
            )
        ).group_by(
            func.coalesce(Product.product_id, Order.product_sku)
        ).order_by(
            func.sum(Order.quantity).desc()
        ).limit(limit).all()
        
        return [
            {
                "sku": str(row.sku_id) if row.sku_id else '-',
                "product_name": row.product_name or '-',
                "manager": row.manager or '-',
                "total_quantity": int(row.total_quantity or 0),
                "order_count": int(row.order_count or 0),
                "total_gmv": float(row.total_gmv or 0),
                "total_profit": float(row.total_profit or 0),
            }
            for row in results
        ]
    
    @staticmethod
    def get_manager_statistics(
        db: Session,
        filters: List
    ) -> List[Dict[str, Any]]:
        """
        获取负责人统计数据（统一规则）
        
        Args:
            db: 数据库会话
            filters: 过滤条件列表（不含负责人筛选）
            
        Returns:
            负责人统计列表，每个元素包含：
            - manager: 负责人
            - total_quantity: 销售件数
            - order_count: 订单数（按父订单去重）
            - total_gmv: GMV
            - total_profit: 利润
        """
        parent_order_key = UnifiedStatisticsService.get_parent_order_key()
        
        # 从店铺表获取负责人信息（Shop.default_manager）
        # 每个订单通过shop_id关联到店铺，获取店铺的默认负责人
        # 使用 COALESCE 处理空值，将没有负责人的订单归类为"未分配"
        # 先按父订单和负责人分组，计算每个父订单的统计数据
        try:
            # 使用 COALESCE 处理空值，确保所有订单都被统计
            # 将没有负责人的订单归类为"未分配"
            manager_expr = case(
                (Shop.default_manager.is_(None), '未分配'),
                (Shop.default_manager == '', '未分配'),
                else_=Shop.default_manager
            )
            
            parent_order_stats = db.query(
                parent_order_key.label('parent_key'),
                manager_expr.label('manager'),
                func.sum(Order.quantity).label('parent_quantity'),
                func.sum(Order.total_price).label('parent_gmv'),
                func.sum(Order.profit).label('parent_profit'),
            ).join(
                Shop, Order.shop_id == Shop.id
            ).filter(
                and_(*filters)
            ).group_by(
                parent_order_key,
                manager_expr
            ).subquery()
            
            # 再按负责人分组，汇总统计数据（订单数按父订单去重）
            results = db.query(
                parent_order_stats.c.manager.label("manager"),
                func.sum(parent_order_stats.c.parent_quantity).label("total_quantity"),
                func.count(parent_order_stats.c.parent_key).label("order_count"),
                func.sum(parent_order_stats.c.parent_gmv).label("total_gmv"),
                func.sum(parent_order_stats.c.parent_profit).label("total_profit"),
            ).group_by(
                parent_order_stats.c.manager
            ).order_by(
                func.sum(parent_order_stats.c.parent_quantity).desc()
            ).all()
        except Exception as e:
            # 如果子查询失败，记录错误并返回空列表
            from loguru import logger
            import traceback
            logger.error(f"负责人统计查询失败: {e}")
            logger.error(traceback.format_exc())
            # 返回空列表，避免500错误
            return []
        
        return [
            {
                "manager": row.manager,
                "total_quantity": int(row.total_quantity or 0),
                "order_count": int(row.order_count or 0),
                "total_gmv": float(row.total_gmv or 0),
                "total_profit": float(row.total_profit or 0),
            }
            for row in results
        ]
    
    @staticmethod
    def parse_date_range(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        解析日期范围参数（统一规则）
        
        Args:
            start_date: 开始日期字符串 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)
            end_date: 结束日期字符串 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)
            days: 天数（如果未提供日期，使用最近N天）
            
        Returns:
            (start_date, end_date) 元组，datetime对象或None
        """
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=HK_TIMEZONE)
            else:
                start_dt = start_dt.astimezone(HK_TIMEZONE)
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=HK_TIMEZONE)
            else:
                end_dt = end_dt.astimezone(HK_TIMEZONE)
        
        # 如果提供了日期范围，直接返回
        if start_dt and end_dt:
            return start_dt, end_dt
        
        # 如果没有提供日期范围，根据days参数决定
        if days:
            end_dt = get_hk_now()
            start_dt = end_dt - timedelta(days=days)
            return start_dt, end_dt
        
        # 如果都没有提供，返回None（统计所有时间）
        return None, None

