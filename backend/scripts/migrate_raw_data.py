"""数据迁移脚本：将现有orders.raw_data迁移到temu_orders_raw表

此脚本用于将现有orders表中的raw_data字段迁移到新的temu_orders_raw表。
运行前请确保：
1. 数据库迁移已完成（add_raw_tables_optimize）
2. 已备份数据库
"""
import json
import sys
from datetime import datetime
from sqlalchemy import text
from loguru import logger

from app.core.database import SessionLocal, engine
from app.models.order import Order
from app.models.temu_orders_raw import TemuOrdersRaw


def migrate_orders_raw_data():
    """迁移订单原始数据"""
    db = SessionLocal()
    try:
        # 查询所有有raw_data的订单
        orders = db.query(Order).filter(Order.raw_data.isnot(None)).all()
        total = len(orders)
        logger.info(f"找到 {total} 条需要迁移的订单数据")
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for order in orders:
            try:
                # 检查是否已经存在raw记录
                existing_raw = db.query(TemuOrdersRaw).filter(
                    TemuOrdersRaw.external_order_id == order.temu_order_id
                ).first()
                
                if existing_raw:
                    logger.debug(f"订单 {order.temu_order_id} 的raw数据已存在，跳过")
                    skipped += 1
                    # 更新关联关系
                    order.raw_data_id = existing_raw.id
                    continue
                
                # 解析raw_data JSON
                try:
                    raw_json = json.loads(order.raw_data) if isinstance(order.raw_data, str) else order.raw_data
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"订单 {order.temu_order_id} 的raw_data格式错误: {e}")
                    errors += 1
                    continue
                
                # 创建raw记录
                raw_record = TemuOrdersRaw(
                    shop_id=order.shop_id,
                    external_order_id=order.temu_order_id,
                    raw_json=raw_json,
                    fetched_at=order.created_at or datetime.utcnow(),
                    created_at=order.created_at or datetime.utcnow()
                )
                db.add(raw_record)
                db.flush()  # 获取ID
                
                # 更新订单的raw_data_id
                order.raw_data_id = raw_record.id
                
                migrated += 1
                
                if migrated % 100 == 0:
                    db.commit()
                    logger.info(f"已迁移 {migrated}/{total} 条记录")
                    
            except Exception as e:
                logger.error(f"迁移订单 {order.temu_order_id} 时出错: {e}")
                errors += 1
                db.rollback()
                continue
        
        # 最终提交
        db.commit()
        
        logger.info(f"迁移完成！总计: {total}, 成功: {migrated}, 跳过: {skipped}, 错误: {errors}")
        
    except Exception as e:
        logger.error(f"迁移过程出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_migration():
    """验证迁移结果"""
    db = SessionLocal()
    try:
        # 统计
        total_orders = db.query(Order).count()
        orders_with_raw_data = db.query(Order).filter(Order.raw_data.isnot(None)).count()
        orders_with_raw_data_id = db.query(Order).filter(Order.raw_data_id.isnot(None)).count()
        total_raw_records = db.query(TemuOrdersRaw).count()
        
        logger.info("迁移验证结果:")
        logger.info(f"  总订单数: {total_orders}")
        logger.info(f"  有raw_data的订单: {orders_with_raw_data}")
        logger.info(f"  有raw_data_id的订单: {orders_with_raw_data_id}")
        logger.info(f"  raw表记录数: {total_raw_records}")
        
        # 检查是否有未关联的订单
        unlinked = db.query(Order).filter(
            Order.raw_data.isnot(None),
            Order.raw_data_id.is_(None)
        ).count()
        
        if unlinked > 0:
            logger.warning(f"  警告: 有 {unlinked} 条订单有raw_data但未关联到raw表")
        else:
            logger.info("  所有有raw_data的订单都已成功关联")
            
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始迁移订单原始数据...")
    
    try:
        migrate_orders_raw_data()
        verify_migration()
        logger.info("迁移脚本执行完成！")
    except Exception as e:
        logger.error(f"迁移脚本执行失败: {e}")
        sys.exit(1)

