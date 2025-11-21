#!/usr/bin/env python3
"""批量获取订单地址信息并更新到数据库"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量（必须在导入任何使用配置的模块之前）
from app.core.env_loader import load_env_file
import os

# 加载 .env 文件
env_file = load_env_file()
if env_file:
    print(f"✅ 已加载 .env 文件: {env_file}")
else:
    print("⚠️  未找到 .env 文件，将使用系统环境变量")

# 获取项目根目录（用于错误提示）
root_dir = project_root.parent if project_root.name == 'backend' else project_root

# 现在导入使用配置的模块（配置类会从环境变量读取）
from app.core.database import SessionLocal
from app.models.order import Order
from app.models.shop import Shop
from app.services.temu_service import get_temu_service
from loguru import logger

# 强制重新初始化配置对象（确保使用最新的环境变量）
from app.core.config import Settings
import app.core.config as config_module
config_module.settings = Settings()

async def fetch_order_addresses(shop_id: int = None, limit: int = None):
    """批量获取订单地址信息"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("开始批量获取订单地址信息...")
        print("=" * 80)
        
        # 验证代理配置
        from app.core.config import settings
        if not settings.TEMU_API_PROXY_URL:
            print("\n❌ 错误: TEMU_API_PROXY_URL 未配置")
            print(f"   请在项目根目录的 .env 文件中添加: TEMU_API_PROXY_URL=http://your-proxy:port")
            print(f"   配置文件路径: {root_dir / '.env'}")
            return
        
        # 获取所有店铺或指定店铺
        if shop_id:
            shops = db.query(Shop).filter(Shop.id == shop_id).all()
        else:
            shops = db.query(Shop).filter(Shop.access_token.isnot(None)).all()
        
        if not shops:
            print("❌ 没有找到配置了access_token的店铺")
            return
        
        total_updated = 0
        total_errors = 0
        
        for shop in shops:
            print(f"\n📦 处理店铺: {shop.shop_name} (ID: {shop.id})")
            
            # 获取该店铺下没有地址信息的订单
            query = db.query(Order).filter(
                Order.shop_id == shop.id,
                Order.parent_order_sn.isnot(None)
            )
            
            # 只处理没有地址信息的订单
            orders_without_address = query.filter(
                (Order.shipping_province.is_(None)) | (Order.shipping_city.is_(None))
            ).all()
            
            if limit:
                orders_without_address = orders_without_address[:limit]
            
            print(f"   找到 {len(orders_without_address)} 个需要获取地址的订单")
            
            if not orders_without_address:
                continue
            
            # 使用和订单同步相同的方式获取Temu服务
            try:
                temu_service = get_temu_service(shop)
                standard_client = temu_service._get_standard_client()
                access_token = temu_service.access_token
            except ValueError as e:
                error_msg = str(e)
                if "代理服务器未配置" in error_msg:
                    print(f"   ❌ {error_msg}")
                    print(f"   💡 提示: 请在项目根目录的 .env 文件中添加: TEMU_API_PROXY_URL=http://your-proxy:port")
                    print(f"   配置文件路径: {root_dir / '.env'}")
                else:
                    print(f"   ❌ 无法创建Temu服务: {e}")
                continue
            except Exception as e:
                print(f"   ❌ 无法创建Temu服务: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            # 按父订单号分组（同一个父订单只需要调用一次API）
            parent_order_sns = {}
            for order in orders_without_address:
                if order.parent_order_sn:
                    if order.parent_order_sn not in parent_order_sns:
                        parent_order_sns[order.parent_order_sn] = []
                    parent_order_sns[order.parent_order_sn].append(order)
            
            print(f"   需要调用 {len(parent_order_sns)} 次API（按父订单分组）")
            
            updated_count = 0
            error_count = 0
            
            for idx, (parent_order_sn, orders) in enumerate(parent_order_sns.items(), 1):
                try:
                    # 调用 bg.order.shippinginfo.v2.get API
                    request_data = {
                        "parentOrderSn": parent_order_sn
                    }
                    
                    try:
                        # _request 方法返回的是 result 部分，如果失败会抛出异常
                        shipping_info = await standard_client._request(
                            api_type="bg.order.shippinginfo.v2.get",
                            request_data=request_data,
                            access_token=access_token
                        )
                    except Exception as e:
                        print(f"   ⚠️  订单 {parent_order_sn} 获取地址失败: {e}")
                        error_count += 1
                        continue
                    
                    if not shipping_info:
                        print(f"   ⚠️  订单 {parent_order_sn} 返回空地址信息")
                        error_count += 1
                        continue
                    
                    # 提取地址信息
                    region_name2 = shipping_info.get('regionName2', '')  # 省/州
                    region_name3 = shipping_info.get('regionName3', '')  # 市
                    region_name1 = shipping_info.get('regionName1', '')  # 国家
                    post_code = shipping_info.get('postCode', '')  # 邮编
                    
                    # 更新所有属于该父订单的订单记录
                    for order in orders:
                        if region_name2:
                            order.shipping_province = region_name2
                        if region_name3:
                            order.shipping_city = region_name3
                        if region_name1:
                            order.shipping_country = region_name1
                        if post_code:
                            order.shipping_postal_code = post_code
                    
                    updated_count += len(orders)
                    
                    if idx % 50 == 0:
                        db.commit()
                        print(f"   已处理 {idx}/{len(parent_order_sns)} 个父订单，更新了 {updated_count} 个订单...")
                    
                except Exception as e:
                    logger.error(f"获取订单 {parent_order_sn} 地址失败: {e}")
                    error_count += 1
                    continue
            
            # 提交剩余的更新
            if updated_count > 0:
                db.commit()
            
            print(f"   ✅ 店铺 {shop.shop_name}: 更新了 {updated_count} 个订单，失败 {error_count} 个")
            total_updated += updated_count
            total_errors += error_count
            
            # 关闭客户端
            await standard_client.close()
        
        print("\n" + "=" * 80)
        print(f"✅ 批量获取完成！")
        print(f"   - 总共更新: {total_updated} 个订单")
        print(f"   - 失败: {total_errors} 个")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 批量获取失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='批量获取订单地址信息')
    parser.add_argument('--shop-id', type=int, help='指定店铺ID（可选）')
    parser.add_argument('--limit', type=int, help='限制处理的订单数量（可选）')
    args = parser.parse_args()
    
    asyncio.run(fetch_order_addresses(shop_id=args.shop_id, limit=args.limit))

