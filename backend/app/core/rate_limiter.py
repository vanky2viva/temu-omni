"""API请求频次控制模块 - 令牌桶算法实现"""
import asyncio
import time
from typing import Optional, Dict
from collections import defaultdict
from loguru import logger
from app.core.config import settings


class TokenBucket:
    """令牌桶限流器"""
    
    def __init__(
        self,
        capacity: int = 60,
        refill_rate: float = 1.0,
        key: Optional[str] = None
    ):
        """
        初始化令牌桶
        
        Args:
            capacity: 令牌桶容量（默认60，即每分钟60次请求）
            refill_rate: 令牌补充速率（每秒补充的令牌数，默认1.0）
            key: 限流键（用于区分不同的限流实例，如店铺ID）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.key = key or "default"
        
        # 当前令牌数量
        self.tokens = float(capacity)
        
        # 上次更新时间
        self.last_refill = time.time()
        
        # 锁，用于线程安全
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1, wait: bool = True) -> bool:
        """
        获取令牌
        
        Args:
            tokens: 需要的令牌数量（默认1）
            wait: 如果令牌不足，是否等待（默认True）
            
        Returns:
            是否成功获取令牌
        """
        async with self._lock:
            # 先补充令牌
            self._refill()
            
            # 检查是否有足够的令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(
                    f"获取令牌成功 - Key: {self.key}, "
                    f"剩余令牌: {self.tokens:.2f}/{self.capacity}"
                )
                return True
            
            # 令牌不足
            if not wait:
                logger.warning(
                    f"令牌不足 - Key: {self.key}, "
                    f"需要: {tokens}, 可用: {self.tokens:.2f}"
                )
                return False
            
            # 计算需要等待的时间
            needed = tokens - self.tokens
            wait_time = needed / self.refill_rate
            
            logger.info(
                f"令牌不足，等待 {wait_time:.2f} 秒 - Key: {self.key}, "
                f"需要: {tokens}, 可用: {self.tokens:.2f}"
            )
            
            # 等待令牌补充
            await asyncio.sleep(wait_time)
            
            # 再次补充并获取令牌
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(
                    f"等待后获取令牌成功 - Key: {self.key}, "
                    f"剩余令牌: {self.tokens:.2f}/{self.capacity}"
                )
                return True
            
            # 理论上不应该到这里
            logger.error(f"等待后仍无法获取令牌 - Key: {self.key}")
            return False
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed > 0:
            # 计算应该补充的令牌数
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
    
    async def get_available_tokens(self) -> float:
        """获取当前可用令牌数"""
        async with self._lock:
            self._refill()
            return self.tokens


class RateLimiter:
    """API请求限流器管理器"""
    
    def __init__(
        self,
        capacity: int = 60,
        refill_rate: float = 1.0,
        enabled: bool = True
    ):
        """
        初始化限流器管理器
        
        Args:
            capacity: 令牌桶容量（默认60）
            refill_rate: 令牌补充速率（默认1.0，即每秒1个令牌）
            enabled: 是否启用限流（默认True）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.enabled = enabled
        
        # 存储不同key的令牌桶
        self._buckets: Dict[str, TokenBucket] = {}
        
        # 全局默认令牌桶
        self._default_bucket: Optional[TokenBucket] = None
    
    def get_bucket(self, key: Optional[str] = None) -> TokenBucket:
        """
        获取指定key的令牌桶，如果不存在则创建
        
        Args:
            key: 限流键（如店铺ID），None表示使用全局限流
            
        Returns:
            令牌桶实例
        """
        if not self.enabled:
            # 如果限流未启用，返回一个不限制的令牌桶
            return TokenBucket(capacity=999999, refill_rate=999999, key=key or "unlimited")
        
        if key is None:
            if self._default_bucket is None:
                self._default_bucket = TokenBucket(
                    capacity=self.capacity,
                    refill_rate=self.refill_rate,
                    key="global"
                )
            return self._default_bucket
        
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                capacity=self.capacity,
                refill_rate=self.refill_rate,
                key=key
            )
        
        return self._buckets[key]
    
    async def acquire(
        self,
        tokens: int = 1,
        key: Optional[str] = None,
        wait: bool = True
    ) -> bool:
        """
        获取令牌
        
        Args:
            tokens: 需要的令牌数量（默认1）
            key: 限流键（如店铺ID），None表示使用全局限流
            wait: 如果令牌不足，是否等待（默认True）
            
        Returns:
            是否成功获取令牌
        """
        bucket = self.get_bucket(key)
        return await bucket.acquire(tokens=tokens, wait=wait)
    
    def reset(self, key: Optional[str] = None):
        """
        重置指定key的令牌桶
        
        Args:
            key: 限流键，None表示重置全局限流
        """
        if key is None:
            if self._default_bucket:
                self._default_bucket.tokens = float(self._default_bucket.capacity)
                self._default_bucket.last_refill = time.time()
        else:
            if key in self._buckets:
                bucket = self._buckets[key]
                bucket.tokens = float(bucket.capacity)
                bucket.last_refill = time.time()


# 全局限流器实例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器实例"""
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            capacity=getattr(settings, 'API_RATE_LIMIT_PER_MINUTE', 60),
            refill_rate=getattr(settings, 'API_RATE_LIMIT_PER_MINUTE', 60) / 60.0,
            enabled=getattr(settings, 'API_RATE_LIMIT_ENABLED', True)
        )
    
    return _rate_limiter

