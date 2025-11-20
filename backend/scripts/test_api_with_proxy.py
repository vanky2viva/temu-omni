#!/usr/bin/env python3
"""测试通过代理获取订单列表和商品列表"""
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService

async def test_api_with_proxy():
    """测试通过代理获取订单列表和商品列表"""
    db = SessionLocal()
    try:
        # 获取所有活跃店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 找到 {len(shops)} 个活跃店铺\n")
        
        for shop in shops:
            print(f"\n{'='*80}")
            print(f"店铺: {shop.shop_name} (ID: {shop.id})")
            print(f"区域: {shop.region}")
            print(f"标准 Access Token: {'有' if shop.access_token else '无'}")
            print(f"CN Access Token: {'有' if shop.cn_access_token else '无'}")
            print(f"{'='*80}\n")
            
            try:
                temu_service = TemuService(shop)
                
                # 测试1: 获取订单列表
                print("📦 测试1: 获取订单列表（通过代理）")
                print("-" * 80)
                try:
                    end_time = int(datetime.now().timestamp())
                    begin_time = int((datetime.now() - timedelta(days=7)).timestamp())
                    
                    print(f"时间范围: {datetime.fromtimestamp(begin_time)} ~ {datetime.fromtimestamp(end_time)}")
                    print("正在请求...")
                    
                    orders_result = await temu_service.get_orders(
                        begin_time=begin_time,
                        end_time=end_time,
                        page_number=1,
                        page_size=10
                    )
                    
                    print(f"✅ 订单API调用成功")
                    print(f"响应类型: {type(orders_result)}")
                    
                    if isinstance(orders_result, dict):
                        total_items = orders_result.get('totalItemNum', 0)
                        page_items = orders_result.get('pageItems', [])
                        
                        print(f"订单总数: {total_items}")
                        print(f"当前页订单数: {len(page_items) if isinstance(page_items, list) else 0}")
                        
                        if page_items and len(page_items) > 0:
                            print(f"\n第一个订单示例（前300字符）:")
                            print(json.dumps(page_items[0], ensure_ascii=False, indent=2)[:300])
                            print("...")
                        else:
                            print("⚠️  当前时间段内没有订单")
                    else:
                        print(f"⚠️  响应格式异常: {orders_result}")
                        
                except Exception as e:
                    print(f"❌ 获取订单列表失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                print("\n")
                
                # 测试2: 获取商品列表（CN端点，不通过代理）
                print("📦 测试2: 获取商品列表（CN端点，直接访问，不通过代理）")
                print("-" * 80)
                try:
                    print("正在请求...")
                    
                    products_result = await temu_service.get_products(
                        page_number=1,
                        page_size=10
                    )
                    
                    print(f"✅ 商品API调用成功")
                    print(f"响应类型: {type(products_result)}")
                    
                    if isinstance(products_result, dict):
                        # CN端点使用 data 字段，标准端点可能使用其他字段
                        product_list = (
                            products_result.get('data') or
                            products_result.get('goodsList') or
                            products_result.get('productList') or
                            products_result.get('pageItems') or
                            []
                        )
                        
                        total_items = (
                            products_result.get('totalCount') or
                            products_result.get('totalItemNum') or
                            products_result.get('total') or
                            0
                        )
                        
                        print(f"商品总数: {total_items}")
                        print(f"当前页商品数: {len(product_list) if isinstance(product_list, list) else 0}")
                        
                        if isinstance(product_list, list) and len(product_list) > 0:
                            print(f"\n第一个商品示例（前300字符）:")
                            print(json.dumps(product_list[0], ensure_ascii=False, indent=2)[:300])
                            print("...")
                        else:
                            print("⚠️  没有商品数据")
                    else:
                        print(f"⚠️  响应格式异常: {products_result}")
                        
                except Exception as e:
                    print(f"❌ 获取商品列表失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                await temu_service.close()
                
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n")
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_api_with_proxy())

