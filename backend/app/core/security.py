"""安全认证工具"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT 配置
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Returns:
        bool: 如果密码匹配返回 True，否则返回 False
        
    Raises:
        ValueError: 如果发生系统错误（如 bcrypt 库问题、编码错误等），
                    这些错误应该被记录为系统错误，而不是简单的认证失败
    """
    try:
        if not plain_password:
            return False
        if not hashed_password:
            # 为了安全，当哈希值为空时也返回 False，而不是抛出异常
            # 这样可以防止通过错误响应类型（500 vs 401）来区分不存在的账户和密码错误的账户
            return False
        
        password_bytes = plain_password.encode('utf-8')
        # hashed_password 已经是字符串格式的bcrypt哈希值
        # bcrypt.checkpw 需要 bytes 格式的哈希值
        hashed_bytes = hashed_password.encode('utf-8')
        
        # 检查哈希值格式（bcrypt 哈希值应该以 $2a$, $2b$ 或 $2y$ 开头）
        if not (hashed_password.startswith('$2a$') or 
                hashed_password.startswith('$2b$') or 
                hashed_password.startswith('$2y$')):
            from loguru import logger
            logger.error(f"无效的密码哈希格式: {hashed_password[:20]}...")
            raise ValueError(f"无效的密码哈希格式")
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError) as e:
        # 这些是系统错误（如无效的哈希格式、类型错误等），应该被记录
        from loguru import logger
        logger.error(f"密码验证系统错误: {e}, 哈希值类型: {type(hashed_password)}, 哈希值长度: {len(hashed_password) if hashed_password else 0}")
        raise ValueError(f"密码验证系统错误: {str(e)}") from e
    except Exception as e:
        # 其他未预期的错误（如 bcrypt 库问题），也应该被记录
        from loguru import logger
        logger.error(f"密码验证未预期的错误: {e}, 哈希值类型: {type(hashed_password)}")
        raise ValueError(f"密码验证系统错误: {str(e)}") from e


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    # bcrypt限制密码最长72字节，需要截断
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # 生成盐并哈希密码
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    # 更新最后登录时间
    try:
        user.last_login_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        # 如果更新最后登录时间失败，记录错误但不影响认证
        from loguru import logger
        logger.warning(f"更新最后登录时间失败: {e}")
        db.rollback()
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

