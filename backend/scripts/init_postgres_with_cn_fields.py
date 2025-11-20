#!/usr/bin/env python3
"""初始化 PostgreSQL 数据库并添加 CN 字段"""
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
from app.models import shop, product, order, activity, import_history, system_config, user
from loguru import logger
from sqlalchemy import text, inspect


def init_postgres_with_cn_fields():
    """初始化 PostgreSQL 数据库并添加 CN 字段"""
    try:
        logger.info("=" * 60)
        logger.info("初始化 PostgreSQL 数据库")
        logger.info("=" * 60)
        
        # 检查数据库类型
        db_url = str(engine.url)
        logger.info(f"数据库URL: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        
        if 'postgresql' not in db_url.lower():
            logger.error(f"❌ 当前数据库不是 PostgreSQL: {db_url}")
            logger.error("请更新 .env 文件中的 DATABASE_URL 为 PostgreSQL 连接字符串")
            logger.error("例如: DATABASE_URL=postgresql://user:password@localhost:5432/temu_omni")
            return False
        
        logger.info("✅ 检测到 PostgreSQL 数据库")
        logger.info("")
        
        # 1. 创建所有表
        logger.info("步骤 1: 创建所有表...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 所有表已创建")
        logger.info("")
        
        # 2. 检查并添加 CN 字段
        logger.info("步骤 2: 检查并添加 CN 字段...")
        inspector = inspect(engine)
        columns = inspector.get_columns('shops')
        existing_cols = [col['name'] for col in columns]
        
        fields_to_add = [
            ('cn_access_token', 'TEXT', 'CN区域访问令牌'),
            ('cn_app_key', 'VARCHAR(200)', 'CN区域App Key'),
            ('cn_app_secret', 'TEXT', 'CN区域App Secret'),
            ('cn_api_base_url', 'VARCHAR(200)', 'CN区域API基础URL'),
        ]
        
        missing_fields = [(name, type_, comment) for name, type_, comment in fields_to_add if name not in existing_cols]
        
        if missing_fields:
            logger.info(f"需要添加 {len(missing_fields)} 个字段")
            with engine.connect() as conn:
                for field_name, field_type, comment in missing_fields:
                    try:
                        # 检查字段是否存在
                        check_sql = text("""
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = 'shops' AND column_name = :field_name
                        """)
                        result = conn.execute(check_sql, {"field_name": field_name}).fetchone()
                        
                        if result:
                            logger.info(f"  字段 {field_name} 已存在，跳过")
                            continue
                        
                        # 添加字段
                        sql = f'ALTER TABLE shops ADD COLUMN {field_name} {field_type}'
                        conn.execute(text(sql))
                        logger.info(f"  ✅ 添加字段: {field_name} ({field_type})")
                    except Exception as e:
                        logger.error(f"  ❌ 添加字段 {field_name} 失败: {e}")
                        raise
                
                conn.commit()
                logger.info("✅ 所有 CN 字段添加成功")
        else:
            logger.info("✅ 所有 CN 字段已存在")
        
        logger.info("")
        
        # 3. 设置默认值
        logger.info("步骤 3: 设置 CN 字段默认值...")
        with engine.connect() as conn:
            conn.execute(text('''
                UPDATE shops 
                SET 
                    cn_api_base_url = COALESCE(cn_api_base_url, 'https://openapi.kuajingmaihuo.com/openapi/router'),
                    cn_app_key = COALESCE(cn_app_key, 'af5bcf5d4bd5a492fa09c2ee302d75b9'),
                    cn_app_secret = COALESCE(cn_app_secret, 'e4f229bb9c4db21daa999e73c8683d42ba0a7094')
                WHERE 
                    cn_api_base_url IS NULL 
                    OR cn_app_key IS NULL 
                    OR cn_app_secret IS NULL
            '''))
            conn.commit()
        logger.info("✅ 默认值设置成功")
        logger.info("")
        
        # 4. 初始化默认用户
        logger.info("步骤 4: 初始化默认用户...")
        try:
            init_default_user()
            logger.info("✅ 默认用户已创建")
        except Exception as e:
            logger.warning(f"⚠️  默认用户可能已存在: {e}")
        logger.info("")
        
        logger.info("=" * 60)
        logger.info("✅ PostgreSQL 数据库初始化完成！")
        logger.info("=" * 60)
        logger.info("")
        logger.info("默认登录信息：")
        logger.info("  用户名: luffyadmin")
        logger.info("  密码: luffy123!@#")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = init_postgres_with_cn_fields()
    sys.exit(0 if success else 1)

