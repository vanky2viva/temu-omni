"""强制清理所有店铺数据脚本"""
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


def force_clear_all_shops():
    """强制清理所有店铺数据（使用原始SQL）"""
    db = SessionLocal()
    
    try:
        logger.info("开始强制清理所有店铺数据...")
        
        # 先删除关联数据（如果外键约束允许）
        try:
            db.execute(text("DELETE FROM orders"))
            logger.info("✓ 已删除所有订单数据")
        except Exception as e:
            logger.warning(f"删除订单数据时出错（可能已删除）: {e}")
        
        try:
            db.execute(text("DELETE FROM products"))
            logger.info("✓ 已删除所有商品数据")
        except Exception as e:
            logger.warning(f"删除商品数据时出错（可能已删除）: {e}")
        
        try:
            db.execute(text("DELETE FROM product_costs"))
            logger.info("✓ 已删除所有商品成本数据")
        except Exception as e:
            logger.warning(f"删除商品成本数据时出错（可能已删除）: {e}")
        
        try:
            db.execute(text("DELETE FROM activities"))
            logger.info("✓ 已删除所有活动数据")
        except Exception as e:
            logger.warning(f"删除活动数据时出错（可能已删除）: {e}")
        
        try:
            db.execute(text("DELETE FROM import_history"))
            logger.info("✓ 已删除所有导入历史数据")
        except Exception as e:
            logger.warning(f"删除导入历史数据时出错（可能已删除）: {e}")
        
        # 最后删除店铺数据
        result = db.execute(text("DELETE FROM shops"))
        deleted_count = result.rowcount
        logger.info(f"✓ 已删除 {deleted_count} 条店铺记录")
        
        db.commit()
        logger.info("✅ 所有数据清理完成！")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 数据清理失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("⚠️  确定要强制删除所有店铺和相关数据吗？此操作不可恢复！(yes/no): ")
    if confirm.lower() == "yes":
        force_clear_all_shops()
    else:
        logger.info("操作已取消")




