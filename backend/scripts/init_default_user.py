#!/usr/bin/env python3
"""初始化默认用户脚本 - 可在 backend 目录下运行"""
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 先导入所有模型以确保关系映射正确初始化
from app.models import *  # noqa: F401, F403
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
            print("✓ 默认管理员用户已存在: luffyadmin")
            return
        
        # 创建默认管理员用户
        password = "luffy123!@#"
        hashed_password = get_password_hash(password)
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
        print("✓ 默认管理员用户创建成功!")
        print("  用户名: luffyadmin")
        print("  密码: luffy123!@#")
        
    except Exception as e:
        logger.error(f"初始化默认用户失败: {str(e)}")
        db.rollback()
        print(f"✗ 初始化默认用户失败: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    """直接运行脚本"""
    print("正在初始化默认管理员用户...")
    init_default_user()

