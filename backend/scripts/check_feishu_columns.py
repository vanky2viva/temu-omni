#!/usr/bin/env python3
"""检查飞书表格列名的脚本"""
import sys
import os
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.feishu_sheets_service import FeishuSheetsService


async def check_columns():
    """检查飞书表格的列名"""
    url = "https://mcnkufobiqbi.feishu.cn/sheets/F3UVshBvXhG9RZt9VgtctDeNngM"
    
    print("=" * 60)
    print("正在读取飞书表格以检查列名...")
    print("=" * 60)
    print(f"表格URL: {url}")
    print()
    
    try:
        service = FeishuSheetsService()
        df = await service.read_sheet_from_url(url)
        
        print(f"成功读取表格，共 {len(df)} 行")
        print(f"\n所有列名:")
        print("-" * 60)
        for i, col in enumerate(df.columns, 1):
            print(f"{i}. {col}")
        
        print("\n" + "=" * 60)
        print("前5行数据预览（仅显示申报价格相关的列）:")
        print("=" * 60)
        
        # 查找与价格状态相关的列
        price_related_cols = [col for col in df.columns if '价格' in col or '状态' in col or '申报' in col]
        
        if price_related_cols:
            print(f"\n找到 {len(price_related_cols)} 个与价格相关的列:")
            for col in price_related_cols:
                print(f"  - {col}")
            print(f"\n这些列的前5行数据:")
            print(df[price_related_cols].head().to_string())
        else:
            print("\n未找到明显的价格相关列，显示所有列的前5行:")
            print(df.head().to_string())
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_columns())

