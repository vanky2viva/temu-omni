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
from app.utils.currency import CurrencyConverter


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
        
        注意：raw_json的结构是：
        {
            'parentOrderMap': {...},  # 父订单信息
            'orderItem': {...},       # 子订单信息
            'fullOrderData': {...}    # 完整订单数据
        }
        
        Args:
            raw_order: 原始订单数据
            
        Returns:
            映射后的订单数据字典
            
        Raises:
            DataMappingError: 映射失败时抛出
        """
        try:
            raw_json = raw_order.raw_json
            
            # 从嵌套结构中提取数据
            parent_order = raw_json.get('parentOrderMap', {})
            order_item = raw_json.get('orderItem', {})
            
            # 如果结构不同，尝试直接从raw_json获取
            if not parent_order and not order_item:
                parent_order = raw_json
                order_item = raw_json
            
            # 提取订单基本信息（优先从orderItem，其次从parentOrderMap）
            order_sn = (
                order_item.get('orderSn') or
                parent_order.get('orderSn') or
                raw_json.get('orderSn')
            )
            temu_order_id = order_sn  # Temu订单ID就是订单号
            parent_order_sn = parent_order.get('parentOrderSn')
            
            # 提取价格信息（优先从orderItem）
            total_price = self._parse_decimal(
                order_item.get('goodsTotalPrice') or
                order_item.get('totalPrice') or
                order_item.get('amount') or
                parent_order.get('totalPrice')
            )
            unit_price = self._parse_decimal(
                order_item.get('goodsPrice') or
                order_item.get('unitPrice') or
                order_item.get('price') or
                parent_order.get('unitPrice')
            )
            currency = order_item.get('currency') or parent_order.get('currency') or 'USD'
            
            # 提取时间信息（主要在parentOrderMap中）
            order_time = self._parse_datetime(
                parent_order.get('parentOrderTime') or
                parent_order.get('orderTime') or
                parent_order.get('createTime')
            )
            payment_time = self._parse_datetime(
                parent_order.get('paymentTime') or
                parent_order.get('payTime')
            )
            shipping_time = self._parse_datetime(
                parent_order.get('parentShippingTime') or
                order_item.get('orderShippingTime') or
                parent_order.get('shippingTime') or
                parent_order.get('shipTime')
            )
            delivery_time = self._parse_datetime(
                (parent_order.get('updateTime') if parent_order.get('parentOrderStatus') == 5 else None) or
                parent_order.get('latestDeliveryTime') or
                parent_order.get('deliveryTime')
            )
            expect_ship_latest_time = self._parse_datetime(
                parent_order.get('expectShipLatestTime')
            )
            
            # 提取订单状态（从parentOrderMap）
            parent_order_status = parent_order.get('parentOrderStatus', 0)
            status = self._map_order_status_from_code(parent_order_status)
            
            # 提取客户信息
            customer_id = parent_order.get('customerId') or parent_order.get('buyerId')
            
            # 提取地址信息
            shipping_info = parent_order.get('shippingInfo') or parent_order.get('address') or {}
            shipping_country = (
                shipping_info.get('country') or
                shipping_info.get('countryName') or
                parent_order.get('shippingCountry')
            )
            shipping_city = (
                shipping_info.get('city') or
                shipping_info.get('cityName') or
                parent_order.get('shippingCity')
            )
            shipping_province = (
                shipping_info.get('province') or
                shipping_info.get('provinceName') or
                shipping_info.get('state') or
                parent_order.get('shippingProvince')
            )
            shipping_postal_code = (
                shipping_info.get('postalCode') or
                shipping_info.get('zipCode') or
                parent_order.get('shippingPostalCode')
            )
            
            # 提取商品信息（从orderItem的productList）
            order_items_data = self._extract_order_items_from_structure(order_item, parent_order)
            
            # 构建订单数据
            order_data = {
                'shop_id': raw_order.shop_id,
                'order_sn': order_sn,
                'temu_order_id': temu_order_id,
                'parent_order_sn': parent_order_sn,
                'total_price': total_price or Decimal('0'),
                'unit_price': unit_price or total_price or Decimal('0'),
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
            
            # 如果价格信息缺失（为0），尝试从商品表中获取价格
            if (total_price is None or total_price == Decimal('0')) and order_data.get('product_sku'):
                product = self.db.query(Product).filter(
                    Product.shop_id == raw_order.shop_id,
                    Product.sku == order_data.get('product_sku')
                ).first()
                
                if product and product.current_price:
                    # 使用商品价格计算订单金额
                    quantity = order_data.get('quantity', 1)
                    unit_price_from_product = product.current_price
                    
                    # 货币转换（USD转CNY）
                    if product.currency == 'USD':
                        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
                        unit_price_cny = unit_price_from_product * Decimal(str(usd_rate))
                    else:
                        unit_price_cny = unit_price_from_product
                    
                    total_price_cny = unit_price_cny * quantity
                    
                    # 更新订单数据
                    order_data['unit_price'] = unit_price_cny
                    order_data['total_price'] = total_price_cny
                    order_data['currency'] = 'CNY'
                    
                    logger.info(
                        f"订单 {order_sn} 价格从商品表中获取: "
                        f"商品SKU={order_data.get('product_sku')}, "
                        f"商品价格={product.current_price} {product.currency}, "
                        f"订单单价={unit_price_cny} CNY, "
                        f"订单总价={total_price_cny} CNY"
                    )
            
            return order_data
            
        except Exception as e:
            logger.error(f"映射订单数据失败 (raw_id={raw_order.id}): {e}")
            import traceback
            logger.error(traceback.format_exc())
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
    
    def _map_order_status_from_code(self, status_code: int) -> OrderStatus:
        """
        将Temu订单状态码映射到本地枚举
        
        根据 Temu API 状态码对应关系：
        - 0: 全部（默认待处理）
        - 1: 待处理 (PENDING)
        - 2: 未发货 (PROCESSING)
        - 3: 已取消 (CANCELLED)
        - 4: 已发货 (SHIPPED)
        - 5: 已送达 (DELIVERED)
        - 41: 部分发货 (SHIPPED)
        - 51: 部分送达 (DELIVERED)
        
        Args:
            status_code: Temu订单状态码
            
        Returns:
            本地订单状态枚举
        """
        order_status_map = {
            0: OrderStatus.PENDING,      # 全部（默认待处理）
            1: OrderStatus.PENDING,      # 待处理
            2: OrderStatus.PROCESSING,   # 未发货
            3: OrderStatus.CANCELLED,    # 已取消
            4: OrderStatus.SHIPPED,      # 已发货 / 部分发货
            5: OrderStatus.DELIVERED,    # 已送达 / 部分送达
            41: OrderStatus.SHIPPED,     # 部分发货（视为已发货）
            51: OrderStatus.DELIVERED,   # 部分送达（视为已送达）
        }
        return order_status_map.get(status_code, OrderStatus.PENDING)
    
    def _extract_order_items_from_structure(
        self, 
        order_item: Dict[str, Any], 
        parent_order: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        从orderItem和parentOrderMap结构中提取订单商品明细
        
        Args:
            order_item: 子订单数据
            parent_order: 父订单数据
            
        Returns:
            订单明细列表
        """
        items = []
        
        # 从orderItem的productList中提取商品信息
        product_list = order_item.get('productList', [])
        
        if product_list and len(product_list) > 0:
            # 有productList，提取每个商品
            for product_info in product_list:
                product_sku_id = product_info.get('productSkuId')
                product_sku = product_info.get('extCode') or ''
                product_id_value = product_info.get('productId')
                spu_id = str(product_id_value) if product_id_value is not None else ''
                
                product_name = (
                    order_item.get('goodsName') or
                    order_item.get('productName') or
                    order_item.get('spec') or
                    'Unknown Product'
                )
                
                quantity = order_item.get('goodsNumber') or order_item.get('quantity') or 1
                unit_price = self._parse_decimal(
                    order_item.get('goodsPrice') or
                    order_item.get('unitPrice') or
                    order_item.get('price')
                )
                total_price = self._parse_decimal(
                    order_item.get('goodsTotalPrice') or
                    order_item.get('totalPrice') or
                    order_item.get('amount')
                )
                currency = order_item.get('currency') or parent_order.get('currency') or 'USD'
                
                items.append({
                    'sku_id': str(product_sku_id) if product_sku_id else None,
                    'product_name': product_name,
                    'product_sku': product_sku,
                    'spu_id': spu_id,
                    'quantity': quantity,
                    'price': unit_price or Decimal('0'),
                    'total_price': total_price or (unit_price * quantity if unit_price else Decimal('0')),
                    'currency': currency,
                })
        else:
            # 没有productList，将orderItem作为一个商品
            product_sku = order_item.get('extCode') or ''
            spu_id_value = order_item.get('spuId') or order_item.get('spu_id')
            spu_id = str(spu_id_value) if spu_id_value is not None else ''
            
            product_name = (
                order_item.get('goodsName') or
                order_item.get('productName') or
                order_item.get('spec') or
                'Unknown Product'
            )
            
            quantity = order_item.get('goodsNumber') or order_item.get('quantity') or 1
            unit_price = self._parse_decimal(
                order_item.get('goodsPrice') or
                order_item.get('unitPrice') or
                order_item.get('price')
            )
            total_price = self._parse_decimal(
                order_item.get('goodsTotalPrice') or
                order_item.get('totalPrice') or
                order_item.get('amount')
            )
            currency = order_item.get('currency') or parent_order.get('currency') or 'USD'
            
            items.append({
                'sku_id': None,
                'product_name': product_name,
                'product_sku': product_sku,
                'spu_id': spu_id,
                'quantity': quantity,
                'price': unit_price or Decimal('0'),
                'total_price': total_price or (unit_price * quantity if unit_price else Decimal('0')),
                'currency': currency,
            })
        
        return items
    
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

