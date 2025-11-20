#!/usr/bin/env python3
"""测试查询指定订单号的订单金额（临时设置代理）"""
import sys
import os
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 临时设置代理URL（如果环境变量中没有）
if not os.getenv('TEMU_API_PROXY_URL'):
    os.environ['TEMU_API_PROXY_URL'] = 'http://172.236.231.45:8001'

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.services.temu_service import TemuService

async def test_order_amount_specific():
    """测试查询指定订单号的订单金额"""
    db = SessionLocal()
    try:
        # 获取活跃店铺
        shop = db.query(Shop).filter(Shop.is_active == True).first()
        if not shop:
            print("❌ 没有找到活跃的店铺")
            return
        
        print(f"✅ 测试店铺: {shop.shop_name}")
        print(f"✅ 代理服务器: {os.getenv('TEMU_API_PROXY_URL')}\n")
        
        temu_service = TemuService(shop)
        
        # 要查询的订单号
        order_sn = "PO-211-02732691354231486"
        
        print("=" * 80)
        print(f"查询订单金额 - 订单号: {order_sn}")
        print("=" * 80)
        
        try:
            amount_result = await temu_service.get_order_amount(order_sn)
            
            print(f"✅ 查询成功\n")
            print("响应数据:")
            print(json.dumps(amount_result, ensure_ascii=False, indent=2))
            
            # 尝试提取关键信息
            if isinstance(amount_result, dict):
                print("\n" + "=" * 80)
                print("关键信息提取:")
                print("=" * 80)
                
                # 常见的金额字段
                amount_fields = [
                    'amount', 'totalAmount', 'total_amount', 'orderAmount', 'order_amount',
                    'paidAmount', 'paid_amount', 'transactionAmount', 'transaction_amount',
                    'settlementAmount', 'settlement_amount', 'finalAmount', 'final_amount',
                    'goodsAmount', 'goods_amount', 'shippingAmount', 'shipping_amount',
                    'discountAmount', 'discount_amount', 'taxAmount', 'tax_amount'
                ]
                
                found_fields = []
                for field in amount_fields:
                    if field in amount_result:
                        found_fields.append(field)
                        print(f"  {field}: {amount_result[field]}")
                
                # 如果有嵌套结构，尝试查找
                for key, value in amount_result.items():
                    if isinstance(value, dict):
                        print(f"\n  {key}:")
                        for sub_key, sub_value in value.items():
                            if any(keyword in sub_key.lower() for keyword in ['amount', 'price', 'total', 'cost', 'fee']):
                                print(f"    {sub_key}: {sub_value}")
                    elif isinstance(value, list):
                        print(f"\n  {key} (列表，共 {len(value)} 项):")
                        for idx, item in enumerate(value[:3]):  # 只显示前3项
                            if isinstance(item, dict):
                                print(f"    [{idx}]:")
                                for sub_key, sub_value in item.items():
                                    if any(keyword in sub_key.lower() for keyword in ['amount', 'price', 'total', 'cost', 'fee']):
                                        print(f"      {sub_key}: {sub_value}")
                
                if not found_fields:
                    print("  ⚠️  未找到常见的金额字段，请查看上面的完整响应数据")
        
        except Exception as e:
            print(f"❌ 查询订单金额失败: {e}")
            import traceback
            traceback.print_exc()
        
        await temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_order_amount_specific())


