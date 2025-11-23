#!/usr/bin/env python3
"""测试后端服务状态"""
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import check_database_connection, SessionLocal
from app.core.config import settings
from app.models.user import User
from loguru import logger

def test_database():
    """测试数据库连接"""
    print("=" * 50)
    print("测试数据库连接...")
    print(f"数据库URL: {settings.DATABASE_URL}")
    
    if check_database_connection():
        print("✅ 数据库连接正常")
    else:
        print("❌ 数据库连接失败")
        return False
    
    # 测试查询用户表
    try:
        db = SessionLocal()
        user_count = db.query(User).count()
        print(f"✅ 用户表查询成功，当前用户数: {user_count}")
        
        # 检查是否有admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print(f"✅ 找到admin用户: {admin_user.username} (激活状态: {admin_user.is_active})")
        else:
            print("⚠️  未找到admin用户，需要初始化")
        db.close()
        return True
    except Exception as e:
        print(f"❌ 查询用户表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """测试配置"""
    print("=" * 50)
    print("测试配置...")
    print(f"SECRET_KEY: {'已设置' if settings.SECRET_KEY else '未设置'}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"DEBUG: {settings.DEBUG}")
    return True

if __name__ == "__main__":
    print("\n🔍 后端服务诊断工具\n")
    
    test_config()
    success = test_database()
    
    print("=" * 50)
    if success:
        print("✅ 所有测试通过")
        sys.exit(0)
    else:
        print("❌ 测试失败，请检查错误信息")
        sys.exit(1)

