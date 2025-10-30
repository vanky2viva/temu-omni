"""Temu API客户端"""
import hashlib
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
    
    async def _request(
        self,
        api_type: str,
        request_data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送API请求（Temu统一路由格式）
        
        Args:
            api_type: API接口类型（如 bg.order.list.v2.get）
            request_data: 业务请求数据
            access_token: 访问令牌
            
        Returns:
            API响应数据
        """
        url = self.base_url
        
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
        
        try:
            # 发送POST请求
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
                logger.error(f"Temu API error: [{error_code}] {error_msg}")
                raise Exception(f"Temu API error: [{error_code}] {error_msg}")
            
            return result.get("result", {})
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Temu API: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling Temu API: {e}")
            raise
    
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

