"""认证API"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from loguru import logger
import traceback

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class UserCreate(BaseModel):
    """用户创建模型"""
    username: str
    email: str  # 改为普通字符串，避免依赖email-validator
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """简单的邮箱验证"""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据模型"""
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """注册新用户"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenData)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        # 查找用户（支持用户名或邮箱登录）
        user = db.query(User).filter(
            (User.username == form_data.username) | (User.email == form_data.username)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        # 将 User 对象转换为 UserResponse
        user_response = UserResponse.model_validate(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 记录其他异常并返回 500 错误
        logger.error(f"登录失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

