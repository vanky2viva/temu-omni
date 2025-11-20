#!/usr/bin/env python3
"""为 PostgreSQL 数据库添加 CN 相关字段"""
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

from app.core.database import engine
from sqlalchemy import text, inspect
from loguru import logger


def add_cn_fields():
    """为 shops 表添加 CN 相关字段"""
    try:
        logger.info("开始检查并添加 CN 字段...")
        
        # 检查数据库类型
        db_url = str(engine.url)
        if 'postgresql' not in db_url.lower():
            logger.warning(f"当前数据库不是 PostgreSQL: {db_url}")
            logger.info("如果是 SQLite，字段应该已经存在。如果是其他数据库，请手动添加字段。")
            return
        
        logger.info("检测到 PostgreSQL 数据库")
        
        # 检查表结构
        inspector = inspect(engine)
        columns = inspector.get_columns('shops')
        existing_cols = [col['name'] for col in columns]
        
        logger.info(f"当前 shops 表有 {len(existing_cols)} 个字段")
        
        # 需要添加的字段
        fields_to_add = [
            ('cn_access_token', 'TEXT', 'CN区域访问令牌'),
            ('cn_app_key', 'VARCHAR(200)', 'CN区域App Key'),
            ('cn_app_secret', 'TEXT', 'CN区域App Secret'),
            ('cn_api_base_url', 'VARCHAR(200)', 'CN区域API基础URL'),
        ]
        
        missing_fields = []
        for field_name, field_type, comment in fields_to_add:
            if field_name not in existing_cols:
                missing_fields.append((field_name, field_type, comment))
        
        if not missing_fields:
            logger.info("✅ 所有 CN 字段已存在")
            return
        
        logger.info(f"需要添加 {len(missing_fields)} 个字段")
        
        # 添加字段（PostgreSQL 使用 IF NOT EXISTS 需要先检查）
        with engine.connect() as conn:
            for field_name, field_type, comment in missing_fields:
                try:
                    # 先检查字段是否存在
                    check_sql = text("""
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'shops' AND column_name = :field_name
                    """)
                    result = conn.execute(check_sql, {"field_name": field_name}).fetchone()
                    
                    if result:
                        logger.info(f"字段 {field_name} 已存在，跳过")
                        continue
                    
                    # 添加字段
                    sql = f'ALTER TABLE shops ADD COLUMN {field_name} {field_type}'
                    conn.execute(text(sql))
                    logger.info(f"✅ 添加字段: {field_name} ({field_type})")
                except Exception as e:
                    logger.error(f"❌ 添加字段 {field_name} 失败: {e}")
                    raise
            
            conn.commit()
            logger.info("✅ 所有字段添加成功")
            
            # 设置默认值
            logger.info("设置默认值...")
            conn.execute(text('''
                UPDATE shops 
                SET cn_api_base_url = 'https://openapi.kuajingmaihuo.com/openapi/router',
                    cn_app_key = 'af5bcf5d4bd5a492fa09c2ee302d75b9',
                    cn_app_secret = 'e4f229bb9c4db21daa999e73c8683d42ba0a7094'
                WHERE cn_api_base_url IS NULL OR cn_api_base_url = ''
            '''))
            conn.commit()
            logger.info("✅ 默认值设置成功")
        
        logger.info("✅ 所有操作完成！")
        
    except Exception as e:
        logger.error(f"❌ 操作失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    add_cn_fields()

