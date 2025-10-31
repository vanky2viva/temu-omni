#!/usr/bin/env python3
"""修复商品表缺失字段的脚本"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine
from loguru import logger


def fix_missing_fields():
    """添加缺失的商品表字段"""
    try:
        with engine.connect() as conn:
            # 检查数据库类型
            db_type = engine.dialect.name
            
            if db_type == 'postgresql':
                # PostgreSQL支持IF NOT EXISTS
                try:
                    conn.execute(text("""
                        ALTER TABLE products 
                        ADD COLUMN IF NOT EXISTS skc_id VARCHAR(100);
                    """))
                    conn.commit()
                    logger.info("PostgreSQL: 已添加 skc_id 字段")
                except Exception as e:
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        logger.info("PostgreSQL: skc_id 字段已存在")
                    else:
                        raise
                
                try:
                    conn.execute(text("""
                        ALTER TABLE products 
                        ADD COLUMN IF NOT EXISTS price_status VARCHAR(50);
                    """))
                    conn.commit()
                    logger.info("PostgreSQL: 已添加 price_status 字段")
                except Exception as e:
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        logger.info("PostgreSQL: price_status 字段已存在")
                    else:
                        raise
                
            elif db_type == 'sqlite':
                # SQLite需要先检查字段是否存在
                cursor = conn.execute(text("PRAGMA table_info(products)"))
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'skc_id' not in columns:
                    conn.execute(text("ALTER TABLE products ADD COLUMN skc_id VARCHAR(100)"))
                    logger.info("SQLite: 已添加 skc_id 字段")
                else:
                    logger.info("SQLite: skc_id 字段已存在")
                
                if 'price_status' not in columns:
                    conn.execute(text("ALTER TABLE products ADD COLUMN price_status VARCHAR(50)"))
                    logger.info("SQLite: 已添加 price_status 字段")
                else:
                    logger.info("SQLite: price_status 字段已存在")
                
                conn.commit()
                
            else:
                logger.warning(f"不支持的数据库类型: {db_type}")
                logger.info("请手动运行以下SQL:")
                logger.info("ALTER TABLE products ADD COLUMN skc_id VARCHAR(100);")
                logger.info("ALTER TABLE products ADD COLUMN price_status VARCHAR(50);")
                return False
            
            logger.success("字段修复完成！")
            return True
            
    except Exception as e:
        logger.error(f"修复字段时出错: {e}")
        logger.info("请手动运行数据库迁移:")
        logger.info("cd backend && alembic upgrade head")
        return False


if __name__ == "__main__":
    logger.info("开始修复商品表缺失字段...")
    success = fix_missing_fields()
    sys.exit(0 if success else 1)

