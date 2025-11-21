"""数据映射服务

负责将原始数据层（raw表）的数据映射到业务表（领域模型层）。
支持字段重命名、类型转换、枚举值本地化等。
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from loguru import logger

from app.models.temu_orders_raw import TemuOrdersRaw
from app.models.temu_products_raw import TemuProductsRaw
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product


class DataMappingError(Exception):
    """数据映射错误"""
    pass


class DataMappingService:
    """数据映射服务"""
    
    def __init__(self, db: Session):
        """
        初始化数据映射服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def map_order_from_raw(self, raw_order: TemuOrdersRaw) -> Dict[str, Any]:
        """
        从原始订单数据映射到业务订单数据
        
        Args:
            raw_order: 原始订单数据
            
        Returns:
            映射后的订单数据字典
            
        Raises:
            DataMappingError: 映射失败时抛出
        """
        try:
            raw_json = raw_order.raw_json
            
            # 提取订单基本信息
            # 注意：这里的字段路径需要根据实际Temu API响应格式调整
            order_sn = self._get_nested_value(raw_json, ['orderSn', 'order_sn', 'orderSn'])
            temu_order_id = self._get_nested_value(raw_json, ['orderId', 'order_id', 'orderId'])
            parent_order_sn = self._get_nested_value(raw_json, ['parentOrderSn', 'parent_order_sn'], default=None)
            
            # 提取价格信息
            total_price = self._parse_decimal(self._get_nested_value(raw_json, ['totalAmount', 'total_amount', 'totalPrice', 'total_price']))
            unit_price = self._parse_decimal(self._get_nested_value(raw_json, ['unitPrice', 'unit_price', 'price']))
            currency = self._get_nested_value(raw_json, ['currency', 'currencyCode'], default='USD')
            
            # 提取时间信息
            order_time = self._parse_datetime(self._get_nested_value(raw_json, ['orderTime', 'order_time', 'createTime', 'create_time']))
            payment_time = self._parse_datetime(self._get_nested_value(raw_json, ['paymentTime', 'payment_time'], default=None))
            shipping_time = self._parse_datetime(self._get_nested_value(raw_json, ['shippingTime', 'shipping_time', 'shipTime'], default=None))
            delivery_time = self._parse_datetime(self._get_nested_value(raw_json, ['deliveryTime', 'delivery_time', 'deliveredTime'], default=None))
            expect_ship_latest_time = self._parse_datetime(self._get_nested_value(raw_json, ['expectShipLatestTime', 'expect_ship_latest_time', 'shipDeadline'], default=None))
            
            # 提取订单状态（需要映射到本地枚举）
            status_str = self._get_nested_value(raw_json, ['status', 'orderStatus', 'order_status'], default='PENDING')
            status = self._map_order_status(status_str)
            
            # 提取客户信息
            customer_id = self._get_nested_value(raw_json, ['customerId', 'customer_id', 'buyerId'], default=None)
            shipping_country = self._get_nested_value(raw_json, ['shippingCountry', 'shipping_country', 'country'], default=None)
            shipping_city = self._get_nested_value(raw_json, ['shippingCity', 'shipping_city', 'city'], default=None)
            shipping_province = self._get_nested_value(raw_json, ['shippingProvince', 'shipping_province', 'province', 'state'], default=None)
            shipping_postal_code = self._get_nested_value(raw_json, ['shippingPostalCode', 'shipping_postal_code', 'postalCode', 'zipCode'], default=None)
            
            # 提取商品信息（订单可能包含多个商品）
            order_items_data = self._extract_order_items(raw_json)
            
            # 构建订单数据
            order_data = {
                'shop_id': raw_order.shop_id,
                'order_sn': order_sn or temu_order_id,
                'temu_order_id': temu_order_id,
                'parent_order_sn': parent_order_sn,
                'total_price': total_price,
                'unit_price': unit_price or total_price,  # 如果没有单价，使用总价
                'currency': currency,
                'status': status,
                'order_time': order_time or datetime.utcnow(),
                'payment_time': payment_time,
                'shipping_time': shipping_time,
                'delivery_time': delivery_time,
                'expect_ship_latest_time': expect_ship_latest_time,
                'customer_id': customer_id,
                'shipping_country': shipping_country,
                'shipping_city': shipping_city,
                'shipping_province': shipping_province,
                'shipping_postal_code': shipping_postal_code,
                'raw_data_id': raw_order.id,
                'order_items': order_items_data,
            }
            
            # 如果有商品信息，提取第一个作为主商品（兼容现有结构）
            if order_items_data:
                first_item = order_items_data[0]
                order_data.update({
                    'product_name': first_item.get('product_name'),
                    'product_sku': first_item.get('product_sku'),
                    'spu_id': first_item.get('spu_id'),
                    'quantity': first_item.get('quantity', 1),
                })
            
            return order_data
            
        except Exception as e:
            logger.error(f"映射订单数据失败 (raw_id={raw_order.id}): {e}")
            raise DataMappingError(f"映射订单数据失败: {e}")
    
    def map_product_from_raw(self, raw_product: TemuProductsRaw) -> Dict[str, Any]:
        """
        从原始商品数据映射到业务商品数据
        
        Args:
            raw_product: 原始商品数据
            
        Returns:
            映射后的商品数据字典
            
        Raises:
            DataMappingError: 映射失败时抛出
        """
        try:
            raw_json = raw_product.raw_json
            
            # 提取商品基本信息
            product_id = self._get_nested_value(raw_json, ['productId', 'product_id', 'id'])
            product_name = self._get_nested_value(raw_json, ['productName', 'product_name', 'name', 'title'])
            sku = self._get_nested_value(raw_json, ['sku', 'skuCode', 'sku_code', 'extCode'], default=None)
            spu_id = self._get_nested_value(raw_json, ['spuId', 'spu_id', 'spuId'], default=None)
            skc_id = self._get_nested_value(raw_json, ['skcId', 'skc_id'], default=None)
            
            # 提取价格信息
            current_price = self._parse_decimal(self._get_nested_value(raw_json, ['price', 'currentPrice', 'current_price', 'salePrice'], default=None))
            currency = self._get_nested_value(raw_json, ['currency', 'currencyCode'], default='USD')
            
            # 提取库存信息
            stock_quantity = self._parse_int(self._get_nested_value(raw_json, ['stock', 'stockQuantity', 'stock_quantity', 'inventory'], default=0))
            
            # 提取销售信息
            total_sales = self._parse_int(self._get_nested_value(raw_json, ['totalSales', 'total_sales', 'sales'], default=0))
            listed_at = self._parse_datetime(self._get_nested_value(raw_json, ['listedAt', 'listed_at', 'listTime', 'createTime'], default=None))
            
            # 提取其他信息
            description = self._get_nested_value(raw_json, ['description', 'desc', 'detail'], default=None)
            image_url = self._get_nested_value(raw_json, ['mainImage', 'main_image', 'image', 'imageUrl'], default=None)
            category = self._get_nested_value(raw_json, ['category', 'categoryName', 'category_name'], default=None)
            manager = self._get_nested_value(raw_json, ['manager', 'managerName'], default=None)
            price_status = self._get_nested_value(raw_json, ['priceStatus', 'price_status'], default=None)
            is_active = self._parse_bool(self._get_nested_value(raw_json, ['isActive', 'is_active', 'onSale', 'status'], default=True))
            
            # 构建商品数据
            product_data = {
                'shop_id': raw_product.shop_id,
                'product_id': str(product_id),
                'product_name': product_name or 'Unknown Product',
                'sku': sku or str(product_id),
                'spu_id': spu_id,
                'skc_id': skc_id,
                'current_price': current_price,
                'currency': currency,
                'stock_quantity': stock_quantity,
                'total_sales': total_sales,
                'listed_at': listed_at,
                'description': description,
                'image_url': image_url,
                'category': category,
                'manager': manager,
                'price_status': price_status,
                'is_active': is_active,
                'raw_data_id': raw_product.id,
            }
            
            return product_data
            
        except Exception as e:
            logger.error(f"映射商品数据失败 (raw_id={raw_product.id}): {e}")
            raise DataMappingError(f"映射商品数据失败: {e}")
    
    def _extract_order_items(self, raw_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        提取订单商品明细
        
        Args:
            raw_json: 原始订单JSON数据
            
        Returns:
            订单明细列表
        """
        items = []
        
        # 尝试多种可能的字段路径
        items_data = (
            self._get_nested_value(raw_json, ['items', 'orderItems', 'order_items', 'products'], default=None) or
            [raw_json]  # 如果没有items字段，将整个订单作为一个item
        )
        
        if not isinstance(items_data, list):
            items_data = [items_data]
        
        for item_data in items_data:
            if not isinstance(item_data, dict):
                continue
            
            sku_id = self._get_nested_value(item_data, ['skuId', 'sku_id', 'productSkuId', 'product_sku_id'])
            product_name = self._get_nested_value(item_data, ['productName', 'product_name', 'name'])
            product_sku = self._get_nested_value(item_data, ['sku', 'skuCode', 'extCode', 'productSku'])
            spu_id = self._get_nested_value(item_data, ['spuId', 'spu_id'], default=None)
            quantity = self._parse_int(self._get_nested_value(item_data, ['quantity', 'qty', 'count'], default=1))
            price = self._parse_decimal(self._get_nested_value(item_data, ['price', 'unitPrice', 'unit_price']))
            total_price = self._parse_decimal(self._get_nested_value(item_data, ['totalPrice', 'total_price', 'amount']))
            currency = self._get_nested_value(item_data, ['currency', 'currencyCode'], default='USD')
            
            if sku_id or product_name:
                items.append({
                    'sku_id': str(sku_id) if sku_id else None,
                    'product_name': product_name,
                    'product_sku': product_sku,
                    'spu_id': spu_id,
                    'quantity': quantity,
                    'price': price or Decimal('0'),
                    'total_price': total_price or (price * quantity if price else Decimal('0')),
                    'currency': currency,
                })
        
        return items
    
    def _get_nested_value(self, data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
        """
        从嵌套字典中获取值，尝试多个可能的键
        
        Args:
            data: 数据字典
            keys: 可能的键列表
            default: 默认值
            
        Returns:
            找到的值或默认值
        """
        for key in keys:
            if key in data:
                return data[key]
        return default
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """解析为Decimal类型"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def _parse_int(self, value: Any, default: int = 0) -> int:
        """解析为整数"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _parse_bool(self, value: Any, default: bool = True) -> bool:
        """解析为布尔值"""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """解析为datetime类型"""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            # 尝试多种日期格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%d',
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        
        try:
            # 尝试时间戳
            return datetime.fromtimestamp(int(value))
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _map_order_status(self, status_str: str) -> OrderStatus:
        """
        将Temu订单状态映射到本地枚举
        
        Args:
            status_str: Temu状态字符串
            
        Returns:
            本地订单状态枚举
        """
        status_map = {
            'PENDING': OrderStatus.PENDING,
            'PAID': OrderStatus.PAID,
            'PROCESSING': OrderStatus.PROCESSING,
            'SHIPPED': OrderStatus.SHIPPED,
            'DELIVERED': OrderStatus.DELIVERED,
            'COMPLETED': OrderStatus.COMPLETED,
            'CANCELLED': OrderStatus.CANCELLED,
            'REFUNDED': OrderStatus.REFUNDED,
            # 可能的Temu状态值（需要根据实际API调整）
            '待支付': OrderStatus.PENDING,
            '已支付': OrderStatus.PAID,
            '处理中': OrderStatus.PROCESSING,
            '已发货': OrderStatus.SHIPPED,
            '已送达': OrderStatus.DELIVERED,
            '已完成': OrderStatus.COMPLETED,
            '已取消': OrderStatus.CANCELLED,
            '已退款': OrderStatus.REFUNDED,
        }
        
        status_str_upper = str(status_str).upper()
        return status_map.get(status_str_upper, status_map.get(status_str, OrderStatus.PENDING))
    
    def save_mapped_order(self, order_data: Dict[str, Any], raw_order: TemuOrdersRaw) -> Order:
        """
        将映射后的订单数据保存到业务表
        
        Args:
            order_data: 映射后的订单数据
            raw_order: 原始订单数据
            
        Returns:
            保存的订单对象
        """
        # 查找或创建订单
        order = self.db.query(Order).filter(
            Order.temu_order_id == order_data['temu_order_id'],
            Order.shop_id == raw_order.shop_id
        ).first()
        
        if order:
            # 更新现有订单
            for key, value in order_data.items():
                if key != 'order_items' and hasattr(order, key):
                    setattr(order, key, value)
            order.raw_data_id = raw_order.id
        else:
            # 创建新订单
            order = Order(**{k: v for k, v in order_data.items() if k != 'order_items'})
            order.raw_data_id = raw_order.id
            self.db.add(order)
            self.db.flush()  # 获取ID
        
        # 保存订单明细
        order_items_data = order_data.get('order_items', [])
        if order_items_data:
            # 删除旧的订单明细
            self.db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()
            
            # 创建新的订单明细
            for item_data in order_items_data:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data
                )
                self.db.add(order_item)
        
        return order
    
    def save_mapped_product(self, product_data: Dict[str, Any], raw_product: TemuProductsRaw) -> Product:
        """
        将映射后的商品数据保存到业务表
        
        Args:
            product_data: 映射后的商品数据
            raw_product: 原始商品数据
            
        Returns:
            保存的商品对象
        """
        # 查找或创建商品
        product = self.db.query(Product).filter(
            Product.product_id == product_data['product_id'],
            Product.shop_id == raw_product.shop_id
        ).first()
        
        if product:
            # 更新现有商品
            for key, value in product_data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            product.raw_data_id = raw_product.id
        else:
            # 创建新商品
            product = Product(**product_data)
            product.raw_data_id = raw_product.id
            self.db.add(product)
        
        return product

