"""货币转换工具"""
from decimal import Decimal
from typing import Optional
from datetime import datetime, timedelta
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """货币转换器"""
    
    # 默认汇率（当API不可用时使用）
    DEFAULT_USD_TO_CNY_RATE = Decimal('7.1')
    
    # 汇率缓存
    _rate_cache: Optional[Decimal] = None
    _cache_time: Optional[datetime] = None
    _cache_duration = timedelta(hours=1)  # 缓存1小时
    
    @classmethod
    def _get_exchange_rate_from_api(cls) -> Optional[Decimal]:
        """
        从极速API获取USD到CNY的实时汇率
        
        Returns:
            汇率值，如果获取失败返回None
        """
        try:
            # 从配置获取API密钥
            api_key = getattr(settings, 'JISUAPI_KEY', None)
            if not api_key:
                logger.warning("极速API密钥未配置，使用默认汇率")
                return None
            
            # 调用极速API获取汇率
            url = "https://api.jisuapi.com/exchange/convert"
            params = {
                "appkey": api_key,
                "from": "USD",
                "to": "CNY",
                "amount": 1
            }
            
            # 使用httpx发送请求（超时5秒）
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # 检查API返回状态
                if data.get("status") == 0 and "result" in data:
                    rate_str = data["result"].get("rate")
                    if rate_str:
                        rate = Decimal(str(rate_str))
                        logger.info(f"成功获取实时汇率: USD/CNY = {rate}")
                        return rate
                    else:
                        logger.warning("API返回数据中未找到汇率信息")
                else:
                    msg = data.get("msg", "未知错误")
                    logger.warning(f"极速API返回错误: {msg}")
                    
        except httpx.TimeoutException:
            logger.warning("获取汇率API超时，使用缓存或默认汇率")
        except httpx.RequestError as e:
            logger.warning(f"获取汇率API请求失败: {e}")
        except Exception as e:
            logger.error(f"获取汇率时发生异常: {e}", exc_info=True)
        
        return None
    
    @classmethod
    def get_usd_to_cny_rate(cls, force_refresh: bool = False) -> Decimal:
        """
        获取USD到CNY的汇率（带缓存）
        
        Args:
            force_refresh: 是否强制刷新（忽略缓存）
            
        Returns:
            汇率值
        """
        now = datetime.now()
        
        # 检查缓存是否有效
        if not force_refresh and cls._rate_cache and cls._cache_time:
            if now - cls._cache_time < cls._cache_duration:
                return cls._rate_cache
        
        # 尝试从API获取实时汇率
        rate = cls._get_exchange_rate_from_api()
        
        if rate:
            # 更新缓存
            cls._rate_cache = rate
            cls._cache_time = now
            return rate
        elif cls._rate_cache:
            # API失败但缓存存在，使用缓存
            logger.info("使用缓存的汇率")
            return cls._rate_cache
        else:
            # 使用默认汇率
            logger.warning("使用默认汇率")
            return cls.DEFAULT_USD_TO_CNY_RATE
    
    @classmethod
    def convert_to_cny(
        cls,
        amount: Decimal,
        from_currency: str,
        rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        将金额转换为CNY
        
        Args:
            amount: 原始金额
            from_currency: 原始货币代码（如 'USD', 'CNY', 'EUR' 等）
            rate: 自定义汇率（可选，如果不提供则使用默认汇率）
            
        Returns:
            转换后的CNY金额
        """
        if not amount or amount == 0:
            return Decimal('0')
        
        # 如果已经是CNY，直接返回
        if from_currency.upper() == 'CNY':
            return amount
        
        # 使用自定义汇率或从API获取的实时汇率
        if rate:
            exchange_rate = rate
        else:
            exchange_rate = cls.get_usd_to_cny_rate()
        
        # 目前只支持USD到CNY的转换
        # 如果需要支持其他货币，可以扩展这个逻辑
        if from_currency.upper() == 'USD':
            return amount * exchange_rate
        elif from_currency.upper() == 'CNY':
            return amount
        else:
            # 对于其他货币，暂时按USD处理（可以根据需要扩展）
            # 或者抛出异常提示不支持
            return amount * exchange_rate
    
    @classmethod
    def convert_from_cny(
        cls,
        amount: Decimal,
        to_currency: str,
        rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        将CNY金额转换为其他货币
        
        Args:
            amount: CNY金额
            to_currency: 目标货币代码
            rate: 自定义汇率（可选）
            
        Returns:
            转换后的金额
        """
        if not amount or amount == 0:
            return Decimal('0')
        
        if to_currency.upper() == 'CNY':
            return amount
        
        if rate:
            exchange_rate = rate
        else:
            exchange_rate = cls.get_usd_to_cny_rate()
        
        if to_currency.upper() == 'USD':
            return amount / exchange_rate
        else:
            # 其他货币暂时按USD处理
            return amount / exchange_rate


# 为了兼容旧代码，添加类属性访问方式
# 使用描述符来实现动态获取
class _RateDescriptor:
    """汇率描述符，用于动态获取汇率值"""
    def __get__(self, obj, objtype=None):
        return CurrencyConverter.get_usd_to_cny_rate()

# 添加类属性，使其可以通过 CurrencyConverter.USD_TO_CNY_RATE 访问
CurrencyConverter.USD_TO_CNY_RATE = _RateDescriptor()

