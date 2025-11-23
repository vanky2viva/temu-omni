"""系统配置API"""
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.system_config import SystemConfig
from app.models.user import User

router = APIRouter(prefix="/system", tags=["system"])


class AppConfigUpdate(BaseModel):
    """应用配置更新模型"""
    app_key: str
    app_secret: str


class AppConfigResponse(BaseModel):
    """应用配置响应模型"""
    app_key: str
    has_app_secret: bool  # 不返回真实的secret


@router.get("/app-config/", response_model=AppConfigResponse)
def get_app_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取应用配置"""
    app_key = db.query(SystemConfig).filter(SystemConfig.key == "temu_app_key").first()
    app_secret = db.query(SystemConfig).filter(SystemConfig.key == "temu_app_secret").first()
    
    return {
        "app_key": app_key.value if app_key else "",
        "has_app_secret": bool(app_secret and app_secret.value)
    }


@router.put("/app-config/")
def update_app_config(config: AppConfigUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新应用配置"""
    # 更新或创建 app_key
    app_key_config = db.query(SystemConfig).filter(SystemConfig.key == "temu_app_key").first()
    if app_key_config:
        app_key_config.value = config.app_key
    else:
        app_key_config = SystemConfig(
            key="temu_app_key",
            value=config.app_key,
            description="Temu应用Key"
        )
        db.add(app_key_config)
    
    # 更新或创建 app_secret
    app_secret_config = db.query(SystemConfig).filter(SystemConfig.key == "temu_app_secret").first()
    if app_secret_config:
        app_secret_config.value = config.app_secret
    else:
        app_secret_config = SystemConfig(
            key="temu_app_secret",
            value=config.app_secret,
            description="Temu应用Secret",
            is_encrypted=True
        )
        db.add(app_secret_config)
    
    db.commit()
    
    return {"message": "应用配置更新成功"}


def get_app_credentials(db: Session = None) -> Dict[str, str]:
    """获取应用凭证（内部使用，现在使用内置配置）"""
    from app.core.config import settings
    return {
        "app_key": settings.TEMU_APP_KEY,
        "app_secret": settings.TEMU_APP_SECRET
    }


@router.get("/scheduler/status")
def get_scheduler_status(current_user: User = Depends(get_current_user)):
    """获取定时任务调度器状态"""
    try:
        from app.core.scheduler import scheduler
        
        if scheduler is None:
            return {
                "running": False,
                "initialized": False,
                "jobs": [],
                "message": "调度器未初始化"
            }
        
        jobs = []
        for job in scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "running": scheduler.running,
            "initialized": True,
            "jobs": jobs,
            "message": "调度器运行中" if scheduler.running else "调度器未运行"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取调度器状态失败: {str(e)}"
        )


class AIConfigUpdate(BaseModel):
    """AI配置更新模型"""
    provider: str  # deepseek/openai
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    timeout_seconds: int = 30
    cache_enabled: bool = True
    cache_ttl_days: int = 30
    daily_limit: int = 1000


class AIConfigResponse(BaseModel):
    """AI配置响应模型"""
    provider: str
    deepseek_api_key: str = ""
    has_deepseek_api_key: bool = False
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    has_openai_api_key: bool = False
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    timeout_seconds: int = 30
    cache_enabled: bool = True
    cache_ttl_days: int = 30
    daily_limit: int = 1000


@router.get("/ai-config/", response_model=AIConfigResponse)
def get_ai_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取AI配置（从数据库读取，不再使用环境变量）"""
    
    # 从数据库读取配置，如果不存在则使用默认值
    def get_config_value(key: str, default: str = "") -> str:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        return config.value if config and config.value else default
    
    def get_config_bool(key: str, default: bool = False) -> bool:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config and config.value:
            return config.value.lower() in ('true', '1', 'yes')
        return default
    
    def get_config_int(key: str, default: int = 0) -> int:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config and config.value:
            try:
                return int(config.value)
            except:
                return default
        return default
    
    provider = get_config_value("ai_provider", "deepseek")
    deepseek_api_key = get_config_value("deepseek_api_key", "")
    openai_api_key = get_config_value("openai_api_key", "")
    
    return {
        "provider": provider,
        "deepseek_api_key": deepseek_api_key,
        "has_deepseek_api_key": bool(deepseek_api_key),
        "deepseek_base_url": get_config_value("deepseek_base_url", "https://api.deepseek.com"),
        "deepseek_model": get_config_value("deepseek_model", "deepseek-chat"),
        "openai_api_key": openai_api_key,
        "has_openai_api_key": bool(openai_api_key),
        "openai_base_url": get_config_value("openai_base_url", "https://api.openai.com/v1"),
        "openai_model": get_config_value("openai_model", "gpt-4o"),
        "timeout_seconds": get_config_int("ai_timeout_seconds", 30),
        "cache_enabled": get_config_bool("ai_cache_enabled", True),
        "cache_ttl_days": get_config_int("ai_cache_ttl_days", 30),
        "daily_limit": get_config_int("ai_daily_limit", 1000),
    }


@router.put("/ai-config/")
def update_ai_config(config: AIConfigUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新AI配置"""
    def update_or_create_config(key: str, value: str, description: str, is_encrypted: bool = False, preserve_if_empty: bool = False):
        """
        更新或创建配置项
        
        Args:
            key: 配置键
            value: 配置值
            description: 配置描述
            is_encrypted: 是否加密
            preserve_if_empty: 如果值为空字符串，是否保留原值（用于 API Key 等敏感信息）
        """
        config_item = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config_item:
            # 如果 preserve_if_empty 为 True 且新值为空，则保留原值
            if preserve_if_empty and not value:
                return  # 不更新，保留原值
            config_item.value = value
        else:
            # 如果 preserve_if_empty 为 True 且值为空，则不创建新配置
            if preserve_if_empty and not value:
                return
            config_item = SystemConfig(
                key=key,
                value=value,
                description=description,
                is_encrypted=is_encrypted
            )
            db.add(config_item)
    
    # 更新配置
    update_or_create_config("ai_provider", config.provider, "AI服务提供商")
    # API Key 如果为空字符串，则保留原值（不更新）
    update_or_create_config("deepseek_api_key", config.deepseek_api_key, "DeepSeek API密钥", is_encrypted=True, preserve_if_empty=True)
    update_or_create_config("deepseek_base_url", config.deepseek_base_url, "DeepSeek API地址")
    update_or_create_config("deepseek_model", config.deepseek_model, "DeepSeek模型名称")
    update_or_create_config("openai_api_key", config.openai_api_key, "OpenAI API密钥", is_encrypted=True, preserve_if_empty=True)
    update_or_create_config("openai_base_url", config.openai_base_url, "OpenAI API地址")
    update_or_create_config("openai_model", config.openai_model, "OpenAI模型名称")
    update_or_create_config("ai_timeout_seconds", str(config.timeout_seconds), "AI API调用超时时间（秒）")
    update_or_create_config("ai_cache_enabled", str(config.cache_enabled).lower(), "是否启用AI结果缓存")
    update_or_create_config("ai_cache_ttl_days", str(config.cache_ttl_days), "AI缓存过期天数")
    update_or_create_config("ai_daily_limit", str(config.daily_limit), "每日AI调用次数限制")
    
    db.commit()
    
    return {"message": "AI配置更新成功"}

