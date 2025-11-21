"""原始数据查询API

提供查询原始数据（raw表）的接口，供AI服务和其他场景使用。
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.temu_orders_raw import TemuOrdersRaw
from app.models.temu_products_raw import TemuProductsRaw
from app.models.shop import Shop

router = APIRouter(prefix="/raw-data", tags=["原始数据"])


@router.get("/orders/{external_order_id}")
def get_order_raw_data(
    external_order_id: str,
    shop_id: Optional[int] = Query(None, description="店铺ID（可选，用于权限验证）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单原始数据
    
    Args:
        external_order_id: Temu订单号
        shop_id: 店铺ID（可选）
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        订单原始数据（JSON格式）
    """
    query = db.query(TemuOrdersRaw).filter(
        TemuOrdersRaw.external_order_id == external_order_id
    )
    
    # 如果指定了shop_id，进行权限验证
    if shop_id:
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(status_code=404, detail="店铺不存在")
        query = query.filter(TemuOrdersRaw.shop_id == shop_id)
    
    raw_order = query.first()
    
    if not raw_order:
        raise HTTPException(status_code=404, detail="订单原始数据不存在")
    
    return {
        "id": raw_order.id,
        "shop_id": raw_order.shop_id,
        "external_order_id": raw_order.external_order_id,
        "raw_json": raw_order.raw_json,
        "fetched_at": raw_order.fetched_at.isoformat() if raw_order.fetched_at else None,
        "created_at": raw_order.created_at.isoformat() if raw_order.created_at else None,
    }


@router.get("/products/{external_product_id}")
def get_product_raw_data(
    external_product_id: str,
    shop_id: Optional[int] = Query(None, description="店铺ID（可选，用于权限验证）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取商品原始数据
    
    Args:
        external_product_id: Temu商品ID
        shop_id: 店铺ID（可选）
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        商品原始数据（JSON格式）
    """
    query = db.query(TemuProductsRaw).filter(
        TemuProductsRaw.external_product_id == external_product_id
    )
    
    # 如果指定了shop_id，进行权限验证
    if shop_id:
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(status_code=404, detail="店铺不存在")
        query = query.filter(TemuProductsRaw.shop_id == shop_id)
    
    raw_product = query.first()
    
    if not raw_product:
        raise HTTPException(status_code=404, detail="商品原始数据不存在")
    
    return {
        "id": raw_product.id,
        "shop_id": raw_product.shop_id,
        "external_product_id": raw_product.external_product_id,
        "raw_json": raw_product.raw_json,
        "fetched_at": raw_product.fetched_at.isoformat() if raw_product.fetched_at else None,
        "created_at": raw_product.created_at.isoformat() if raw_product.created_at else None,
    }


@router.post("/batch")
def get_batch_raw_data(
    order_ids: Optional[List[str]] = Query(None, description="订单ID列表"),
    product_ids: Optional[List[str]] = Query(None, description="商品ID列表"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表（用于过滤）"),
    limit: int = Query(100, ge=1, le=1000, description="最大返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量获取原始数据
    
    供AI服务和其他需要批量原始数据的场景使用。
    
    Args:
        order_ids: 订单ID列表
        product_ids: 商品ID列表
        shop_ids: 店铺ID列表（用于过滤）
        limit: 最大返回数量
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        批量原始数据
    """
    result = {
        "orders": [],
        "products": [],
        "total": 0
    }
    
    # 查询订单原始数据
    if order_ids:
        query = db.query(TemuOrdersRaw).filter(
            TemuOrdersRaw.external_order_id.in_(order_ids[:limit])
        )
        if shop_ids:
            query = query.filter(TemuOrdersRaw.shop_id.in_(shop_ids))
        
        raw_orders = query.limit(limit).all()
        result["orders"] = [
            {
                "id": ro.id,
                "shop_id": ro.shop_id,
                "external_order_id": ro.external_order_id,
                "raw_json": ro.raw_json,
                "fetched_at": ro.fetched_at.isoformat() if ro.fetched_at else None,
            }
            for ro in raw_orders
        ]
        result["total"] += len(raw_orders)
    
    # 查询商品原始数据
    if product_ids:
        query = db.query(TemuProductsRaw).filter(
            TemuProductsRaw.external_product_id.in_(product_ids[:limit])
        )
        if shop_ids:
            query = query.filter(TemuProductsRaw.shop_id.in_(shop_ids))
        
        raw_products = query.limit(limit).all()
        result["products"] = [
            {
                "id": rp.id,
                "shop_id": rp.shop_id,
                "external_product_id": rp.external_product_id,
                "raw_json": rp.raw_json,
                "fetched_at": rp.fetched_at.isoformat() if rp.fetched_at else None,
            }
            for rp in raw_products
        ]
        result["total"] += len(raw_products)
    
    return result

