#!/usr/bin/env python3
"""从 description 字段提取 SPU ID 并更新到 spu_id 字段

使用方法:
    python3 scripts/migrate_spu_id_from_description.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from loguru import logger

def migrate_spu_id():
    """从 description 字段提取 SPU ID"""
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 统计需要更新的记录数
        count_query = text("""
            SELECT COUNT(*) 
            FROM products 
            WHERE description LIKE 'SPU: %' 
            AND (spu_id IS NULL OR spu_id = '')
        """)
        result = db.execute(count_query)
        total_count = result.scalar()
        
        if total_count == 0:
            logger.info("没有需要迁移的 SPU ID 数据")
            return
        
        logger.info(f"发现 {total_count} 条记录需要迁移 SPU ID")
        
        # 提取并更新 SPU ID
        # PostgreSQL 使用 REGEXP_REPLACE，SQLite 使用 SUBSTR
        if 'postgresql' in settings.DATABASE_URL.lower():
            update_query = text("""
                UPDATE products 
                SET spu_id = REGEXP_REPLACE(description, '^SPU:\\s*', '', 'g')
                WHERE description LIKE 'SPU: %' 
                AND (spu_id IS NULL OR spu_id = '')
            """)
        else:
            # SQLite 版本
            update_query = text("""
                UPDATE products 
                SET spu_id = TRIM(SUBSTR(description, 5))
                WHERE description LIKE 'SPU: %' 
                AND (spu_id IS NULL OR spu_id = '')
            """)
        
        result = db.execute(update_query)
        updated_count = result.rowcount
        db.commit()
        
        logger.info(f"成功迁移 {updated_count} 条记录的 SPU ID")
        
        # 验证结果
        verify_query = text("""
            SELECT COUNT(*) 
            FROM products 
            WHERE description LIKE 'SPU: %' 
            AND (spu_id IS NULL OR spu_id = '')
        """)
        result = db.execute(verify_query)
        remaining_count = result.scalar()
        
        if remaining_count > 0:
            logger.warning(f"仍有 {remaining_count} 条记录未成功迁移，请检查数据格式")
        else:
            logger.info("所有 SPU ID 迁移完成！")
            
    except Exception as e:
        db.rollback()
        logger.error(f"迁移 SPU ID 时发生错误: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    logger.info("开始迁移 SPU ID 数据...")
    migrate_spu_id()
    logger.info("迁移完成！")

