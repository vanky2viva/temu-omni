"""Temu API服务层 - 支持多店铺、多区域、环境切换"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger

from app.temu.client import TemuAPIClient
from app.models.shop import Shop, ShopEnvironment, ShopRegion


class TemuService:
    """Temu API服务封装"""
    
    # 区域对应的API基础URL
    REGION_API_URLS = {
        ShopRegion.US: "https://openapi-b-us.temu.com/openapi/router",
        ShopRegion.EU: "https://openapi-b-eu.temu.com/openapi/router",
        ShopRegion.GLOBAL: "https://openapi-b-global.temu.com/openapi/router",
    }
    
    def __init__(self, shop: Shop):
        """
        初始化Temu服务
        
        Args:
            shop: 店铺模型实例
        """
        self.shop = shop
        
        # 获取API基础URL
        api_base_url = shop.api_base_url or self.REGION_API_URLS.get(
            shop.region, 
            self.REGION_API_URLS[ShopRegion.US]
        )
        
        # 创建API客户端
        self.client = TemuAPIClient(
            app_key=shop.app_key,
            app_secret=shop.app_secret
        )
        
        # 覆盖base_url
        self.client.base_url = api_base_url
        
        logger.info(
            f"初始化Temu服务 - 店铺: {shop.shop_name}, "
            f"区域: {shop.region}, 环境: {shop.environment}, "
            f"API URL: {api_base_url}"
        )
    
    @property
    def access_token(self) -> str:
        """获取访问令牌"""
        if not self.shop.access_token:
            raise ValueError(f"店铺 {self.shop.shop_name} 未配置访问令牌")
        return self.shop.access_token
    
    def is_sandbox(self) -> bool:
        """判断是否为沙盒环境"""
        return self.shop.environment == ShopEnvironment.SANDBOX
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.shop.environment == ShopEnvironment.PRODUCTION
    
    async def verify_token(self) -> Dict[str, Any]:
        """
        验证Token是否有效
        
        Returns:
            Token信息
        """
        try:
            token_info = await self.client.get_token_info(self.access_token)
            
            # 验证Token对应的Mall ID是否匹配
            if str(token_info.get('mallId')) != self.shop.shop_id:
                logger.warning(
                    f"Token的Mall ID ({token_info.get('mallId')}) "
                    f"与店铺ID ({self.shop.shop_id}) 不匹配"
                )
            
            logger.info(f"Token验证成功 - 店铺: {self.shop.shop_name}")
            return token_info
            
        except Exception as e:
            logger.error(f"Token验证失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def get_orders(
        self,
        begin_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page_number: int = 1,
        page_size: int = 100,
        order_status: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取订单列表
        
        Args:
            begin_time: 开始时间（Unix时间戳）
            end_time: 结束时间（Unix时间戳）
            page_number: 页码
            page_size: 每页数量
            order_status: 订单状态
            
        Returns:
            订单数据
        """
        # 默认查询最近30天
        if not end_time:
            end_time = int(datetime.now().timestamp())
        if not begin_time:
            begin_time = int((datetime.now() - timedelta(days=30)).timestamp())
        
        try:
            orders = await self.client.get_orders(
                access_token=self.access_token,
                begin_time=begin_time,
                end_time=end_time,
                page_number=page_number,
                page_size=page_size,
                order_status=order_status
            )
            
            logger.info(
                f"获取订单成功 - 店铺: {self.shop.shop_name}, "
                f"总数: {orders.get('totalItemNum', 0)}, "
                f"当前页: {page_number}"
            )
            
            return orders
            
        except Exception as e:
            logger.error(f"获取订单失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def get_order_detail(self, order_sn: str) -> Dict[str, Any]:
        """
        获取订单详情
        
        Args:
            order_sn: 订单编号
            
        Returns:
            订单详情
        """
        try:
            order = await self.client.get_order_detail(
                access_token=self.access_token,
                order_sn=order_sn
            )
            
            logger.info(f"获取订单详情成功 - 订单号: {order_sn}")
            return order
            
        except Exception as e:
            logger.error(f"获取订单详情失败 - 订单号: {order_sn}, 错误: {e}")
            raise
    
    async def get_products(
        self,
        page_number: int = 1,
        page_size: int = 100,
        goods_status: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取商品列表
        
        Args:
            page_number: 页码
            page_size: 每页数量
            goods_status: 商品状态
            
        Returns:
            商品数据
        """
        try:
            products = await self.client.get_products(
                access_token=self.access_token,
                page_number=page_number,
                page_size=page_size,
                goods_status=goods_status
            )
            
            logger.info(
                f"获取商品成功 - 店铺: {self.shop.shop_name}, "
                f"页码: {page_number}"
            )
            
            return products
            
        except Exception as e:
            logger.error(f"获取商品失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def get_product_detail(self, goods_id: int) -> Dict[str, Any]:
        """
        获取商品详情
        
        Args:
            goods_id: 商品ID
            
        Returns:
            商品详情
        """
        try:
            product = await self.client.get_product_detail(
                access_token=self.access_token,
                goods_id=goods_id
            )
            
            logger.info(f"获取商品详情成功 - 商品ID: {goods_id}")
            return product
            
        except Exception as e:
            logger.error(f"获取商品详情失败 - 商品ID: {goods_id}, 错误: {e}")
            raise
    
    async def get_product_categories(
        self,
        parent_cat_id: int = 0
    ) -> Dict[str, Any]:
        """
        获取商品分类
        
        Args:
            parent_cat_id: 父分类ID，0表示查询根分类
            
        Returns:
            分类数据
        """
        try:
            categories = await self.client.get_product_categories(
                access_token=self.access_token,
                parent_cat_id=parent_cat_id
            )
            
            logger.info(
                f"获取商品分类成功 - 店铺: {self.shop.shop_name}, "
                f"父分类ID: {parent_cat_id}"
            )
            
            return categories
            
        except Exception as e:
            logger.error(f"获取商品分类失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def get_warehouses(self) -> Dict[str, Any]:
        """
        获取仓库列表
        
        Returns:
            仓库数据
        """
        try:
            warehouses = await self.client.get_warehouses(
                access_token=self.access_token
            )
            
            logger.info(f"获取仓库列表成功 - 店铺: {self.shop.shop_name}")
            return warehouses
            
        except Exception as e:
            logger.error(f"获取仓库列表失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.close()


def get_temu_service(shop: Shop) -> TemuService:
    """
    工厂函数：创建Temu服务实例
    
    Args:
        shop: 店铺模型
        
    Returns:
        TemuService实例
    """
    if not shop.is_active:
        raise ValueError(f"店铺 {shop.shop_name} 已禁用")
    
    if not shop.access_token:
        raise ValueError(f"店铺 {shop.shop_name} 未配置访问令牌")
    
    return TemuService(shop)

