"""应用配置"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, Field, model_validator
import secrets


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "Temu-Omni"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    # SECRET_KEY: 生产环境必须通过环境变量设置，开发环境允许使用随机生成的值
    SECRET_KEY: Optional[str] = Field(default=None, description="JWT密钥，生产环境必须设置")
    
    # 数据库配置
    # DATABASE_URL: 生产环境必须通过环境变量设置，开发环境允许使用SQLite默认值
    DATABASE_URL: Optional[str] = Field(default=None, description="数据库连接URL，生产环境必须设置")
    
    # Temu API配置（从环境变量读取）
    TEMU_APP_KEY: str = ""  # 标准端点App Key，必须通过环境变量设置
    TEMU_APP_SECRET: str = ""  # 标准端点App Secret，必须通过环境变量设置
    TEMU_API_BASE_URL: str = "https://agentpartner.temu.com/api"
    
    # Temu CN API配置（从环境变量读取）
    TEMU_CN_APP_KEY: str = ""  # CN端点App Key，必须通过环境变量设置
    TEMU_CN_APP_SECRET: str = ""  # CN端点App Secret，必须通过环境变量设置
    
    # Temu API 代理配置（必须）
    TEMU_API_PROXY_URL: Optional[str] = ""  # 代理服务器地址，必须通过环境变量设置
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @model_validator(mode='after')
    def validate_critical_settings(self):
        """验证关键配置项"""
        # SECRET_KEY 和 DATABASE_URL 必须设置，无论是否为 DEBUG 模式
        # 这样可以防止生产环境意外使用默认值
        if not self.SECRET_KEY:
            if self.DEBUG:
                # DEBUG 模式下，生成一个随机密钥（每次启动都不同）
                # 但发出警告，提醒开发者应该设置环境变量
                import warnings
                warnings.warn(
                    "SECRET_KEY 未设置，在 DEBUG 模式下使用随机生成的密钥。"
                    "生产环境必须通过环境变量设置 SECRET_KEY。",
                    UserWarning
                )
                self.SECRET_KEY = secrets.token_urlsafe(32)
            else:
                raise ValueError(
                    "SECRET_KEY环境变量未设置。生产环境必须设置SECRET_KEY环境变量。"
                    "请通过环境变量或.env文件设置SECRET_KEY。"
                )
        
        if not self.DATABASE_URL:
            if self.DEBUG:
                # DEBUG 模式下，使用 SQLite 默认值
                # 但发出警告，提醒开发者应该设置环境变量
                import warnings
                warnings.warn(
                    "DATABASE_URL 未设置，在 DEBUG 模式下使用 SQLite 默认数据库。"
                    "生产环境必须通过环境变量设置 DATABASE_URL。",
                    UserWarning
                )
                self.DATABASE_URL = "sqlite:///./temu_omni.db"
            else:
                raise ValueError(
                    "DATABASE_URL环境变量未设置。生产环境必须设置DATABASE_URL环境变量。"
                    "请通过环境变量或.env文件设置DATABASE_URL。"
                )
        return self
    
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
    
    # HTTP客户端配置
    HTTP_TIMEOUT: float = 30.0  # HTTP请求超时时间（秒）
    HTTP_CONNECT_TIMEOUT: float = 10.0  # HTTP连接超时时间（秒）
    HTTP_READ_TIMEOUT: float = 30.0  # HTTP读取超时时间（秒）
    HTTP_MAX_CONNECTIONS: int = 100  # 最大连接数
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20  # 最大保持活跃连接数
    
    # 数据库配置
    DB_POOL_SIZE: int = 10  # 数据库连接池大小
    DB_MAX_OVERFLOW: int = 20  # 数据库连接池最大溢出数
    DB_POOL_TIMEOUT: int = 30  # 获取数据库连接超时时间（秒）
    DB_POOL_RECYCLE: int = 3600  # 数据库连接回收时间（秒）
    DB_QUERY_TIMEOUT: int = 30  # 数据库查询超时时间（秒）
    
    # 同步任务配置
    SYNC_TASK_TIMEOUT: int = 3600  # 同步任务超时时间（秒，1小时）
    SYNC_BATCH_SIZE: int = 100  # 同步批次大小
    SYNC_MAX_RETRIES: int = 3  # 同步任务最大重试次数
    
    # 时区配置
    TIMEZONE: str = "Asia/Shanghai"
    
    # 回款配置
    SETTLEMENT_DAYS_AFTER_DELIVERY: int = 7  # 签收后N天回款
    
    # AI服务配置（已移除环境变量支持，改为从数据库配置页面读取）
    # 以下仅作为代码中的默认值，实际配置应从数据库 system_configs 表读取
    
    # OpenRouter API配置（FrogGPT）
    OPENROUTER_API_KEY: Optional[str] = Field(default=None, description="OpenRouter API密钥")
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"  # 默认模型
    OPENROUTER_TIMEOUT: float = 60.0  # 请求超时时间（秒）
    OPENROUTER_HTTP_REFERER: Optional[str] = Field(default=None, description="HTTP Referer（用于免费使用）")
    OPENROUTER_X_TITLE: str = "Temu Omni"  # X-Title头
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

