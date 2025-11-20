"""应用配置"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "Temu-Omni"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    
    # 数据库配置
    DATABASE_URL: str
    
    # Temu API配置（内置）
    TEMU_APP_KEY: str = "798478197604e93f6f2ce4c2e833041u"
    TEMU_APP_SECRET: str = "776a96163c56c53e237f5456d4e14765301aa8aa"
    TEMU_API_BASE_URL: str = "https://agentpartner.temu.com/api"
    
    # Temu API 代理配置（必须）
    TEMU_API_PROXY_URL: str = "http://172.236.231.45:8001"  # 代理服务器地址，所有 API 请求必须通过此代理服务器
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # 数据同步配置
    AUTO_SYNC_ENABLED: bool = True
    SYNC_INTERVAL_MINUTES: int = 30
    
    # API限流配置
    API_RATE_LIMIT_ENABLED: bool = True
    API_RATE_LIMIT_PER_MINUTE: int = 60  # 每分钟最大请求数
    
    # API重试配置
    API_RETRY_MAX_ATTEMPTS: int = 3  # 最大重试次数
    API_RETRY_BACKOFF_FACTOR: float = 2.0  # 重试退避因子（指数退避）
    API_RETRY_INITIAL_DELAY: float = 1.0  # 初始重试延迟（秒）
    
    # 时区配置
    TIMEZONE: str = "Asia/Shanghai"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

