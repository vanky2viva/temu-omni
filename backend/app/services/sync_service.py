"""数据同步服务 - 从Temu API同步数据到数据库"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from loguru import logger

from app.models.shop import Shop
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.services.temu_service import TemuService, get_temu_service


class SyncService:
    """数据同步服务"""
    
    def __init__(self, db: Session, shop: Shop):
        """
        初始化同步服务
        
        Args:
            db: 数据库会话
            shop: 店铺模型
        """
        self.db = db
        self.shop = shop
        self.temu_service = get_temu_service(shop)
    
    async def sync_orders(
        self,
        begin_time: Optional[int] = None,
        end_time: Optional[int] = None,
        full_sync: bool = False
    ) -> Dict[str, int]:
        """
        同步订单数据
        
        Args:
            begin_time: 开始时间（Unix时间戳，秒）
            end_time: 结束时间（Unix时间戳，秒）
            full_sync: 是否全量同步
                - True: 全量同步，不限制时间范围（如果begin_time未指定，则从最早开始）
                - False: 增量同步，从最后同步时间开始（如果从未同步，则同步最近7天）
            
        Returns:
            同步统计 {new: 新增数量, updated: 更新数量, total: 总数}
        """
        stats = {"new": 0, "updated": 0, "total": 0, "failed": 0}
        self._current_stats = stats  # 用于在_process_order中更新统计
        
        try:
            # 设置结束时间为当前时间
            if not end_time:
                end_time = int(datetime.now().timestamp())
            
            # 设置开始时间
            if not begin_time:
                if full_sync:
                    # 全量同步：从最早开始（设置为0或一个很早的时间）
                    # Temu API可能不支持从0开始，所以设置为1年前
                    begin_time = int((datetime.now() - timedelta(days=365)).timestamp())
                    logger.info(f"全量同步：从1年前开始同步订单")
                else:
                    # 增量同步：从最后同步时间开始，如果从未同步则从7天前开始
                    if self.shop.last_sync_at:
                        begin_time = int(self.shop.last_sync_at.timestamp())
                        logger.info(f"增量同步：从最后同步时间 {self.shop.last_sync_at} 开始")
                    else:
                        # 从未同步，同步最近7天
                        begin_time = int((datetime.now() - timedelta(days=7)).timestamp())
                        logger.info(f"首次同步：从7天前开始同步订单")
            
            logger.info(
                f"开始同步订单 - 店铺: {self.shop.shop_name}, "
                f"模式: {'全量同步' if full_sync else '增量同步'}, "
                f"时间范围: {datetime.fromtimestamp(begin_time)} ~ {datetime.fromtimestamp(end_time)}, "
                f"通过代理: 是（订单API必须通过代理服务器）"
            )
            
            page_number = 1
            page_size = 100
            
            while True:
                # 获取订单列表
                result = await self.temu_service.get_orders(
                    begin_time=begin_time,
                    end_time=end_time,
                    page_number=page_number,
                    page_size=page_size
                )
                
                total_items = result.get('totalItemNum', 0)
                page_items = result.get('pageItems', [])
                
                if not page_items:
                    break
                
                # 处理每个订单
                for item in page_items:
                    try:
                        self._process_order(item)
                        # 立即提交每个订单，避免批量插入时的重复键错误
                        self.db.commit()
                        stats["total"] += 1
                    except Exception as e:
                        logger.error(f"处理订单失败: {e}, 订单数据: {item}")
                        self.db.rollback()  # 回滚失败的订单
                        stats["failed"] += 1
                
                # 检查是否还有更多页
                if page_number * page_size >= total_items:
                    break
                
                page_number += 1
            
            # 更新店铺最后同步时间
            self.shop.last_sync_at = datetime.now()
            self.db.commit()
            
            logger.info(
                f"订单同步完成 - 店铺: {self.shop.shop_name}, "
                f"总数: {stats['total']}, 失败: {stats['failed']}"
            )
            
            return stats
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"订单同步失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    def _process_order(self, order_data: Dict[str, Any]):
        """
        处理单个订单数据
        
        Args:
            order_data: 订单数据（包含parentOrderMap和orderList）
        """
        parent_order = order_data.get('parentOrderMap', {})
        order_list = order_data.get('orderList', [])
        
        if not parent_order or not order_list:
            logger.warning(f"订单数据格式不完整: {order_data}")
            return
        
        parent_order_sn = parent_order.get('parentOrderSn')
        
        # 处理父订单下的每个子订单
        for order_item in order_list:
            order_sn = order_item.get('orderSn')
            if not order_sn:
                logger.warning(f"子订单缺少orderSn: {order_item}")
                continue
            
            # 查找现有订单（使用唯一约束：order_sn + product_sku + spu_id）
            product_sku = order_item.get('spec') or order_item.get('sku') or ''
            spu_id = order_item.get('spuId') or order_item.get('spu_id') or ''
            
            existing_order = self.db.query(Order).filter(
                Order.order_sn == order_sn,
                Order.product_sku == product_sku,
                Order.spu_id == spu_id
            ).first()
            
            if existing_order:
                # 更新现有订单
                is_updated = self._update_order(existing_order, order_item, parent_order, order_data)
                if is_updated:
                    stats = getattr(self, '_current_stats', {})
                    stats['updated'] = stats.get('updated', 0) + 1
            else:
                # 创建新订单
                self._create_order(order_item, parent_order, order_data)
                stats = getattr(self, '_current_stats', {})
                stats['new'] = stats.get('new', 0) + 1
    
    def _create_order(
        self, 
        order_item: Dict[str, Any], 
        parent_order: Dict[str, Any],
        full_order_data: Dict[str, Any]
    ):
        """
        创建新订单
        
        Args:
            order_item: 子订单数据
            parent_order: 父订单数据
            full_order_data: 完整订单数据（用于保存raw_data）
        """
        # 映射订单状态
        order_status = self._map_order_status(parent_order.get('parentOrderStatus', 0))
        
        # 提取时间信息（支持秒和毫秒时间戳）
        # 根据 API 文档，时间字段在 parentOrderMap 中
        order_time = self._parse_timestamp(parent_order.get('parentOrderTime'))
        # 发货时间可能在 parentOrderMap 中（parentShippingTime）或 orderList 中（orderShippingTime）
        shipping_time = self._parse_timestamp(
            parent_order.get('parentShippingTime') or 
            order_item.get('orderShippingTime') or
            parent_order.get('shippingTime') or 
            parent_order.get('shipTime')
        )
        # 送达时间在 parentOrderMap 中（latestDeliveryTime）
        delivery_time = self._parse_timestamp(
            parent_order.get('latestDeliveryTime') or
            parent_order.get('deliveryTime') or 
            parent_order.get('deliverTime')
        )
        # 支付时间可能在 parentOrderMap 中
        payment_time = self._parse_timestamp(parent_order.get('paymentTime') or parent_order.get('payTime'))
        
        # 提取价格信息
        # 价格可能在order_item或parent_order中，优先从order_item获取
        unit_price = self._parse_decimal(
            order_item.get('goodsPrice') or 
            order_item.get('unitPrice') or 
            order_item.get('price') or 
            parent_order.get('unitPrice') or 
            0
        )
        total_price = self._parse_decimal(
            order_item.get('goodsTotalPrice') or 
            order_item.get('totalPrice') or 
            order_item.get('amount') or 
            parent_order.get('totalPrice') or 
            unit_price * order_item.get('goodsNumber', 1)
        )
        currency = order_item.get('currency') or parent_order.get('currency') or 'USD'
        
        # 提取商品信息
        product_name = (
            order_item.get('goodsName') or 
            order_item.get('productName') or 
            order_item.get('spec') or 
            'Unknown Product'
        )
        product_sku = order_item.get('spec') or order_item.get('sku') or ''
        spu_id = order_item.get('spuId') or order_item.get('spu_id') or ''
        goods_id = order_item.get('goodsId') or order_item.get('goods_id') or ''
        quantity = order_item.get('goodsNumber') or order_item.get('quantity') or 1
        
        # 提取地址信息
        shipping_info = parent_order.get('shippingInfo') or parent_order.get('address') or {}
        shipping_country = (
            shipping_info.get('country') or 
            shipping_info.get('countryName') or 
            parent_order.get('shippingCountry') or 
            ''
        )
        shipping_city = (
            shipping_info.get('city') or 
            shipping_info.get('cityName') or 
            parent_order.get('shippingCity') or 
            ''
        )
        shipping_province = (
            shipping_info.get('province') or 
            shipping_info.get('provinceName') or 
            shipping_info.get('state') or 
            parent_order.get('shippingProvince') or 
            ''
        )
        shipping_postal_code = (
            shipping_info.get('postalCode') or 
            shipping_info.get('zipCode') or 
            parent_order.get('shippingPostalCode') or 
            ''
        )
        
        # 提取客户信息
        customer_id = parent_order.get('customerId') or parent_order.get('buyerId') or ''
        
        # 创建订单对象
        order = Order(
            shop_id=self.shop.id,
            order_sn=order_item.get('orderSn'),
            temu_order_id=parent_order.get('parentOrderSn'),
            parent_order_sn=parent_order.get('parentOrderSn'),
            
            # 商品信息
            product_name=product_name,
            product_sku=product_sku,
            spu_id=spu_id,
            quantity=quantity,
            
            # 金额信息
            unit_price=unit_price,
            total_price=total_price,
            currency=currency,
            
            # 状态和时间
            status=order_status,
            order_time=order_time or datetime.now(),
            payment_time=payment_time,
            shipping_time=shipping_time,
            delivery_time=delivery_time,
            
            # 客户和地址信息
            customer_id=customer_id if customer_id else None,
            shipping_country=shipping_country if shipping_country else None,
            shipping_city=shipping_city if shipping_city else None,
            shipping_province=shipping_province if shipping_province else None,
            shipping_postal_code=shipping_postal_code if shipping_postal_code else None,
            
            # 保存原始数据
            raw_data=json.dumps(full_order_data, ensure_ascii=False),
            notes=f"Environment: {self.shop.environment.value}, GoodsID: {goods_id}"
        )
        
        self.db.add(order)
        logger.debug(f"创建新订单: {order.order_sn}, SKU: {product_sku}, SPU: {spu_id}")
    
    def _update_order(
        self, 
        order: Order, 
        order_item: Dict[str, Any], 
        parent_order: Dict[str, Any],
        full_order_data: Dict[str, Any]
    ) -> bool:
        """
        更新现有订单
        
        Args:
            order: 现有订单对象
            order_item: 子订单数据
            parent_order: 父订单数据
            full_order_data: 完整订单数据
            
        Returns:
            是否进行了更新
        """
        updated = False
        
        # 更新订单状态
        new_status = self._map_order_status(parent_order.get('parentOrderStatus', 0))
        if order.status != new_status:
            order.status = new_status
            updated = True
            logger.debug(f"更新订单状态: {order.order_sn} -> {new_status}")
        
        # 更新时间信息
        payment_time = self._parse_timestamp(parent_order.get('paymentTime') or parent_order.get('payTime'))
        if payment_time and order.payment_time != payment_time:
            order.payment_time = payment_time
            updated = True
        
        shipping_time = self._parse_timestamp(parent_order.get('shippingTime') or parent_order.get('shipTime'))
        if shipping_time and order.shipping_time != shipping_time:
            order.shipping_time = shipping_time
            updated = True
        
        delivery_time = self._parse_timestamp(parent_order.get('deliveryTime') or parent_order.get('deliverTime'))
        if delivery_time and order.delivery_time != delivery_time:
            order.delivery_time = delivery_time
            updated = True
        
        # 更新价格信息（如果价格发生变化）
        unit_price = self._parse_decimal(
            order_item.get('goodsPrice') or 
            order_item.get('unitPrice') or 
            order_item.get('price') or 
            parent_order.get('unitPrice')
        )
        total_price = self._parse_decimal(
            order_item.get('goodsTotalPrice') or 
            order_item.get('totalPrice') or 
            order_item.get('amount') or 
            parent_order.get('totalPrice')
        )
        
        if unit_price and order.unit_price != unit_price:
            order.unit_price = unit_price
            updated = True
        
        if total_price and order.total_price != total_price:
            order.total_price = total_price
            updated = True
        
        # 更新原始数据
        new_raw_data = json.dumps(full_order_data, ensure_ascii=False)
        if order.raw_data != new_raw_data:
            order.raw_data = new_raw_data
            updated = True
        
        # 更新父订单关系（如果缺失）
        parent_order_sn = parent_order.get('parentOrderSn')
        if parent_order_sn and not order.parent_order_sn:
            order.parent_order_sn = parent_order_sn
            updated = True
        
        return updated
    
    def _map_order_status(self, temu_status: int) -> OrderStatus:
        """
        映射Temu订单状态到系统订单状态
        
        根据 Temu API 文档：
        - 0: 全部
        - 1: PENDING（待处理）
        - 2: UN_SHIPPING（待发货）
        - 3: CANCELED（订单已取消）
        - 4: SHIPPED（订单已发货）
        - 5: RECEIPTED（订单已收货）
        - 41: 部分发货（仅本地店铺）
        - 51: 部分收货（仅本地店铺）
        
        Args:
            temu_status: Temu订单状态码
            
        Returns:
            系统订单状态
        """
        order_status_map = {
            0: OrderStatus.PENDING,      # 全部（默认待处理）
            1: OrderStatus.PENDING,      # PENDING（待处理）
            2: OrderStatus.PROCESSING,   # UN_SHIPPING（待发货）
            3: OrderStatus.CANCELLED,    # CANCELED（订单已取消）
            4: OrderStatus.SHIPPED,      # SHIPPED（订单已发货）
            5: OrderStatus.DELIVERED,    # RECEIPTED（订单已收货）
            41: OrderStatus.SHIPPED,     # 部分发货（视为已发货）
            51: OrderStatus.DELIVERED,   # 部分收货（视为已收货）
        }
        return order_status_map.get(temu_status, OrderStatus.PENDING)
    
    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """
        解析时间戳（支持秒和毫秒）
        
        Args:
            timestamp: 时间戳（秒或毫秒）
            
        Returns:
            datetime对象或None
        """
        if timestamp is None:
            return None
        
        try:
            # 转换为整数
            ts = int(timestamp)
            
            # 如果是毫秒时间戳（大于10位），转换为秒
            if ts > 9999999999:
                ts = ts / 1000
            
            return datetime.fromtimestamp(ts)
        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"解析时间戳失败: {timestamp}, 错误: {e}")
            return None
    
    def _parse_decimal(self, value: Any) -> Decimal:
        """
        解析金额为Decimal类型
        
        Args:
            value: 金额值（可能是字符串、数字等）
            
        Returns:
            Decimal对象
        """
        if value is None:
            return Decimal('0.00')
        
        try:
            return Decimal(str(value)).quantize(Decimal('0.01'))
        except (ValueError, TypeError) as e:
            logger.warning(f"解析金额失败: {value}, 错误: {e}")
            return Decimal('0.00')
    
    async def sync_products(self, full_sync: bool = False) -> Dict[str, int]:
        """
        同步商品数据
        
        Args:
            full_sync: 是否全量同步
                - True: 全量同步，同步所有商品
                - False: 增量同步，只同步新增和更新的商品（通过商品ID判断）
            
        Returns:
            同步统计
        """
        stats = {"new": 0, "updated": 0, "total": 0, "failed": 0}
        self._current_stats = stats  # 用于在_process_product中更新统计
        
        try:
            sync_mode = "全量同步" if full_sync else "增量同步"
            logger.info(
                f"开始同步商品 - 店铺: {self.shop.shop_name}, "
                f"模式: {sync_mode}, "
                f"通过代理: 否（CN端点直接访问，无需代理）"
            )
            
            page_number = 1
            page_size = 100
            
            while True:
                # 获取商品列表
                result = await self.temu_service.get_products(
                    page_number=page_number,
                    page_size=page_size
                )
                
                # 处理API返回为null的情况
                if result is None:
                    logger.info(f"商品列表为空 - 店铺: {self.shop.shop_name}")
                    break
                
                # 获取商品列表数据（可能的字段名：data, goodsList, productList, pageItems等）
                # CN端点使用 'data' 字段，标准端点可能使用其他字段
                product_list = (
                    result.get('data') or  # CN端点使用此字段
                    result.get('goodsList') or 
                    result.get('productList') or 
                    result.get('pageItems') or 
                    result.get('list') or 
                    []
                )
                
                # 获取总数（CN端点可能使用 totalCount 或其他字段）
                total_items = (
                    result.get('totalCount') or  # CN端点可能使用此字段
                    result.get('totalItemNum') or 
                    result.get('total') or 
                    result.get('totalNum') or
                    0
                )
                
                if not product_list:
                    logger.info(f"当前页无商品数据 - 店铺: {self.shop.shop_name}, 页码: {page_number}")
                    break
                
                # 处理每个商品
                for product_item in product_list:
                    try:
                        self._process_product(product_item)
                        # 立即提交每个商品，避免批量插入时的重复键错误
                        self.db.commit()
                        stats["total"] += 1
                    except Exception as e:
                        logger.error(f"处理商品失败: {e}, 商品数据: {product_item}")
                        self.db.rollback()  # 回滚失败的商品
                        stats["failed"] += 1
                
                # 检查是否还有更多页
                if total_items > 0 and page_number * page_size >= total_items:
                    break
                
                # 如果没有总数信息，检查当前页是否为空或小于page_size
                if not total_items and len(product_list) < page_size:
                    break
                
                page_number += 1
            
            logger.info(
                f"商品同步完成 - 店铺: {self.shop.shop_name}, "
                f"新增: {stats['new']}, 更新: {stats['updated']}, "
                f"总数: {stats['total']}, 失败: {stats['failed']}"
            )
            
            return stats
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"商品同步失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    def _process_product(self, product_data: Dict[str, Any]):
        """
        处理单个商品数据
        
        Args:
            product_data: 商品数据
        """
        # 提取商品ID（可能是goodsId, productId, id等）
        # CN端点使用 productId，标准端点可能使用 goodsId
        goods_id = (
            str(product_data.get('productId')) or  # CN端点使用此字段
            str(product_data.get('goodsId')) or 
            str(product_data.get('id')) or 
            ''
        )
        
        if not goods_id:
            logger.warning(f"商品数据缺少ID: {product_data}")
            return
        
        # 处理 SKU 列表
        # CN端点使用 productSkuSummaries，标准端点可能使用 skuInfoList 或 skuList
        sku_list = (
            product_data.get('productSkuSummaries') or  # CN端点使用此字段
            product_data.get('skuInfoList') or 
            product_data.get('skuList') or 
            []
        )
        
        # 如果没有 SKU 列表，将整个商品作为一个 SKU 处理
        if not sku_list:
            self._create_or_update_product_from_data(product_data, goods_id)
        else:
            # 为每个 SKU 创建/更新商品记录
            for sku_data in sku_list:
                # 合并商品数据和 SKU 数据
                combined_data = {**product_data, **sku_data}
                
                # CN端点：productSkuId 作为 product_id，productId 作为 spu_id
                # 标准端点：skuId 作为 product_id，goodsId 作为 spu_id
                sku_id = (
                    str(sku_data.get('productSkuId')) or  # CN端点使用此字段
                    str(sku_data.get('skuId')) or 
                    str(sku_data.get('id')) or 
                    ''
                )
                
                if sku_id:
                    # 设置商品ID和SPU ID
                    combined_data['productId'] = sku_id  # 使用 SKU ID 作为商品 ID
                    combined_data['goodsId'] = sku_id  # 兼容标准端点
                    combined_data['spuId'] = goods_id  # 使用商品 ID 作为 SPU ID
                    self._create_or_update_product_from_data(combined_data, sku_id)
    
    def _create_or_update_product_from_data(self, product_data: Dict[str, Any], goods_id: str):
        """
        从商品数据创建或更新商品记录
        
        Args:
            product_data: 商品数据（可能包含 SKU 数据）
            goods_id: 商品/SKU ID
        """
        
        # 查找现有商品（根据shop_id + product_id）
        existing_product = self.db.query(Product).filter(
            Product.shop_id == self.shop.id,
            Product.product_id == goods_id
        ).first()
        
        if existing_product:
            # 更新现有商品
            is_updated = self._update_product(existing_product, product_data)
            if is_updated:
                stats = getattr(self, '_current_stats', {})
                stats['updated'] = stats.get('updated', 0) + 1
        else:
            # 创建新商品
            self._create_product(product_data)
            stats = getattr(self, '_current_stats', {})
            stats['new'] = stats.get('new', 0) + 1
    
    def _create_product(self, product_data: Dict[str, Any]):
        """
        创建新商品
        
        Args:
            product_data: 商品数据
        """
        # 提取商品ID（CN端点使用productId，标准端点可能使用goodsId）
        goods_id = (
            str(product_data.get('productId')) or  # CN端点使用此字段
            str(product_data.get('goodsId')) or 
            str(product_data.get('id')) or 
            ''
        )
        
        # 提取商品名称（CN端点使用productName，标准端点可能使用goodsName）
        product_name = (
            product_data.get('productName') or  # CN端点使用此字段
            product_data.get('skuName') or  # SKU 名称（如果有）
            product_data.get('goodsName') or 
            product_data.get('title') or 
            product_data.get('name') or 
            product_data.get('outGoodsSn') or  # 商品外部编号作为备选
            'Unknown Product'
        )
        
        # 如果商品名称仍然为空或默认值，尝试从 SKU 信息中获取
        if not product_name or product_name == 'Unknown Product':
            sku_info_list = (
                product_data.get('productSkuSummaries') or  # CN端点使用此字段
                product_data.get('skuInfoList') or 
                product_data.get('skuList') or 
                []
            )
            if sku_info_list and len(sku_info_list) > 0:
                # 使用第一个 SKU 的名称
                first_sku = sku_info_list[0]
                product_name = (
                    first_sku.get('skuName') or
                    first_sku.get('goodsName') or
                    first_sku.get('outSkuSn') or  # SKU 外部编号
                    product_name
                )
        
        # 提取SKU（CN端点使用extCode，标准端点可能使用outSkuSn）
        sku = (
            product_data.get('extCode') or  # CN端点使用此字段（SKU外部编号）
            product_data.get('outSkuSn') or  # SKU 外部编号（标准端点）
            product_data.get('sku') or 
            product_data.get('goodsSku') or 
            product_data.get('productSku') or 
            product_data.get('skuSn') or  # SKU 编号
            ''
        )
        
        # 如果 SKU 为空，尝试从 SKU 信息列表中获取
        if not sku:
            sku_info_list = (
                product_data.get('productSkuSummaries') or  # CN端点使用此字段
                product_data.get('skuInfoList') or 
                product_data.get('skuList') or 
                []
            )
            if sku_info_list and len(sku_info_list) > 0:
                first_sku = sku_info_list[0]
                sku = (
                    first_sku.get('extCode') or  # CN端点使用此字段
                    first_sku.get('outSkuSn') or
                    first_sku.get('skuSn') or
                    first_sku.get('sku') or
                    ''
                )
        
        # 提取SPU ID和SKC ID
        # CN端点：如果当前是SKU，spuId已经在_process_product中设置；如果是商品本身，使用productId作为spuId
        spu_id = (
            str(product_data.get('spuId')) or  # 如果是从SKU处理来的，已经有spuId
            str(product_data.get('spu_id')) or 
            str(product_data.get('productId')) or  # CN端点：商品ID可以作为SPU ID
            ''
        )
        skc_id = (
            str(product_data.get('productSkcId')) or  # CN端点使用此字段
            str(product_data.get('skcId')) or 
            str(product_data.get('skc_id')) or 
            ''
        )
        
        # 提取价格信息
        current_price = self._parse_decimal(
            product_data.get('price') or 
            product_data.get('goodsPrice') or 
            product_data.get('salePrice') or 
            product_data.get('currentPrice') or 
            0
        )
        currency = product_data.get('currency') or 'USD'
        
        # 提取库存信息
        stock_quantity = (
            product_data.get('stock') or 
            product_data.get('stockQuantity') or 
            product_data.get('inventory') or 
            product_data.get('availableStock') or 
            0
        )
        try:
            stock_quantity = int(stock_quantity)
        except (ValueError, TypeError):
            stock_quantity = 0
        
        # 提取状态信息
        # CN端点使用skcSiteStatus，标准端点可能使用goodsStatus
        goods_status = (
            product_data.get('skcSiteStatus') or  # CN端点使用此字段
            product_data.get('goodsStatus') or 
            product_data.get('status')
        )
        is_active = True  # 默认在售
        if goods_status is not None:
            # 状态可能是数字或字符串
            # 通常：1=在售，0=下架，或其他状态码
            # CN端点：skcSiteStatus可能是状态码，需要根据实际值判断
            if isinstance(goods_status, int):
                is_active = goods_status == 1 or goods_status == 2  # 1或2可能表示在售
            elif isinstance(goods_status, str):
                is_active = goods_status.lower() in ['1', '2', 'active', 'on_sale', 'onsale', 'published']
        
        # 提取其他信息
        description = product_data.get('description') or product_data.get('goodsDesc') or ''
        image_url = (
            product_data.get('mainImageUrl') or  # CN端点使用此字段
            product_data.get('imageUrl') or 
            product_data.get('image') or 
            product_data.get('mainImage') or 
            ''
        )
        # CN端点使用leafCat或categories，标准端点可能使用category
        category = (
            product_data.get('leafCat') or  # CN端点可能使用此字段
            product_data.get('category') or 
            product_data.get('categoryName') or 
            product_data.get('catName') or 
            ''
        )
        # 如果category是字典，提取名称
        if isinstance(category, dict):
            category = category.get('name') or category.get('catName') or str(category)
        price_status = (
            product_data.get('priceStatus') or 
            product_data.get('price_status') or 
            ''
        )
        
        # 创建商品对象
        product = Product(
            shop_id=self.shop.id,
            product_id=goods_id,
            product_name=product_name,
            sku=sku if sku else None,
            spu_id=spu_id if spu_id else None,
            skc_id=skc_id if skc_id else None,
            current_price=current_price,
            currency=currency,
            stock_quantity=stock_quantity,
            is_active=is_active,
            description=description if description else None,
            image_url=image_url if image_url else None,
            category=category if category else None,
            price_status=price_status if price_status else None,
            manager=None  # 需要手动分配
        )
        
        self.db.add(product)
        logger.debug(f"创建新商品: {product.product_name}, ID: {goods_id}, SKU: {sku}")
    
    def _update_product(self, product: Product, product_data: Dict[str, Any]) -> bool:
        """
        更新现有商品
        
        Args:
            product: 现有商品对象
            product_data: 商品数据
            
        Returns:
            是否进行了更新
        """
        updated = False
        
        # 更新商品名称（优先使用 SKU 名称）
        new_name = (
            product_data.get('skuName') or  # SKU 名称（如果有）
            product_data.get('goodsName') or 
            product_data.get('productName') or 
            product_data.get('title') or 
            product_data.get('name')
        )
        
        # 如果商品名称仍然为空，尝试从 SKU 信息列表中获取
        if not new_name:
            sku_info_list = product_data.get('skuInfoList') or product_data.get('skuList') or []
            if sku_info_list and len(sku_info_list) > 0:
                first_sku = sku_info_list[0]
                new_name = (
                    first_sku.get('skuName') or
                    first_sku.get('goodsName') or
                    first_sku.get('outSkuSn') or
                    new_name
                )
        
        if new_name and product.product_name != new_name:
            product.product_name = new_name
            updated = True
        
        # 更新SKU
        new_sku = (
            product_data.get('outSkuSn') or  # SKU 外部编号（优先）
            product_data.get('sku') or 
            product_data.get('goodsSku') or 
            product_data.get('productSku') or
            product_data.get('skuSn')  # SKU 编号
        )
        
        # 如果 SKU 为空，尝试从 SKU 信息列表中获取
        if not new_sku:
            sku_info_list = product_data.get('skuInfoList') or product_data.get('skuList') or []
            if sku_info_list and len(sku_info_list) > 0:
                first_sku = sku_info_list[0]
                new_sku = (
                    first_sku.get('outSkuSn') or
                    first_sku.get('skuSn') or
                    first_sku.get('sku') or
                    new_sku
                )
        if new_sku and product.sku != new_sku:
            product.sku = new_sku
            updated = True
        
        # 更新价格
        new_price = self._parse_decimal(
            product_data.get('price') or 
            product_data.get('goodsPrice') or 
            product_data.get('salePrice') or 
            product_data.get('currentPrice')
        )
        if new_price and product.current_price != new_price:
            product.current_price = new_price
            updated = True
        
        # 更新库存
        new_stock = (
            product_data.get('stock') or 
            product_data.get('stockQuantity') or 
            product_data.get('inventory') or 
            product_data.get('availableStock')
        )
        if new_stock is not None:
            try:
                new_stock = int(new_stock)
                if product.stock_quantity != new_stock:
                    product.stock_quantity = new_stock
                    updated = True
            except (ValueError, TypeError):
                pass
        
        # 更新状态
        goods_status = product_data.get('goodsStatus') or product_data.get('status')
        if goods_status is not None:
            if isinstance(goods_status, int):
                new_is_active = goods_status == 1
            elif isinstance(goods_status, str):
                new_is_active = goods_status.lower() in ['1', 'active', 'on_sale', 'onsale']
            else:
                new_is_active = product.is_active
            
            if product.is_active != new_is_active:
                product.is_active = new_is_active
                updated = True
        
        # 更新SPU ID和SKC ID（如果缺失）
        spu_id = (
            str(product_data.get('spuId')) or 
            str(product_data.get('spu_id')) or 
            ''
        )
        if spu_id and not product.spu_id:
            product.spu_id = spu_id
            updated = True
        
        skc_id = (
            str(product_data.get('skcId')) or 
            str(product_data.get('skc_id')) or 
            ''
        )
        if skc_id and not product.skc_id:
            product.skc_id = skc_id
            updated = True
        
        # 更新其他信息
        description = product_data.get('description') or product_data.get('goodsDesc')
        if description and product.description != description:
            product.description = description
            updated = True
        
        image_url = (
            product_data.get('imageUrl') or 
            product_data.get('image') or 
            product_data.get('mainImage')
        )
        if image_url and product.image_url != image_url:
            product.image_url = image_url
            updated = True
        
        category = (
            product_data.get('category') or 
            product_data.get('categoryName') or 
            product_data.get('catName')
        )
        if category and product.category != category:
            product.category = category
            updated = True
        
        price_status = (
            product_data.get('priceStatus') or 
            product_data.get('price_status')
        )
        if price_status and product.price_status != price_status:
            product.price_status = price_status
            updated = True
        
        if updated:
            logger.debug(f"更新商品: {product.product_name}, ID: {product.product_id}")
        
        return updated
    
    async def sync_categories(self) -> int:
        """
        同步商品分类
        
        Returns:
            分类数量
        """
        try:
            logger.info(f"开始同步商品分类 - 店铺: {self.shop.shop_name}")
            
            # 获取根分类
            result = await self.temu_service.get_product_categories(parent_cat_id=0)
            categories = result.get('goodsCatsList', [])
            
            logger.info(
                f"商品分类同步完成 - 店铺: {self.shop.shop_name}, "
                f"分类数量: {len(categories)}"
            )
            
            return len(categories)
            
        except Exception as e:
            logger.error(f"商品分类同步失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def sync_all(self, full_sync: bool = False) -> Dict[str, Any]:
        """
        同步所有数据
        
        Args:
            full_sync: 是否全量同步
            
        Returns:
            同步统计
        """
        logger.info(f"开始全量同步 - 店铺: {self.shop.shop_name}")
        
        results = {}
        
        try:
            # 同步订单
            results['orders'] = await self.sync_orders(full_sync=full_sync)
            
            # 同步商品
            results['products'] = await self.sync_products(full_sync=full_sync)
            
            # 同步分类
            results['categories'] = await self.sync_categories()
            
            logger.info(f"全量同步完成 - 店铺: {self.shop.shop_name}")
            
            return results
            
        except Exception as e:
            logger.error(f"全量同步失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
        finally:
            await self.temu_service.close()


async def sync_shop_data(db: Session, shop_id: int, full_sync: bool = False) -> Dict[str, Any]:
    """
    同步指定店铺的数据
    
    Args:
        db: 数据库会话
        shop_id: 店铺ID
        full_sync: 是否全量同步
        
    Returns:
        同步统计
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise ValueError(f"店铺不存在: {shop_id}")
    
    sync_service = SyncService(db, shop)
    return await sync_service.sync_all(full_sync=full_sync)


async def sync_all_shops(db: Session, full_sync: bool = False) -> Dict[int, Dict[str, Any]]:
    """
    同步所有启用的店铺
    
    Args:
        db: 数据库会话
        full_sync: 是否全量同步
        
    Returns:
        各店铺的同步统计
    """
    shops = db.query(Shop).filter(Shop.is_active == True).all()
    
    results = {}
    for shop in shops:
        try:
            sync_service = SyncService(db, shop)
            results[shop.id] = await sync_service.sync_all(full_sync=full_sync)
        except Exception as e:
            logger.error(f"店铺同步失败 - {shop.shop_name}: {e}")
            results[shop.id] = {"error": str(e)}
    
    return results

