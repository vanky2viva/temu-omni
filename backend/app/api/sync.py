"""数据同步API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.shop import Shop
from app.temu import TemuAPIClient

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/shops/{shop_id}/orders")
async def sync_shop_orders(
    shop_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    同步店铺订单数据
    
    Args:
        shop_id: 店铺ID
        days: 同步最近N天的数据
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    if not shop.app_key or not shop.app_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺未配置API密钥"
        )
    
    if not shop.access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺未授权，请先配置access_token"
        )
    
    try:
        # 创建API客户端（使用店铺的API密钥）
        client = TemuAPIClient(
            app_key=shop.app_key,
            app_secret=shop.app_secret
        )
        
        # 计算时间范围
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=days)).timestamp())
        
        # 获取订单数据
        orders_data = await client.get_orders(
            access_token=shop.access_token,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=100
        )
        
        await client.close()
        
        # 更新同步时间
        shop.last_sync_at = datetime.now()
        db.commit()
        
        return {
            "success": True,
            "message": f"成功同步订单数据",
            "data": orders_data,
            "synced_at": shop.last_sync_at
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败: {str(e)}"
        )


@router.post("/shops/{shop_id}/products")
async def sync_shop_products(
    shop_id: int,
    db: Session = Depends(get_db)
):
    """同步店铺商品数据"""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    if not shop.app_key or not shop.app_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺未配置API密钥"
        )
    
    if not shop.access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺未授权"
        )
    
    try:
        client = TemuAPIClient(
            app_key=shop.app_key,
            app_secret=shop.app_secret
        )
        
        products_data = await client.get_products(
            access_token=shop.access_token,
            page=1,
            page_size=100
        )
        
        await client.close()
        
        return {
            "success": True,
            "message": "成功同步商品数据",
            "data": products_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败: {str(e)}"
        )

