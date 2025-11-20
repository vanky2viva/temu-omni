#!/usr/bin/env python3
"""命令行同步店铺数据（订单和商品）"""
import asyncio
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        root_env = project_root.parent / '.env'
        if root_env.exists():
            load_dotenv(root_env)
except ImportError:
    pass

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.sync_service import SyncService
from loguru import logger


async def sync_shop_cli(shop_id: int = None, shop_name: str = None, full_sync: bool = False, sync_orders: bool = True, sync_products: bool = True):
    """命令行同步店铺数据"""
    db = SessionLocal()
    
    try:
        # 查找店铺
        if shop_id:
            shop = db.query(Shop).filter(Shop.id == shop_id).first()
        elif shop_name:
            shop = db.query(Shop).filter(Shop.shop_name == shop_name).first()
        else:
            print("❌ 请指定店铺ID或店铺名称")
            print("\n可用店铺列表:")
            shops = db.query(Shop).all()
            for s in shops:
                print(f"  - {s.shop_name} (ID: {s.id}, 状态: {'启用' if s.is_active else '禁用'})")
            return
        
        if not shop:
            print(f"❌ 未找到店铺")
            if shop_id:
                print(f"   店铺ID: {shop_id}")
            if shop_name:
                print(f"   店铺名称: {shop_name}")
            print("\n可用店铺列表:")
            shops = db.query(Shop).all()
            for s in shops:
                print(f"  - {s.shop_name} (ID: {s.id}, 状态: {'启用' if s.is_active else '禁用'})")
            return
        
        if not shop.is_active:
            print(f"⚠️  店铺已禁用: {shop.shop_name}")
            print("   如需同步，请先启用店铺")
            return
        
        print("=" * 80)
        print(f"📦 店铺信息:")
        print(f"   店铺名称: {shop.shop_name}")
        print(f"   店铺ID: {shop.id}")
        print(f"   区域: {shop.region}")
        print(f"   环境: {shop.environment}")
        print(f"   Token状态: {'已配置' if shop.access_token else '未配置'}")
        print("=" * 80)
        print(f"🔄 同步选项:")
        print(f"   全量同步: {'是' if full_sync else '否（增量同步）'}")
        print(f"   同步订单: {'是' if sync_orders else '否'}")
        print(f"   同步商品: {'是' if sync_products else '否'}")
        print("=" * 80)
        print()
        
        sync_service = SyncService(db, shop)
        
        # 同步订单
        if sync_orders:
            print("📋 开始同步订单...")
            print("-" * 80)
            try:
                orders_result = await sync_service.sync_orders(full_sync=full_sync)
                print("-" * 80)
                print("✅ 订单同步完成!")
                print(f"   总数: {orders_result.get('total', 0)}")
                print(f"   新增: {orders_result.get('new', 0)}")
                print(f"   更新: {orders_result.get('updated', 0)}")
                print(f"   失败: {orders_result.get('failed', 0)}")
                print()
            except Exception as e:
                print(f"❌ 订单同步失败: {e}")
                import traceback
                traceback.print_exc()
                print()
        
        # 同步商品
        if sync_products:
            print("📦 开始同步商品...")
            print("-" * 80)
            try:
                products_result = await sync_service.sync_products(full_sync=full_sync)
                print("-" * 80)
                print("✅ 商品同步完成!")
                print(f"   总数: {products_result.get('total', 0)}")
                print(f"   新增: {products_result.get('new', 0)}")
                print(f"   更新: {products_result.get('updated', 0)}")
                print(f"   失败: {products_result.get('failed', 0)}")
                if 'active_products' in products_result:
                    print(f"   在售商品: {products_result.get('active_products', 0)}")
                if 'products_with_sku' in products_result:
                    print(f"   有SKU商品: {products_result.get('products_with_sku', 0)}")
                print()
            except Exception as e:
                print(f"❌ 商品同步失败: {e}")
                import traceback
                traceback.print_exc()
                print()
        
        await sync_service.temu_service.close()
        
        print("=" * 80)
        print("🎉 同步任务完成!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="命令行同步店铺数据")
    parser.add_argument(
        "--shop-id",
        type=int,
        help="店铺ID"
    )
    parser.add_argument(
        "--shop-name",
        type=str,
        help="店铺名称"
    )
    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="全量同步（默认：增量同步）"
    )
    parser.add_argument(
        "--orders-only",
        action="store_true",
        help="仅同步订单"
    )
    parser.add_argument(
        "--products-only",
        action="store_true",
        help="仅同步商品"
    )
    
    args = parser.parse_args()
    
    if not args.shop_id and not args.shop_name:
        print("❌ 请指定店铺ID (--shop-id) 或店铺名称 (--shop-name)")
        print("\n示例:")
        print("  python sync_shop_cli.py --shop-id 6")
        print("  python sync_shop_cli.py --shop-name 'echofrog'")
        print("  python sync_shop_cli.py --shop-name 'echofrog' --full-sync")
        print("  python sync_shop_cli.py --shop-id 6 --orders-only")
        print("  python sync_shop_cli.py --shop-id 6 --products-only")
        sys.exit(1)
    
    sync_orders = not args.products_only
    sync_products = not args.orders_only
    
    asyncio.run(sync_shop_cli(
        shop_id=args.shop_id,
        shop_name=args.shop_name,
        full_sync=args.full_sync,
        sync_orders=sync_orders,
        sync_products=sync_products
    ))

