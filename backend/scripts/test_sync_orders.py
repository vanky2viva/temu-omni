#!/usr/bin/env python3
"""测试订单同步功能"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 临时设置代理URL
if not os.getenv('TEMU_API_PROXY_URL'):
    os.environ['TEMU_API_PROXY_URL'] = 'http://172.236.231.45:8001'

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.sync_service import SyncService

async def test_sync_orders():
    """测试订单同步"""
    db = SessionLocal()
    try:
        # 查找"festival finds"店铺
        shop = db.query(Shop).filter(Shop.shop_name.ilike('%festival finds%')).first()
        
        if not shop:
            print("❌ 未找到 'festival finds' 店铺")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name} (ID: {shop.id})")
        print(f"   最后同步时间: {shop.last_sync_at}")
        
        # 创建同步服务
        sync_service = SyncService(db, shop)
        
        print("\n" + "=" * 80)
        print("开始同步订单（全量同步，1年）")
        print("=" * 80)
        
        try:
            # 执行同步
            stats = await sync_service.sync_orders(full_sync=True)
            
            print("\n✅ 同步完成！")
            print(f"\n统计结果:")
            print(f"  总数: {stats.get('total', 0)}")
            print(f"  新增: {stats.get('new', 0)}")
            print(f"  更新: {stats.get('updated', 0)}")
            print(f"  失败: {stats.get('failed', 0)}")
            
            # 检查数据库中的订单数
            from app.models.order import Order
            order_count = db.query(Order).filter(Order.shop_id == shop.id).count()
            print(f"\n数据库中的订单数: {order_count}")
            
            if order_count > 0:
                # 显示最近的订单
                recent_orders = db.query(Order).filter(Order.shop_id == shop.id).order_by(Order.order_time.desc()).limit(5).all()
                print(f"\n最近的订单:")
                for order in recent_orders:
                    print(f"  - {order.order_sn} | {order.order_time} | {order.status}")
            
        except Exception as e:
            print(f"\n❌ 同步失败: {e}")
            import traceback
            traceback.print_exc()
        
        await sync_service.temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_sync_orders())

