"""商品管理API"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product, ProductCost
from app.models.shop import Shop
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductCostCreate, ProductCostResponse
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    shop_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取商品列表"""
    query = db.query(Product)
    
    if shop_id:
        query = query.filter(Product.shop_id == shop_id)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    products = query.offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """获取商品详情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """创建商品"""
    data = product.model_dump()
    # 若未指定负责人，则使用店铺默认负责人
    if not data.get('manager'):
        shop = db.query(Shop).filter(Shop.id == data['shop_id']).first()
        if shop and getattr(shop, 'default_manager', None):
            data['manager'] = shop.default_manager
    db_product = Product(**data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """更新商品信息"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除商品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    db.delete(product)
    db.commit()
    return None


# 商品成本管理
@router.get("/{product_id}/costs", response_model=List[ProductCostResponse])
def get_product_costs(product_id: int, db: Session = Depends(get_db)):
    """获取商品成本历史"""
    costs = db.query(ProductCost).filter(
        ProductCost.product_id == product_id
    ).order_by(ProductCost.effective_from.desc()).all()
    return costs


@router.post("/costs", response_model=ProductCostResponse, status_code=status.HTTP_201_CREATED)
def create_product_cost(cost: ProductCostCreate, db: Session = Depends(get_db)):
    """添加商品成本记录"""
    # 检查商品是否存在
    product = db.query(Product).filter(Product.id == cost.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 将之前的成本记录设置结束时间
    previous_costs = db.query(ProductCost).filter(
        ProductCost.product_id == cost.product_id,
        ProductCost.effective_to.is_(None)
    ).all()
    
    for prev_cost in previous_costs:
        prev_cost.effective_to = cost.effective_from
    
    # 创建新成本记录
    db_cost = ProductCost(**cost.model_dump())
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

