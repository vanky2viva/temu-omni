#!/usr/bin/env python3
"""测试CN端点是否可以直接访问（不通过代理）"""
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

async def test_cn_direct():
    """测试CN端点是否可以直接访问"""
    db = SessionLocal()
    try:
        # 获取所有活跃店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 找到 {len(shops)} 个活跃店铺\n")
        
        for shop in shops:
            if not shop.cn_access_token:
                print(f"⚠️  店铺 {shop.shop_name} 没有配置 CN Access Token，跳过")
                continue
                
            print(f"\n{'='*80}")
            print(f"店铺: {shop.shop_name} (ID: {shop.id})")
            print(f"区域: {shop.region}")
            print(f"CN Access Token: {'有' if shop.cn_access_token else '无'}")
            print(f"{'='*80}\n")
            
            try:
                temu_service = TemuService(shop)
                
                # 测试: 获取商品列表（CN端点，不通过代理）
                print("📦 测试: 获取商品列表（CN端点，直接访问，不通过代理）")
                print("-" * 80)
                try:
                    print("正在请求...")
                    
                    products_result = await temu_service.get_products(
                        page_number=1,
                        page_size=10
                    )
                    
                    print(f"✅ 商品API调用成功（直接访问）")
                    print(f"响应类型: {type(products_result)}")
                    
                    if isinstance(products_result, dict):
                        # CN端点使用 data 字段
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
    asyncio.run(test_cn_direct())

