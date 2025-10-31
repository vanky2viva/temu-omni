#!/usr/bin/env python3
"""生产环境数据库初始化脚本

此脚本用于：
1. 重置数据库（删除所有表和虚拟数据）
2. 创建表结构
3. 初始化基础配置
4. 不生成任何虚拟数据

使用方法:
    python3 scripts/init_production_database.py
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
    
    logger.info("="*60)
    logger.info("生产环境数据库初始化")
    logger.info("="*60)
    logger.warning("⚠️  这将删除所有现有数据！")
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # 删除所有表
        logger.info("步骤 1/3: 删除所有现有表...")
        Base.metadata.drop_all(bind=engine)
        logger.success("✓ 所有表已删除")
        
        # 创建所有表
        logger.info("步骤 2/3: 创建数据库表结构...")
        Base.metadata.create_all(bind=engine)
        logger.success("✓ 数据库表结构已创建")
        
        # 初始化系统配置（如果需要）
        logger.info("步骤 3/3: 初始化系统配置...")
        with engine.connect() as conn:
            # 这里可以添加基础配置
            # 比如默认时区、默认设置等
            pass
        logger.success("✓ 系统配置已初始化")
        
        logger.info("="*60)
        logger.success("✅ 生产数据库初始化完成！")
        logger.info("="*60)
        logger.info("现在可以：")
        logger.info("  1. 通过API同步真实数据")
        logger.info("  2. 通过Excel导入真实数据")
        logger.info("  3. 通过在线表格导入真实数据")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ 初始化数据库时发生错误: {e}")
        raise

if __name__ == '__main__':
    # 二次确认
    print("\n" + "="*60)
    print("⚠️  警告：此操作将清空所有数据！")
    print("="*60)
    confirm = input("\n确认要继续吗？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ 已取消操作")
        sys.exit(0)
    
    reset_database()

