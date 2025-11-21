"""初始化默认用户"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from loguru import logger
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User


def init_default_user():
    """初始化默认管理员用户（从环境变量读取配置）"""
    db: Session = SessionLocal()
    try:
        # 从环境变量读取配置
        admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
        
        # 检查默认用户是否已存在
        existing_user = db.query(User).filter(User.username == admin_username).first()
        
        if existing_user:
            logger.info(f"默认管理员用户已存在: {admin_username}，跳过初始化")
            return
        
        # 创建默认管理员用户
        hashed_password = get_password_hash(admin_password)
        default_user = User(
            username=admin_username,
            email=admin_email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
        )
        
        db.add(default_user)
        db.commit()
        logger.info(f"默认管理员用户创建成功: {admin_username}")
        
    except Exception as e:
        logger.error(f"初始化默认用户失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    """直接运行脚本"""
    init_default_user()

