"""Redis客户端工具类"""
import json
from typing import Optional, Any
import redis
from loguru import logger
from app.core.config import settings


class RedisClient:
    """Redis客户端单例"""
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        """获取Redis客户端实例（单例模式）"""
        if cls._instance is None:
            try:
                cls._instance = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # 测试连接
                cls._instance.ping()
                logger.info(f"Redis连接成功: {settings.REDIS_URL}")
            except Exception as e:
                logger.warning(f"Redis连接失败: {e}，将使用无缓存模式")
                # 如果Redis不可用，设置_instance为None，后续操作会优雅降级
                cls._instance = None
                # 不抛出异常，允许应用继续运行（无缓存模式）
                return None
        
        return cls._instance
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值（会自动序列化为JSON）
            ttl: 过期时间（秒），None表示不过期
            
        Returns:
            是否设置成功
        """
        try:
            client = cls.get_client()
            if client is None:
                return False  # Redis不可用，返回False但不抛出异常
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            if ttl:
                return client.setex(key, ttl, value)
            else:
                return client.set(key, value)
        except Exception as e:
            logger.warning(f"Redis设置缓存失败: {key}, 错误: {e}")
            return False
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或出错则返回None
        """
        try:
            client = cls.get_client()
            if client is None:
                return None  # Redis不可用，返回None但不抛出异常
            value = client.get(key)
            if value is None:
                return None
            # 尝试解析为JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.warning(f"Redis获取缓存失败: {key}, 错误: {e}")
            return None
    
    @classmethod
    def delete(cls, *keys: str) -> int:
        """
        删除缓存
        
        Args:
            *keys: 要删除的缓存键（可变参数）
            
        Returns:
            删除的键数量
        """
        try:
            client = cls.get_client()
            if client is None:
                return 0  # Redis不可用，返回0但不抛出异常
            return client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis删除缓存失败: {keys}, 错误: {e}")
            return 0
    
    @classmethod
    def delete_pattern(cls, pattern: str) -> int:
        """
        按模式删除缓存
        
        Args:
            pattern: 匹配模式（如 "stats:*"）
            
        Returns:
            删除的键数量
        """
        try:
            client = cls.get_client()
            if client is None:
                return 0  # Redis不可用，返回0但不抛出异常
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis按模式删除缓存失败: {pattern}, 错误: {e}")
            return 0
    
    @classmethod
    def exists(cls, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        try:
            client = cls.get_client()
            if client is None:
                return False  # Redis不可用，返回False但不抛出异常
            return client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Redis检查缓存存在性失败: {key}, 错误: {e}")
            return False
    
    @classmethod
    def clear_all(cls) -> bool:
        """
        清空所有缓存（谨慎使用）
        
        Returns:
            是否成功
        """
        try:
            client = cls.get_client()
            if client is None:
                return False  # Redis不可用，返回False但不抛出异常
            client.flushdb()
            logger.warning("Redis已清空所有缓存")
            return True
        except Exception as e:
            logger.error(f"Redis清空缓存失败: {e}")
            return False


# 导出便捷函数
def get_redis_client() -> redis.Redis:
    """获取Redis客户端"""
    return RedisClient.get_client()


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """设置缓存"""
    return RedisClient.set(key, value, ttl)


def get_cache(key: str) -> Optional[Any]:
    """获取缓存"""
    return RedisClient.get(key)


def delete_cache(*keys: str) -> int:
    """删除缓存"""
    return RedisClient.delete(*keys)


def delete_cache_pattern(pattern: str) -> int:
    """按模式删除缓存"""
    return RedisClient.delete_pattern(pattern)

