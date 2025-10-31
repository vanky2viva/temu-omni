#!/usr/bin/env python3
"""检查订单数据"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_orders():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 检查订单数据
        result = conn.execute(text("""
            SELECT order_sn, product_sku, product_name, total_price, quantity, currency 
            FROM orders 
            LIMIT 5
        """))
        
        print("前5条订单数据:")
        for row in result:
            print(f"  订单号: {row[0]}")
            print(f"  SKU: {row[1] or '(空)'}")
            print(f"  商品名: {row[2][:40] if row[2] else '(空)'}")
            print(f"  金额: {row[3]}, 货币: {row[4]}, 数量: {row[5]}")
            print()
        
        # 检查原始数据
        result2 = conn.execute(text("""
            SELECT order_sn, raw_data 
            FROM orders 
            WHERE product_sku IS NULL OR product_sku = ''
            LIMIT 1
        """))
        
        row2 = result2.fetchone()
        if row2 and row2[1]:
            data = json.loads(row2[1])
            print(f"\n订单 {row2[0]} 的原始数据列名:")
            for key in list(data.keys())[:30]:
                print(f"  - {key}: {str(data[key])[:50]}")

if __name__ == '__main__':
    check_orders()

