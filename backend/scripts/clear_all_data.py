"""清理所有本地数据脚本"""
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
        # 尝试从父目录加载
        root_env = backend_dir.parent / '.env'
        if root_env.exists():
            load_dotenv(root_env)
except ImportError:
    # 如果没有 dotenv，尝试直接设置环境变量
    pass

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.order import Order
from app.models.product import Product, ProductCost
from app.models.shop import Shop
from app.models.activity import Activity
from app.models.import_history import ImportHistory
from loguru import logger


def clear_all_data():
    """清理所有数据（保留店铺结构）"""
    db: Session = SessionLocal()
    
    try:
        logger.info("开始清理所有数据...")
        
        # 删除订单数据
        deleted_orders = db.query(Order).delete()
        logger.info(f"✓ 已删除 {deleted_orders} 条订单记录")
        
        # 删除商品成本数据
        deleted_costs = db.query(ProductCost).delete()
        logger.info(f"✓ 已删除 {deleted_costs} 条商品成本记录")
        
        # 删除商品数据
        deleted_products = db.query(Product).delete()
        logger.info(f"✓ 已删除 {deleted_products} 条商品记录")
        
        # 删除活动数据
        deleted_activities = db.query(Activity).delete()
        logger.info(f"✓ 已删除 {deleted_activities} 条活动记录")
        
        # 删除导入历史
        deleted_imports = db.query(ImportHistory).delete()
        logger.info(f"✓ 已删除 {deleted_imports} 条导入历史记录")
        
        # 删除店铺数据（可选，如果需要保留店铺结构，可以注释掉）
        # deleted_shops = db.query(Shop).delete()
        # logger.info(f"✓ 已删除 {deleted_shops} 条店铺记录")
        
        db.commit()
        logger.info("✅ 数据清理完成！")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 数据清理失败: {e}")
        raise
    finally:
        db.close()


def clear_shops_only():
    """仅清理店铺数据"""
    db: Session = SessionLocal()
    
    try:
        logger.info("开始清理店铺数据...")
        
        # 删除店铺数据（会级联删除关联的订单和商品）
        deleted_shops = db.query(Shop).delete()
        logger.info(f"✓ 已删除 {deleted_shops} 条店铺记录")
        
        db.commit()
        logger.info("✅ 店铺数据清理完成！")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 店铺数据清理失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清理本地数据")
    parser.add_argument(
        "--shops-only",
        action="store_true",
        help="仅清理店铺数据（会级联删除关联数据）"
    )
    
    args = parser.parse_args()
    
    if args.shops_only:
        confirm = input("⚠️  确定要删除所有店铺数据吗？此操作不可恢复！(yes/no): ")
        if confirm.lower() == "yes":
            clear_shops_only()
        else:
            logger.info("操作已取消")
    else:
        confirm = input("⚠️  确定要清理所有订单、商品等数据吗？店铺数据将保留。(yes/no): ")
        if confirm.lower() == "yes":
            clear_all_data()
        else:
            logger.info("操作已取消")

