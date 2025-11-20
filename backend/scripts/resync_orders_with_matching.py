#!/usr/bin/env python3
"""重新同步订单并匹配商品成本"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.models.order import Order
from app.services.sync_service import SyncService


async def resync_orders(shop_name: str = None, clear_old: bool = False):
    """
    重新同步订单并自动匹配商品成本
    
    Args:
        shop_name: 店铺名称，如果为None则同步所有店铺
        clear_old: 是否清除旧订单数据
    """
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("重新同步订单（自动匹配商品成本）")
        print("=" * 80)
        
        # 查询店铺
        if shop_name:
            shops = db.query(Shop).filter(
                Shop.shop_name == shop_name,
                Shop.is_active == True
            ).all()
            if not shops:
                print(f"❌ 未找到店铺: {shop_name}")
                return
        else:
            shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        print(f"\n找到 {len(shops)} 个启用的店铺\n")
        
        for idx, shop in enumerate(shops, 1):
            print("=" * 80)
            print(f"【{idx}/{len(shops)}】同步店铺: {shop.shop_name} (ID: {shop.id})")
            print("=" * 80)
            
            # 统计旧数据
            old_order_count = db.query(Order).filter(Order.shop_id == shop.id).count()
            print(f"📊 旧订单数: {old_order_count}")
            
            # 清除旧数据（如果指定）
            if clear_old and old_order_count > 0:
                print(f"\n🗑️  清除旧订单数据...")
                deleted = db.query(Order).filter(Order.shop_id == shop.id).delete()
                db.commit()
                print(f"   ✅ 已清除 {deleted} 条旧订单")
            
            # 同步订单
            print(f"\n🔄 开始同步订单...")
            print("-" * 80)
            
            try:
                sync_service = SyncService(db, shop)
                # 全量同步最近90天的订单
                result = await sync_service.sync_orders(full_sync=False)
                await sync_service.temu_service.close()
                
                print("-" * 80)
                print(f"✅ 订单同步完成!")
                print(f"   新增: {result.get('new', 0)}")
                print(f"   更新: {result.get('updated', 0)}")
                print(f"   失败: {result.get('failed', 0)}")
                
                # 统计新数据
                new_order_count = db.query(Order).filter(Order.shop_id == shop.id).count()
                orders_with_cost = db.query(Order).filter(
                    Order.shop_id == shop.id,
                    Order.total_cost.isnot(None)
                ).count()
                
                print(f"\n📊 同步后统计:")
                print(f"   总订单数: {new_order_count}")
                print(f"   有成本信息: {orders_with_cost} ({orders_with_cost/new_order_count*100:.1f}%)" if new_order_count > 0 else "   有成本信息: 0 (0%)")
                
                # 财务统计
                if orders_with_cost > 0:
                    from decimal import Decimal
                    orders = db.query(Order).filter(
                        Order.shop_id == shop.id,
                        Order.total_cost.isnot(None)
                    ).all()
                    
                    total_gmv = sum(order.total_price for order in orders)
                    total_cost = sum(order.total_cost for order in orders)
                    total_profit = sum(order.profit for order in orders if order.profit)
                    profit_margin = (total_profit / total_gmv * 100) if total_gmv > 0 else 0
                    
                    print(f"\n💰 财务统计:")
                    print(f"   GMV（营业额）: {total_gmv:.2f}")
                    print(f"   总成本: {total_cost:.2f}")
                    print(f"   总利润: {total_profit:.2f}")
                    print(f"   利润率: {profit_margin:.2f}%")
                
            except Exception as e:
                print(f"❌ 同步失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 80)
        print("✅ 所有店铺订单同步完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    shop_name = None
    clear_old = False
    
    if len(sys.argv) > 1:
        shop_name = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2].lower() in ['true', '1', 'yes']:
        clear_old = True
    
    print(f"\n参数说明:")
    print(f"  店铺名称: {shop_name or '所有店铺'}")
    print(f"  清除旧数据: {clear_old}")
    print()
    
    asyncio.run(resync_orders(shop_name, clear_old))

