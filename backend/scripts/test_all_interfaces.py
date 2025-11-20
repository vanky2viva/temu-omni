#!/usr/bin/env python3
"""全面测试商品查询接口，尝试获取17个在售商品"""
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


async def test_all_interfaces():
    """测试所有商品查询接口"""
    db = SessionLocal()
    
    try:
        # 查找festival finds店铺
        shop = db.query(Shop).filter(Shop.shop_name == "festival finds").first()
        if not shop:
            print("❌ 未找到festival finds店铺")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name} (ID: {shop.id})")
        print()
        
        # 创建Temu服务
        temu_service = TemuService(shop)
        
        # ========== 测试1: bg.goods.list.get 不带筛选参数 ==========
        print("=" * 80)
        print("📋 测试1: bg.goods.list.get 接口（不带筛选）")
        print("=" * 80)
        
        all_products_set = set()
        active_products_set = set()
        
        try:
            # 只获取前3页，看看分页是否正常
            for page in range(1, 4):
                result = await temu_service.get_products(
                    page_number=page,
                    page_size=20
                )
                
                product_list = result.get('data') or []
                total = result.get('totalCount') or result.get('total') or 0
                
                print(f"\n第 {page} 页:")
                print(f"  API返回总数: {total}")
                print(f"  当前页商品数: {len(product_list)}")
                
                if not product_list:
                    print("  ⚠️  当前页无数据")
                    break
                
                # 统计商品
                for product in product_list:
                    product_id = str(product.get('productId') or product.get('goodsId') or '')
                    product_name = (product.get('productName') or product.get('goodsName') or '未知')[:40]
                    skc_site_status = product.get('skcSiteStatus')
                    
                    all_products_set.add(product_id)
                    
                    if skc_site_status == 1:
                        active_products_set.add(product_id)
                        print(f"  ✅ 在售: {product_id} - {product_name}")
                
                print(f"  累计去重: 总数={len(all_products_set)}, 在售={len(active_products_set)}")
        
        except Exception as e:
            print(f"  ❌ 错误: {e}")
        
        print(f"\n测试1结果: 去重后总数={len(all_products_set)}, 在售={len(active_products_set)}")
        
        # ========== 测试2: bg.goods.list.get 带 skcSiteStatus=1 筛选 ==========
        print("\n" + "=" * 80)
        print("📋 测试2: bg.goods.list.get 接口（带 skcSiteStatus=1 筛选）")
        print("=" * 80)
        
        filtered_products_set = set()
        
        try:
            # 获取前5页
            for page in range(1, 6):
                result = await temu_service.get_products(
                    page_number=page,
                    page_size=20,
                    skc_site_status=1  # 只获取在售商品
                )
                
                product_list = result.get('data') or []
                total = result.get('totalCount') or result.get('total') or 0
                
                print(f"\n第 {page} 页:")
                print(f"  API返回总数: {total}")
                print(f"  当前页商品数: {len(product_list)}")
                
                if not product_list:
                    print("  ⚠️  当前页无数据")
                    break
                
                # 统计商品
                page_active = 0
                for product in product_list:
                    product_id = str(product.get('productId') or product.get('goodsId') or '')
                    product_name = (product.get('productName') or product.get('goodsName') or '未知')[:40]
                    skc_site_status = product.get('skcSiteStatus')
                    
                    filtered_products_set.add(product_id)
                    
                    if skc_site_status == 1:
                        page_active += 1
                        print(f"  ✅ {product_id} - {product_name} (状态: {skc_site_status})")
                    else:
                        print(f"  ⚠️  {product_id} - {product_name} (状态: {skc_site_status}) <- 不是在售状态!")
                
                print(f"  当前页在售: {page_active}/{len(product_list)}")
                print(f"  累计去重: {len(filtered_products_set)}")
        
        except Exception as e:
            print(f"  ❌ 错误: {e}")
        
        print(f"\n测试2结果: 去重后总数={len(filtered_products_set)}")
        
        # ========== 测试3: 尝试直接调用API获取更多商品 ==========
        print("\n" + "=" * 80)
        print("📋 测试3: 尝试使用不同的pageSize")
        print("=" * 80)
        
        large_page_products = set()
        
        try:
            # 尝试一次性获取100个商品
            result = await temu_service.get_products(
                page_number=1,
                page_size=100
            )
            
            product_list = result.get('data') or []
            total = result.get('totalCount') or result.get('total') or 0
            
            print(f"\n使用 pageSize=100:")
            print(f"  API返回总数: {total}")
            print(f"  实际返回商品数: {len(product_list)}")
            
            active_count = 0
            for product in product_list:
                product_id = str(product.get('productId') or product.get('goodsId') or '')
                skc_site_status = product.get('skcSiteStatus')
                
                large_page_products.add(product_id)
                
                if skc_site_status == 1:
                    active_count += 1
            
            print(f"  去重后总数: {len(large_page_products)}")
            print(f"  在售商品数: {active_count}")
        
        except Exception as e:
            print(f"  ❌ 错误: {e}")
        
        await temu_service.close()
        
        # ========== 最终统计 ==========
        print("\n" + "=" * 80)
        print("📊 最终统计结果:")
        print("=" * 80)
        print(f"测试1 (不筛选): 去重后总数={len(all_products_set)}, 在售={len(active_products_set)}")
        print(f"测试2 (筛选): 去重后总数={len(filtered_products_set)}")
        print(f"测试3 (大pageSize): 去重后总数={len(large_page_products)}")
        print()
        print(f"预期应该有 17 个在售商品")
        print()
        
        if len(active_products_set) > 0:
            print("在售商品列表 (测试1):")
            for idx, product_id in enumerate(sorted(active_products_set), 1):
                print(f"  {idx}. {product_id}")
        
        # 分析问题
        print("\n" + "=" * 80)
        print("🔍 问题分析:")
        print("=" * 80)
        if len(all_products_set) < 17:
            print("⚠️  去重后的商品总数少于17个，可能是分页功能异常")
            print("   建议：检查API的分页参数是否正确，或联系API支持")
        
        if len(active_products_set) < 17:
            print(f"⚠️  在售商品数 ({len(active_products_set)}) 少于预期 (17)")
            print("   可能原因：")
            print("   1. 实际在售商品数少于17个")
            print("   2. API返回的数据不完整")
            print("   3. 分类或筛选条件限制了结果")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_all_interfaces())

