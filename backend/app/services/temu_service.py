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
        
        重要：不同端点需要使用不同的 app_key/secret 和 access_token：
        - 订单API：使用标准端点（US/EU/GLOBAL）的 app_key/secret 和标准 access_token
        - 商品API：如果配置了 CN access_token，使用 CN 端点的 app_key/secret 和 CN access_token
                  否则使用标准端点的 app_key/secret 和标准 access_token
        
        Args:
            shop: 店铺模型实例
        """
        self.shop = shop
        
        # 注意：不再在初始化时创建固定的客户端
        # 而是在需要时根据操作类型（订单/商品）动态创建对应的客户端
        # 这样可以确保使用正确的 app_key/secret 和 access_token
        
        logger.info(
            f"初始化Temu服务 - 店铺: {shop.shop_name}, "
            f"区域: {shop.region}, 环境: {shop.environment}"
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
        验证Token是否有效（验证标准端点的Token）
        
        Returns:
            Token信息
        """
        try:
            # 使用标准端点的客户端验证Token
            standard_client = self._get_standard_client()
            token_info = await standard_client.get_token_info(self.access_token)
            await standard_client.close()
            
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
    
    def _get_standard_client(self) -> TemuAPIClient:
        """
        获取标准端点（US/EU/GLOBAL）的客户端
        
        用于订单等需要使用标准端点的操作
        使用标准端点的 app_key/secret（从环境变量或店铺配置读取）
        """
        # 获取标准端点的API基础URL（根据店铺区域）
        api_base_url = self.shop.api_base_url or self.REGION_API_URLS.get(
            self.shop.region, 
            self.REGION_API_URLS[ShopRegion.US]
        )
        
        # 优先使用店铺自己的 app_key 和 app_secret（标准端点）
        # 如果店铺没有配置，则使用全局配置（US端点的app_key/secret）
        from app.core.config import settings
        app_key = self.shop.app_key or settings.TEMU_APP_KEY
        app_secret = self.shop.app_secret or settings.TEMU_APP_SECRET
        
        # 获取代理配置（所有请求都必须通过代理）
        proxy_url = settings.TEMU_API_PROXY_URL
        
        if not proxy_url:
            raise ValueError(
                "代理服务器未配置。所有 API 请求必须通过代理服务器。"
                "请在配置中设置 TEMU_API_PROXY_URL。"
            )
        
        # 创建标准端点客户端（必须通过代理）
        client = TemuAPIClient(
            app_key=app_key,
            app_secret=app_secret,
            proxy_url=proxy_url
        )
        client.base_url = api_base_url
        
        logger.debug(
            f"创建标准端点客户端 - 店铺: {self.shop.shop_name}, "
            f"区域: {self.shop.region}, "
            f"API URL: {api_base_url}, "
            f"App Key: {app_key[:10]}..., "
            f"使用代理: {'是' if proxy_url else '否'}"
        )
        
        return client
    
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
        
        注意：订单API必须使用标准端点（US/EU/GLOBAL）的 app_key/secret 和 access_token
        CN端点仅支持商品列表、发品、库存、备货履约等操作
        
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
            # 订单API必须使用标准端点的access_token（不是CN access_token）
            if not self.shop.access_token:
                raise ValueError(
                    f"店铺 {self.shop.shop_name} 未配置标准端点的 Access Token。"
                    f"订单API需要使用标准端点的 Access Token，不能使用CN端点的 Token。"
                )
            
            # 使用标准端点的客户端（使用标准端点的 app_key/secret）
            standard_client = self._get_standard_client()
            
            logger.info(
                f"使用标准端点获取订单 - 店铺: {self.shop.shop_name}, "
                f"区域: {self.shop.region}, "
                f"API URL: {standard_client.base_url}"
            )
            
            orders = await standard_client.get_orders(
                access_token=self.access_token,
                begin_time=begin_time,
                end_time=end_time,
                page_number=page_number,
                page_size=page_size,
                order_status=order_status
            )
            
            await standard_client.close()
            
            logger.info(
                f"获取订单成功 - 店铺: {self.shop.shop_name}, "
                f"总数: {orders.get('totalItemNum', 0)}, "
                f"当前页: {page_number}"
            )
            
            return orders
            
        except Exception as e:
            logger.error(f"获取订单失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def get_order_detail(self, parent_order_sn: str) -> Dict[str, Any]:
        """
        获取订单详情
        
        使用标准端点的 app_key/secret 和 access_token
        
        注意：此接口需要父订单号（parentOrderSn），不是子订单号
        
        Args:
            parent_order_sn: 父订单编号（必填）
            
        Returns:
            订单详情
        """
        try:
            # 使用标准端点的客户端
            standard_client = self._get_standard_client()
            order = await standard_client.get_order_detail(
                access_token=self.access_token,
                parent_order_sn=parent_order_sn
            )
            await standard_client.close()
            
            logger.info(f"获取订单详情成功 - 父订单号: {parent_order_sn}")
            return order
            
        except Exception as e:
            logger.error(f"获取订单详情失败 - 父订单号: {parent_order_sn}, 错误: {e}")
            raise
    
    async def get_products(
        self,
        page_number: int = 1,
        page_size: int = 100,
        goods_status: Optional[int] = None,
        skc_site_status: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取商品列表（根据API端点动态选择接口类型）
        
        根据API文档：https://agentpartner.temu.com/document?cataId=875198836203&docId=899313688269
        
        使用 CN 区域的配置（cn_app_key, cn_app_secret, cn_access_token）
        端点：使用店铺配置的 cn_api_base_url 或默认 https://openapi.kuajingmaihuo.com/openapi/router
        
        根据API端点自动选择接口类型：
        - PARTNER区域（openapi-b-partner.temu.com）: 使用 bg.glo.goods.list.get
        - CN区域（openapi.kuajingmaihuo.com）: 使用 bg.goods.list.get
        
        Args:
            page_number: 页码（从1开始）
            page_size: 每页数量
            goods_status: 商品状态（已废弃，使用skc_site_status）
            skc_site_status: SKC站点状态（0=未加入站点，1=已加入站点/在售）
            
        Returns:
            商品数据
        """
        try:
            # 使用 CN 区域配置获取商品列表
            # 使用店铺配置的 cn_api_base_url 或默认 https://openapi.kuajingmaihuo.com/openapi/router 端点
            # 根据API端点动态选择接口类型（PARTNER区域使用bg.glo.goods.list.get，CN区域使用bg.goods.list.get）
            
            # 检查CN区域配置
            if not self.shop.cn_access_token:
                raise ValueError(
                    f"店铺 {self.shop.shop_name} 未配置 CN Access Token。"
                    f"商品列表同步需要使用 CN 区域的 access_token。"
                )
            
            from app.core.config import settings
            
            # 获取 CN 区域配置（必须全部来自 CN 区域）
            cn_api_url = self.shop.cn_api_base_url or 'https://openapi.kuajingmaihuo.com/openapi/router'
            cn_app_key = self.shop.cn_app_key or settings.TEMU_CN_APP_KEY
            cn_app_secret = self.shop.cn_app_secret or settings.TEMU_CN_APP_SECRET
            cn_access_token = self.shop.cn_access_token
            
            # 验证 CN 配置完整性
            if not cn_app_key or not cn_app_secret:
                raise ValueError(
                    "CN 区域配置不完整：必须同时配置 cn_app_key、cn_app_secret 和 cn_access_token"
                )
            
            # 创建 CN 客户端（使用 CN 区域的 app_key、secret 和接口地址）
            cn_client = TemuAPIClient(
                app_key=cn_app_key,
                app_secret=cn_app_secret,
                proxy_url=""  # 空字符串表示不使用代理，CN端点直接访问
            )
            cn_client.base_url = cn_api_url
            
            logger.info(
                f"使用 CN 端点获取商品列表 - 店铺: {self.shop.shop_name}, "
                f"API URL: {cn_api_url}, "
                f"页码: {page_number}, 每页: {page_size}"
            )
            
            # 构建请求参数
            request_data = {
                "page": page_number,  # 页码（从1开始）
                "pageSize": page_size,  # 页面大小
            }
            
            # 如果指定了skc_site_status，添加筛选参数（1=已加入站点/在售）
            if skc_site_status is not None:
                request_data["skcSiteStatus"] = skc_site_status
                logger.debug(f"使用状态筛选参数 - skcSiteStatus: {skc_site_status}")
            
            # 根据API URL动态选择API类型
            # PARTNER区域（openapi-b-partner）使用 bg.glo.goods.list.get
            # CN区域（openapi.kuajingmaihuo.com）使用 bg.goods.list.get
            if 'openapi-b-partner' in cn_api_url:
                api_type = "bg.glo.goods.list.get"
                logger.info(f"检测到PARTNER区域接口 ({cn_api_url})，使用: {api_type}")
            elif 'partner' in cn_api_url.lower() and 'openapi-b' in cn_api_url:
                api_type = "bg.glo.goods.list.get"
                logger.info(f"检测到PARTNER区域接口 ({cn_api_url})，使用: {api_type}")
            else:
                api_type = "bg.goods.list.get"
                logger.info(f"使用CN区域接口 ({cn_api_url}): {api_type}")
            
            # 使用动态选择的API类型
            logger.info(f"使用 {api_type} 接口获取商品列表...")
            products = await cn_client._request(
                api_type=api_type,
                request_data=request_data,
                access_token=cn_access_token,
                flat_params=True
            )
            api_type_used = api_type
            logger.info(f"✅ 成功使用 {api_type} 接口获取商品列表")
            
            await cn_client.close()
            
            if products is None:
                raise ValueError("未能获取商品数据，接口返回空结果")
            
            logger.info(
                f"获取商品成功 - 店铺: {self.shop.shop_name}, "
                f"页码: {page_number}, "
                f"使用的接口: {api_type_used}, "
                f"使用的端点: {cn_api_url}"
            )
            
            return products
            
        except Exception as e:
            logger.error(f"获取商品失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def search_products(
        self,
        page_number: int = 1,
        page_size: int = 100,
        product_skuld_list: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        查询货品生命周期状态（使用 bg.product.search 接口）
        
        根据API文档：https://agentpartner.temu.com/document?cataId=875198836203&docId=877297510235
        
        如果配置了 CN access_token，使用 CN 端点的 app_key/secret 和 CN access_token
        否则使用标准端点的 app_key/secret 和标准 access_token
        
        Args:
            page_number: 页编号（从1开始）
            page_size: 页大小
            product_skuld_list: 货品skuld列表（可选）
            
        Returns:
            货品数据，包含：
            - total: 总数
            - dataList: 数据列表
            - skcList: skc列表
        """
        try:
            # 获取mallId（优先从token信息获取，否则尝试从shop_id转换）
            mall_id = None
            
            # 如果配置了 CN access_token，使用 CN 端点
            if self.shop.cn_access_token:
                logger.info(f"使用 CN 端点查询货品生命周期状态 - 店铺: {self.shop.shop_name}")
                
                # 获取 CN 区域配置
                from app.core.config import settings
                cn_api_url = self.shop.cn_api_base_url or 'https://openapi.kuajingmaihuo.com/openapi/router'
                cn_app_key = self.shop.cn_app_key or settings.TEMU_CN_APP_KEY
                cn_app_secret = self.shop.cn_app_secret or settings.TEMU_CN_APP_SECRET
                cn_access_token = self.shop.cn_access_token
                
                # 验证 CN 配置完整性
                if not cn_app_key or not cn_app_secret:
                    raise ValueError(
                        "CN 区域配置不完整：必须同时配置 cn_app_key、cn_app_secret 和 cn_access_token"
                    )
                
                # 创建 CN 客户端
                cn_client = TemuAPIClient(
                    app_key=cn_app_key,
                    app_secret=cn_app_secret,
                    proxy_url=""  # CN端点直接访问
                )
                cn_client.base_url = cn_api_url
                
                # 尝试从token信息获取mallId
                try:
                    token_info = await cn_client.get_token_info(cn_access_token)
                    mall_id = token_info.get('mallId')
                    logger.info(f"从CN token信息获取mallId: {mall_id}")
                except Exception as e:
                    logger.warning(f"无法从CN token获取mallId: {e}")
                    # 尝试从shop_id转换
                    try:
                        mall_id = int(self.shop.shop_id)
                    except ValueError:
                        raise ValueError(
                            f"无法获取mallId：shop_id ({self.shop.shop_id}) 不是有效的数字，"
                            f"且无法从token信息获取mallId"
                        )
                
                logger.info(
                    f"CN 端点配置 - API URL: {cn_api_url}, "
                    f"App Key: {cn_app_key[:10]}..., "
                    f"Token: {cn_access_token[:10]}..., "
                    f"MallId: {mall_id}"
                )
                
                # 构建请求参数
                # 根据API文档：pageNum和pageSize是必填参数
                request_data = {
                    "mallId": int(mall_id),  # 商家Id（必填）
                    "pageNum": page_number,  # 页编号（从1开始，必填）
                    "pageSize": page_size,  # 页大小（必填）
                }
                
                # 如果提供了货品skuld列表，添加到请求中
                if product_skuld_list:
                    request_data["productSkuldList"] = product_skuld_list
                
                # 调用 bg.product.search API (使用平铺参数)
                result = await cn_client._request(
                    api_type="bg.product.search",
                    request_data=request_data,
                    access_token=cn_access_token,
                    flat_params=True
                )
                
                await cn_client.close()
                
                logger.info(
                    f"查询货品生命周期状态成功 - 店铺: {self.shop.shop_name}, "
                    f"页码: {page_number}, 总数: {result.get('total', 0)}"
                )
                
                return result
            else:
                # 使用标准端点
                if not self.shop.access_token:
                    raise ValueError(
                        f"店铺 {self.shop.shop_name} 未配置 Access Token。"
                        f"请配置标准端点的 Access Token 或 CN 端点的 Access Token。"
                    )
                
                # 使用标准端点的客户端
                standard_client = self._get_standard_client()
                
                # 尝试从token信息获取mallId
                try:
                    token_info = await standard_client.get_token_info(self.access_token)
                    mall_id = token_info.get('mallId')
                    logger.info(f"从标准token信息获取mallId: {mall_id}")
                except Exception as e:
                    logger.warning(f"无法从标准token获取mallId: {e}")
                    # 尝试从shop_id转换
                    try:
                        mall_id = int(self.shop.shop_id)
                    except ValueError:
                        raise ValueError(
                            f"无法获取mallId：shop_id ({self.shop.shop_id}) 不是有效的数字，"
                            f"且无法从token信息获取mallId"
                        )
                
                logger.info(
                    f"使用标准端点查询货品生命周期状态 - 店铺: {self.shop.shop_name}, "
                    f"区域: {self.shop.region}, MallId: {mall_id}"
                )
                
                # 构建请求参数
                # 根据API文档：pageNum和pageSize是必填参数
                request_data = {
                    "mallId": int(mall_id),  # 商家Id（必填）
                    "pageNum": page_number,  # 页编号（从1开始，必填）
                    "pageSize": page_size,  # 页大小（必填）
                }
                
                if product_skuld_list:
                    request_data["productSkuldList"] = product_skuld_list
                
                # 调用 API
                result = await standard_client._request(
                    api_type="bg.product.search",
                    request_data=request_data,
                    access_token=self.access_token
                )
                
                await standard_client.close()
                
                logger.info(
                    f"查询货品生命周期状态成功 - 店铺: {self.shop.shop_name}, "
                    f"页码: {page_number}, 总数: {result.get('total', 0)}"
                )
                
                return result
                
        except Exception as e:
            logger.error(f"查询货品生命周期状态失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def get_product_detail(self, goods_id: int) -> Dict[str, Any]:
        """
        获取商品详情
        
        如果配置了 CN access_token，使用 CN 端点；否则使用标准端点
        
        Args:
            goods_id: 商品ID
            
        Returns:
            商品详情
        """
        try:
            # 如果配置了 CN access_token，使用 CN 端点
            if self.shop.cn_access_token:
                cn_api_url = self.shop.cn_api_base_url or 'https://openapi.kuajingmaihuo.com/openapi/router'
                # CN App Key和Secret必须从环境变量或店铺配置中获取，不能硬编码
                from app.core.config import settings
                cn_app_key = self.shop.cn_app_key or settings.TEMU_CN_APP_KEY
                cn_app_secret = self.shop.cn_app_secret or settings.TEMU_CN_APP_SECRET
                
                cn_client = TemuAPIClient(
                    app_key=cn_app_key,
                    app_secret=cn_app_secret
                )
                cn_client.base_url = cn_api_url
                
                # CN端点可能使用不同的API类型，这里需要根据实际情况调整
                # 暂时使用标准客户端的方法，如果失败再调整
                product = await cn_client.get_product_detail(
                    access_token=self.shop.cn_access_token,
                    goods_id=goods_id
                )
                await cn_client.close()
            else:
                # 使用标准端点
                standard_client = self._get_standard_client()
                product = await standard_client.get_product_detail(
                    access_token=self.access_token,
                    goods_id=goods_id
                )
                await standard_client.close()
            
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
        
        使用标准端点的 app_key/secret 和 access_token
        
        Args:
            parent_cat_id: 父分类ID，0表示查询根分类
            
        Returns:
            分类数据
        """
        try:
            # 使用标准端点的客户端
            standard_client = self._get_standard_client()
            categories = await standard_client.get_product_categories(
                access_token=self.access_token,
                parent_cat_id=parent_cat_id
            )
            await standard_client.close()
            
            logger.info(
                f"获取商品分类成功 - 店铺: {self.shop.shop_name}, "
                f"父分类ID: {parent_cat_id}"
            )
            
            return categories
            
        except Exception as e:
            logger.error(f"获取商品分类失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def get_order_amount(self, order_sn: str) -> Dict[str, Any]:
        """
        查询订单金额（成交金额）
        
        参考文档: https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=ba20da993f7d4605909dd49a5c186c21
        
        Args:
            order_sn: 订单编号（父订单号或子订单号）
            
        Returns:
            订单金额信息
        """
        try:
            # 订单金额查询使用标准端点
            if not self.shop.access_token:
                raise ValueError(
                    f"店铺 {self.shop.shop_name} 未配置标准端点的 Access Token。"
                    f"订单金额查询需要使用标准端点的 Access Token。"
                )
            
            # 使用标准端点的客户端
            standard_client = self._get_standard_client()
            
            logger.info(
                f"查询订单金额 - 店铺: {self.shop.shop_name}, "
                f"订单号: {order_sn}"
            )
            
            amount_info = await standard_client.get_order_amount(
                access_token=self.access_token,
                order_sn=order_sn
            )
            
            await standard_client.close()
            
            logger.info(
                f"查询订单金额成功 - 店铺: {self.shop.shop_name}, "
                f"订单号: {order_sn}"
            )
            
            return amount_info
            
        except Exception as e:
            logger.error(f"查询订单金额失败 - 店铺: {self.shop.shop_name}, 订单号: {order_sn}, 错误: {e}")
            raise
    
    async def get_warehouses(self) -> Dict[str, Any]:
        """
        获取仓库列表
        
        使用标准端点的 app_key/secret 和 access_token
        
        Returns:
            仓库数据
        """
        try:
            # 使用标准端点的客户端
            standard_client = self._get_standard_client()
            warehouses = await standard_client.get_warehouses(
                access_token=self.access_token
            )
            await standard_client.close()
            
            logger.info(f"获取仓库列表成功 - 店铺: {self.shop.shop_name}")
            return warehouses
            
        except Exception as e:
            logger.error(f"获取仓库列表失败 - 店铺: {self.shop.shop_name}, 错误: {e}")
            raise
    
    async def close(self):
        """
        关闭客户端连接
        
        注意：由于现在使用动态创建的客户端，这个方法可能不再需要
        但保留以保持向后兼容性
        """
        # 不再需要关闭固定的客户端，因为现在使用动态创建的客户端
        pass


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

