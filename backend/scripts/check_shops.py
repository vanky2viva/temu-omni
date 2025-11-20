"""检查店铺数据脚本"""
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
from app.models.shop import Shop
from loguru import logger


def check_shops():
    """检查店铺数据"""
    db: Session = SessionLocal()
    
    try:
        shops = db.query(Shop).all()
        logger.info(f"数据库中共有 {len(shops)} 个店铺：")
        
        for shop in shops:
            logger.info(f"  - ID: {shop.id}, 名称: {shop.shop_name}, 地区: {shop.region}, Token: {'已配置' if shop.access_token else '未配置'}")
        
        return shops
        
    except Exception as e:
        logger.error(f"检查店铺数据失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    check_shops()



