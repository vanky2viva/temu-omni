#!/usr/bin/env python3
"""重置admin用户密码"""
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from loguru import logger
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User

def reset_admin_password(new_password: str = "admin123"):
    """重置admin用户密码"""
    db: Session = SessionLocal()
    try:
        # 查找admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            logger.error("未找到admin用户")
            return False
        
        # 重置密码
        hashed_password = get_password_hash(new_password)
        admin_user.hashed_password = hashed_password
        admin_user.is_active = True
        
        db.commit()
        logger.info(f"admin用户密码已重置为: {new_password}")
        return True
        
    except Exception as e:
        logger.error(f"重置密码失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔐 重置admin用户密码\n")
    
    # 默认密码为 admin123
    password = sys.argv[1] if len(sys.argv) > 1 else "admin123"
    
    if reset_admin_password(password):
        print(f"✅ 密码已重置为: {password}")
        sys.exit(0)
    else:
        print("❌ 密码重置失败")
        sys.exit(1)
