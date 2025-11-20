"""重建数据库脚本"""
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

from app.core.database import Base, engine, SessionLocal
from app.core.init_default_user import init_default_user
from loguru import logger


def recreate_database():
    """重建数据库"""
    try:
        logger.info("开始重建数据库...")
        
        # 删除所有表
        logger.info("删除所有表...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✓ 所有表已删除")
        
        # 创建所有表
        logger.info("创建所有表...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ 所有表已创建")
        
        # 初始化默认用户
        logger.info("初始化默认用户...")
        init_default_user()
        logger.info("✓ 默认用户已创建")
        
        logger.info("✅ 数据库重建完成！")
        logger.info("")
        logger.info("默认登录信息：")
        logger.info("  用户名: luffyadmin")
        logger.info("  密码: luffy123!@#")
        
    except Exception as e:
        logger.error(f"❌ 数据库重建失败: {e}")
        raise


if __name__ == "__main__":
    confirm = input("⚠️  确定要删除并重建数据库吗？此操作不可恢复！(yes/no): ")
    if confirm.lower() == "yes":
        recreate_database()
    else:
        logger.info("操作已取消")



