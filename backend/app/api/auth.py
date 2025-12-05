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
        logger.info(f"登录请求: username={form_data.username}")
        
        # 检查输入参数
        if not form_data.username:
            logger.warning("用户名为空")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名不能为空"
            )
        if not form_data.password:
            logger.warning("密码为空")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码不能为空"
            )
        
        # 检查数据库连接
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            logger.debug("数据库连接检查通过")
        except Exception as db_error:
            logger.error(f"数据库连接失败: {db_error}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"数据库连接失败: {str(db_error)}"
            )
        
        # 查找用户（支持用户名或邮箱登录）
        try:
            logger.debug(f"开始查询用户: {form_data.username}")
            user = db.query(User).filter(
                (User.username == form_data.username) | (User.email == form_data.username)
            ).first()
            logger.debug(f"用户查询结果: {'找到用户' if user else '未找到用户'}")
        except Exception as query_error:
            logger.error(f"查询用户失败: {query_error}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询用户失败: {str(query_error)}"
            )
        
        if not user:
            logger.warning(f"用户不存在: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"找到用户: id={user.id}, username={user.username}, is_active={user.is_active}")
        
        # 验证密码
        try:
            if not verify_password(form_data.password, user.hashed_password):
                logger.warning(f"密码错误: username={form_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError as ve:
            # 捕获密码验证的系统错误（如 bcrypt 库问题、编码错误等）
            # 这些错误应该被记录为系统错误，而不是认证失败
            logger.error(f"密码验证系统错误: {ve}, username={form_data.username}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码验证系统错误，请稍后重试或联系管理员"
            )
        
        if not user.is_active:
            logger.warning(f"用户未激活: username={form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )
        
        # 创建访问令牌
        try:
            logger.debug("开始创建访问令牌")
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.username},
                expires_delta=access_token_expires
            )
            logger.debug("访问令牌创建成功")
        except Exception as token_error:
            logger.error(f"创建令牌失败: {token_error}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建访问令牌失败: {str(token_error)}"
            )
        
        # 将 User 对象转换为 UserResponse
        try:
            logger.debug("开始转换用户数据")
            logger.debug(f"用户对象字段: id={user.id}, username={user.username}, email={getattr(user, 'email', None)}, is_active={getattr(user, 'is_active', None)}, is_superuser={getattr(user, 'is_superuser', None)}")
            # 直接手动构建响应，避免 Pydantic 验证问题
            user_response = UserResponse(
                id=user.id,
                username=user.username,
                email=user.email if user.email else "",
                is_active=user.is_active if user.is_active is not None else True,
                is_superuser=user.is_superuser if user.is_superuser is not None else False,
            )
            logger.debug(f"用户数据转换成功: {user_response}")
        except Exception as validate_error:
            logger.error(f"用户数据验证失败: {validate_error}")
            logger.error(f"用户对象信息: id={user.id}, username={user.username}, email={getattr(user, 'email', 'N/A')}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"用户数据验证失败: {str(validate_error)}"
            )
        
        logger.info(f"登录成功: username={form_data.username}, user_id={user.id}")
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
        logger.error(f"登录失败（未知错误）: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

