#!/usr/bin/env python3
"""测试获取商品列表"""
import sys
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService

async def test_get_products():
    """测试获取商品列表"""
    db = SessionLocal()
    try:
        # 获取所有店铺
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        
        if not shops:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 找到 {len(shops)} 个活跃店铺\n")
        
        for shop in shops:
            print(f"\n{'='*60}")
            print(f"店铺: {shop.shop_name} (ID: {shop.id})")
            print(f"区域: {shop.region}")
            print(f"Access Token: {'有' if shop.access_token else '无'}")
            print(f"CN Access Token: {'有' if shop.cn_access_token else '无'}")
            print(f"{'='*60}\n")
            
            try:
                # 创建TemuService（需要先创建SyncService）
                from app.services.sync_service import SyncService
                sync_service = SyncService(db, shop)
                temu_service = sync_service.temu_service
                
                # 获取商品列表（第一页，每页10条）
                print(f"正在获取商品列表（第1页，每页10条）...")
                products_response = await temu_service.get_products(
                    page_number=1,
                    page_size=10
                )
                
                # 打印响应结构
                print(f"\n✅ API响应类型: {type(products_response)}")
                print(f"✅ API响应内容（前500字符）:")
                response_str = json.dumps(products_response, ensure_ascii=False, indent=2)
                print(response_str[:500])
                if len(response_str) > 500:
                    print("...")
                
                # 检查响应结构
                if isinstance(products_response, dict):
                    # 检查是否有商品列表
                    goods_list = products_response.get('goodsList') or products_response.get('goods_list') or products_response.get('data') or products_response.get('result')
                    
                    if goods_list:
                        print(f"\n✅ 找到商品列表，数量: {len(goods_list) if isinstance(goods_list, list) else 'N/A'}")
                        
                        if isinstance(goods_list, list) and len(goods_list) > 0:
                            print(f"\n第一个商品示例:")
                            first_product = goods_list[0]
                            print(json.dumps(first_product, ensure_ascii=False, indent=2)[:500])
                    else:
                        print(f"\n⚠️  响应中没有找到商品列表字段")
                        print(f"响应键: {list(products_response.keys())}")
                        
                        # 检查是否有错误信息
                        if 'errorCode' in products_response or 'error' in products_response:
                            print(f"\n❌ API返回错误:")
                            print(json.dumps(products_response, ensure_ascii=False, indent=2))
                else:
                    print(f"\n⚠️  响应不是字典类型: {type(products_response)}")
                
                await temu_service.close()
                
            except Exception as e:
                print(f"\n❌ 获取商品列表失败: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n")
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_get_products())

