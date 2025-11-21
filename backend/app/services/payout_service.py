"""回款计划服务"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from loguru import logger

from app.models.payout import Payout, PayoutStatus
from app.models.order import Order
from app.core.config import settings


class PayoutService:
    """回款计划服务"""
    
    def __init__(self, db: Session):
        """
        初始化回款计划服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        # 从配置获取回款天数，默认7天
        self.settlement_days = getattr(settings, 'SETTLEMENT_DAYS_AFTER_DELIVERY', 7)
    
    def create_payout_for_order(self, order: Order) -> Optional[Payout]:
        """
        为订单创建回款计划
        
        Args:
            order: 订单对象
            
        Returns:
            创建的回款计划对象，如果订单未签收则返回None
        """
        # 只有已签收的订单才创建回款计划
        if not order.delivery_time:
            return None
        
        # 检查是否已存在回款计划
        existing_payout = self.db.query(Payout).filter(
            Payout.order_id == order.id
        ).first()
        
        if existing_payout:
            logger.debug(f"订单 {order.order_sn} 已存在回款计划")
            return existing_payout
        
        # 计算回款日期
        payout_date = order.delivery_time.date() + timedelta(days=self.settlement_days)
        
        # 创建回款计划
        payout = Payout(
            shop_id=order.shop_id,
            order_id=order.id,
            payout_date=payout_date,
            payout_amount=order.total_price,
            currency=order.currency or 'USD',
            status=PayoutStatus.PENDING,
            raw_data_id=order.raw_data_id
        )
        
        self.db.add(payout)
        self.db.flush()
        
        logger.info(f"为订单 {order.order_sn} 创建回款计划: {payout_date}, 金额: {order.total_price}")
        
        return payout
    
    def create_payouts_for_delivered_orders(
        self,
        shop_id: Optional[int] = None,
        delivery_date: Optional[date] = None
    ) -> Dict[str, int]:
        """
        为已签收的订单批量创建回款计划
        
        Args:
            shop_id: 店铺ID（可选，None表示所有店铺）
            delivery_date: 签收日期（可选，None表示所有已签收订单）
            
        Returns:
            统计信息
        """
        # 查询已签收但未创建回款计划的订单
        query = self.db.query(Order).filter(
            Order.delivery_time.isnot(None),
            ~Order.id.in_(
                self.db.query(Payout.order_id).subquery()
            )
        )
        
        if shop_id:
            query = query.filter(Order.shop_id == shop_id)
        
        if delivery_date:
            # 查询指定日期签收的订单
            start_datetime = datetime.combine(delivery_date, datetime.min.time())
            end_datetime = datetime.combine(delivery_date, datetime.max.time())
            query = query.filter(
                and_(
                    Order.delivery_time >= start_datetime,
                    Order.delivery_time <= end_datetime
                )
            )
        
        orders = query.all()
        
        created = 0
        skipped = 0
        
        for order in orders:
            try:
                payout = self.create_payout_for_order(order)
                if payout:
                    created += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"为订单 {order.order_sn} 创建回款计划失败: {e}")
                skipped += 1
        
        self.db.commit()
        
        return {
            'total': len(orders),
            'created': created,
            'skipped': skipped
        }
    
    def get_payouts(
        self,
        shop_ids: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[PayoutStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        查询回款计划列表
        
        Args:
            shop_ids: 店铺ID列表
            start_date: 开始日期
            end_date: 结束日期
            status: 回款状态
            page: 页码
            page_size: 每页数量
            
        Returns:
            回款计划列表和分页信息
        """
        query = self.db.query(Payout)
        
        if shop_ids:
            query = query.filter(Payout.shop_id.in_(shop_ids))
        
        if start_date:
            query = query.filter(Payout.payout_date >= start_date)
        
        if end_date:
            query = query.filter(Payout.payout_date <= end_date)
        
        if status:
            query = query.filter(Payout.status == status)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        payouts = query.order_by(Payout.payout_date.desc()).offset(offset).limit(page_size).all()
        
        return {
            'items': payouts,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def update_payout_status(self, payout_id: int, status: PayoutStatus) -> Payout:
        """
        更新回款状态
        
        Args:
            payout_id: 回款计划ID
            status: 新状态
            
        Returns:
            更新后的回款计划对象
        """
        payout = self.db.query(Payout).filter(Payout.id == payout_id).first()
        
        if not payout:
            raise ValueError(f"回款计划 {payout_id} 不存在")
        
        payout.status = status
        payout.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"更新回款计划 {payout_id} 状态为 {status}")
        
        return payout
    
    def get_payout_summary(
        self,
        shop_ids: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取回款统计汇总
        
        Args:
            shop_ids: 店铺ID列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计汇总信息
        """
        query = self.db.query(Payout)
        
        if shop_ids:
            query = query.filter(Payout.shop_id.in_(shop_ids))
        
        if start_date:
            query = query.filter(Payout.payout_date >= start_date)
        
        if end_date:
            query = query.filter(Payout.payout_date <= end_date)
        
        # 按状态统计
        pending_query = query.filter(Payout.status == PayoutStatus.PENDING)
        paid_query = query.filter(Payout.status == PayoutStatus.PAID)
        
        pending_amount = pending_query.with_entities(
            func.sum(Payout.payout_amount)
        ).scalar() or 0
        
        paid_amount = paid_query.with_entities(
            func.sum(Payout.payout_amount)
        ).scalar() or 0
        
        total_amount = pending_amount + paid_amount
        
        # 未来7天和30天的回款
        today = date.today()
        next_7_days = today + timedelta(days=7)
        next_30_days = today + timedelta(days=30)
        
        payout_7_days = query.filter(
            and_(
                Payout.payout_date >= today,
                Payout.payout_date <= next_7_days,
                Payout.status == PayoutStatus.PENDING
            )
        ).with_entities(func.sum(Payout.payout_amount)).scalar() or 0
        
        payout_30_days = query.filter(
            and_(
                Payout.payout_date >= today,
                Payout.payout_date <= next_30_days,
                Payout.status == PayoutStatus.PENDING
            )
        ).with_entities(func.sum(Payout.payout_amount)).scalar() or 0
        
        return {
            'total_amount': float(total_amount),
            'pending_amount': float(pending_amount),
            'paid_amount': float(paid_amount),
            'payout_7_days': float(payout_7_days),
            'payout_30_days': float(payout_30_days),
            'pending_count': pending_query.count(),
            'paid_count': paid_query.count(),
        }

