"""数据同步API"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.shop import Shop
from app.models.user import User
from app.services.sync_service import sync_shop_data, sync_all_shops
from app.services.temu_service import get_temu_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/shops/{shop_id}/verify-token")
async def verify_shop_token(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证店铺Token
    
    测试店铺的API配置是否正确
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    try:
        temu_service = get_temu_service(shop)
        token_info = await temu_service.verify_token()
        await temu_service.close()
        
        return {
            "success": True,
            "message": "Token验证成功",
            "data": {
                "mall_id": token_info.get('mallId'),
                "region_id": token_info.get('regionId'),
                "expires_at": token_info.get('expiredTime'),
                "api_count": len(token_info.get('apiScopeList', [])),
                "environment": shop.environment.value,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token验证失败: {str(e)}"
        )


@router.post("/shops/{shop_id}/orders")
async def sync_shop_orders(
    shop_id: int,
    full_sync: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步指定店铺的订单数据
    
    Args:
        shop_id: 店铺ID
        full_sync: 是否全量同步（默认同步最近7天，全量同步最近30天）
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    if not shop.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺已禁用"
        )
    
    try:
        from app.services.sync_service import SyncService
        
        sync_service = SyncService(db, shop)
        result = await sync_service.sync_orders(full_sync=full_sync)
        await sync_service.temu_service.close()
        
        return {
            "success": True,
            "message": f"订单同步完成",
            "data": {
                "shop_id": shop_id,
                "shop_name": shop.shop_name,
                "environment": shop.environment.value,
                "stats": result
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订单同步失败: {str(e)}"
        )


@router.post("/shops/{shop_id}/products")
async def sync_shop_products(
    shop_id: int,
    full_sync: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步指定店铺的商品数据
    
    Args:
        shop_id: 店铺ID
        full_sync: 是否全量同步
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    if not shop.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺已禁用"
        )
    
    try:
        from app.services.sync_service import SyncService
        
        sync_service = SyncService(db, shop)
        result = await sync_service.sync_products(full_sync=full_sync)
        await sync_service.temu_service.close()
        
        return {
            "success": True,
            "message": "商品同步完成",
            "data": {
                "shop_id": shop_id,
                "shop_name": shop.shop_name,
                "environment": shop.environment.value,
                "stats": result
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"商品同步失败: {str(e)}"
        )


@router.post("/shops/{shop_id}/all")
async def sync_shop_all_data(
    shop_id: int,
    full_sync: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步指定店铺的所有数据（订单+商品+分类）
    
    Args:
        shop_id: 店铺ID
        full_sync: 是否全量同步
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    if not shop.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺已禁用"
        )
    
    try:
        result = await sync_shop_data(db, shop_id, full_sync=full_sync)
        
        return {
            "success": True,
            "message": "数据同步完成",
            "data": {
                "shop_id": shop_id,
                "shop_name": shop.shop_name,
                "environment": shop.environment.value,
                "region": shop.region.value,
                "results": result
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据同步失败: {str(e)}"
        )


@router.post("/all-shops")
async def sync_all_shops_data(
    full_sync: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步所有启用店铺的数据
    
    Args:
        full_sync: 是否全量同步
    """
    try:
        results = await sync_all_shops(db, full_sync=full_sync)
        
        # 统计
        success_count = sum(1 for r in results.values() if 'error' not in r)
        failed_count = len(results) - success_count
        
        return {
            "success": True,
            "message": f"批量同步完成",
            "data": {
                "total_shops": len(results),
                "success": success_count,
                "failed": failed_count,
                "results": results
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量同步失败: {str(e)}"
        )


@router.get("/shops/{shop_id}/status")
async def get_sync_status(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取店铺的同步状态
    
    Returns:
        店铺同步信息
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    # 统计订单和商品数量
    from app.models.order import Order
    from app.models.product import Product
    
    order_count = db.query(Order).filter(Order.shop_id == shop_id).count()
    product_count = db.query(Product).filter(Product.shop_id == shop_id).count()
    
    return {
        "shop_id": shop_id,
        "shop_name": shop.shop_name,
        "environment": shop.environment.value,
        "region": shop.region.value,
        "is_active": shop.is_active,
        "last_sync_at": shop.last_sync_at,
        "has_api_config": bool(shop.access_token),
        "data_count": {
            "orders": order_count,
            "products": product_count
        }
    }
