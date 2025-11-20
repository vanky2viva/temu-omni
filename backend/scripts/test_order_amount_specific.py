#!/usr/bin/env python3
"""测试查询指定订单号的订单金额"""
import sys
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        
        print(f"✅ 测试店铺: {shop.shop_name}\n")
        
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
                    'settlementAmount', 'settlement_amount', 'finalAmount', 'final_amount'
                ]
                
                for field in amount_fields:
                    if field in amount_result:
                        print(f"  {field}: {amount_result[field]}")
                
                # 如果有嵌套结构，尝试查找
                for key, value in amount_result.items():
                    if isinstance(value, dict):
                        print(f"\n  {key}:")
                        for sub_key, sub_value in value.items():
                            if 'amount' in sub_key.lower() or 'price' in sub_key.lower() or 'total' in sub_key.lower():
                                print(f"    {sub_key}: {sub_value}")
        
        except Exception as e:
            print(f"❌ 查询订单金额失败: {e}")
            import traceback
            traceback.print_exc()
        
        await temu_service.close()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_order_amount_specific())


