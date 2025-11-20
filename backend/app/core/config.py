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
    
    # Temu API配置（从环境变量读取）
    TEMU_APP_KEY: str = ""  # 标准端点App Key，必须通过环境变量设置
    TEMU_APP_SECRET: str = ""  # 标准端点App Secret，必须通过环境变量设置
    TEMU_API_BASE_URL: str = "https://agentpartner.temu.com/api"
    
    # Temu CN API配置（从环境变量读取）
    TEMU_CN_APP_KEY: str = ""  # CN端点App Key，必须通过环境变量设置
    TEMU_CN_APP_SECRET: str = ""  # CN端点App Secret，必须通过环境变量设置
    
    # Temu API 代理配置（必须）
    TEMU_API_PROXY_URL: str = ""  # 代理服务器地址，必须通过环境变量设置
    
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

