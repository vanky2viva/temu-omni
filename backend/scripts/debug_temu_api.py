#!/usr/bin/env python3
"""Debug Token Info and Test Pagination"""
import asyncio
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService
from app.temu.client import TemuAPIClient
from app.core.config import settings

async def debug_token_and_api():
    db = SessionLocal()
    try:
        # 查找festival finds店铺
        shop = db.query(Shop).filter(Shop.shop_name == "festival finds").first()
        if not shop:
            print("❌ 未找到festival finds店铺")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name}")
        print(f"   Shop ID (DB): {shop.shop_id}")
        print(f"   Has CN Access Token: {bool(shop.cn_access_token)}")
        print("-" * 60)
        
        if not shop.cn_access_token:
            print("❌ 没有 CN Access Token，无法测试 CN 接口")
            return

        # 配置 CN Client
        cn_app_key = shop.cn_app_key or settings.TEMU_CN_APP_KEY
        cn_app_secret = shop.cn_app_secret or settings.TEMU_CN_APP_SECRET
        cn_access_token = shop.cn_access_token
        
        client = TemuAPIClient(
            app_key=cn_app_key,
            app_secret=cn_app_secret,
            proxy_url=""
        )
        client.base_url = shop.cn_api_base_url or 'https://openapi.kuajingmaihuo.com/openapi/router'
        
        # 1. 获取 Token 信息
        print("\n🔍 1. 获取 Token 信息 (bg.open.accesstoken.info.get)...")
        try:
            token_info = await client.get_token_info(cn_access_token)
            print("✅ Token Info:")
            print(json.dumps(token_info, indent=2, ensure_ascii=False))
            
            real_mall_id = token_info.get('mallId')
            print(f"👉 获取到的 Mall ID: {real_mall_id}")
            
            # 如果拿到了 Mall ID，尝试 bg.product.search
            if real_mall_id:
                print(f"\n🔍 2. 尝试使用 Mall ID ({real_mall_id}) 调用 bg.product.search...")
                search_req = {
                    "mallId": int(real_mall_id),
                    "pageNum": 1,
                    "pageSize": 20
                }
                try:
                    search_res = await client._request("bg.product.search", search_req, cn_access_token)
                    print("✅ bg.product.search 成功:")
                    total = search_res.get('total', 0)
                    data_list = search_res.get('dataList', [])
                    print(f"   Total: {total}")
                    print(f"   Data Count: {len(data_list)}")
                    
                    # 统计在售
                    active_count = 0
                    for item in data_list:
                        if item.get('selectStatus') == 1:
                            active_count += 1
                    print(f"   Active Count (selectStatus=1): {active_count}")
                    
                except Exception as e:
                    print(f"❌ bg.product.search 失败: {e}")
            
        except Exception as e:
            print(f"❌ 获取 Token 信息失败: {e}")
            
        # 2. 测试 bg.goods.list.get 分页参数
        print(f"\n🔍 3. 测试 bg.goods.list.get 分页参数...")
        
        async def test_list(param_name_page, param_name_size):
            print(f"\n   👉 测试参数名: {param_name_page}, {param_name_size}")
            
            # page 1
            req1 = {param_name_page: 1, param_name_size: 10}
            res1 = await client._request("bg.goods.list.get", req1, cn_access_token)
            list1 = res1.get('data', [])
            ids1 = [item.get('productId') or item.get('goodsId') for item in list1]
            print(f"      Page 1 IDs: {ids1[:3]}...")
            
            # page 2
            req2 = {param_name_page: 2, param_name_size: 10}
            res2 = await client._request("bg.goods.list.get", req2, cn_access_token)
            list2 = res2.get('data', [])
            ids2 = [item.get('productId') or item.get('goodsId') for item in list2]
            print(f"      Page 2 IDs: {ids2[:3]}...")
            
            if ids1 and ids2 and ids1[0] == ids2[0]:
                print("      ⚠️ 分页无效 (数据相同)")
            else:
                print("      ✅ 分页生效 (数据不同)")

        await test_list("pageNumber", "pageSize")
        await test_list("page", "pageSize")
        await test_list("pageNum", "pageSize")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ 发生未捕获异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_token_and_api())

