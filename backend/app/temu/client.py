"""Temu API客户端"""
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional, List
import httpx
from loguru import logger
from app.core.config import settings


class TemuAPIClient:
    """Temu API客户端"""
    
    def __init__(self, app_key: str = None, app_secret: str = None):
        """
        初始化Temu API客户端
        
        Args:
            app_key: 应用Key，如不提供则使用配置文件中的值
            app_secret: 应用Secret，如不提供则使用配置文件中的值
        """
        self.app_key = app_key or settings.TEMU_APP_KEY
        self.app_secret = app_secret or settings.TEMU_APP_SECRET
        self.base_url = settings.TEMU_API_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """
        生成API签名
        
        根据Temu API文档的签名规则生成签名
        """
        # 按键排序参数
        sorted_params = sorted(params.items())
        
        # 拼接参数字符串
        param_str = ""
        for key, value in sorted_params:
            if value is not None:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, separators=(',', ':'))
                param_str += f"{key}{value}"
        
        # 加上app_secret进行HMAC-SHA256签名
        sign_str = self.app_secret + param_str + self.app_secret
        sign = hmac.new(
            self.app_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        
        return sign
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            method: 请求方法
            endpoint: API端点
            data: 请求数据
            access_token: 访问令牌
            
        Returns:
            API响应数据
        """
        url = f"{self.base_url}/{endpoint}"
        
        # 构建请求参数
        params = {
            "app_key": self.app_key,
            "timestamp": int(time.time()),
        }
        
        if access_token:
            params["access_token"] = access_token
        
        if data:
            params.update(data)
        
        # 生成签名
        params["sign"] = self._generate_sign(params)
        
        try:
            # 发送请求
            if method.upper() == "GET":
                response = await self.client.get(url, params=params)
            else:
                response = await self.client.post(url, json=params)
            
            response.raise_for_status()
            result = response.json()
            
            # 检查业务错误
            if result.get("error_code") != 0:
                error_msg = result.get("error_msg", "Unknown error")
                logger.error(f"Temu API error: {error_msg}")
                raise Exception(f"Temu API error: {error_msg}")
            
            return result.get("data", {})
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Temu API: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling Temu API: {e}")
            raise
    
    async def get_orders(
        self,
        access_token: str,
        start_time: int,
        end_time: int,
        page: int = 1,
        page_size: int = 100,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取订单列表
        
        Args:
            access_token: 访问令牌
            start_time: 开始时间（Unix时间戳）
            end_time: 结束时间（Unix时间戳）
            page: 页码
            page_size: 每页数量
            status: 订单状态筛选
            
        Returns:
            订单列表数据
        """
        data = {
            "start_time": start_time,
            "end_time": end_time,
            "page": page,
            "page_size": page_size,
        }
        
        if status:
            data["status"] = status
        
        return await self._request("POST", "order/list", data, access_token)
    
    async def get_order_detail(
        self,
        access_token: str,
        order_sn: str
    ) -> Dict[str, Any]:
        """
        获取订单详情
        
        Args:
            access_token: 访问令牌
            order_sn: 订单编号
            
        Returns:
            订单详情数据
        """
        data = {"order_sn": order_sn}
        return await self._request("POST", "order/detail", data, access_token)
    
    async def get_products(
        self,
        access_token: str,
        page: int = 1,
        page_size: int = 100,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取商品列表
        
        Args:
            access_token: 访问令牌
            page: 页码
            page_size: 每页数量
            status: 商品状态筛选
            
        Returns:
            商品列表数据
        """
        data = {
            "page": page,
            "page_size": page_size,
        }
        
        if status:
            data["status"] = status
        
        return await self._request("POST", "product/list", data, access_token)
    
    async def get_product_detail(
        self,
        access_token: str,
        product_id: str
    ) -> Dict[str, Any]:
        """
        获取商品详情
        
        Args:
            access_token: 访问令牌
            product_id: 商品ID
            
        Returns:
            商品详情数据
        """
        data = {"product_id": product_id}
        return await self._request("POST", "product/detail", data, access_token)
    
    async def get_activities(
        self,
        access_token: str,
        start_time: int,
        end_time: int,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        获取活动列表
        
        Args:
            access_token: 访问令牌
            start_time: 开始时间（Unix时间戳）
            end_time: 结束时间（Unix时间戳）
            page: 页码
            page_size: 每页数量
            
        Returns:
            活动列表数据
        """
        data = {
            "start_time": start_time,
            "end_time": end_time,
            "page": page,
            "page_size": page_size,
        }
        
        return await self._request("POST", "activity/list", data, access_token)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

