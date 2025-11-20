#!/usr/bin/env python3
"""统计API返回的在售商品数量"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService


async def count_active_products():
    """统计在售商品数量"""
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
        
        total_active = 0
        total_products = 0
        page_number = 1
        page_size = 100
        total_items = 0  # API返回的总数
        
        print("🔄 开始统计在售商品...")
        print("-" * 60)
        
        while page_number <= 20:  # 最多检查20页
            # 获取商品列表
            result = await temu_service.get_products(page_number=page_number, page_size=page_size)
            
            # 解析商品列表
            product_list = result.get('data') or []
            
            # 获取总数（第一次获取）
            if total_items == 0:
                total_items = (
                    result.get('totalCount') or 
                    result.get('totalItemNum') or 
                    result.get('total') or 
                    result.get('totalNum') or
                    0
                )
            
            if not product_list:
                break
            
            # 统计当前页
            page_active = 0
            for product in product_list:
                total_products += 1
                # 检查状态字段（不能使用or，因为0会被当作False）
                skc_site_status = None
                if 'skcSiteStatus' in product:
                    skc_site_status = product.get('skcSiteStatus')
                
                if skc_site_status == 1:
                    page_active += 1
                    total_active += 1
                    # 显示在售商品信息
                    product_id = product.get('productId') or product.get('goodsId') or '未知'
                    product_name = (product.get('productName') or product.get('goodsName') or '未知')[:50]
                    print(f"   在售商品: {product_id} - {product_name}")
            
            print(f"第 {page_number} 页: 总数 {len(product_list)}, 在售 {page_active}, API总数: {total_items}")
            
            # 检查是否还有更多页
            if total_items > 0:
                # 如果已获取的商品数达到总数，停止
                if total_products >= total_items:
                    break
            else:
                # 如果没有总数信息，检查当前页是否小于page_size
                if len(product_list) < page_size:
                    break
            
            page_number += 1
        
        await temu_service.close()
        
        print("-" * 60)
        print(f"📊 统计结果:")
        print(f"   总商品数: {total_products}")
        print(f"   在售商品数: {total_active}")
        print(f"   不在售商品数: {total_products - total_active}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(count_active_products())

