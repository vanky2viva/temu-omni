"""报表服务"""
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from loguru import logger

from app.models.report_snapshot import ReportSnapshot, ReportType
from app.models.order import Order, OrderStatus
from app.models.shop import Shop


class ReportService:
    """报表服务"""
    
    def __init__(self, db: Session):
        """
        初始化报表服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def generate_daily_metrics(self, shop_id: int, report_date: date) -> Dict[str, Any]:
        """
        生成日报指标
        
        Args:
            shop_id: 店铺ID
            report_date: 报表日期
            
        Returns:
            日报指标数据
        """
        # 计算日期范围
        start_datetime = datetime.combine(report_date, datetime.min.time())
        end_datetime = datetime.combine(report_date, datetime.max.time())
        
        # 查询订单
        orders = self.db.query(Order).filter(
            and_(
                Order.shop_id == shop_id,
                Order.order_time >= start_datetime,
                Order.order_time <= end_datetime
            )
        ).all()
        
        # 计算指标
        total_orders = len(orders)
        gmv = sum(float(order.total_price) for order in orders)
        
        # 按状态统计
        status_counts = {}
        for status in OrderStatus:
            status_counts[status.value] = sum(1 for o in orders if o.status == status)
        
        # 退款订单
        refunded_orders = [o for o in orders if o.status == OrderStatus.REFUNDED]
        refund_count = len(refunded_orders)
        refund_rate = refund_count / total_orders if total_orders > 0 else 0
        refund_amount = sum(float(o.total_price) for o in refunded_orders)
        
        # 成本和利润
        total_cost = sum(float(o.total_cost or 0) for o in orders)
        total_profit = sum(float(o.profit or 0) for o in orders)
        profit_rate = total_profit / gmv if gmv > 0 else 0
        
        # Top商品（按数量）
        product_sales = {}
        for order in orders:
            key = order.product_sku or order.product_name or 'Unknown'
            if key not in product_sales:
                product_sales[key] = {
                    'product_name': order.product_name,
                    'product_sku': order.product_sku,
                    'quantity': 0,
                    'amount': 0
                }
            product_sales[key]['quantity'] += order.quantity
            product_sales[key]['amount'] += float(order.total_price)
        
        top_products = sorted(
            product_sales.values(),
            key=lambda x: x['quantity'],
            reverse=True
        )[:10]
        
        # 构建指标数据
        metrics = {
            'date': report_date.isoformat(),
            'total_orders': total_orders,
            'gmv': gmv,
            'refund_count': refund_count,
            'refund_rate': refund_rate,
            'refund_amount': refund_amount,
            'total_cost': total_cost,
            'total_profit': total_profit,
            'profit_rate': profit_rate,
            'status_counts': status_counts,
            'top_products': top_products,
        }
        
        return metrics
    
    def save_daily_report(
        self,
        shop_id: int,
        report_date: date,
        metrics: Dict[str, Any],
        ai_summary: Optional[str] = None
    ) -> ReportSnapshot:
        """
        保存日报快照
        
        Args:
            shop_id: 店铺ID
            report_date: 报表日期
            metrics: 指标数据
            ai_summary: AI生成的总结（可选）
            
        Returns:
            保存的报表快照对象
        """
        # 查找或创建报表快照
        snapshot = self.db.query(ReportSnapshot).filter(
            and_(
                ReportSnapshot.shop_id == shop_id,
                ReportSnapshot.date == report_date,
                ReportSnapshot.type == ReportType.DAILY.value
            )
        ).first()
        
        if snapshot:
            # 更新现有快照
            snapshot.metrics = metrics
            if ai_summary:
                snapshot.ai_summary = ai_summary
            snapshot.updated_at = datetime.utcnow()
        else:
            # 创建新快照
            snapshot = ReportSnapshot(
                shop_id=shop_id,
                date=report_date,
                type=ReportType.DAILY.value,
                metrics=metrics,
                ai_summary=ai_summary
            )
            self.db.add(snapshot)
        
        self.db.flush()
        
        logger.info(f"保存日报快照: shop_id={shop_id}, date={report_date}")
        
        return snapshot
    
    def get_daily_report(
        self,
        shop_id: int,
        report_date: date
    ) -> Optional[ReportSnapshot]:
        """
        获取日报快照
        
        Args:
            shop_id: 店铺ID
            report_date: 报表日期
            
        Returns:
            报表快照对象，如果不存在则返回None
        """
        return self.db.query(ReportSnapshot).filter(
            and_(
                ReportSnapshot.shop_id == shop_id,
                ReportSnapshot.date == report_date,
                ReportSnapshot.type == ReportType.DAILY.value
            )
        ).first()
    
    def get_report_history(
        self,
        shop_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        获取历史报表
        
        Args:
            shop_id: 店铺ID
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            page_size: 每页数量
            
        Returns:
            历史报表列表和分页信息
        """
        query = self.db.query(ReportSnapshot).filter(
            ReportSnapshot.shop_id == shop_id,
            ReportSnapshot.type == ReportType.DAILY.value
        )
        
        if start_date:
            query = query.filter(ReportSnapshot.date >= start_date)
        
        if end_date:
            query = query.filter(ReportSnapshot.date <= end_date)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        snapshots = query.order_by(ReportSnapshot.date.desc()).offset(offset).limit(page_size).all()
        
        return {
            'items': snapshots,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def compare_reports(
        self,
        shop_id: int,
        date1: date,
        date2: date
    ) -> Dict[str, Any]:
        """
        对比两个日期的报表
        
        Args:
            shop_id: 店铺ID
            date1: 日期1
            date2: 日期2
            
        Returns:
            对比结果
        """
        report1 = self.get_daily_report(shop_id, date1)
        report2 = self.get_daily_report(shop_id, date2)
        
        if not report1 or not report2:
            raise ValueError("报表不存在")
        
        metrics1 = report1.metrics
        metrics2 = report2.metrics
        
        # 计算变化
        def calc_change(old, new):
            if old == 0:
                return 0 if new == 0 else 100
            return ((new - old) / old) * 100
        
        comparison = {
            'date1': date1.isoformat(),
            'date2': date2.isoformat(),
            'gmv': {
                'date1': metrics1.get('gmv', 0),
                'date2': metrics2.get('gmv', 0),
                'change': calc_change(metrics1.get('gmv', 0), metrics2.get('gmv', 0))
            },
            'total_orders': {
                'date1': metrics1.get('total_orders', 0),
                'date2': metrics2.get('total_orders', 0),
                'change': calc_change(metrics1.get('total_orders', 0), metrics2.get('total_orders', 0))
            },
            'refund_rate': {
                'date1': metrics1.get('refund_rate', 0),
                'date2': metrics2.get('refund_rate', 0),
                'change': calc_change(metrics1.get('refund_rate', 0), metrics2.get('refund_rate', 0))
            },
            'profit_rate': {
                'date1': metrics1.get('profit_rate', 0),
                'date2': metrics2.get('profit_rate', 0),
                'change': calc_change(metrics1.get('profit_rate', 0), metrics2.get('profit_rate', 0))
            },
        }
        
        return comparison

