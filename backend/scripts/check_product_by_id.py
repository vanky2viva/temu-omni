#!/usr/bin/env python3
"""根据ID查询商品信息"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.product import Product


def check_product(product_id: str):
    """查询商品信息"""
    db = SessionLocal()
    
    try:
        # 尝试作为整数ID查询
        try:
            product = db.query(Product).filter(Product.id == int(product_id)).first()
            if product:
                print(f"✅ 找到商品 (数据库ID: {product.id})")
                print(f"   商品名称: {product.product_name}")
                print(f"   Temu商品ID: {product.product_id or '无'}")
                print(f"   SKU货号: {product.sku or '无'}")
                print(f"   SPU ID: {product.spu_id or '无'}")
                print(f"   状态: {'在售中' if product.is_active else '未发布'}")
                print(f"   供货价: {product.current_price} {product.currency}")
                return
        except ValueError:
            pass
        
        # 尝试作为Temu商品ID查询
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if product:
            print(f"✅ 找到商品 (Temu商品ID: {product.product_id})")
            print(f"   数据库ID: {product.id}")
            print(f"   商品名称: {product.product_name}")
            print(f"   SKU货号: {product.sku or '无'}")
            print(f"   SPU ID: {product.spu_id or '无'}")
            print(f"   状态: {'在售中' if product.is_active else '未发布'}")
            print(f"   供货价: {product.current_price} {product.currency}")
            return
        
        # 尝试作为SPU ID查询
        product = db.query(Product).filter(Product.spu_id == product_id).first()
        if product:
            print(f"✅ 找到商品 (SPU ID: {product.spu_id})")
            print(f"   数据库ID: {product.id}")
            print(f"   商品名称: {product.product_name}")
            print(f"   Temu商品ID: {product.product_id or '无'}")
            print(f"   SKU货号: {product.sku or '无'}")
            print(f"   状态: {'在售中' if product.is_active else '未发布'}")
            print(f"   供货价: {product.current_price} {product.currency}")
            return
        
        # 尝试作为SKU查询
        product = db.query(Product).filter(Product.sku == product_id).first()
        if product:
            print(f"✅ 找到商品 (SKU: {product.sku})")
            print(f"   数据库ID: {product.id}")
            print(f"   商品名称: {product.product_name}")
            print(f"   Temu商品ID: {product.product_id or '无'}")
            print(f"   SPU ID: {product.spu_id or '无'}")
            print(f"   状态: {'在售中' if product.is_active else '未发布'}")
            print(f"   供货价: {product.current_price} {product.currency}")
            return
        
        print(f"❌ 未找到ID为 {product_id} 的商品")
        print()
        print("📋 数据库中所有商品列表:")
        products = db.query(Product).all()
        for p in products:
            print(f"   - 数据库ID: {p.id}, Temu商品ID: {p.product_id}, SPU: {p.spu_id}, SKU: {p.sku or '无'}, 名称: {p.product_name[:50]}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python check_product_by_id.py <商品ID/SPU_ID/SKU>")
        sys.exit(1)
    
    product_id = sys.argv[1]
    check_product(product_id)

