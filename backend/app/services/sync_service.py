"""数据同步服务 - 从Temu API同步数据到数据库"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
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
            begin_time: 开始时间
            end_time: 结束时间
            full_sync: 是否全量同步
            
        Returns:
            同步统计 {new: 新增数量, updated: 更新数量, total: 总数}
        """
        stats = {"new": 0, "updated": 0, "total": 0, "failed": 0}
        
        try:
            # 默认同步最近7天的订单
            if not end_time:
                end_time = int(datetime.now().timestamp())
            if not begin_time:
                days = 30 if full_sync else 7
                begin_time = int((datetime.now() - timedelta(days=days)).timestamp())
            
            logger.info(
                f"开始同步订单 - 店铺: {self.shop.shop_name}, "
                f"时间范围: {datetime.fromtimestamp(begin_time)} ~ {datetime.fromtimestamp(end_time)}"
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
                        logger.error(f"处理订单失败: {e}")
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
            order_data: 订单数据
        """
        parent_order = order_data.get('parentOrderMap', {})
        order_list = order_data.get('orderList', [])
        
        # 处理父订单下的每个子订单
        for order_item in order_list:
            order_sn = order_item.get('orderSn')
            
            # 查找现有订单
            existing_order = self.db.query(Order).filter(
                Order.order_sn == order_sn
            ).first()
            
            if existing_order:
                # 更新现有订单
                self._update_order(existing_order, order_item, parent_order)
            else:
                # 创建新订单
                self._create_order(order_item, parent_order)
    
    def _create_order(self, order_item: Dict[str, Any], parent_order: Dict[str, Any]):
        """创建新订单"""
        # 映射订单状态
        order_status_map = {
            0: OrderStatus.PENDING,
            1: OrderStatus.PENDING,
            2: OrderStatus.PROCESSING,
            3: OrderStatus.SHIPPED,
            4: OrderStatus.DELIVERED,
            5: OrderStatus.CANCELLED,
        }
        
        temu_status = parent_order.get('parentOrderStatus', 0)
        order_status = order_status_map.get(temu_status, OrderStatus.PENDING)
        
        # 创建订单对象
        order = Order(
            shop_id=self.shop.id,
            order_sn=order_item.get('orderSn'),
            temu_order_id=parent_order.get('parentOrderSn'),
            
            # 商品信息
            product_name=order_item.get('spec', 'Unknown Product'),
            product_sku=order_item.get('spec', ''),
            quantity=order_item.get('goodsNumber', 1),
            
            # 金额信息
            unit_price=0.0,
            total_price=0.0,
            currency='USD',
            
            # 状态和时间
            status=order_status,
            order_time=datetime.fromtimestamp(parent_order.get('parentOrderTime', 0)),
            
            # 备注
            notes=f"Environment: {self.shop.environment.value}, GoodsID: {order_item.get('goodsId', '')}"
        )
        
        self.db.add(order)
        logger.debug(f"创建新订单: {order.order_sn}")
    
    def _update_order(
        self, 
        order: Order, 
        order_item: Dict[str, Any], 
        parent_order: Dict[str, Any]
    ):
        """更新现有订单"""
        # 映射订单状态
        order_status_map = {
            0: OrderStatus.PENDING,
            1: OrderStatus.PENDING,
            2: OrderStatus.PROCESSING,
            3: OrderStatus.SHIPPED,
            4: OrderStatus.DELIVERED,
            5: OrderStatus.CANCELLED,
        }
        
        temu_status = parent_order.get('parentOrderStatus', 0)
        new_status = order_status_map.get(temu_status, order.status)
        
        # 只更新状态发生变化的订单
        if order.status != new_status:
            order.status = new_status
            logger.debug(f"更新订单状态: {order.order_sn} -> {new_status}")
    
    async def sync_products(self, full_sync: bool = False) -> Dict[str, int]:
        """
        同步商品数据
        
        Args:
            full_sync: 是否全量同步
            
        Returns:
            同步统计
        """
        stats = {"new": 0, "updated": 0, "total": 0, "failed": 0}
        
        try:
            logger.info(f"开始同步商品 - 店铺: {self.shop.shop_name}")
            
            page_number = 1
            page_size = 100
            
            while True:
                # 获取商品列表
                result = await self.temu_service.get_products(
                    page_number=page_number,
                    page_size=page_size
                )
                
                # 注意：商品列表可能返回null（测试账号暂无商品）
                if result is None:
                    logger.info(f"商品列表为空 - 店铺: {self.shop.shop_name}")
                    break
                
                # TODO: 处理商品数据
                # 具体实现取决于API返回的数据结构
                
                # 这里暂时跳出循环，因为测试账号没有商品数据
                break
            
            self.db.commit()
            
            logger.info(
                f"商品同步完成 - 店铺: {self.shop.shop_name}, "
                f"总数: {stats['total']}"
            )
            
            return stats
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"商品同步失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
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

