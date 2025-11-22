"""ForgGPT 工具函数（Tool Functions）"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger

from app.services.statistics import StatisticsService
from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductCost
from app.models.shop import Shop


class ForgGPTTools:
    """ForgGPT 工具函数集合"""
    
    def __init__(self, db: Session):
        """
        初始化工具集合
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def get_order_statistics(
        self,
        shop_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取订单统计数据（深度聚合版）
        
        Args:
            shop_id: 店铺ID（可选）
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
            status: 订单状态（可选）
            
        Returns:
            统计数据字典
        """
        try:
            # 解析日期
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # 设置为当天的23:59:59
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
            
            # 解析状态
            order_status = None
            if status:
                try:
                    order_status = OrderStatus[status.upper()]
                except KeyError:
                    pass
            
            # 构建店铺ID列表
            shop_ids = [shop_id] if shop_id else None
            
            # 获取统计
            stats = StatisticsService.get_order_statistics(
                self.db,
                shop_ids=shop_ids,
                start_date=start_dt,
                end_date=end_dt,
                status=order_status
            )
            
            return {
                "success": True,
                "data": stats
            }
        except Exception as e:
            logger.error(f"获取订单统计失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def query_orders(
        self,
        shop_id: Optional[int] = None,
        sku: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 200
    ) -> Dict[str, Any]:
        """
        查询订单明细
        
        Args:
            shop_id: 店铺ID（可选）
            sku: SKU货号（可选）
            status: 订单状态（可选）
            start_time: 开始时间（YYYY-MM-DD格式）
            end_time: 结束时间（YYYY-MM-DD格式）
            limit: 返回数量限制（默认200）
            
        Returns:
            订单列表
        """
        try:
            query = self.db.query(Order)
            
            # 筛选条件
            if shop_id:
                query = query.filter(Order.shop_id == shop_id)
            
            if sku:
                query = query.filter(Order.product_sku == sku)
            
            if status:
                try:
                    order_status = OrderStatus[status.upper()]
                    query = query.filter(Order.status == order_status)
                except KeyError:
                    pass
            
            if start_time:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d')
                query = query.filter(Order.order_time >= start_dt)
            
            if end_time:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(Order.order_time <= end_dt)
            
            # 排序和限制
            orders = query.order_by(Order.order_time.desc()).limit(limit).all()
            
            # 转换为字典
            orders_data = []
            for order in orders:
                orders_data.append({
                    "order_sn": order.order_sn,
                    "product_name": order.product_name,
                    "product_sku": order.product_sku,
                    "quantity": order.quantity,
                    "total_price": float(order.total_price or 0),
                    "profit": float(order.profit or 0),
                    "status": order.status.value,
                    "order_time": order.order_time.isoformat() if order.order_time else None,
                    "shop_id": order.shop_id
                })
            
            return {
                "success": True,
                "count": len(orders_data),
                "data": orders_data
            }
        except Exception as e:
            logger.error(f"查询订单失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_product_sales(
        self,
        shop_id: Optional[int] = None,
        sku: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取指定SKU最近30天的销量和GMV
        
        Args:
            shop_id: 店铺ID（可选）
            sku: SKU货号（可选）
            
        Returns:
            销量和GMV数据
        """
        try:
            # 计算30天前
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # 构建查询
            query = self.db.query(
                Product.id,
                Product.product_name,
                Product.sku,
                func.sum(Order.quantity).label('total_sales'),
                func.sum(Order.total_price).label('total_gmv'),
                func.sum(Order.profit).label('total_profit')
            ).join(
                Order, Product.id == Order.product_id
            ).filter(
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
                Order.order_time >= thirty_days_ago
            )
            
            if shop_id:
                query = query.filter(Order.shop_id == shop_id)
            
            if sku:
                query = query.filter(Product.sku == sku)
            
            results = query.group_by(
                Product.id, Product.product_name, Product.sku
            ).all()
            
            # 转换为字典
            products_data = []
            for result in results:
                products_data.append({
                    "product_name": result.product_name,
                    "sku": result.sku,
                    "total_sales": int(result.total_sales or 0),
                    "total_gmv": float(result.total_gmv or 0),
                    "total_profit": float(result.total_profit or 0)
                })
            
            return {
                "success": True,
                "count": len(products_data),
                "data": products_data
            }
        except Exception as e:
            logger.error(f"获取商品销量失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_sku_profit(
        self,
        sku: str
    ) -> Dict[str, Any]:
        """
        获取 SKU 的利润结构
        
        Args:
            sku: SKU货号
            
        Returns:
            利润结构数据
        """
        try:
            # 查找商品
            product = self.db.query(Product).filter(Product.sku == sku).first()
            
            if not product:
                return {
                    "success": False,
                    "error": f"未找到SKU: {sku}"
                }
            
            # 获取当前成本价
            cost_record = self.db.query(ProductCost).filter(
                ProductCost.product_id == product.id,
                ProductCost.effective_to.is_(None)
            ).first()
            
            # 获取最近30天的销量和利润
            thirty_days_ago = datetime.now() - timedelta(days=30)
            sales_stats = self.db.query(
                func.sum(Order.quantity).label('total_sales'),
                func.sum(Order.total_price).label('total_gmv'),
                func.sum(Order.profit).label('total_profit')
            ).filter(
                Order.product_id == product.id,
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
                Order.order_time >= thirty_days_ago
            ).first()
            
            # 计算毛利率
            supply_price = float(product.current_price or 0)
            cost_price = float(cost_record.cost_price or 0) if cost_record else 0
            gross_margin = ((supply_price - cost_price) / supply_price * 100) if supply_price > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "sku": sku,
                    "product_name": product.product_name,
                    "supply_price": supply_price,
                    "cost_price": cost_price,
                    "gross_margin": round(gross_margin, 2),
                    "recent_30d_sales": int(sales_stats.total_sales or 0),
                    "recent_30d_gmv": float(sales_stats.total_gmv or 0),
                    "recent_30d_profit": float(sales_stats.total_profit or 0)
                }
            }
        except Exception as e:
            logger.error(f"获取SKU利润结构失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_shop_list(self) -> Dict[str, Any]:
        """
        获取所有店铺列表
        
        Returns:
            店铺列表
        """
        try:
            shops = self.db.query(Shop).all()
            
            shops_data = []
            for shop in shops:
                shops_data.append({
                    "id": shop.id,
                    "shop_name": shop.shop_name,
                    "environment": shop.environment.value,
                    "region": shop.region,
                    "is_active": shop.is_active
                })
            
            return {
                "success": True,
                "count": len(shops_data),
                "data": shops_data
            }
        except Exception as e:
            logger.error(f"获取店铺列表失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_collection_details(
        self,
        shop_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        order_sn: Optional[str] = None,
        limit: int = 500
    ) -> Dict[str, Any]:
        """
        获取回款详细数据（最小粒度，按订单级别）
        
        回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额
        
        Args:
            shop_id: 店铺ID（可选）
            start_date: 开始日期（回款日期范围，YYYY-MM-DD格式）
            end_date: 结束日期（回款日期范围，YYYY-MM-DD格式）
            order_sn: 订单号（精确匹配，可选）
            limit: 返回数量限制（默认500）
            
        Returns:
            回款详细数据列表
        """
        try:
            from sqlalchemy import func, and_, text, or_
            from datetime import timedelta
            
            # 回款日期 = delivery_time + 8天
            # 注意：价格已统一存储为CNY，直接使用total_price字段
            collection_date_expr = func.date(Order.delivery_time + text("INTERVAL '8 days'"))
            
            # 确定日期范围
            if not end_date:
                latest_delivery = self.db.query(func.max(Order.delivery_time)).filter(
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivery_time.isnot(None)
                ).scalar()
                
                if latest_delivery:
                    latest_delivery_date = latest_delivery.date() if isinstance(latest_delivery, datetime) else latest_delivery
                    end_date_dt = datetime.combine(latest_delivery_date + timedelta(days=15), datetime.min.time())
                else:
                    end_date_dt = datetime.now() + timedelta(days=7)
            else:
                end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_date_dt = end_date_dt.replace(hour=23, minute=59, second=59)
            
            if not start_date:
                start_date_dt = end_date_dt - timedelta(days=30)
            else:
                start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
            
            # 构建查询条件
            filters = [
                Order.status == OrderStatus.DELIVERED,
                Order.delivery_time.isnot(None),
                collection_date_expr >= start_date_dt.date(),
                collection_date_expr <= end_date_dt.date()
            ]
            
            if shop_id:
                filters.append(Order.shop_id == shop_id)
            
            if order_sn:
                filters.append(
                    or_(
                        Order.order_sn == order_sn,
                        Order.parent_order_sn == order_sn
                    )
                )
            
            # 查询数据
            results = self.db.query(
                Order.order_sn,
                Order.parent_order_sn,
                Shop.shop_name,
                Order.product_name,
                Order.product_sku,
                Order.quantity,
                Order.total_price,
                Order.delivery_time,
                collection_date_expr.label("collection_date"),
                Order.status
            ).join(
                Shop, Shop.id == Order.shop_id
            ).filter(
                and_(*filters)
            ).order_by(
                collection_date_expr.desc(),
                Order.order_time.desc()
            ).limit(limit).all()
            
            # 转换为字典
            # 注意：价格已统一存储为CNY，直接使用total_price字段
            collection_data = []
            for row in results:
                collection_amount = float(row.total_price or 0)
                
                collection_data.append({
                    "order_sn": row.order_sn,
                    "parent_order_sn": row.parent_order_sn,
                    "shop_name": row.shop_name,
                    "product_name": row.product_name or '',
                    "product_sku": row.product_sku or '',
                    "quantity": row.quantity or 0,
                    "total_price": float(row.total_price or 0),
                    "delivery_time": row.delivery_time.isoformat() if row.delivery_time else None,
                    "collection_date": row.collection_date.strftime("%Y-%m-%d") if row.collection_date else '',
                    "collection_amount": round(collection_amount, 2),
                    "order_status": row.status.value if row.status else ''
                })
            
            return {
                "success": True,
                "count": len(collection_data),
                "data": collection_data
            }
        except Exception as e:
            logger.error(f"获取回款详细数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_order_details(
        self,
        shop_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        order_sn: Optional[str] = None,
        product_sku: Optional[str] = None,
        limit: int = 200
    ) -> Dict[str, Any]:
        """
        获取订单详细数据（包含所有订单字段和关联信息）
        
        Args:
            shop_id: 店铺ID（可选）
            start_date: 开始日期（订单时间，YYYY-MM-DD格式）
            end_date: 结束日期（订单时间，YYYY-MM-DD格式）
            status: 订单状态（可选）
            order_sn: 订单号（模糊匹配，可选）
            product_sku: 商品SKU（模糊匹配，可选）
            limit: 返回数量限制（默认200）
            
        Returns:
            订单详细数据列表
        """
        try:
            from sqlalchemy import or_
            
            query = self.db.query(Order, Shop.shop_name).outerjoin(
                Shop, Shop.id == Order.shop_id
            )
            
            # 应用过滤条件
            filters = []
            
            if shop_id:
                filters.append(Order.shop_id == shop_id)
            
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                filters.append(Order.order_time >= start_dt)
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                filters.append(Order.order_time <= end_dt)
            
            if status:
                try:
                    order_status = OrderStatus[status.upper()]
                    filters.append(Order.status == order_status)
                except KeyError:
                    pass
            
            if order_sn:
                filters.append(
                    or_(
                        Order.order_sn.ilike(f"%{order_sn}%"),
                        Order.parent_order_sn.ilike(f"%{order_sn}%")
                    )
                )
            
            if product_sku:
                filters.append(Order.product_sku.ilike(f"%{product_sku}%"))
            
            if filters:
                query = query.filter(and_(*filters))
            
            # 排序和限制
            orders = query.order_by(Order.order_time.desc()).limit(limit).all()
            
            # 转换为字典
            orders_data = []
            for order, shop_name in orders:
                orders_data.append({
                    "id": order.id,
                    "order_sn": order.order_sn,
                    "parent_order_sn": order.parent_order_sn,
                    "temu_order_id": order.temu_order_id,
                    "shop_id": order.shop_id,
                    "shop_name": shop_name,
                    "product_id": order.product_id,
                    "product_name": order.product_name,
                    "product_sku": order.product_sku,
                    "spu_id": order.spu_id,
                    "quantity": order.quantity or 0,
                    "unit_price": float(order.unit_price or 0),
                    "total_price": float(order.total_price or 0),
                    "currency": order.currency or 'USD',
                    "unit_cost": float(order.unit_cost) if order.unit_cost else None,
                    "total_cost": float(order.total_cost) if order.total_cost else None,
                    "profit": float(order.profit) if order.profit else None,
                    "status": order.status.value if order.status else '',
                    "order_time": order.order_time.isoformat() if order.order_time else '',
                    "payment_time": order.payment_time.isoformat() if order.payment_time else None,
                    "shipping_time": order.shipping_time.isoformat() if order.shipping_time else None,
                    "delivery_time": order.delivery_time.isoformat() if order.delivery_time else None,
                    "expect_ship_latest_time": order.expect_ship_latest_time.isoformat() if order.expect_ship_latest_time else None,
                    "customer_id": order.customer_id,
                    "shipping_country": order.shipping_country,
                    "shipping_city": order.shipping_city,
                    "shipping_province": order.shipping_province,
                    "shipping_postal_code": order.shipping_postal_code,
                })
            
            return {
                "success": True,
                "count": len(orders_data),
                "data": orders_data
            }
        except Exception as e:
            logger.error(f"获取订单详细数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_collection_statistics(
        self,
        shop_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取回款统计数据（汇总数据，按日期和店铺分组）
        
        回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额
        
        Args:
            shop_id: 店铺ID（可选）
            start_date: 开始日期（回款日期范围，YYYY-MM-DD格式）
            end_date: 结束日期（回款日期范围，YYYY-MM-DD格式）
            days: 天数（如果未提供日期范围，默认30天）
            
        Returns:
            回款统计数据，包含：
            - summary: 汇总信息（总回款金额、总订单数、店铺列表）
            - table_data: 表格数据（按日期和店铺分组的回款金额）
            - chart_data: 图表数据（日期列表和每个店铺的折线图数据）
        """
        try:
            from sqlalchemy import func, and_, text
            from datetime import timedelta
            
            # 回款日期 = delivery_time + 8天
            # 注意：价格已统一存储为CNY，直接使用total_price字段
            collection_date_expr = func.date(Order.delivery_time + text("INTERVAL '8 days'"))
            
            # 确定日期范围
            if not end_date:
                latest_delivery = self.db.query(func.max(Order.delivery_time)).filter(
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivery_time.isnot(None)
                ).scalar()
                
                if latest_delivery:
                    latest_delivery_date = latest_delivery.date() if isinstance(latest_delivery, datetime) else latest_delivery
                    end_date_dt = datetime.combine(latest_delivery_date + timedelta(days=15), datetime.min.time())
                else:
                    end_date_dt = datetime.now() + timedelta(days=7)
            else:
                end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_date_dt = end_date_dt.replace(hour=23, minute=59, second=59)
            
            if not start_date:
                start_date_dt = end_date_dt - timedelta(days=days)
            else:
                start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
            
            # 构建查询条件
            filters = [
                Order.status == OrderStatus.DELIVERED,
                Order.delivery_time.isnot(None),
                collection_date_expr >= start_date_dt.date(),
                collection_date_expr <= end_date_dt.date()
            ]
            
            if shop_id:
                filters.append(Order.shop_id == shop_id)
            
            # 按店铺和回款日期分组统计
            # 注意：价格已统一存储为CNY，直接使用total_price字段
            results = self.db.query(
                Shop.id.label("shop_id"),
                Shop.shop_name,
                collection_date_expr.label("collection_date"),
                func.sum(Order.total_price).label("collection_amount"),
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
            total_collection = self.db.query(
                func.sum(Order.total_price).label("total_amount"),
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
                "success": True,
                "data": {
                    "summary": {
                        "total_amount": float(total_collection.total_amount or 0),
                        "total_orders": int(total_collection.total_orders or 0),
                        "shops": sorted(list(shop_list))
                    },
                    "table_data": table_data,
                    "chart_data": {
                        "dates": date_list,
                        "series": chart_series
                    },
                    "period": {
                        "start_date": start_date_dt.isoformat(),
                        "end_date": end_date_dt.isoformat(),
                        "days": days
                    }
                }
            }
        except Exception as e:
            logger.error(f"获取回款统计数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_product_cost_details(
        self,
        product_id: Optional[int] = None,
        product_id_temu: Optional[str] = None,
        sku: Optional[str] = None,
        include_history: bool = True
    ) -> Dict[str, Any]:
        """
        获取商品成本详细数据（包含历史成本记录）
        
        Args:
            product_id: 商品ID（数据库ID，可选）
            product_id_temu: Temu商品ID（可选）
            sku: 商品SKU（可选）
            include_history: 是否包含历史成本记录（默认True）
            
        Returns:
            商品成本详细数据
        """
        try:
            query = self.db.query(Product)
            
            filters = []
            
            if product_id:
                filters.append(Product.id == product_id)
            
            if product_id_temu:
                filters.append(Product.product_id == product_id_temu)
            
            if sku:
                filters.append(Product.sku == sku)
            
            if filters:
                query = query.filter(and_(*filters))
            
            products = query.limit(10).all()
            
            if not products:
                return {
                    "success": False,
                    "error": "未找到匹配的商品"
                }
            
            # 转换为字典
            cost_data = []
            for product in products:
                # 获取当前成本
                current_cost = self.db.query(ProductCost).filter(
                    ProductCost.product_id == product.id,
                    ProductCost.effective_to.is_(None)
                ).first()
                
                # 获取历史成本记录
                cost_history = []
                if include_history:
                    history_costs = self.db.query(ProductCost).filter(
                        ProductCost.product_id == product.id
                    ).order_by(ProductCost.effective_from.desc()).all()
                    
                    for cost in history_costs:
                        cost_history.append({
                            "cost_price": float(cost.cost_price or 0),
                            "currency": cost.currency or 'USD',
                            "effective_from": cost.effective_from.isoformat() if cost.effective_from else None,
                            "effective_to": cost.effective_to.isoformat() if cost.effective_to else None,
                            "notes": cost.notes,
                            "created_at": cost.created_at.isoformat() if cost.created_at else None,
                        })
                
                cost_data.append({
                    "product_id": product.id,
                    "product_name": product.product_name or '',
                    "sku": product.sku or '',
                    "product_id_temu": product.product_id,
                    "current_cost": float(current_cost.cost_price) if current_cost and current_cost.cost_price else None,
                    "current_cost_currency": current_cost.currency if current_cost else None,
                    "current_cost_effective_from": current_cost.effective_from.isoformat() if current_cost and current_cost.effective_from else None,
                    "cost_history": cost_history,
                })
            
            return {
                "success": True,
                "count": len(cost_data),
                "data": cost_data
            }
        except Exception as e:
            logger.error(f"获取商品成本详细数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 工具描述（Tool Schema）定义
TOOLS_SCHEMA = [
    {
        "name": "get_order_statistics",
        "description": "获取订单统计数据（GMV、订单量、利润、退款率）。支持店铺、时间范围、状态过滤。",
        "parameters": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "type": "integer",
                    "description": "店铺ID（可选）"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD格式）"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD格式）"
                },
                "status": {
                    "type": "string",
                    "description": "订单状态（可选：PENDING, PAID, SHIPPED, DELIVERED, RECEIPTED, CANCELLED, REFUNDED）"
                }
            }
        }
    },
    {
        "name": "query_orders",
        "description": "查询订单明细，可按状态、SKU、时间范围筛选",
        "parameters": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "type": "integer",
                    "description": "店铺ID（可选）"
                },
                "sku": {
                    "type": "string",
                    "description": "SKU货号（可选）"
                },
                "status": {
                    "type": "string",
                    "description": "订单状态（可选）"
                },
                "start_time": {
                    "type": "string",
                    "description": "开始时间（YYYY-MM-DD格式）"
                },
                "end_time": {
                    "type": "string",
                    "description": "结束时间（YYYY-MM-DD格式）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制（默认200）",
                    "default": 200
                }
            }
        }
    },
    {
        "name": "get_product_sales",
        "description": "获取指定SKU最近30天的销量和GMV",
        "parameters": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "type": "integer",
                    "description": "店铺ID（可选）"
                },
                "sku": {
                    "type": "string",
                    "description": "SKU货号（可选）"
                }
            }
        }
    },
    {
        "name": "get_sku_profit",
        "description": "获取 SKU 的利润结构（价格、成本、毛利额、毛利率）",
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "SKU货号",
                    "required": True
                }
            },
            "required": ["sku"]
        }
    },
    {
        "name": "get_shop_list",
        "description": "获取所有店铺列表",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_collection_details",
        "description": "获取回款详细数据（最小粒度，按订单级别）。回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额。返回每个订单的回款信息，包括订单号、商品信息、回款日期、回款金额等。",
        "parameters": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "type": "integer",
                    "description": "店铺ID（可选）"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期（回款日期范围，YYYY-MM-DD格式）"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期（回款日期范围，YYYY-MM-DD格式）"
                },
                "order_sn": {
                    "type": "string",
                    "description": "订单号（精确匹配，可选）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制（默认500）",
                    "default": 500
                }
            }
        }
    },
    {
        "name": "get_order_details",
        "description": "获取订单详细数据（包含所有订单字段和关联信息）。返回订单的完整信息，包括订单号、商品信息、价格、成本、利润、状态、时间信息、客户信息等。",
        "parameters": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "type": "integer",
                    "description": "店铺ID（可选）"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期（订单时间，YYYY-MM-DD格式）"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期（订单时间，YYYY-MM-DD格式）"
                },
                "status": {
                    "type": "string",
                    "description": "订单状态（可选：PENDING, PAID, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED）"
                },
                "order_sn": {
                    "type": "string",
                    "description": "订单号（模糊匹配，可选）"
                },
                "product_sku": {
                    "type": "string",
                    "description": "商品SKU（模糊匹配，可选）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制（默认200）",
                    "default": 200
                }
            }
        }
    },
    {
        "name": "get_product_cost_details",
        "description": "获取商品成本详细数据（包含历史成本记录）。返回商品的当前成本和历史成本记录，包括成本价格、生效时间、货币等信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "商品ID（数据库ID，可选）"
                },
                "product_id_temu": {
                    "type": "string",
                    "description": "Temu商品ID（可选）"
                },
                "sku": {
                    "type": "string",
                    "description": "商品SKU（可选）"
                },
                "include_history": {
                    "type": "boolean",
                    "description": "是否包含历史成本记录（默认True）",
                    "default": True
                }
            }
        }
    },
    {
        "name": "get_collection_statistics",
        "description": "【重要】获取回款统计数据（汇总数据，按日期和店铺分组）。这是获取回款金额的主要接口。当用户询问回款、收款、回款金额、回款统计、财务管理中的回款数据时，必须使用此工具。回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额。返回总回款金额、每日回款金额（按店铺分组）、回款趋势等数据。",
        "parameters": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "type": "integer",
                    "description": "店铺ID（可选）"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期（回款日期范围，YYYY-MM-DD格式）"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期（回款日期范围，YYYY-MM-DD格式）"
                },
                "days": {
                    "type": "integer",
                    "description": "天数（如果未提供日期范围，默认30天）",
                    "default": 30
                }
            }
        }
    }
]


