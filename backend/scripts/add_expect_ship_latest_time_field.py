#!/usr/bin/env python3
"""添加 expect_ship_latest_time 字段到订单表"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models.order import Order
from sqlalchemy import text

def add_expect_ship_latest_time_field():
    """添加 expect_ship_latest_time 字段"""
    print("开始添加 expect_ship_latest_time 字段...")
    
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='orders' AND column_name='expect_ship_latest_time'
            """))
            
            if result.fetchone():
                print("✅ 字段 expect_ship_latest_time 已存在，跳过")
                return
            
            # 添加字段
            conn.execute(text("""
                ALTER TABLE orders 
                ADD COLUMN expect_ship_latest_time TIMESTAMP NULL
            """))
            conn.commit()
            print("✅ 成功添加 expect_ship_latest_time 字段")
            
    except Exception as e:
        print(f"❌ 添加字段失败: {e}")
        raise

if __name__ == "__main__":
    add_expect_ship_latest_time_field()

