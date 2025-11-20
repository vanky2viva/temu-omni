#!/usr/bin/env python3
"""Update Shop ID"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop

def update_shop_id():
    db = SessionLocal()
    try:
        shop = db.query(Shop).filter(Shop.shop_name == "festival finds").first()
        if not shop:
            print("❌ 未找到店铺")
            return
            
        print(f"当前 Shop ID: {shop.shop_id}")
        new_id = "634418224627868"
        shop.shop_id = new_id
        db.commit()
        print(f"✅ Shop ID 已更新为: {new_id}")
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_shop_id()

