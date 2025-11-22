"""实时计算GMV和利润的服务"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case, and_, or_
from decimal import Decimal
from typing import Optional
from loguru import logger

from app.models.order import Order
from app.models.product import Product, ProductCost
from app.utils.currency import CurrencyConverter


class RealtimeCalculationService:
    """实时计算服务 - 根据订单时间和商品信息实时计算GMV、成本、利润"""
    
    @staticmethod
    def get_product_price_at_time(
        db: Session, 
        product_id: int, 
        order_time
    ) -> Optional[Decimal]:
        """
        获取订单时间有效的商品价格
        
        Args:
            db: 数据库会话
            product_id: 商品ID
            order_time: 订单时间
            
        Returns:
            商品价格，如果未找到返回None
        """
        # 目前商品表只有current_price，没有价格历史
        # 后续可以扩展为查找价格历史表
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            return product.current_price
        return None
    
    @staticmethod
    def get_product_cost_at_time(
        db: Session, 
        product_id: int, 
        order_time
    ) -> Optional[Decimal]:
        """
        获取订单时间有效的商品成本价
        
        Args:
            db: 数据库会话
            product_id: 商品ID
            order_time: 订单时间
            
        Returns:
            成本价，如果未找到返回None
        """
        # 查找订单时间有效的成本记录
        cost_record = db.query(ProductCost).filter(
            and_(
                ProductCost.product_id == product_id,
                ProductCost.effective_from <= order_time,
                or_(
                    ProductCost.effective_to.is_(None),
                    ProductCost.effective_to > order_time
                )
            )
        ).order_by(ProductCost.effective_from.desc()).first()
        
        if cost_record:
            return cost_record.cost_price
        return None
    
    @staticmethod
    def calculate_order_gmv(
        db: Session, 
        order: Order,
        use_stored: bool = False
    ) -> Decimal:
        """
        计算订单GMV
        
        Args:
            db: 数据库会话
            order: 订单对象
            use_stored: 是否优先使用存储的值（用于兼容）
            
        Returns:
            GMV（供货价 × 数量）
        """
        # 如果使用存储值且存在，直接返回
        if use_stored and order.total_price:
            return order.total_price
        
        # 实时计算
        if not order.product_id:
            return Decimal('0')
        
        supply_price = RealtimeCalculationService.get_product_price_at_time(
            db, order.product_id, order.order_time
        )
        
        if supply_price is None:
            return Decimal('0')
        
        return supply_price * Decimal(order.quantity)
    
    @staticmethod
    def calculate_order_cost(
        db: Session, 
        order: Order,
        use_stored: bool = False
    ) -> Decimal:
        """
        计算订单成本
        
        Args:
            db: 数据库会话
            order: 订单对象
            use_stored: 是否优先使用存储的值（用于兼容）
            
        Returns:
            总成本（单位成本 × 数量）
        """
        # 如果使用存储值且存在，直接返回
        if use_stored and order.total_cost:
            return order.total_cost
        
        # 实时计算
        if not order.product_id:
            return Decimal('0')
        
        unit_cost = RealtimeCalculationService.get_product_cost_at_time(
            db, order.product_id, order.order_time
        )
        
        if unit_cost is None:
            return Decimal('0')
        
        return unit_cost * Decimal(order.quantity)
    
    @staticmethod
    def calculate_order_profit(
        db: Session, 
        order: Order,
        use_stored: bool = False
    ) -> Optional[Decimal]:
        """
        计算订单利润
        
        Args:
            db: 数据库会话
            order: 订单对象
            use_stored: 是否优先使用存储的值（用于兼容）
            
        Returns:
            利润（GMV - 成本），如果无法计算返回None
        """
        # 如果使用存储值且存在，直接返回
        if use_stored and order.profit is not None:
            return order.profit
        
        # 实时计算
        gmv = RealtimeCalculationService.calculate_order_gmv(db, order, use_stored=False)
        cost = RealtimeCalculationService.calculate_order_cost(db, order, use_stored=False)
        
        # 如果成本为0，可能表示未找到成本记录，返回None
        if cost == Decimal('0') and not order.product_id:
            return None
        
        return gmv - cost
    
    @staticmethod
    def build_gmv_expression(order_table, usd_rate: Decimal):
        """
        构建GMV计算的SQL表达式（用于查询）
        
        Args:
            order_table: 订单表（Order类或别名）
            usd_rate: USD到CNY的汇率
            
        Returns:
            SQL表达式
        """
        from sqlalchemy import select
        
        # 子查询：获取商品价格
        product_price_subq = (
            select(Product.current_price)
            .where(Product.id == order_table.product_id)
            .scalar_subquery()
        )
        
        # GMV = 商品价格 × 数量
        gmv = func.coalesce(product_price_subq, Decimal('0')) * order_table.quantity
        
        # 货币转换
        return case(
            (order_table.currency == 'USD', gmv * usd_rate),
            (order_table.currency == 'CNY', gmv),
            else_=gmv * usd_rate
        )
    
    @staticmethod
    def build_cost_expression(order_table, usd_rate: Decimal):
        """
        构建成本计算的SQL表达式（用于查询）
        
        Args:
            order_table: 订单表（Order类或别名）
            usd_rate: USD到CNY的汇率
            
        Returns:
            SQL表达式
        """
        from sqlalchemy import select
        
        # 子查询：获取订单时间有效的成本价
        cost_price_subq = (
            select(ProductCost.cost_price)
            .where(
                and_(
                    ProductCost.product_id == order_table.product_id,
                    ProductCost.effective_from <= order_table.order_time,
                    or_(
                        ProductCost.effective_to.is_(None),
                        ProductCost.effective_to > order_table.order_time
                    )
                )
            )
            .order_by(ProductCost.effective_from.desc())
            .limit(1)
            .scalar_subquery()
        )
        
        # 成本 = 成本价 × 数量
        cost = func.coalesce(cost_price_subq, Decimal('0')) * order_table.quantity
        
        # 货币转换
        return case(
            (order_table.currency == 'USD', cost * usd_rate),
            (order_table.currency == 'CNY', cost),
            else_=cost * usd_rate
        )
    
    @staticmethod
    def build_profit_expression(order_table, usd_rate: Decimal):
        """
        构建利润计算的SQL表达式（用于查询）
        
        Args:
            order_table: 订单表（Order类或别名）
            usd_rate: USD到CNY的汇率
            
        Returns:
            SQL表达式
        """
        gmv_expr = RealtimeCalculationService.build_gmv_expression(order_table, usd_rate)
        cost_expr = RealtimeCalculationService.build_cost_expression(order_table, usd_rate)
        
        # 利润 = GMV - 成本
        return gmv_expr - cost_expr

