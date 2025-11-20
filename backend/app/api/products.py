"""商品管理API"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.product import Product, ProductCost
from app.models.shop import Shop
from app.models.user import User
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductCostCreate, ProductCostResponse, ProductCostUpdate
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    shop_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    manager: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取商品列表"""
    query = db.query(Product)
    
    if shop_id:
        query = query.filter(Product.shop_id == shop_id)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    if manager:
        query = query.filter(Product.manager == manager)
    
    if category:
        query = query.filter(Product.category == category)
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (Product.product_name.like(search_term)) |
            (Product.sku.like(search_term)) |
            (Product.product_id.like(search_term))
        )
    
    products = query.offset(skip).limit(limit).all()
    
    # 为每个商品填充负责人和当前成本价格
    for product in products:
        # 填充负责人（如果商品没有负责人，使用店铺的默认负责人）
        if not product.manager and product.shop:
            product.manager = product.shop.default_manager or ''
        
        # 获取当前有效的成本价格（effective_to为None的记录）
        current_cost = db.query(ProductCost).filter(
            ProductCost.product_id == product.id,
            ProductCost.effective_to.is_(None)
        ).order_by(ProductCost.effective_from.desc()).first()
        
        # 动态添加当前成本价格字段到product对象
        if current_cost:
            product.current_cost_price = current_cost.cost_price
            product.cost_currency = current_cost.currency
        else:
            product.current_cost_price = None
            product.cost_currency = None
    
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取商品详情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 获取当前有效的成本价格
    current_cost = db.query(ProductCost).filter(
        ProductCost.product_id == product.id,
        ProductCost.effective_to.is_(None)
    ).order_by(ProductCost.effective_from.desc()).first()
    
    if current_cost:
        product.current_cost_price = current_cost.cost_price
        product.cost_currency = current_cost.currency
    else:
        product.current_cost_price = None
        product.cost_currency = None
    
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新商品信息"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    update_data = product_update.model_dump(exclude_unset=True)
    # 如果更新了价格，确保货币为CNY
    if 'current_price' in update_data:
        product.currency = 'CNY'
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def get_product_costs(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取商品成本历史"""
    costs = db.query(ProductCost).filter(
        ProductCost.product_id == product_id
    ).order_by(ProductCost.effective_from.desc()).all()
    return costs


@router.post("/costs", response_model=ProductCostResponse, status_code=status.HTTP_201_CREATED)
def create_product_cost(cost: ProductCostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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


@router.put("/{product_id}/cost", response_model=ProductCostResponse)
def update_product_cost(
    product_id: int,
    cost_update: ProductCostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """快速更新商品成本价格（直接更新或创建新的成本记录）"""
    # 检查商品是否存在
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 获取当前有效的成本记录
    current_cost = db.query(ProductCost).filter(
        ProductCost.product_id == product_id,
        ProductCost.effective_to.is_(None)
    ).order_by(ProductCost.effective_from.desc()).first()
    
    now = datetime.utcnow()
    
    # 如果存在当前成本记录且价格相同，直接返回
    if current_cost and current_cost.cost_price == cost_update.cost_price and current_cost.currency == cost_update.currency:
        return current_cost
    
    # 将之前的成本记录设置结束时间
    if current_cost:
        current_cost.effective_to = now
    
    # 创建新的成本记录（确保货币为CNY）
    new_cost = ProductCost(
        product_id=product_id,
        cost_price=cost_update.cost_price,
        currency=cost_update.currency or "CNY",
        effective_from=now
    )
    db.add(new_cost)
    db.commit()
    db.refresh(new_cost)
    return new_cost


@router.delete("/", status_code=status.HTTP_200_OK)
def clear_all_products(
    shop_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清理商品数据
    
    Args:
        shop_id: 可选，如果提供则只清理指定店铺的商品，否则清理所有商品
    """
    try:
        query = db.query(Product)
        
        if shop_id:
            query = query.filter(Product.shop_id == shop_id)
            count = query.count()
            query.delete(synchronize_session=False)
            message = f"已清理店铺 {shop_id} 的 {count} 条商品数据"
        else:
            count = query.count()
            query.delete(synchronize_session=False)
            message = f"已清理所有 {count} 条商品数据"
        
        db.commit()
        
        return {
            "success": True,
            "message": message,
            "deleted_count": count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理商品数据失败: {str(e)}"
        )

