#!/usr/bin/env python3
"""诊断登录问题脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# 先导入所有模型以确保关系映射正确初始化
from app.models import *  # noqa: F401, F403

from sqlalchemy import inspect, text
from loguru import logger
from app.core.database import engine, SessionLocal, Base
from app.core.config import settings
from app.models.user import User


def check_database_connection():
    """检查数据库连接"""
    print("=" * 60)
    print("1. 检查数据库连接...")
    print("=" * 60)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ 数据库连接正常")
        print(f"  数据库URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else '已隐藏'}")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        return False


def check_tables_exist():
    """检查表是否存在"""
    print("\n" + "=" * 60)
    print("2. 检查数据库表...")
    print("=" * 60)
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['users', 'shops', 'orders', 'products']
        missing_tables = []
        
        for table in required_tables:
            if table in tables:
                print(f"✓ 表 '{table}' 存在")
            else:
                print(f"✗ 表 '{table}' 不存在")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n缺少表: {', '.join(missing_tables)}")
            return False
        return True
    except Exception as e:
        print(f"✗ 检查表失败: {str(e)}")
        return False


def check_users_exist():
    """检查用户是否存在"""
    print("\n" + "=" * 60)
    print("3. 检查用户数据...")
    print("=" * 60)
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        print(f"✓ 用户表中有 {user_count} 个用户")
        
        if user_count == 0:
            print("✗ 没有用户，需要创建默认用户")
            return False
        
        # 检查默认用户
        default_user = db.query(User).filter(User.username == "luffyadmin").first()
        if default_user:
            print(f"✓ 默认用户 'luffyadmin' 存在")
            print(f"  邮箱: {default_user.email}")
            print(f"  是否激活: {default_user.is_active}")
            print(f"  是否超级用户: {default_user.is_superuser}")
            return True
        else:
            print("✗ 默认用户 'luffyadmin' 不存在")
            return False
    except Exception as e:
        print(f"✗ 检查用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def check_secret_key():
    """检查SECRET_KEY配置"""
    print("\n" + "=" * 60)
    print("4. 检查配置...")
    print("=" * 60)
    if settings.SECRET_KEY and settings.SECRET_KEY != "your-secret-key-here-change-in-production":
        print("✓ SECRET_KEY 已配置")
        return True
    else:
        print("✗ SECRET_KEY 未正确配置")
        return False


def create_tables():
    """创建数据库表"""
    print("\n" + "=" * 60)
    print("正在创建数据库表...")
    print("=" * 60)
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"✗ 创建表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def create_default_user():
    """创建默认用户"""
    print("\n" + "=" * 60)
    print("正在创建默认用户...")
    print("=" * 60)
    db = SessionLocal()
    try:
        from app.core.security import get_password_hash
        
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == "luffyadmin").first()
        if existing_user:
            print("✓ 默认用户已存在，跳过创建")
            return True
        
        # 创建默认用户
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
        print("✓ 默认用户创建成功!")
        print("  用户名: luffyadmin")
        print("  密码: luffy123!@#")
        return True
    except Exception as e:
        print(f"✗ 创建用户失败: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🔍 Temu-Omni 登录问题诊断工具")
    print("=" * 60 + "\n")
    
    # 检查数据库连接
    if not check_database_connection():
        print("\n❌ 请先确保数据库服务正在运行")
        print("   如果使用Docker: docker-compose up -d postgres")
        print("   如果使用本地PostgreSQL: 请检查PostgreSQL服务状态")
        sys.exit(1)
    
    # 检查表
    tables_ok = check_tables_exist()
    
    # 检查用户
    users_ok = check_users_exist()
    
    # 检查配置
    config_ok = check_secret_key()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 诊断结果")
    print("=" * 60)
    
    if not tables_ok:
        print("\n⚠️  数据库表缺失，需要初始化数据库")
        response = input("是否现在创建数据库表？(y/n): ").strip().lower()
        if response == 'y':
            if not create_tables():
                print("\n❌ 创建表失败，请检查错误信息")
                sys.exit(1)
            # 重新检查用户
            users_ok = check_users_exist()
    
    if not users_ok:
        print("\n⚠️  没有用户，需要创建默认用户")
        response = input("是否现在创建默认用户？(y/n): ").strip().lower()
        if response == 'y':
            if not create_default_user():
                print("\n❌ 创建用户失败，请检查错误信息")
                sys.exit(1)
    
    if not config_ok:
        print("\n⚠️  SECRET_KEY未正确配置")
        print("   请检查 backend/.env 文件中的 SECRET_KEY 配置")
    
    # 最终检查
    print("\n" + "=" * 60)
    print("✅ 最终检查")
    print("=" * 60)
    
    if check_database_connection() and check_tables_exist() and check_users_exist():
        print("\n✅ 所有检查通过！现在应该可以正常登录了")
        print("\n默认登录信息：")
        print("  用户名: luffyadmin")
        print("  密码: luffy123!@#")
    else:
        print("\n❌ 仍有问题未解决，请根据上述提示进行修复")


if __name__ == "__main__":
    main()

