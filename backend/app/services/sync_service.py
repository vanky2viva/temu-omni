"""数据同步服务 - 从Temu API同步数据到数据库"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from sqlalchemy.orm import Session
from loguru import logger
import pytz

from app.models.shop import Shop
from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductCost
from app.models.temu_orders_raw import TemuOrdersRaw
from app.models.temu_products_raw import TemuProductsRaw
from app.services.temu_service import TemuService, get_temu_service
from app.services.data_mapping_service import DataMappingService, DataMappingError
from app.core.redis_client import RedisClient
from app.core.config import settings

# 北京时间时区（UTC+8）
BEIJING_TIMEZONE = pytz.timezone(getattr(settings, 'TIMEZONE', 'Asia/Shanghai'))


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
        self.mapping_service = DataMappingService(db)
    
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
        
        # 获取当前有效的成本价（不使用历史成本，统一使用当前成本）
        cost_price = None
        cost_currency = None
        # 获取当前有效的成本价（effective_to为NULL的记录）
        cost_record = self.db.query(ProductCost).filter(
            ProductCost.product_id == product.id,
            ProductCost.effective_to.is_(None)
        ).order_by(ProductCost.effective_from.desc()).first()
        
        if cost_record:
            cost_price = cost_record.cost_price
            cost_currency = cost_record.currency
            logger.debug(
                f"找到商品 {product.sku} 当前有效的成本价: {cost_price} {cost_currency} (所有订单使用此成本)"
            )
        
        return {
            'product_id': product.id,
            'supply_price': supply_price,
            'cost_price': cost_price,
            'cost_currency': cost_currency,  # 返回成本价的货币
            'currency': product.currency
        }
    
    async def sync_orders(
        self,
        begin_time: Optional[int] = None,
        end_time: Optional[int] = None,
        full_sync: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, int]:
        """
        同步订单数据
        
        Args:
            begin_time: 开始时间（Unix时间戳，秒）
            end_time: 结束时间（Unix时间戳，秒）
            full_sync: 是否全量同步
                - True: 全量同步，不限制时间范围（如果begin_time未指定，则从最早开始）
                - False: 增量同步，从最后同步时间开始（如果从未同步，则同步最近7天）
            progress_callback: 进度回调函数，接收 (当前进度百分比, 当前步骤描述, time_info) 参数
            
        Returns:
            同步统计 {new: 新增数量, updated: 更新数量, total: 总数}
        """
        stats = {"new": 0, "updated": 0, "total": 0, "failed": 0}
        self._current_stats = stats  # 用于在_process_order中更新统计
        self._progress_callback = progress_callback  # 保存回调函数
        self._sync_start_time = datetime.now()  # 记录同步开始时间
        
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
            total_items = 0  # 总订单数
            
            while True:
                try:
                    # 获取订单列表（添加超时保护）
                    result = await self.temu_service.get_orders(
                        begin_time=begin_time,
                        end_time=end_time,
                        page_number=page_number,
                        page_size=page_size
                    )
                    
                    total_items = result.get('totalItemNum', 0)
                    page_items = result.get('pageItems', [])
                    
                    # 首次获取到总数时更新进度
                    if page_number == 1 and total_items > 0 and progress_callback:
                        progress_callback(20, f"发现 {total_items} 个订单，开始同步...", None)
                        logger.info(f"发现 {total_items} 个订单，开始同步...")
                    
                    if not page_items:
                        break
                except Exception as e:
                    logger.error(f"获取订单列表失败 (页码: {page_number}): {e}")
                    # 如果获取订单列表失败，尝试跳过当前页继续
                    if page_number == 1:
                        # 第一页失败，无法继续
                        raise
                    else:
                        # 非第一页失败，记录错误但继续尝试下一页
                        logger.warning(f"跳过第 {page_number} 页，继续同步...")
                        page_number += 1
                        continue
                
                # 性能优化：批量预加载当前页的订单ID，减少数据库查询
                order_sns = [item.get('orderSn') or item.get('order_sn') for item in page_items if item.get('orderSn') or item.get('order_sn')]
                existing_orders_map = {}
                if order_sns:
                    # 批量查询当前页可能存在的订单
                    existing_orders = self.db.query(Order).filter(
                        Order.shop_id == self.shop.id,
                        Order.temu_order_id.in_(order_sns)
                    ).all()
                    # 构建订单SN到订单对象的映射
                    for order in existing_orders:
                        existing_orders_map[order.temu_order_id] = order
                
                # 批量处理订单（每100个提交一次，提高性能）
                batch_size = 100
                batch_count = 0
                
                # 处理每个订单
                for item in page_items:
                    try:
                        # 传递预加载的订单映射，减少查询
                        self._process_order(item, existing_orders_map=existing_orders_map)
                        batch_count += 1
                        stats["total"] += 1
                        
                        # 批量提交：每100个订单提交一次，或处理完当前页时提交
                        if batch_count >= batch_size or item == page_items[-1]:
                            try:
                                self.db.commit()
                            except Exception as commit_error:
                                logger.error(f"提交数据库事务失败: {commit_error}")
                                self.db.rollback()
                                # 继续处理下一个订单，不中断整个同步过程
                            batch_count = 0
                        
                        # 优化进度更新频率：每50个订单更新一次（减少回调开销）
                        if progress_callback and total_items > 0 and stats["total"] % 50 == 0:
                            progress_percent = 20 + int((stats["total"] / total_items) * 40)
                            
                            # 计算处理速度和剩余时间
                            current_time = datetime.now()
                            start_time = getattr(self, '_sync_start_time', current_time)
                            elapsed_time = (current_time - start_time).total_seconds()
                            
                            # 构建时间信息
                            time_info = None
                            if elapsed_time > 0 and stats["total"] > 0:
                                processing_speed = stats["total"] / elapsed_time
                                remaining_items = total_items - stats["total"]
                                estimated_remaining_seconds = remaining_items / processing_speed if processing_speed > 0 else 0
                                
                                time_info = {
                                    "elapsed_seconds": elapsed_time,
                                    "processing_speed": processing_speed,
                                    "estimated_remaining_seconds": estimated_remaining_seconds,
                                    "processed_count": stats["total"],
                                    "total_count": total_items
                                }
                                
                                # 每处理100个订单记录一次详细日志
                                if stats["total"] % 100 == 0:
                                    # 格式化剩余时间
                                    if estimated_remaining_seconds < 60:
                                        time_str = f"{int(estimated_remaining_seconds)}秒"
                                    elif estimated_remaining_seconds < 3600:
                                        minutes = int(estimated_remaining_seconds // 60)
                                        seconds = int(estimated_remaining_seconds % 60)
                                        time_str = f"{minutes}分{seconds}秒"
                                    else:
                                        hours = int(estimated_remaining_seconds // 3600)
                                        minutes = int((estimated_remaining_seconds % 3600) // 60)
                                        time_str = f"{hours}小时{minutes}分钟"
                                    
                                    log_msg = (
                                        f"正在同步订单: {stats['total']}/{total_items} | "
                                        f"速度: {processing_speed:.1f} 订单/秒 | "
                                        f"剩余时间: {time_str} | "
                                        f"新增: {stats['new']}, 更新: {stats['updated']}"
                                    )
                                    # 通过回调函数记录日志
                                    if hasattr(progress_callback, '_log_callback'):
                                        progress_callback._log_callback(log_msg)
                            
                            progress_callback(
                                progress_percent,
                                f"正在同步订单: {stats['total']}/{total_items} (新增: {stats['new']}, 更新: {stats['updated']})",
                                time_info
                            )
                            
                    except Exception as e:
                        logger.error(f"处理订单失败: {e}, 订单数据: {item}")
                        try:
                            self.db.rollback()  # 回滚失败的订单
                        except Exception as rollback_error:
                            logger.error(f"回滚事务失败: {rollback_error}")
                            # 尝试重新创建数据库会话
                            try:
                                self.db.close()
                                from app.core.database import SessionLocal
                                self.db = SessionLocal()
                                logger.info("已重新创建数据库会话")
                            except Exception as reconnect_error:
                                logger.error(f"重新创建数据库会话失败: {reconnect_error}")
                        stats["failed"] += 1
                        batch_count = 0  # 重置批量计数
                        # 继续处理下一个订单，不中断整个同步过程
                
                # 确保当前页的所有订单都已提交
                if batch_count > 0:
                    self.db.commit()
                    batch_count = 0
                
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
    
    def _process_order(self, order_data: Dict[str, Any], existing_orders_map: Optional[Dict[str, Any]] = None):
        """
        处理单个订单数据（三层架构：先存raw表，再映射到业务表）
        
        Args:
            order_data: 订单数据（包含parentOrderMap和orderList）
            existing_orders_map: 预加载的订单映射（可选，用于性能优化）
        """
        parent_order = order_data.get('parentOrderMap', {})
        order_list = order_data.get('orderList', [])
        
        if not parent_order or not order_list:
            logger.warning(f"订单数据格式不完整: {order_data}")
            return
        
        parent_order_sn = parent_order.get('parentOrderSn')
        
        # 处理父订单下的每个子订单
        # 注意：无论订单的履约类型（fulfillmentType）是什么（fulfillBySeller 或 fulfillByCooperativeWarehouse），
        # 所有订单都会被同步到数据库，不根据履约类型过滤
        for order_item in order_list:
            order_sn = order_item.get('orderSn')
            if not order_sn:
                logger.warning(f"子订单缺少orderSn: {order_item}")
                continue
            
            # 步骤1: 先保存原始数据到raw表
            raw_order = self._save_order_to_raw(order_sn, order_data, order_item, parent_order)
            if not raw_order:
                logger.error(f"保存订单原始数据失败: {order_sn}")
                continue
            
            # 步骤2: 使用原有逻辑处理订单（保持稳定性），但关联raw_data_id
            self._process_order_legacy(order_item, parent_order, order_data, raw_order, existing_orders_map)
    
    def _save_order_to_raw(
        self, 
        order_sn: str, 
        full_order_data: Dict[str, Any],
        order_item: Dict[str, Any],
        parent_order: Dict[str, Any]
    ) -> Optional[TemuOrdersRaw]:
        """
        保存订单原始数据到raw表
        
        Args:
            order_sn: 订单号
            full_order_data: 完整订单数据
            order_item: 子订单数据
            parent_order: 父订单数据
            
        Returns:
            保存的raw订单对象，失败返回None
        """
        try:
            # 构建包含子订单和父订单信息的完整原始数据
            raw_json = {
                'parentOrderMap': parent_order,
                'orderItem': order_item,
                'fullOrderData': full_order_data
            }
            
            # 检查是否已存在
            existing_raw = self.db.query(TemuOrdersRaw).filter(
                TemuOrdersRaw.external_order_id == order_sn,
                TemuOrdersRaw.shop_id == self.shop.id
            ).first()
            
            if existing_raw:
                # 更新现有记录
                existing_raw.raw_json = raw_json
                existing_raw.fetched_at = datetime.now()
                return existing_raw
            else:
                # 创建新记录
                raw_order = TemuOrdersRaw(
                    shop_id=self.shop.id,
                    external_order_id=order_sn,
                    raw_json=raw_json,
                    fetched_at=datetime.now()
                )
                self.db.add(raw_order)
                self.db.flush()  # 获取ID
                return raw_order
                
        except Exception as e:
            logger.error(f"保存订单原始数据失败: {order_sn}, 错误: {e}")
            return None
    
    def _map_and_save_order(
        self,
        raw_order: TemuOrdersRaw,
        order_item: Dict[str, Any],
        parent_order: Dict[str, Any]
    ):
        """
        使用映射服务将raw订单映射到业务表
        
        Args:
            raw_order: 原始订单数据
            order_item: 子订单数据
            parent_order: 父订单数据
        """
        # 由于DataMappingService期望的格式可能与实际API格式不完全匹配，
        # 我们需要先调整raw_json格式，或者直接使用现有的处理逻辑
        # 这里先尝试使用映射服务，如果失败则回退
        
        # 调整raw_json格式以匹配映射服务的期望
        # 将order_item和parent_order合并为一个订单对象
        adjusted_raw_json = {
            **order_item,
            **parent_order,
            'orderSn': order_item.get('orderSn'),
            'orderId': order_item.get('orderSn'),
            'parentOrderSn': parent_order.get('parentOrderSn'),
        }
        
        # 临时更新raw_json以进行映射（映射后可以恢复）
        original_raw_json = raw_order.raw_json
        raw_order.raw_json = adjusted_raw_json
        
        try:
            # 使用映射服务映射
            order_data = self.mapping_service.map_order_from_raw(raw_order)
            
            # 保存映射后的订单
            order = self.mapping_service.save_mapped_order(order_data, raw_order)
            
            # 恢复原始raw_json
            raw_order.raw_json = original_raw_json
            
            # 更新统计
            stats = getattr(self, '_current_stats', {})
            if order.id:  # 如果是新创建的订单
                stats['new'] = stats.get('new', 0) + 1
            else:
                stats['updated'] = stats.get('updated', 0) + 1
                
        except Exception as e:
            # 恢复原始raw_json
            raw_order.raw_json = original_raw_json
            raise DataMappingError(f"映射订单失败: {e}")
    
    def _process_order_legacy(
        self,
        order_item: Dict[str, Any], 
        parent_order: Dict[str, Any],
        full_order_data: Dict[str, Any],
        raw_order: Optional[TemuOrdersRaw] = None,
        existing_orders_map: Optional[Dict[str, Any]] = None
    ):
        """
        原有的订单处理逻辑（保持稳定性，但关联raw_data_id）
        
        Args:
            order_item: 子订单数据
            parent_order: 父订单数据
            full_order_data: 完整订单数据
            raw_order: 原始订单数据（可选）
        """
        order_sn = order_item.get('orderSn')
        if not order_sn:
            return
        
        # 提取包裹号（从order_item或parent_order的packageSnInfo中提取）
        package_sn = None
        # 优先从order_item中提取
        package_sn_info = order_item.get('packageSnInfo') or parent_order.get('packageSnInfo')
        if package_sn_info and isinstance(package_sn_info, list) and len(package_sn_info) > 0:
            # 取第一个包裹号
            package_sn = package_sn_info[0].get('packageSn') if isinstance(package_sn_info[0], dict) else None
        # 如果order_item中没有，尝试从parent_order中提取
        if not package_sn:
            parent_package_sn_info = parent_order.get('packageSnInfo')
            if parent_package_sn_info and isinstance(parent_package_sn_info, list) and len(parent_package_sn_info) > 0:
                package_sn = parent_package_sn_info[0].get('packageSn') if isinstance(parent_package_sn_info[0], dict) else None
        
        # 查找现有订单（使用唯一约束：order_sn + product_sku + spu_id）
        # 从 productList 中提取真正的SKU信息（extCode字段）
        product_list = order_item.get('productList', [])
        if product_list and len(product_list) > 0:
            product_info = product_list[0]
            product_sku = product_info.get('extCode') or ''
            product_id_value = product_info.get('productId')
            spu_id = str(product_id_value) if product_id_value is not None else ''
        else:
            product_sku = order_item.get('extCode') or ''
            spu_id_value = order_item.get('spuId') or order_item.get('spu_id')
            spu_id = str(spu_id_value) if spu_id_value is not None else ''
        
        # 性能优化：优先使用预加载的订单映射，减少数据库查询
        existing_order = None
        if existing_orders_map and order_sn in existing_orders_map:
            # 从预加载的映射中获取订单
            candidate_order = existing_orders_map[order_sn]
            # 检查是否匹配（order_sn + product_sku + spu_id）
            if (candidate_order.order_sn == order_sn and 
                candidate_order.product_sku == product_sku and 
                candidate_order.spu_id == spu_id):
                existing_order = candidate_order
            elif candidate_order.order_sn == order_sn and candidate_order.spu_id == spu_id:
                existing_order = candidate_order
        
        # 如果预加载映射中没有找到，再查询数据库（降级处理）
        if not existing_order:
            # 首先尝试精确匹配
            existing_order = self.db.query(Order).filter(
                Order.order_sn == order_sn,
                Order.product_sku == product_sku,
                Order.spu_id == spu_id
            ).first()
            
            if not existing_order and spu_id:
                existing_order = self.db.query(Order).filter(
                    Order.order_sn == order_sn,
                    Order.spu_id == spu_id
                ).first()
            
            if not existing_order:
                existing_order = self.db.query(Order).filter(
                    Order.temu_order_id == order_sn
                ).first()
        
        if existing_order:
            # 更新现有订单
            is_updated = self._update_order(existing_order, order_item, parent_order, full_order_data)
            if is_updated and raw_order:
                existing_order.raw_data_id = raw_order.id
            if is_updated:
                stats = getattr(self, '_current_stats', {})
                stats['updated'] = stats.get('updated', 0) + 1
        else:
            # 创建新订单
            try:
                order = self._create_order(order_item, parent_order, full_order_data, raw_order)
                stats = getattr(self, '_current_stats', {})
                stats['new'] = stats.get('new', 0) + 1
            except Exception as create_error:
                error_msg = str(create_error)
                if 'UniqueViolation' in error_msg or 'duplicate key' in error_msg.lower():
                    existing_order = self.db.query(Order).filter(
                        Order.temu_order_id == order_sn
                    ).first()
                    if existing_order:
                        is_updated = self._update_order(existing_order, order_item, parent_order, full_order_data)
                        if is_updated and raw_order:
                            existing_order.raw_data_id = raw_order.id
                        if is_updated:
                            stats = getattr(self, '_current_stats', {})
                            stats['updated'] = stats.get('updated', 0) + 1
                else:
                    raise
    
    def _create_order(
        self, 
        order_item: Dict[str, Any], 
        parent_order: Dict[str, Any],
        full_order_data: Dict[str, Any],
        raw_order: Optional[TemuOrdersRaw] = None
    ):
        """
        创建新订单
        
        Args:
            order_item: 子订单数据
            parent_order: 父订单数据
            full_order_data: 完整订单数据（用于保存raw_data）
            raw_order: 原始订单数据（可选）
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
        
        # 价格信息将在匹配商品后从商品表的供货价（current_price）计算
        # 不直接从API响应中获取价格，因为价格应该从商品列表中填入的供货价计算
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
        
        # 提取客户信息（仅客户ID，不存储其他个人信息）
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
            # 匹配到商品，计算并存储GMV、成本、利润
            # 所有价格统一转换为CNY存储
            from app.utils.currency import CurrencyConverter
            usd_rate = Decimal(str(CurrencyConverter.USD_TO_CNY_RATE))
            
            # 获取供货价，转换为CNY
            supply_price = price_info.get('supply_price') or Decimal('0')
            product_currency = price_info.get('currency', 'USD')
            
            # 将供货价转换为CNY
            if product_currency == 'USD':
                unit_price_cny = supply_price * usd_rate
            else:
                unit_price_cny = supply_price
            
            # 存储时使用CNY值，但保留原始货币信息
            unit_price = unit_price_cny
            total_price = unit_price * Decimal(quantity) if quantity else Decimal('0')
            
            # 获取成本价，转换为CNY
            cost_price_from_db = price_info.get('cost_price')
            cost_currency = price_info.get('cost_currency')  # 成本价的货币
            matched_product_id = price_info['product_id']
            
            # 如果成本价存在，转换为CNY
            unit_cost = None
            if cost_price_from_db is not None:
                # 如果成本价货币未指定，使用商品货币
                if not cost_currency:
                    cost_currency = product_currency
                
                # 将成本价转换为CNY
                if cost_currency == 'USD':
                    unit_cost = cost_price_from_db * usd_rate
                else:
                    unit_cost = cost_price_from_db
                
                logger.debug(
                    f"成本价货币转换: {cost_price_from_db} {cost_currency} -> {unit_cost} CNY"
                )
            
            # 计算总成本和利润（基于该SKU的数量，所有值都是CNY）
            if unit_cost is not None and quantity:
                total_cost = unit_cost * Decimal(quantity)
                profit = total_price - total_cost
                logger.info(
                    f"✅ 订单 {order_item.get('orderSn')} 成功匹配商品并计算价格和成本 - "
                    f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {spu_id}, "
                    f"数量: {quantity}, 单价（供货价）: {unit_price}, GMV: {total_price}, "
                    f"单位成本: {unit_cost}, 总成本: {total_cost}, 利润: {profit}"
                )
            else:
                # 匹配到商品但无成本价，只计算GMV，成本和利润为NULL
                total_cost = None
                profit = None
                logger.warning(
                    f"⚠️  订单 {order_item.get('orderSn')} "
                    f"(productSkuId: {product_sku_id}, extCode: {product_sku}) "
                    f"匹配到商品但无成本价或数量为0，无法计算成本和利润，GMV: {total_price}"
                )
        else:
            # 如果未匹配到商品，价格设为0
            unit_price = Decimal('0')
            total_price = Decimal('0')
            unit_cost = None
            total_cost = None
            profit = None
            matched_product_id = None
            logger.warning(
                f"❌ 订单 {order_item.get('orderSn')} 未找到匹配商品 - "
                f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {spu_id}。"
                f"请检查商品列表中是否已添加对应的商品和供货价，订单GMV将设为0"
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
            package_sn=package_sn,  # 包裹号
            
            # 商品信息
            product_id=matched_product_id,  # 匹配到的商品ID
            product_name=product_name,
            product_sku=product_sku,
            spu_id=spu_id,
            quantity=quantity,  # 该SKU的数量
            
            # 金额信息（该SKU的金额，统一存储为CNY）
            # 注意：unit_price和total_price统一存储为CNY，currency字段保留原始货币信息
            unit_price=unit_price,  # 已转换为CNY
            total_price=total_price,  # 已转换为CNY
            currency=currency,  # 保留原始货币信息（USD/CNY等）
            
            # 成本和利润（该SKU的成本和利润，统一存储为CNY）
            unit_cost=unit_cost,  # 已转换为CNY
            total_cost=total_cost,  # 已转换为CNY
            profit=profit,  # 已转换为CNY
            
            # 状态和时间
            status=order_status,
            order_time=order_time or datetime.now(),
            payment_time=payment_time,
            shipping_time=shipping_time,
            expect_ship_latest_time=expect_ship_latest_time,
            delivery_time=delivery_time,
            
            # 客户信息
            customer_id=customer_id if customer_id else None,
            
            # 关联原始数据
            raw_data_id=raw_order.id if raw_order else None,
            
            # 注意：raw_data字段已废弃，现在使用raw_data_id关联到temu_orders_raw表
            # raw_data=json.dumps(full_order_data, ensure_ascii=False),  # 已废弃
            notes=f"Environment: {self.shop.environment.value}, GoodsID: {goods_id}"
        )
        
        self.db.add(order)
        logger.debug(
            f"创建新订单: {order.order_sn}, SKU: {product_sku}, SPU: {spu_id}, "
            f"数量: {quantity}, 总价: {total_price}, 利润: {profit}"
        )
        
        # 清除相关统计缓存
        self._invalidate_statistics_cache(order.shop_id, order.order_time.date())
        
        # 返回创建的订单对象
        return order
    
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
        
        # 提取包裹号（从order_item或parent_order的packageSnInfo中提取）
        package_sn = None
        # 优先从order_item中提取
        package_sn_info = order_item.get('packageSnInfo') or parent_order.get('packageSnInfo')
        if package_sn_info and isinstance(package_sn_info, list) and len(package_sn_info) > 0:
            # 取第一个包裹号
            package_sn = package_sn_info[0].get('packageSn') if isinstance(package_sn_info[0], dict) else None
        # 如果order_item中没有，尝试从parent_order中提取
        if not package_sn:
            parent_package_sn_info = parent_order.get('packageSnInfo')
            if parent_package_sn_info and isinstance(parent_package_sn_info, list) and len(parent_package_sn_info) > 0:
                package_sn = parent_package_sn_info[0].get('packageSn') if isinstance(parent_package_sn_info[0], dict) else None
        
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
        
        # 价格信息将在匹配商品后从商品表的供货价（current_price）更新
        # 不直接从API响应中获取价格，因为价格应该从商品列表中填入的供货价计算
        
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
            not order.product_id  # 如果没有关联商品，尝试重新匹配
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
                # 使用商品的供货价（current_price）更新订单价格
                supply_price = price_info.get('supply_price') or Decimal('0')
                new_unit_price = supply_price
                new_total_price = new_unit_price * Decimal(order.quantity) if order.quantity else Decimal('0')
                
                # 更新订单价格（如果发生变化）
                if order.unit_price != new_unit_price:
                    order.unit_price = new_unit_price
                    updated = True
                
                if order.total_price != new_total_price:
                    order.total_price = new_total_price
                    updated = True
                
                unit_cost = price_info['cost_price']
                
                if unit_cost is not None and order.quantity:
                    # 计算总成本和利润（使用更新后的总价）
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
        
        # 注意：raw_data字段已废弃，现在使用raw_data_id关联到temu_orders_raw表
        # 更新raw_data_id关联（如果需要）
        # new_raw_data = json.dumps(full_order_data, ensure_ascii=False)  # 已废弃
        # if order.raw_data != new_raw_data:
        #     order.raw_data = new_raw_data
        #     updated = True
        
        # 更新父订单关系（如果缺失）
        parent_order_sn = parent_order.get('parentOrderSn')
        if parent_order_sn and not order.parent_order_sn:
            order.parent_order_sn = parent_order_sn
            updated = True
        
        # 更新包裹号
        if package_sn and order.package_sn != package_sn:
            order.package_sn = package_sn
            updated = True
        
        # 如果订单已更新，清除相关统计缓存
        if updated:
            self._invalidate_statistics_cache(order.shop_id, order.order_time.date())
        
        return updated
    
    def _invalidate_statistics_cache(self, shop_id: int, order_date: date):
        """
        订单更新时清除相关统计缓存
        
        Args:
            shop_id: 店铺ID
            order_date: 订单日期
        """
        try:
            # 清除该店铺该日期的所有统计缓存
            pattern = f"stats:*shop*{shop_id}*date*{order_date}*"
            deleted = RedisClient.delete_pattern(pattern)
            if deleted > 0:
                logger.debug(f"已清除统计缓存: shop_id={shop_id}, date={order_date}, 删除{deleted}个键")
            
            # 也清除包含该店铺ID的所有统计缓存（更宽泛的匹配）
            pattern2 = f"stats:order:shops:*{shop_id}*"
            deleted2 = RedisClient.delete_pattern(pattern2)
            if deleted2 > 0:
                logger.debug(f"已清除统计缓存（宽泛匹配）: shop_id={shop_id}, 删除{deleted2}个键")
        except Exception as e:
            # 缓存清除失败不应该影响主流程
            logger.warning(f"清除统计缓存失败: {e}")
    
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
        
        重要：时间戳通常是从 UTC 时间计算的，所以需要转换为北京时间。
        返回的 datetime 是 naive datetime（不带时区信息），但表示的是北京时间，
        可以直接存储到数据库。
        
        Args:
            timestamp: 时间戳（秒或毫秒）
            
        Returns:
            datetime对象（naive，表示北京时间），如果解析失败返回None
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
    
    async def sync_products(self, full_sync: bool = False, progress_callback: Optional[callable] = None) -> Dict[str, int]:
        """
        同步商品数据
        
        Args:
            full_sync: 是否全量同步
                - True: 全量同步，同步所有商品
                - False: 增量同步，只同步新增和更新的商品（通过商品ID判断）
            progress_callback: 进度回调函数，接收 (当前进度百分比, 当前步骤描述) 参数
            
        Returns:
            同步统计
        """
        stats = {"new": 0, "updated": 0, "total": 0, "failed": 0}
        self._current_stats = stats  # 用于在_process_product中更新统计
        self._progress_callback = progress_callback  # 保存回调函数
        
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
            
            # 用于追踪商品总数的变量
            total_items = 0
            
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
                current_total = (
                    result.get('totalCount') or  # CN端点可能使用此字段
                    result.get('totalItemNum') or 
                    result.get('total') or 
                    result.get('totalNum') or
                    0
                )
                
                # 更新总数（第一次获取或更准确的值）
                if current_total > 0:
                    total_items = current_total
                    # 首次获取到总数时更新进度
                    if page_number == 1 and progress_callback:
                        progress_callback(60, f"发现 {total_items} 个商品，开始同步...")
                
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
                
                for idx, product_item in enumerate(product_list):
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
                        
                        # 实时更新进度（商品同步占60%-90%）
                        if progress_callback and total_items > 0:
                            current_product = (page_number - 1) * page_size + idx + 1
                            progress_callback(
                                60 + int((current_product / total_items) * 30),
                                f"正在同步商品: {stats['total']}/{total_items}"
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
                        
                        # 步骤1: 先保存原始数据到raw表
                        raw_product = self._save_product_to_raw(product_item)
                        if not raw_product:
                            logger.error(f"保存商品原始数据失败: {product_id}")
                            continue
                        
                        # 步骤2: 处理商品（关联raw_data_id）
                        self._process_product(product_item, raw_product)
                        stats["total"] += 1
                        
                        # 批量提交：每100个商品提交一次，提高性能
                        if stats["total"] % 100 == 0:
                            self.db.commit()
                    except Exception as e:
                        logger.error(f"处理商品失败: {e}, 商品ID: {product_id}, 商品名称: {product_name}")
                        self.db.rollback()  # 回滚失败的商品
                        stats["failed"] += 1
                
                # 确保当前页的所有商品都已提交
                if stats["total"] % 100 != 0:
                    self.db.commit()
                
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
    
    def _save_product_to_raw(self, product_data: Dict[str, Any]) -> Optional[TemuProductsRaw]:
        """
        保存商品原始数据到raw表
        
        Args:
            product_data: 商品数据
            
        Returns:
            保存的raw商品对象，失败返回None
        """
        try:
            # 提取商品ID
            product_id = (
                str(product_data.get('productId')) or
                str(product_data.get('goodsId')) or
                str(product_data.get('id')) or
                ''
            )
            
            if not product_id:
                logger.warning(f"商品数据缺少ID，无法保存到raw表: {product_data}")
                return None
            
            # 检查是否已存在
            existing_raw = self.db.query(TemuProductsRaw).filter(
                TemuProductsRaw.external_product_id == product_id,
                TemuProductsRaw.shop_id == self.shop.id
            ).first()
            
            if existing_raw:
                # 更新现有记录
                existing_raw.raw_json = product_data
                existing_raw.fetched_at = datetime.now()
                return existing_raw
            else:
                # 创建新记录
                raw_product = TemuProductsRaw(
                    shop_id=self.shop.id,
                    external_product_id=product_id,
                    raw_json=product_data,
                    fetched_at=datetime.now()
                )
                self.db.add(raw_product)
                self.db.flush()  # 获取ID
                return raw_product
                
        except Exception as e:
            logger.error(f"保存商品原始数据失败: {product_id}, 错误: {e}")
            return None
    
    def _process_product(self, product_data: Dict[str, Any], raw_product: Optional[TemuProductsRaw] = None):
        """
        处理单个商品数据（三层架构：关联raw_data_id）
        
        Args:
            product_data: 商品数据
            raw_product: 原始商品数据（可选）
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
                    
                    self._create_or_update_product_from_data(combined_data, sku_id, raw_product)
                else:
                    logger.warning(f"SKU数据缺少ID，跳过 - SKU索引: {idx}, SKU数据: {sku_data}")
    
    def _create_or_update_product_from_data(
        self, 
        product_data: Dict[str, Any], 
        goods_id: str,
        raw_product: Optional[TemuProductsRaw] = None
    ):
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
            if is_updated and raw_product:
                existing_product.raw_data_id = raw_product.id
            if is_updated:
                stats = getattr(self, '_current_stats', {})
                stats['updated'] = stats.get('updated', 0) + 1
        else:
            # 创建新商品
            product = self._create_product(product_data)
            if raw_product and product:
                product.raw_data_id = raw_product.id
            stats = getattr(self, '_current_stats', {})
            stats['new'] = stats.get('new', 0) + 1
    
    def _create_product(self, product_data: Dict[str, Any]) -> Optional[Product]:
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
        return product
    
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

