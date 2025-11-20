#!/usr/bin/env python3
"""测试 bg.product.search 接口"""
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


async def test_product_search():
    """测试查询货品生命周期状态"""
    db = SessionLocal()
    
    try:
        # 查找festival finds店铺
        shop = db.query(Shop).filter(Shop.shop_name == "festival finds").first()
        if not shop:
            print("❌ 未找到festival finds店铺")
            return
        
        print(f"✅ 找到店铺: {shop.shop_name} (ID: {shop.id})")
        print(f"   店铺ID (mallId): {shop.shop_id}")
        print()
        
        # 创建Temu服务
        temu_service = TemuService(shop)
        
        print("🔍 开始查询货品生命周期状态...")
        print("=" * 80)
        
        # 查询第一页
        page_number = 1
        page_size = 100
        total_active = 0
        total_products = 0
        
        while page_number <= 10:
            result = await temu_service.search_products(
                page_number=page_number,
                page_size=page_size
            )
            
            # 解析返回数据
            total = result.get('total', 0)
            data_list = result.get('dataList', [])
            
            if not data_list:
                print(f"第 {page_number} 页: 无数据")
                break
            
            print(f"\n📄 第 {page_number} 页:")
            print(f"   API返回总数: {total}")
            print(f"   当前页数据数: {len(data_list)}")
            print("-" * 80)
            
            # 处理每个货品
            page_active = 0
            for item in data_list:
                total_products += 1
                
                # 显示基本信息
                product_id = item.get('productId') or item.get('id') or '未知'
                product_name = item.get('productName') or item.get('name') or '未知'
                
                # 检查选品状态（selectStatus）
                select_status = item.get('selectStatus')
                
                # 检查skcList
                skc_list = item.get('skcList', [])
                
                # 判断是否在售（根据selectStatus，通常1表示在售）
                is_active = select_status == 1 if select_status is not None else False
                
                if is_active:
                    page_active += 1
                    total_active += 1
                    print(f"   ✅ 在售商品: {product_id} - {product_name[:50]}")
                    print(f"      选品状态: {select_status}")
                    print(f"      SKC数量: {len(skc_list)}")
                    
                    # 显示前3个SKC信息
                    for idx, skc in enumerate(skc_list[:3], 1):
                        skc_id = skc.get('skcId')
                        print(f"      SKC {idx}: ID={skc_id}")
                else:
                    print(f"   ⏸️  非在售: {product_id} - {product_name[:50]} (状态: {select_status})")
            
            print(f"\n   第 {page_number} 页统计: 总数 {len(data_list)}, 在售 {page_active}")
            
            # 检查是否还有更多页
            if total > 0:
                if total_products >= total:
                    break
            else:
                if len(data_list) < page_size:
                    break
            
            page_number += 1
        
        await temu_service.close()
        
        print("\n" + "=" * 80)
        print(f"📊 统计结果:")
        print(f"   总货品数: {total_products}")
        print(f"   在售货品数: {total_active}")
        print(f"   不在售货品数: {total_products - total_active}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_product_search())

