"""数据同步服务 - 从Temu API同步数据到数据库"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from loguru import logger

from app.models.shop import Shop
from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductCost
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
    
    def _get_product_price_by_sku(
        self, 
        product_sku: str, 
        order_time: Optional[datetime] = None,
        product_sku_id: Optional[str] = None,
        spu_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        根据productSkuId、extCode或spu_id获取商品的供货价和成本价
        
        Args:
            product_sku: 商品SKU货号（extCode）
            order_time: 订单时间（用于查找当时有效的成本价）
            product_sku_id: Temu商品SKU ID（优先使用，对应Product.product_id）
            spu_id: SPU ID（备选匹配方式）
            
        Returns:
            包含商品信息的字典，如果未找到则返回None
            {
                'product_id': 商品ID,
                'supply_price': 供货价（current_price）,
                'cost_price': 成本价（order_time时有效的成本）,
                'currency': 货币
            }
        """
        product = None
        match_method = None
        
        # 优先级1：通过 productSkuId 匹配（对应 Product.product_id）
        if product_sku_id:
            product = self.db.query(Product).filter(
                Product.shop_id == self.shop.id,
                Product.product_id == str(product_sku_id)
            ).first()
            
            if product:
                match_method = "productSkuId"
                logger.debug(f"✅ 通过productSkuId匹配到商品: {product_sku_id} -> {product.sku}")
        
        # 优先级2：通过 extCode (SKU货号) 匹配
        if not product and product_sku:
            product = self.db.query(Product).filter(
                Product.shop_id == self.shop.id,
                Product.sku == product_sku
            ).first()
            
            if product:
                match_method = "extCode"
                logger.debug(f"✅ 通过extCode (SKU货号)匹配到商品: {product_sku} -> {product.product_id}")
        
        # 优先级3：通过 spu_id 匹配（备用）
        if not product and spu_id:
            product = self.db.query(Product).filter(
                Product.shop_id == self.shop.id,
                Product.spu_id == spu_id
            ).first()
            
            if product:
                match_method = "spu_id"
                logger.debug(f"✅ 通过spu_id匹配到商品: {spu_id} -> {product.sku}")
        
        if not product:
            logger.debug(
                f"❌ 未找到匹配的商品 - "
                f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {spu_id}"
            )
            return None
        
        # 获取供货价
        supply_price = product.current_price
        
        # 获取订单时间有效的成本价
        cost_price = None
        if order_time:
            # 查询在订单时间有效的成本记录
            # effective_from <= order_time AND (effective_to IS NULL OR effective_to > order_time)
            cost_record = self.db.query(ProductCost).filter(
                ProductCost.product_id == product.id,
                ProductCost.effective_from <= order_time,
                (ProductCost.effective_to.is_(None)) | (ProductCost.effective_to > order_time)
            ).order_by(ProductCost.effective_from.desc()).first()
            
            if cost_record:
                cost_price = cost_record.cost_price
                logger.debug(
                    f"找到商品 {product.sku} 在 {order_time} 的有效成本价: {cost_price}"
                )
        else:
            # 如果没有订单时间，获取当前有效的成本价
            cost_record = self.db.query(ProductCost).filter(
                ProductCost.product_id == product.id,
                ProductCost.effective_to.is_(None)
            ).first()
            
            if cost_record:
                cost_price = cost_record.cost_price
        
        return {
            'product_id': product.id,
            'supply_price': supply_price,
            'cost_price': cost_price,
            'currency': product.currency
        }
    
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
            import traceback
            logger.error(traceback.format_exc())
            raise
        finally:
            # 确保数据库会话正确关闭（虽然依赖注入会处理，但这里确保资源释放）
            pass
    
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
            # 从 productList 中提取真正的SKU信息（extCode字段）
            product_list = order_item.get('productList', [])
            if product_list and len(product_list) > 0:
                product_info = product_list[0]
                product_sku = product_info.get('extCode') or ''  # 真正的SKU货号
                # 将productId转换为字符串，因为数据库中spu_id是String类型
                product_id_value = product_info.get('productId')
                spu_id = str(product_id_value) if product_id_value is not None else ''
            else:
                # 如果没有productList，尝试从order_item中获取extCode（旧格式数据）
                product_sku = order_item.get('extCode') or ''
                spu_id_value = order_item.get('spuId') or order_item.get('spu_id')
                spu_id = str(spu_id_value) if spu_id_value is not None else ''
            
            # 首先尝试精确匹配（order_sn + product_sku + spu_id）
            existing_order = self.db.query(Order).filter(
                Order.order_sn == order_sn,
                Order.product_sku == product_sku,
                Order.spu_id == spu_id
            ).first()
            
            # 如果精确匹配失败，尝试仅通过order_sn和spu_id查找
            # 这样即使旧订单的product_sku是错误的（如"1pc"），也能找到并更新
            if not existing_order and spu_id:
                existing_order = self.db.query(Order).filter(
                    Order.order_sn == order_sn,
                    Order.spu_id == spu_id
                ).first()
            
            # 如果仍然找不到，尝试仅通过temu_order_id（即order_sn）查找
            # 因为temu_order_id有唯一约束，如果订单已存在，应该能通过这个找到
            if not existing_order:
                existing_order = self.db.query(Order).filter(
                    Order.temu_order_id == order_sn
                ).first()
            
            if existing_order:
                # 更新现有订单
                is_updated = self._update_order(existing_order, order_item, parent_order, order_data)
                if is_updated:
                    stats = getattr(self, '_current_stats', {})
                    stats['updated'] = stats.get('updated', 0) + 1
            else:
                # 创建新订单（如果遇到唯一约束错误，可能是并发导致的，尝试查找并更新）
                try:
                    self._create_order(order_item, parent_order, order_data)
                    stats = getattr(self, '_current_stats', {})
                    stats['new'] = stats.get('new', 0) + 1
                except Exception as create_error:
                    # 如果是唯一约束错误，可能是并发创建导致的，尝试查找并更新
                    error_msg = str(create_error)
                    if 'UniqueViolation' in error_msg or 'duplicate key' in error_msg.lower():
                        # 尝试再次查找订单
                        existing_order = self.db.query(Order).filter(
                            Order.temu_order_id == order_sn
                        ).first()
                        if existing_order:
                            # 找到订单，更新它
                            is_updated = self._update_order(existing_order, order_item, parent_order, order_data)
                            if is_updated:
                                stats = getattr(self, '_current_stats', {})
                                stats['updated'] = stats.get('updated', 0) + 1
                        else:
                            # 找不到订单，重新抛出异常
                            raise
                    else:
                        # 其他错误，重新抛出
                        raise
    
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
        # 预期最晚发货时间
        expect_ship_latest_time = self._parse_timestamp(parent_order.get('expectShipLatestTime'))
        # 签收时间：如果订单状态为已收货（status=5），使用updateTime；否则使用latestDeliveryTime
        parent_order_status = parent_order.get('parentOrderStatus')
        if parent_order_status == 5:  # RECEIPTED（已收货）
            # 使用updateTime作为签收时间（更准确）
            delivery_time = self._parse_timestamp(parent_order.get('updateTime'))
        else:
            # 使用latestDeliveryTime作为最晚送达时间
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
        
        # 从 productList 中提取真正的SKU信息
        product_list = order_item.get('productList', [])
        if product_list and len(product_list) > 0:
            product_info = product_list[0]
            product_sku_id = product_info.get('productSkuId')  # Temu商品SKU ID
            # 优先使用extCode（真正的SKU货号），如果为空则保持为空（不使用spec作为备用）
            product_sku = product_info.get('extCode') or ''
            # 将productId转换为字符串，因为数据库中spu_id是String类型
            product_id_value = product_info.get('productId')
            spu_id = str(product_id_value) if product_id_value is not None else ''
        else:
            product_sku_id = None
            # 如果没有productList，说明可能是旧格式数据，extCode应该在order_item中
            product_sku = order_item.get('extCode') or ''
            spu_id_value = order_item.get('spuId') or order_item.get('spu_id')
            spu_id = str(spu_id_value) if spu_id_value is not None else ''
        
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
        
        # 根据productSkuId、extCode或spu_id匹配商品，获取供货价和成本价
        # 注意：同一订单可能包含多个SKU，每个SKU会创建单独的订单记录
        # 优先级：productSkuId > extCode (SKU货号) > spu_id
        unit_cost = None
        total_cost = None
        profit = None
        matched_product_id = None
        
        # 尝试匹配商品
        price_info = self._get_product_price_by_sku(
            product_sku=product_sku,  # extCode (SKU货号)
            order_time=order_time,
            product_sku_id=product_sku_id,  # productSkuId (优先级1)
            spu_id=spu_id  # SPU ID (优先级3)
        )
        
        if price_info:
            unit_cost = price_info['cost_price']
            matched_product_id = price_info['product_id']
            
            # 计算总成本和利润（基于该SKU的数量）
            if unit_cost is not None and quantity:
                total_cost = unit_cost * Decimal(quantity)
                profit = total_price - total_cost
                logger.info(
                    f"✅ 订单 {order_item.get('orderSn')} 成功匹配商品并计算成本 - "
                    f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {spu_id}, "
                    f"数量: {quantity}, 单价: {unit_price}, 总价: {total_price}, "
                    f"单位成本: {unit_cost}, 总成本: {total_cost}, 利润: {profit}"
                )
            else:
                logger.warning(
                    f"⚠️  订单 {order_item.get('orderSn')} "
                    f"(productSkuId: {product_sku_id}, extCode: {product_sku}) "
                    f"匹配到商品但无成本价或数量为0，无法计算利润"
                )
        else:
            logger.warning(
                f"❌ 订单 {order_item.get('orderSn')} 未找到匹配商品 - "
                f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {spu_id}。"
                f"请检查商品列表中是否已添加对应的商品和成本价"
            )
        
        # 创建订单对象
        # 注意：temu_order_id 使用子订单号（orderSn），因为子订单号是唯一的
        # parent_order_sn 字段存储父订单号，用于关联同一父订单下的多个子订单
        # 同一订单号可以包含多个不同的SKU，每个SKU一条记录
        order = Order(
            shop_id=self.shop.id,
            order_sn=order_item.get('orderSn'),
            temu_order_id=order_item.get('orderSn'),  # 使用子订单号作为唯一标识
            parent_order_sn=parent_order.get('parentOrderSn'),
            
            # 商品信息
            product_id=matched_product_id,  # 匹配到的商品ID
            product_name=product_name,
            product_sku=product_sku,
            spu_id=spu_id,
            quantity=quantity,  # 该SKU的数量
            
            # 金额信息（该SKU的金额）
            unit_price=unit_price,
            total_price=total_price,
            currency=currency,
            
            # 成本和利润（该SKU的成本和利润）
            unit_cost=unit_cost,
            total_cost=total_cost,
            profit=profit,
            
            # 状态和时间
            status=order_status,
            order_time=order_time or datetime.now(),
            payment_time=payment_time,
            shipping_time=shipping_time,
            expect_ship_latest_time=expect_ship_latest_time,
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
        logger.debug(
            f"创建新订单: {order.order_sn}, SKU: {product_sku}, SPU: {spu_id}, "
            f"数量: {quantity}, 总价: {total_price}, 利润: {profit}"
        )
    
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
        
        shipping_time = self._parse_timestamp(
            parent_order.get('parentShippingTime') or 
            order_item.get('orderShippingTime') or
            parent_order.get('shippingTime') or 
            parent_order.get('shipTime')
        )
        if shipping_time and order.shipping_time != shipping_time:
            order.shipping_time = shipping_time
            updated = True
        
        # 更新预期最晚发货时间
        expect_ship_latest_time = self._parse_timestamp(parent_order.get('expectShipLatestTime'))
        if expect_ship_latest_time and order.expect_ship_latest_time != expect_ship_latest_time:
            order.expect_ship_latest_time = expect_ship_latest_time
            updated = True
        
        # 签收时间：仅当订单状态为5（已送达）时，使用updateTime作为签收时间
        # 其他状态不设置签收时间（因为未签收），如果之前有值则清空
        parent_order_status = parent_order.get('parentOrderStatus')
        delivery_time = None
        if parent_order_status == 5:  # 已送达（状态码5）
            # 使用updateTime作为签收时间（更准确）
            delivery_time = self._parse_timestamp(parent_order.get('updateTime'))
        
        # 更新签收时间：如果状态为5且有签收时间，则更新；如果状态不是5，则清空
        if parent_order_status == 5:
            if delivery_time and order.delivery_time != delivery_time:
                order.delivery_time = delivery_time
                updated = True
        else:
            # 状态不是5，清空签收时间
            if order.delivery_time is not None:
                order.delivery_time = None
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
        
        # 更新SKU货号（如果API中有extCode，优先使用extCode修正）
        product_list = order_item.get('productList', [])
        if product_list and len(product_list) > 0:
            product_info = product_list[0]
            new_product_sku = product_info.get('extCode') or ''
            # 如果新的extCode不为空，则更新（无论当前值是什么）
            if new_product_sku and new_product_sku.strip():
                new_product_sku = new_product_sku.strip()
                old_sku = order.product_sku or ''
                
                # 定义无效的SKU值（这些不是真正的extCode格式）
                invalid_sku_patterns = [
                    '1', '1pc', 'Random 1PCS', 'random 1pcs', 
                    'RANDOM 1PCS', '1PCS', '1pcs', 'random',
                    'Random', 'RANDOM'
                ]
                
                # 判断是否需要更新
                should_update = False
                
                if not old_sku or old_sku == '':
                    # 当前SKU为空，应该更新
                    should_update = True
                elif old_sku in invalid_sku_patterns:
                    # 当前SKU是无效格式，应该更新
                    should_update = True
                elif old_sku.isdigit():
                    # 当前SKU是纯数字，应该更新
                    should_update = True
                elif old_sku != new_product_sku:
                    # 当前SKU与新值不同，且新值看起来是有效的extCode格式（包含字母），应该更新
                    if any(c.isalpha() for c in new_product_sku):
                        should_update = True
                
                if should_update:
                    order.product_sku = new_product_sku
                    updated = True
                    logger.info(f"更新订单SKU货号: {order.order_sn} -> {old_sku} -> {new_product_sku}")
        
        # 更新成本和利润信息
        # 每次同步时都尝试重新匹配商品并计算成本（如果之前没有成本或商品已更新）
        # 这样可以确保即使之前没有匹配到商品，在商品添加后也能自动计算成本
        should_recalculate_cost = (
            order.unit_cost is None or 
            order.total_cost is None or 
            order.profit is None or
            not order.product_id or  # 如果没有关联商品，尝试重新匹配
            (updated and (unit_price or total_price))  # 价格更新时重新计算
        )
        
        if should_recalculate_cost:
            # 从order_item中提取productSkuId、extCode和spu_id用于匹配（使用完整匹配逻辑）
            product_list = order_item.get('productList', [])
            if product_list and len(product_list) > 0:
                product_info = product_list[0]
                product_sku_id = product_info.get('productSkuId')  # 优先级1
                product_sku = product_info.get('extCode') or order.product_sku or ''  # 优先级2: extCode
                # 将productId转换为字符串，因为数据库中spu_id是String类型
                product_id_value = product_info.get('productId')
                item_spu_id = str(product_id_value) if product_id_value is not None else (order.spu_id or '')  # 优先级3
            else:
                product_sku_id = None
                product_sku = order.product_sku or ''  # 使用已有的product_sku
                item_spu_id = order.spu_id or ''
            
            # 尝试匹配商品（使用完整的匹配逻辑，优先级：productSkuId > extCode > spu_id）
            price_info = self._get_product_price_by_sku(
                product_sku=product_sku,  # extCode (SKU货号) - 优先级2
                order_time=order.order_time,
                product_sku_id=product_sku_id,  # productSkuId (优先级1)
                spu_id=item_spu_id  # SPU ID (优先级3)
            )
            
            if price_info:
                unit_cost = price_info['cost_price']
                
                if unit_cost is not None and order.quantity:
                    # 计算总成本和利润
                    new_total_cost = unit_cost * Decimal(order.quantity)
                    new_profit = order.total_price - new_total_cost
                    
                    # 更新成本和利润（无论是否变化都更新，确保数据准确）
                    order.unit_cost = unit_cost
                    order.total_cost = new_total_cost
                    order.profit = new_profit
                    updated = True
                    
                    # 更新商品关联（如果缺失或需要更新）
                    if not order.product_id or order.product_id != price_info['product_id']:
                        order.product_id = price_info['product_id']
                        updated = True
                    
                    logger.info(
                        f"✅ 订单 {order.order_sn} 成功计算成本和利润 - "
                        f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {item_spu_id}, "
                        f"单位成本: {unit_cost}, 总成本: {new_total_cost}, 利润: {new_profit}"
                    )
                else:
                    logger.warning(
                        f"⚠️  订单 {order.order_sn} 匹配到商品但无成本价或数量为0 - "
                        f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {item_spu_id}"
                    )
            else:
                logger.debug(
                    f"❌ 订单 {order.order_sn} 未找到匹配商品 - "
                    f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {item_spu_id}"
                )
        
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
        
        根据 Temu API 状态码对应关系：
        - 1: 待处理 (PENDING)
        - 2: 未发货 (UN_SHIPPING) -> PROCESSING
        - 3: 已取消 (CANCELLED)
        - 4: 已发货 (SHIPPED)
        - 4: 部分发货 (SHIPPED) - 也是状态码4
        - 5: 已送达 (DELIVERED)
        - 5: 部分送达 (DELIVERED) - 也是状态码5
        
        Args:
            temu_status: Temu订单状态码
            
        Returns:
            系统订单状态
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
        return order_status_map.get(temu_status, OrderStatus.PENDING)
    
    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """
        解析时间戳（支持秒和毫秒），并转换为北京时间（UTC+8）
        
        Args:
            timestamp: 时间戳（秒或毫秒）
            
        Returns:
            datetime对象（北京时间，UTC+8）或None
        """
        if timestamp is None:
            return None
        
        try:
            # 转换为整数
            ts = int(timestamp)
            
            # 如果是毫秒时间戳（大于10位），转换为秒
            if ts > 9999999999:
                ts = ts / 1000
            
            # 从UTC时间戳创建datetime对象（UTC时区）
            utc_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            
            # 转换为北京时间（UTC+8）
            beijing_tz = timezone(timedelta(hours=8))
            beijing_dt = utc_dt.astimezone(beijing_tz)
            
            # 返回naive datetime（不带时区信息），但已经是北京时间
            # 这样存储到数据库时不会有时区问题
            return beijing_dt.replace(tzinfo=None)
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
            max_pages = 1000  # 设置最大页数限制，防止无限循环
            total_fetched = 0  # 累计获取的商品数（包括跳过的）
            
            logger.info(f"开始分页获取商品 - 店铺: {self.shop.shop_name}, 每页: {page_size}")
            
            while page_number <= max_pages:
                # 获取商品列表
                # 使用 skc_site_status=1 筛选在售商品
                result = await self.temu_service.get_products(
                    page_number=page_number,
                    page_size=page_size,
                    skc_site_status=1  # 只获取在售商品
                )
                
                # 处理API返回为null的情况
                if result is None:
                    logger.info(f"商品列表为空 - 店铺: {self.shop.shop_name}, 页码: {page_number}")
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
                
                # 记录当前页信息
                logger.info(
                    f"获取商品列表 - 店铺: {self.shop.shop_name}, "
                    f"页码: {page_number}, "
                    f"当前页商品数: {len(product_list)}, "
                    f"API返回总数: {total_items if total_items > 0 else '未知'}"
                )
                
                if not product_list:
                    logger.info(f"当前页无商品数据 - 店铺: {self.shop.shop_name}, 页码: {page_number}")
                    break
                
                # 累计获取的商品数
                total_fetched += len(product_list)
                
                # 处理每个商品（只处理在售商品）
                page_active_count = 0  # 当前页在售商品数
                page_sku_count = 0  # 当前页有SKU的商品数
                page_skipped_count = 0  # 当前页跳过的非在售商品数
                
                for product_item in product_list:
                    try:
                        # 记录商品基本信息（用于调试）
                        product_id = (
                            str(product_item.get('productId')) or 
                            str(product_item.get('goodsId')) or 
                            str(product_item.get('id')) or 
                            '未知'
                        )
                        product_name = (
                            product_item.get('productName') or 
                            product_item.get('goodsName') or 
                            product_item.get('name') or 
                            '未知商品'
                        )
                        
                        # 检查商品状态（只处理在售商品）
                        # CN端点使用 skcSiteStatus 字段：1=在售，0=不在售
                        # 注意：不能使用 or 操作符，因为0会被当作False
                        goods_status = None
                        if 'skcSiteStatus' in product_item:
                            goods_status = product_item.get('skcSiteStatus')
                        elif 'goodsStatus' in product_item:
                            goods_status = product_item.get('goodsStatus')
                        elif 'status' in product_item:
                            goods_status = product_item.get('status')
                        
                        is_active_status = False
                        if goods_status is not None:
                            if isinstance(goods_status, int):
                                # 只判断是否为1（在售），0表示不在售
                                is_active_status = goods_status == 1
                            elif isinstance(goods_status, str):
                                is_active_status = goods_status.lower() in ['1', 'active', 'on_sale', 'onsale', 'published']
                        
                        # 如果商品不在售，跳过处理
                        if not is_active_status:
                            page_skipped_count += 1
                            logger.debug(
                                f"跳过非在售商品 - 商品ID: {product_id}, "
                                f"商品名称: {product_name}, "
                                f"状态: {goods_status}"
                            )
                            continue
                        
                        page_active_count += 1
                        
                        # 检查是否有SKU（仅用于统计，不影响处理）
                        has_sku = bool(
                            product_item.get('extCode') or 
                            product_item.get('outSkuSn') or
                            product_item.get('productSkuSummaries') or
                            product_item.get('skuInfoList') or
                            product_item.get('skuList')
                        )
                        if has_sku:
                            page_sku_count += 1
                        
                        self._process_product(product_item)
                        # 立即提交每个商品，避免批量插入时的重复键错误
                        self.db.commit()
                        stats["total"] += 1
                    except Exception as e:
                        logger.error(f"处理商品失败: {e}, 商品ID: {product_id}, 商品名称: {product_name}")
                        self.db.rollback()  # 回滚失败的商品
                        stats["failed"] += 1
                
                # 记录当前页统计
                logger.info(
                    f"第 {page_number} 页处理完成 - "
                    f"获取: {len(product_list)}, "
                    f"在售(处理): {page_active_count}, "
                    f"跳过(非在售): {page_skipped_count}, "
                    f"有SKU: {page_sku_count}, "
                    f"累计总数: {stats['total']}"
                )
                
                # 检查是否还有更多页
                # 如果当前页商品数为0，说明没有更多数据了
                if len(product_list) == 0:
                    logger.info(f"已获取所有商品（当前页为空）- 店铺: {self.shop.shop_name}, 总页数: {page_number}")
                    break
                
                # 如果有总数信息，检查是否已经获取完所有商品
                if total_items > 0:
                    # 使用累计获取的商品数来判断
                    if total_fetched >= total_items:
                        logger.info(f"已获取所有商品（已达到总数）- 店铺: {self.shop.shop_name}, 总页数: {page_number}, 总数: {total_items}, 已获取: {total_fetched}")
                        break
                else:
                    # 如果没有总数信息，检查当前页是否小于page_size（可能是最后一页）
                    if len(product_list) < page_size:
                        logger.info(f"已获取所有商品（当前页商品数小于每页数量且无总数信息）- 店铺: {self.shop.shop_name}, 总页数: {page_number}, 当前页商品数: {len(product_list)}")
                    break
                
                page_number += 1
            
            if page_number > max_pages:
                logger.warning(f"达到最大页数限制 - 店铺: {self.shop.shop_name}, 最大页数: {max_pages}")
            
            # 统计同步后的商品状态
            active_products = self.db.query(Product).filter(
                Product.shop_id == self.shop.id,
                Product.is_active == True
            ).count()
            
            products_with_sku = self.db.query(Product).filter(
                Product.shop_id == self.shop.id,
                Product.sku.isnot(None),
                Product.sku != ''
            ).count()
            
            logger.info(
                f"商品同步完成 - 店铺: {self.shop.shop_name}, "
                f"新增: {stats['new']}, 更新: {stats['updated']}, "
                f"总数: {stats['total']}, 失败: {stats['failed']}, "
                f"在售商品: {active_products}, 有SKU商品: {products_with_sku}"
            )
            
            # 同步完成后，建立成本价格的映射关系
            # 基于 productSkuId (product_id) 和 extCode (SKU货号) 匹配已有商品的成本价格，
            # 自动复制到没有成本价格的新商品
            # 注意：供货价格（current_price）由用户手动录入，不从API获取
            # 成本价格（ProductCost）由用户手动录入，或通过此映射自动匹配
            logger.info(f"开始建立成本价格映射关系 - 店铺: {self.shop.shop_name}")
            mapped_count = self._map_supply_cost_prices()
            if mapped_count > 0:
                logger.info(f"成本价格映射完成 - 为 {mapped_count} 个商品自动匹配了成本价格")
            
            return stats
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"商品同步失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        finally:
            # 确保数据库会话正确关闭
            pass
    
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
            logger.debug(f"商品没有SKU列表，作为单个SKU处理 - 商品ID: {goods_id}")
            self._create_or_update_product_from_data(product_data, goods_id)
        else:
            logger.debug(f"商品有 {len(sku_list)} 个SKU，分别处理 - 商品ID: {goods_id}")
            # 为每个 SKU 创建/更新商品记录
            for idx, sku_data in enumerate(sku_list):
                # 合并商品数据和 SKU 数据（SKU数据优先，覆盖商品数据中的同名字段）
                # 但需要保留商品级别的状态字段（skcSiteStatus），因为SKU数据中可能没有
                combined_data = {**product_data, **sku_data}
                # 如果SKU数据中没有状态字段，保留商品级别的状态字段
                if 'skcSiteStatus' not in sku_data or sku_data.get('skcSiteStatus') is None:
                    if 'skcSiteStatus' in product_data:
                        combined_data['skcSiteStatus'] = product_data['skcSiteStatus']
                if 'goodsStatus' not in sku_data or sku_data.get('goodsStatus') is None:
                    if 'goodsStatus' in product_data:
                        combined_data['goodsStatus'] = product_data['goodsStatus']
                if 'status' not in sku_data or sku_data.get('status') is None:
                    if 'status' in product_data:
                        combined_data['status'] = product_data['status']
                
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
                    
                    # 记录SKU信息（包括所有可能的SKU字段）
                    ext_code = sku_data.get('extCode', '')
                    out_sku_sn = sku_data.get('outSkuSn', '')
                    logger.debug(
                        f"处理第 {idx+1} 个SKU - SKU ID: {sku_id}, "
                        f"extCode: '{ext_code}', outSkuSn: {out_sku_sn}, "
                        f"sku: {sku_data.get('sku')}, skuSn: {sku_data.get('skuSn')}"
                    )
                    
                    # 如果extCode是空字符串，记录警告以便调试
                    if ext_code == '':
                        logger.debug(
                            f"SKU extCode为空字符串 - SKU ID: {sku_id}, "
                            f"将尝试从其他字段获取SKU信息"
                        )
                    
                    self._create_or_update_product_from_data(combined_data, sku_id)
                else:
                    logger.warning(f"SKU数据缺少ID，跳过 - SKU索引: {idx}, SKU数据: {sku_data}")
    
    def _create_or_update_product_from_data(self, product_data: Dict[str, Any], goods_id: str):
        """
        从商品数据创建或更新商品记录
        
        Args:
            product_data: 商品数据（可能包含 SKU 数据）
            goods_id: 商品/SKU ID
        """
        
        # 确保 goods_id 是字符串类型（数据库中 product_id 是 character varying 类型）
        goods_id_str = str(goods_id) if goods_id is not None else ''
        
        # 查找现有商品（根据shop_id + product_id）
        existing_product = self.db.query(Product).filter(
            Product.shop_id == self.shop.id,
            Product.product_id == goods_id_str
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
        # 辅助函数：过滤空字符串和None
        def get_non_empty_value(*values):
            for v in values:
                if v and str(v).strip():  # 过滤None、空字符串和只包含空格的字符串
                    return str(v).strip()
            return None
        
        sku = get_non_empty_value(
            product_data.get('extCode'),  # CN端点使用此字段（SKU外部编号）
            product_data.get('outSkuSn'),  # SKU 外部编号（标准端点）
            product_data.get('sku'),
            product_data.get('goodsSku'),
            product_data.get('productSku'),
            product_data.get('skuSn'),  # SKU 编号
            product_data.get('outGoodsSn'),  # 商品外部编号（可能包含SKU信息）
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
                # 遍历所有SKU，找到第一个有extCode的
                for sku_item in sku_info_list:
                    sku = get_non_empty_value(
                        sku_item.get('extCode'),  # CN端点使用此字段
                        sku_item.get('outSkuSn'),
                        sku_item.get('skuSn'),
                        sku_item.get('sku'),
                        sku_item.get('productSkuId'),  # 使用SKU ID作为备选
                    )
                    if sku:
                        break
        
        # 如果SKU仍然为空，记录调试信息
        if not sku:
            logger.warning(
                f"商品SKU为空 - 商品ID: {goods_id}, 商品名称: {product_name}, "
                f"尝试的字段值: extCode={product_data.get('extCode')}, "
                f"outSkuSn={product_data.get('outSkuSn')}, sku={product_data.get('sku')}, "
                f"goodsSku={product_data.get('goodsSku')}, productSku={product_data.get('productSku')}, "
                f"skuSn={product_data.get('skuSn')}, "
                f"productSkuSummaries存在={bool(product_data.get('productSkuSummaries'))}, "
                f"skuInfoList存在={bool(product_data.get('skuInfoList'))}, "
                f"skuList存在={bool(product_data.get('skuList'))}"
            )
            # 记录所有可能的SKU相关字段
            sku_related_keys = [k for k in product_data.keys() if 'sku' in k.lower() or 'code' in k.lower() or 'sn' in k.lower()]
            if sku_related_keys:
                logger.debug(f"商品数据中包含的SKU相关字段: {sku_related_keys}")
                for key in sku_related_keys[:10]:  # 只记录前10个，避免日志过长
                    logger.debug(f"  {key}: {product_data.get(key)}")
        
        # 提取SPU ID和SKC ID
        # CN端点：如果当前是SKU，spuId已经在_process_product中设置；如果是商品本身，使用productId作为spuId
        spu_id_value = (
            product_data.get('spuId') or 
            product_data.get('spu_id') or 
            product_data.get('productId')  # CN端点：商品ID可以作为SPU ID
        )
        spu_id = str(spu_id_value) if spu_id_value is not None else ''
        skc_id = (
            str(product_data.get('productSkcId')) or  # CN端点使用此字段
            str(product_data.get('skcId')) or 
            str(product_data.get('skc_id')) or 
            ''
        )
        
        # 价格信息：供货价格（current_price）由用户手动录入，不从API获取
        # 创建新商品时，current_price 设为 None，等待用户在商品列表中手动录入
        current_price = None
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
        # 注意：不能使用 or 操作符，因为0会被当作False
        goods_status = None
        if 'skcSiteStatus' in product_data:
            goods_status = product_data.get('skcSiteStatus')
        elif 'goodsStatus' in product_data:
            goods_status = product_data.get('goodsStatus')
        elif 'status' in product_data:
            goods_status = product_data.get('status')
        
        # 只根据API返回的状态字段判断是否在售，不依赖SKU
        # CN端点：skcSiteStatus=1 表示在售，0 表示不在售
        is_active = False
        if goods_status is not None:
            if isinstance(goods_status, int):
                is_active = goods_status == 1  # 只判断是否为1（在售），0表示不在售
            elif isinstance(goods_status, str):
                is_active = goods_status.lower() in ['1', 'active', 'on_sale', 'onsale', 'published']
        # 如果API没有返回状态信息，默认为不在售
        
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
        
        # 确保 goods_id 是字符串类型（数据库中 product_id 是 character varying 类型）
        goods_id_str = str(goods_id) if goods_id is not None else ''
        
        # 创建商品对象
        product = Product(
            shop_id=self.shop.id,
            product_id=goods_id_str,
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
        
        # 更新SKU（与创建逻辑保持一致，包括extCode字段）
        # 辅助函数：过滤空字符串和None
        def get_non_empty_value(*values):
            for v in values:
                if v and str(v).strip():  # 过滤None、空字符串和只包含空格的字符串
                    return str(v).strip()
            return None
        
        new_sku = get_non_empty_value(
            product_data.get('extCode'),  # CN端点使用此字段（SKU外部编号）
            product_data.get('outSkuSn'),  # SKU 外部编号（标准端点）
            product_data.get('sku'),
            product_data.get('goodsSku'),
            product_data.get('productSku'),
            product_data.get('skuSn'),  # SKU 编号
            product_data.get('outGoodsSn'),  # 商品外部编号（可能包含SKU信息）
        )
        
        # 如果 SKU 为空，尝试从 SKU 信息列表中获取
        if not new_sku:
            sku_info_list = (
                product_data.get('productSkuSummaries') or  # CN端点使用此字段
                product_data.get('skuInfoList') or 
                product_data.get('skuList') or 
                []
            )
            if sku_info_list and len(sku_info_list) > 0:
                # 遍历所有SKU，找到第一个有extCode的
                for sku_item in sku_info_list:
                    new_sku = get_non_empty_value(
                        sku_item.get('extCode'),  # CN端点使用此字段
                        sku_item.get('outSkuSn'),
                        sku_item.get('skuSn'),
                        sku_item.get('sku'),
                        sku_item.get('productSkuId'),  # 使用SKU ID作为备选
                    )
                    if new_sku:
                        break
        
        # 如果当前SKU为空且新SKU也为空，记录警告
        if not product.sku and not new_sku:
            logger.warning(
                f"更新商品时SKU仍为空 - 商品ID: {product.product_id}, 商品名称: {product.product_name}, "
                f"尝试的字段值: extCode={product_data.get('extCode')}, "
                f"outSkuSn={product_data.get('outSkuSn')}, sku={product_data.get('sku')}, "
                f"goodsSku={product_data.get('goodsSku')}, productSku={product_data.get('productSku')}, "
                f"skuSn={product_data.get('skuSn')}"
            )
        
        # 如果找到了新的SKU，且与当前SKU不同，则更新
        # 如果当前SKU为空（None），且找到了新的SKU，也应该更新
        if new_sku and product.sku != new_sku:
            logger.info(f"更新商品SKU: {product.product_name} (ID: {product.product_id}), 旧SKU: {product.sku}, 新SKU: {new_sku}")
            product.sku = new_sku
            updated = True
        # 如果当前SKU为空，但新SKU也为空，不更新（避免将None更新为None）
        
        # 更新价格：供货价格由用户手动录入，不从API更新
        # 如果用户已经手动录入了供货价格，则保留用户录入的值，不从API覆盖
        # 如果当前供货价格为空，也不从API获取（等待用户手动录入）
        # 因此这里不更新 current_price
        
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
        # 只根据API返回的状态字段判断是否在售，不依赖SKU
        goods_status = (
            product_data.get('skcSiteStatus') or  # CN端点使用此字段
            product_data.get('goodsStatus') or 
            product_data.get('status')
        )
        
        new_is_active = False
        if goods_status is not None:
            if isinstance(goods_status, int):
                new_is_active = goods_status == 1  # 只判断是否为1（在售）
            elif isinstance(goods_status, str):
                new_is_active = goods_status.lower() in ['1', 'active', 'on_sale', 'onsale', 'published']
        # 如果API没有返回状态信息，默认为不在售
            
            if product.is_active != new_is_active:
                product.is_active = new_is_active
                updated = True
        
        # 更新SPU ID和SKC ID（如果缺失）
        spu_id_value = (
            product_data.get('spuId') or 
            product_data.get('spu_id') or 
            product_data.get('productId')
        )
        spu_id = str(spu_id_value) if spu_id_value is not None else ''
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
    
    def _map_supply_cost_prices(self) -> int:
        """
        建立成本价格的映射关系
        
        基于 productSkuId (product_id) 和 extCode (SKU货号) 匹配已有商品的成本价格，
        自动复制到没有成本价格的新商品
        
        匹配优先级：
        1. productSkuId (product_id) - 第一优先级
        2. extCode (SKU货号) - 第二优先级
        
        注意：
        - 供货价格（current_price）由用户手动录入，不从API获取
        - 成本价格（ProductCost）由用户手动录入，或通过此映射自动匹配
        
        参考文档：ORDER_PRODUCT_MATCHING.md
        
        Returns:
            成功建立映射的商品数量
        """
        from datetime import datetime
        
        mapped_count = 0
        
        try:
            # 查找当前店铺下所有没有成本价格的商品
            products_without_cost = self.db.query(Product).filter(
                Product.shop_id == self.shop.id,
                ~Product.id.in_(
                    self.db.query(ProductCost.product_id).filter(
                        ProductCost.effective_to.is_(None)
                    )
                )
            ).all()
            
            if not products_without_cost:
                logger.debug(f"所有商品已有成本价格，无需映射 - 店铺: {self.shop.shop_name}")
                return 0
            
            logger.info(f"找到 {len(products_without_cost)} 个没有成本价格的商品 - 店铺: {self.shop.shop_name}")
            
            # 为每个没有成本价格的商品查找匹配的成本价格
            for product in products_without_cost:
                matched_cost = None
                match_method = None
                
                # 优先级1: 通过 productSkuId (product_id) 匹配
                # 对应 ORDER_PRODUCT_MATCHING.md 中的第一优先级
                if product.product_id:
                    # 确保 product_id 是字符串类型（数据库中 product_id 是 character varying 类型）
                    product_id_str = str(product.product_id) if product.product_id is not None else ''
                    
                    # 查找相同 product_id 且有效成本价格的商品（可以是其他店铺的）
                    matched_product = self.db.query(Product).filter(
                        Product.product_id == product_id_str,
                        Product.id != product.id,
                        Product.product_id.isnot(None),
                        Product.product_id != ''
                    ).join(ProductCost).filter(
                        ProductCost.effective_to.is_(None)
                    ).first()
                    
                    if matched_product:
                        # 获取匹配商品的当前成本价格
                        matched_cost = self.db.query(ProductCost).filter(
                            ProductCost.product_id == matched_product.id,
                            ProductCost.effective_to.is_(None)
                        ).order_by(ProductCost.effective_from.desc()).first()
                        if matched_cost:
                            match_method = "productSkuId (product_id)"
                
                # 优先级2: 通过 extCode (SKU货号) 匹配
                # 对应 ORDER_PRODUCT_MATCHING.md 中的第二优先级
                if not matched_cost and product.sku:
                    # 查找相同 SKU 且有效成本价格的商品（可以是其他店铺的）
                    matched_product = self.db.query(Product).filter(
                        Product.sku == product.sku,
                        Product.id != product.id,
                        Product.sku.isnot(None),
                        Product.sku != ''
                    ).join(ProductCost).filter(
                        ProductCost.effective_to.is_(None)
                    ).first()
                    
                    if matched_product:
                        # 获取匹配商品的当前成本价格
                        matched_cost = self.db.query(ProductCost).filter(
                            ProductCost.product_id == matched_product.id,
                            ProductCost.effective_to.is_(None)
                        ).order_by(ProductCost.effective_from.desc()).first()
                        if matched_cost:
                            match_method = "extCode (SKU货号)"
                
                # 如果找到匹配的成本价格，复制到当前商品
                if matched_cost:
                    try:
                        # 创建新的成本价格记录
                        new_cost = ProductCost(
                            product_id=product.id,
                            cost_price=matched_cost.cost_price,
                            currency=matched_cost.currency,
                            effective_from=datetime.utcnow(),
                            notes=f"自动映射自{matched_cost.product.product_name}（通过{match_method}匹配）"
                        )
                        self.db.add(new_cost)
                        self.db.commit()
                        
                        mapped_count += 1
                        logger.debug(
                            f"✅ 为商品 {product.product_name} (SKU: {product.sku or 'N/A'}) "
                            f"自动匹配成本价格 {matched_cost.cost_price} {matched_cost.currency} "
                            f"（通过{match_method}匹配）"
                        )
                    except Exception as e:
                        self.db.rollback()
                        logger.warning(f"为商品 {product.id} 创建成本价格记录失败: {e}")
                        continue
            
            return mapped_count
            
        except Exception as e:
            logger.error(f"建立价格映射关系失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return mapped_count
    
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
            
            # 同步分类（已禁用，无需获取商品分类）
            # results['categories'] = await self.sync_categories()
            
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

