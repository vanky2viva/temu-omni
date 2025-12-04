#!/usr/bin/env python3
"""
登录问题诊断脚本
用于检查登录相关的配置和数据库状态
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, check_database_connection, engine
from app.core.config import settings
from app.models.user import User
from app.core.security import verify_password, get_password_hash
from loguru import logger

def diagnose_login():
    """诊断登录问题"""
    print("=" * 60)
    print("登录问题诊断")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n1. 检查配置...")
    print(f"   DATABASE_URL: {'已设置' if settings.DATABASE_URL else '未设置'}")
    print(f"   SECRET_KEY: {'已设置' if settings.SECRET_KEY else '未设置'}")
    if settings.SECRET_KEY:
        print(f"   SECRET_KEY 长度: {len(settings.SECRET_KEY)}")
    
    # 2. 检查数据库连接
    print("\n2. 检查数据库连接...")
    try:
        if check_database_connection():
            print("   ✓ 数据库连接正常")
        else:
            print("   ✗ 数据库连接失败")
            return
    except Exception as e:
        print(f"   ✗ 数据库连接异常: {e}")
        return
    
    # 3. 检查用户表是否存在
    print("\n3. 检查用户表...")
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if 'users' in tables:
            print("   ✓ users 表存在")
        else:
            print("   ✗ users 表不存在，需要运行数据库迁移")
            return
    except Exception as e:
        print(f"   ✗ 检查表失败: {e}")
        return
    
    # 4. 检查用户数据
    print("\n4. 检查用户数据...")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"   用户总数: {len(users)}")
        if users:
            print("   用户列表:")
            for user in users:
                print(f"     - ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 激活: {user.is_active}")
        else:
            print("   ⚠ 没有用户，需要创建默认用户")
            print("   运行: python -m app.core.init_default_user")
    except Exception as e:
        print(f"   ✗ 查询用户失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # 5. 测试密码验证
    print("\n5. 测试密码验证...")
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if admin_user:
            print(f"   找到 admin 用户")
            print(f"   密码哈希: {admin_user.hashed_password[:20]}...")
            try:
                # 测试密码验证
                test_result = verify_password('admin123', admin_user.hashed_password)
                print(f"   密码验证测试 (admin123): {'✓ 通过' if test_result else '✗ 失败'}")
            except Exception as e:
                print(f"   ✗ 密码验证异常: {e}")
        else:
            print("   ⚠ admin 用户不存在")
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    diagnose_login()


