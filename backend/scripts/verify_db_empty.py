"""验证数据库是否为空"""
import sys
import os
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from dotenv import load_dotenv
    env_path = backend_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from sqlalchemy import text
from app.core.database import SessionLocal
from loguru import logger

def verify_empty():
    db = SessionLocal()
    try:
        # 检查所有表
        tables = ['shops', 'orders', 'products', 'product_costs', 'activities', 'import_history']
        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            logger.info(f"{table}: {count} 条记录")
        
        # 检查 shops 表
        result = db.execute(text("SELECT id, shop_name, region FROM shops"))
        shops = result.fetchall()
        if shops:
            logger.warning(f"发现 {len(shops)} 个店铺:")
            for shop in shops:
                logger.warning(f"  - ID: {shop[0]}, Name: {shop[1]}, Region: {shop[2]}")
        else:
            logger.info("✅ 数据库为空，没有店铺数据")
    finally:
        db.close()

if __name__ == "__main__":
    verify_empty()


