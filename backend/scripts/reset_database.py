#!/usr/bin/env python3
"""重置数据库：删除所有表并重新创建

使用方法:
    python3 scripts/reset_database.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models import shop, product, order, activity, import_history, system_config
from loguru import logger

def reset_database():
    """重置数据库：删除所有表并重新创建"""
    
    logger.info("开始重置数据库...")
    logger.warning("⚠️  这将删除所有数据！")
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # 删除所有表
        logger.info("删除所有表...")
        Base.metadata.drop_all(bind=engine)
        
        # 创建所有表
        logger.info("创建所有表（包含新的 spu_id 字段）...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ 数据库重置完成！")
        logger.info("现在可以重新导入数据了。")
        
    except Exception as e:
        logger.error(f"重置数据库时发生错误: {e}")
        raise

if __name__ == '__main__':
    reset_database()

