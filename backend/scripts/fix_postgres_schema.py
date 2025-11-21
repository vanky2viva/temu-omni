"""修复 PostgreSQL 数据库表结构脚本"""
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

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from loguru import logger


def fix_schema():
    """修复数据库表结构"""
    db = SessionLocal()
    try:
        logger.info("开始修复数据库表结构...")
        
        # 检查是否是 PostgreSQL
        db_url = str(engine.url)
        if 'postgresql' not in db_url:
            logger.info("当前数据库不是 PostgreSQL，跳过修复")
            return
        
        # 添加缺失的 parent_order_sn 列
        try:
            db.execute(text("""
                ALTER TABLE orders 
                ADD COLUMN IF NOT EXISTS parent_order_sn VARCHAR(100);
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_orders_parent_order_sn 
                ON orders(parent_order_sn);
            """))
            db.commit()
            logger.info("✅ 已添加 parent_order_sn 列和索引")
        except Exception as e:
            logger.warning(f"添加 parent_order_sn 列时出错（可能已存在）: {e}")
            db.rollback()
        
        logger.info("✅ 数据库表结构修复完成！")
        
    except Exception as e:
        logger.error(f"❌ 修复数据库表结构失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_schema()




