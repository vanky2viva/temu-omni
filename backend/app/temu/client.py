"""Temu API客户端"""
import asyncio
import hashlib
import json
import time
from typing import Dict, Any, Optional, List
import httpx
from loguru import logger
from app.core.config import settings
from app.core.rate_limiter import get_rate_limiter


class TemuAPIClient:
    """Temu API客户端"""
    
    def __init__(self, app_key: str = None, app_secret: str = None, proxy_url: str = None):
        """
        初始化Temu API客户端
        
        Args:
            app_key: 应用Key，如不提供则使用配置文件中的值
            app_secret: 应用Secret，如不提供则使用配置文件中的值
            proxy_url: 代理服务器URL，None表示使用配置文件中的值，空字符串""表示不使用代理
        """
        self.app_key = app_key or settings.TEMU_APP_KEY
        self.app_secret = app_secret or settings.TEMU_APP_SECRET
        self.base_url = settings.TEMU_API_BASE_URL
        # 如果proxy_url是None，使用配置中的值；如果是空字符串，不使用代理；否则使用传入的值
        if proxy_url is None:
            self.proxy_url = settings.TEMU_API_PROXY_URL
        elif proxy_url == "":
            self.proxy_url = None
        else:
            self.proxy_url = proxy_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.rate_limiter = get_rate_limiter()
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """
        生成API签名（MD5算法）
        
        签名规则（基于Temu官方文档）：
        1. 将所有参数（除sign外）按key字母顺序排序
        2. 拼接成 key1value1key2value2... 格式
        3. 在前后各加上 app_secret
        4. 对整个字符串进行MD5加密并转大写
        """
        temp = []
        # 按键排序参数
        sorted_params = sorted(params.items())
        
        # 拼接参数字符串
        for key, value in sorted_params:
            if value is not None:
                # 如果值是字典或列表，转换为JSON字符串
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
                # 去除字符串两端的引号
                temp.append(str(key) + str(value).strip('\"'))
        
        un_sign = ''.join(temp)
        # app_secret + 参数字符串 + app_secret
        un_sign = str(self.app_secret) + un_sign + str(self.app_secret)
        # MD5加密并转大写
        sign = hashlib.md5(un_sign.encode('utf-8')).hexdigest().upper()
        
        return sign
    
    async def _request_via_proxy(
        self,
        api_type: str,
        request_data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        通过代理服务器发送API请求（带重试机制）
        
        Args:
            api_type: API接口类型（如 bg.order.list.v2.get）
            request_data: 业务请求数据
            access_token: 访问令牌
            
        Returns:
            API响应数据
        
        注意：如果代理服务器已配置 TEMU_APP_KEY 和 TEMU_APP_SECRET 环境变量，
        可以不在请求中传入 app_key 和 app_secret（代理服务器会自动使用环境变量中的值）。
        当前实现会传入 app_key 和 app_secret，这样可以覆盖代理服务器的默认配置。
        """
        max_attempts = settings.API_RETRY_MAX_ATTEMPTS
        initial_delay = settings.API_RETRY_INITIAL_DELAY
        backoff_factor = settings.API_RETRY_BACKOFF_FACTOR
        
        proxy_request = {
            "api_type": api_type,
            "request_data": request_data,
            "access_token": access_token,
            # 传入 app_key 和 app_secret（如果代理服务器已配置环境变量，这些参数可选）
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            # 传入 base_url，让代理服务器知道要请求哪个API地址
            "api_base_url": self.base_url
        }
        
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                # 限流检查
                await self.rate_limiter.acquire(tokens=1, wait=True)
                
                headers = {"Content-Type": "application/json"}
                response = await self.client.post(
                    f"{self.proxy_url}/api/proxy",
                    headers=headers,
                    json=proxy_request
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 检查代理响应
                if not result.get("success", False):
                    error_code = result.get("error_code", "未知")
                    error_msg = result.get("error_msg", "未知错误")
                    
                    # 判断是否为可重试的错误
                    if self._is_retryable_error(error_code, error_msg):
                        if attempt < max_attempts:
                            delay = initial_delay * (backoff_factor ** (attempt - 1))
                            logger.warning(
                                f"代理服务器错误（可重试）: [{error_code}] {error_msg}, "
                                f"第 {attempt}/{max_attempts} 次尝试，{delay:.2f}秒后重试"
                            )
                            await asyncio.sleep(delay)
                            continue
                    
                    logger.error(f"代理服务器错误: [{error_code}] {error_msg}")
                    raise Exception(f"代理服务器错误: [{error_code}] {error_msg}")
                
                return result.get("result", {})
                
            except httpx.HTTPStatusError as e:
                # HTTP状态错误（如429限流、500服务器错误等）
                if self._is_retryable_http_error(e.response.status_code) and attempt < max_attempts:
                    delay = initial_delay * (backoff_factor ** (attempt - 1))
                    logger.warning(
                        f"HTTP错误（可重试）: {e.response.status_code}, "
                        f"第 {attempt}/{max_attempts} 次尝试，{delay:.2f}秒后重试"
                    )
                    await asyncio.sleep(delay)
                    last_exception = e
                    continue
                logger.error(f"HTTP状态错误: {e.response.status_code}")
                raise
                
            except httpx.RequestError as e:
                # 网络请求错误（连接超时、网络不可达等）
                if attempt < max_attempts:
                    delay = initial_delay * (backoff_factor ** (attempt - 1))
                    logger.warning(
                        f"网络请求错误（可重试）: {e}, "
                        f"第 {attempt}/{max_attempts} 次尝试，{delay:.2f}秒后重试"
                    )
                    await asyncio.sleep(delay)
                    last_exception = e
                    continue
                logger.error(f"网络请求错误: {e}")
                raise
                
            except Exception as e:
                # 其他错误，不重试
                logger.error(f"通过代理请求异常: {e}")
                raise
        
        # 所有重试都失败
        if last_exception:
            raise last_exception
        raise Exception("请求失败：达到最大重试次数")
    
    async def _request(
        self,
        api_type: str,
        request_data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送API请求（Temu统一路由格式，带重试机制）
        
        Args:
            api_type: API接口类型（如 bg.order.list.v2.get）
            request_data: 业务请求数据
            access_token: 访问令牌
            
        Returns:
            API响应数据
        """
        # 如果配置了代理 URL，通过代理发送请求（重试已在_request_via_proxy中处理）
        if self.proxy_url:
            return await self._request_via_proxy(api_type, request_data, access_token)
        
        max_attempts = settings.API_RETRY_MAX_ATTEMPTS
        initial_delay = settings.API_RETRY_INITIAL_DELAY
        backoff_factor = settings.API_RETRY_BACKOFF_FACTOR
        
        url = self.base_url
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                # 限流检查（直接请求时）
                await self.rate_limiter.acquire(tokens=1, wait=True)
                
                # 构建通用参数
                timestamp = int(time.time())
                common_params = {
                    "app_key": self.app_key,
                    "data_type": "JSON",
                    "timestamp": timestamp,
                    "type": api_type,
                    "version": "V1"
                }
                
                # 添加access_token（如果提供）
                if access_token:
                    common_params["access_token"] = access_token
                
                # 合并所有参数
                all_params = {**common_params}
                if request_data:
                    # 业务参数放在 request 字段中
                    all_params["request"] = request_data
                
                # 生成签名
                sign = self._generate_sign(all_params)
                
                # 最终请求体
                request_payload = {**all_params, "sign": sign}
                
                # 直接发送POST请求到 Temu API
                headers = {"Content-Type": "application/json"}
                response = await self.client.post(
                    url, 
                    headers=headers,
                    content=json.dumps(request_payload)
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 检查业务错误
                if not result.get("success", False):
                    error_code = result.get("errorCode", "未知")
                    error_msg = result.get("errorMsg", "未知错误")
                    
                    # 判断是否为可重试的错误
                    if self._is_retryable_error(str(error_code), error_msg) and attempt < max_attempts:
                        delay = initial_delay * (backoff_factor ** (attempt - 1))
                        logger.warning(
                            f"Temu API错误（可重试）: [{error_code}] {error_msg}, "
                            f"第 {attempt}/{max_attempts} 次尝试，{delay:.2f}秒后重试"
                        )
                        await asyncio.sleep(delay)
                        continue
                    
                    logger.error(f"Temu API error: [{error_code}] {error_msg}")
                    raise Exception(f"Temu API error: [{error_code}] {error_msg}")
                
                return result.get("result", {})
                
            except httpx.HTTPStatusError as e:
                # HTTP状态错误（如429限流、500服务器错误等）
                if self._is_retryable_http_error(e.response.status_code) and attempt < max_attempts:
                    delay = initial_delay * (backoff_factor ** (attempt - 1))
                    logger.warning(
                        f"HTTP错误（可重试）: {e.response.status_code}, "
                        f"第 {attempt}/{max_attempts} 次尝试，{delay:.2f}秒后重试"
                    )
                    await asyncio.sleep(delay)
                    last_exception = e
                    continue
                logger.error(f"HTTP状态错误: {e.response.status_code}")
                raise
                
            except httpx.RequestError as e:
                # 网络请求错误（连接超时、网络不可达等）
                if attempt < max_attempts:
                    delay = initial_delay * (backoff_factor ** (attempt - 1))
                    logger.warning(
                        f"网络请求错误（可重试）: {e}, "
                        f"第 {attempt}/{max_attempts} 次尝试，{delay:.2f}秒后重试"
                    )
                    await asyncio.sleep(delay)
                    last_exception = e
                    continue
                logger.error(f"网络请求错误: {e}")
                raise
                
            except Exception as e:
                # 其他错误，不重试
                logger.error(f"Error calling Temu API: {e}")
                raise
        
        # 所有重试都失败
        if last_exception:
            raise last_exception
        raise Exception("请求失败：达到最大重试次数")
    
    def _is_retryable_error(self, error_code: str, error_msg: str) -> bool:
        """
        判断错误是否可重试
        
        Args:
            error_code: 错误码
            error_msg: 错误消息
            
        Returns:
            是否可重试
        """
        # 系统繁忙、限流等错误可重试
        retryable_codes = ['1000000', '1000001', '429', '500', '502', '503', '504']
        retryable_keywords = ['busy', 'rate limit', 'timeout', 'temporary', 'retry']
        
        error_code_str = str(error_code).upper()
        error_msg_lower = str(error_msg).lower()
        
        # 检查错误码
        for code in retryable_codes:
            if code in error_code_str:
                return True
        
        # 检查错误消息关键词
        for keyword in retryable_keywords:
            if keyword in error_msg_lower:
                return True
        
        return False
    
    def _is_retryable_http_error(self, status_code: int) -> bool:
        """
        判断HTTP状态码是否可重试
        
        Args:
            status_code: HTTP状态码
            
        Returns:
            是否可重试
        """
        # 429 (Too Many Requests), 5xx 服务器错误可重试
        return status_code == 429 or (500 <= status_code < 600)
    
    async def get_orders(
        self,
        access_token: str,
        begin_time: int,
        end_time: int,
        page_number: int = 1,
        page_size: int = 100,
        order_status: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取订单列表（V2版本）
        
        Args:
            access_token: 访问令牌
            begin_time: 开始时间（Unix时间戳）
            end_time: 结束时间（Unix时间戳）
            page_number: 页码
            page_size: 每页数量
            order_status: 订单状态筛选
            
        Returns:
            订单列表数据
        """
        data = {
            "beginTime": begin_time,
            "endTime": end_time,
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        
        if order_status is not None:
            data["orderStatus"] = order_status
        
        return await self._request("bg.order.list.v2.get", data, access_token)
    
    async def get_order_detail(
        self,
        access_token: str,
        order_sn: str
    ) -> Dict[str, Any]:
        """
        获取订单详情（V2版本）
        
        Args:
            access_token: 访问令牌
            order_sn: 订单编号
            
        Returns:
            订单详情数据
        """
        data = {"orderSn": order_sn}
        return await self._request("bg.order.detail.v2.get", data, access_token)
    
    async def get_products(
        self,
        access_token: str,
        page_number: int = 1,
        page_size: int = 100,
        goods_status: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取商品列表
        
        Args:
            access_token: 访问令牌
            page_number: 页码
            page_size: 每页数量
            goods_status: 商品状态筛选
            
        Returns:
            商品列表数据
        """
        data = {
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        
        if goods_status is not None:
            data["goodsStatus"] = goods_status
        
        return await self._request("bg.local.goods.list.query", data, access_token)
    
    async def get_product_detail(
        self,
        access_token: str,
        goods_id: int
    ) -> Dict[str, Any]:
        """
        获取商品详情
        
        Args:
            access_token: 访问令牌
            goods_id: 商品ID
            
        Returns:
            商品详情数据
        """
        data = {"goodsId": goods_id}
        return await self._request("bg.local.goods.detail.query", data, access_token)
    
    async def get_product_categories(
        self,
        access_token: str,
        parent_cat_id: int = 0
    ) -> Dict[str, Any]:
        """
        获取商品分类
        
        Args:
            access_token: 访问令牌
            parent_cat_id: 父分类ID，0表示查询根分类
            
        Returns:
            商品分类数据
        """
        data = {"parentCatId": parent_cat_id}
        return await self._request("bg.local.goods.cats.get", data, access_token)
    
    async def get_warehouses(
        self,
        access_token: str
    ) -> Dict[str, Any]:
        """
        获取仓库列表
        
        Args:
            access_token: 访问令牌
            
        Returns:
            仓库列表数据
        """
        data = {}
        return await self._request("bg.logistics.warehouse.list.get", data, access_token)
    
    async def get_token_info(
        self,
        access_token: str
    ) -> Dict[str, Any]:
        """
        查询Token信息
        
        Args:
            access_token: 访问令牌
            
        Returns:
            Token信息
        """
        data = {}
        return await self._request("bg.open.accesstoken.info.get", data, access_token)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

