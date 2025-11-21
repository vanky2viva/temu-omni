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
    }
]

