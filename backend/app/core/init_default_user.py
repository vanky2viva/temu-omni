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
    """初始化默认管理员用户"""
    db: Session = SessionLocal()
    try:
        # 检查默认用户是否已存在
        existing_user = db.query(User).filter(User.username == "luffyadmin").first()
        
        if existing_user:
            logger.info("默认管理员用户已存在，跳过初始化")
            return
        
        # 创建默认管理员用户
        hashed_password = get_password_hash("luffy123!@#")
        default_user = User(
            username="luffyadmin",
            email="admin@luffy.com",
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
        )
        
        db.add(default_user)
        db.commit()
        logger.info("默认管理员用户创建成功: luffyadmin")
        
    except Exception as e:
        logger.error(f"初始化默认用户失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    """直接运行脚本"""
    init_default_user()

