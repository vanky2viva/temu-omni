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


def get_app_credentials(db: Session) -> Dict[str, str]:
    """获取应用凭证（内部使用）"""
    app_key = db.query(SystemConfig).filter(SystemConfig.key == "temu_app_key").first()
    app_secret = db.query(SystemConfig).filter(SystemConfig.key == "temu_app_secret").first()
    
    if not app_key or not app_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先配置应用的App Key和App Secret"
        )
    
    return {
        "app_key": app_key.value,
        "app_secret": app_secret.value
    }

