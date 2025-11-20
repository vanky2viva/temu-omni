"""清理订单数据脚本"""
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
    pass

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.order import Order
from loguru import logger


def clear_orders(shop_id: int = None):
    """清理订单数据
    
    Args:
        shop_id: 店铺ID，如果指定则只清理该店铺的订单，否则清理所有订单
    """
    db: Session = SessionLocal()
    
    try:
        if shop_id:
            logger.info(f"开始清理店铺 {shop_id} 的订单数据...")
            deleted_count = db.query(Order).filter(Order.shop_id == shop_id).delete()
            logger.info(f"✓ 已删除 {deleted_count} 条订单记录（店铺ID: {shop_id}）")
        else:
            logger.info("开始清理所有订单数据...")
            deleted_count = db.query(Order).delete()
            logger.info(f"✓ 已删除 {deleted_count} 条订单记录")
        
        db.commit()
        logger.info("✅ 订单数据清理完成！")
        return deleted_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 订单数据清理失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清理订单数据")
    parser.add_argument(
        "--shop-id",
        type=int,
        default=None,
        help="店铺ID，如果指定则只清理该店铺的订单（可选）"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="跳过确认提示，直接执行清理"
    )
    
    args = parser.parse_args()
    
    if args.shop_id:
        message = f"⚠️  确定要删除店铺 {args.shop_id} 的所有订单数据吗？此操作不可恢复！(yes/no): "
    else:
        message = "⚠️  确定要删除所有订单数据吗？此操作不可恢复！(yes/no): "
    
    if args.yes:
        confirm = "yes"
    else:
        confirm = input(message)
    
    if confirm.lower() == "yes":
        clear_orders(shop_id=args.shop_id)
    else:
        logger.info("操作已取消")

