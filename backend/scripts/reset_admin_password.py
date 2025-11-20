"""重置管理员密码脚本"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = backend_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        root_env = backend_dir.parent / '.env'
        if root_env.exists():
            load_dotenv(root_env)
except ImportError:
    pass

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from loguru import logger


def reset_admin_password(new_password: str = "luffy123!@#"):
    """重置管理员密码"""
    db: Session = SessionLocal()
    
    try:
        # 查找管理员用户
        admin_user = db.query(User).filter(User.username == "luffyadmin").first()
        
        if not admin_user:
            # 如果用户不存在，创建新用户
            logger.info("管理员用户不存在，正在创建...")
            hashed_password = get_password_hash(new_password)
            admin_user = User(
                username="luffyadmin",
                email="admin@luffy.com",
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin_user)
            logger.info("✅ 管理员用户创建成功")
        else:
            # 重置密码
            logger.info("找到管理员用户，正在重置密码...")
            admin_user.hashed_password = get_password_hash(new_password)
            admin_user.is_active = True
            admin_user.is_superuser = True
            logger.info("✅ 管理员密码已重置")
        
        db.commit()
        
        logger.info(f"✅ 管理员账户信息：")
        logger.info(f"   用户名: luffyadmin")
        logger.info(f"   密码: {new_password}")
        logger.info(f"   邮箱: admin@luffy.com")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 重置密码失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="重置管理员密码")
    parser.add_argument(
        "--password",
        type=str,
        default="luffy123!@#",
        help="新密码（默认: luffy123!@#）"
    )
    
    args = parser.parse_args()
    
    reset_admin_password(args.password)

