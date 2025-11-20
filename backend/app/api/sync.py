"""数据同步API"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.shop import Shop
from app.models.user import User
from app.services.sync_service import sync_shop_data, sync_all_shops, SyncService

router = APIRouter(prefix="/sync", tags=["sync"])

# 存储同步进度（实际生产环境应使用Redis等）
_sync_progress: Dict[int, Dict[str, Any]] = {}


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
        from app.services.temu_service import TemuService
        temu_service = TemuService(shop)
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


async def _sync_shop_with_progress(shop_id: int, full_sync: bool, db: Session):
    """执行同步并更新进度"""
    try:
        # 初始化进度
        _sync_progress[shop_id] = {
            "status": "running",
            "progress": 0,
            "current_step": "初始化",
            "orders": None,
            "products": None,
            "error": None,
            "start_time": datetime.now().isoformat(),
        }
        
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            _sync_progress[shop_id] = {
                "status": "error",
                "error": "店铺不存在",
            }
            return
        
        sync_service = SyncService(db, shop)
        
        # 同步订单
        _sync_progress[shop_id].update({
            "progress": 20,
            "current_step": "正在同步订单数据...",
        })
        try:
            orders_result = await sync_service.sync_orders(full_sync=full_sync)
            # 确保返回的结果包含统计信息
            if isinstance(orders_result, dict):
                _sync_progress[shop_id]["orders"] = orders_result
            else:
                _sync_progress[shop_id]["orders"] = {
                    "total": 0,
                    "new": 0,
                    "updated": 0,
                    "failed": 0,
                    "error": "返回格式异常"
                }
        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(f"订单同步失败 - 店铺ID: {shop_id}, 错误: {error_msg}\n{traceback.format_exc()}")
            _sync_progress[shop_id]["orders"] = {
                "total": 0,
                "new": 0,
                "updated": 0,
                "failed": 0,
                "error": error_msg
            }
        
        # 同步商品
        _sync_progress[shop_id].update({
            "progress": 70,
            "current_step": "正在同步商品数据...",
        })
        try:
            products_result = await sync_service.sync_products(full_sync=full_sync)
            # 确保返回的结果包含统计信息
            if isinstance(products_result, dict):
                _sync_progress[shop_id]["products"] = products_result
            else:
                _sync_progress[shop_id]["products"] = {
                    "total": 0,
                    "new": 0,
                    "updated": 0,
                    "failed": 0,
                    "error": "返回格式异常"
                }
        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(f"商品同步失败 - 店铺ID: {shop_id}, 错误: {error_msg}\n{traceback.format_exc()}")
            _sync_progress[shop_id]["products"] = {
                "total": 0,
                "new": 0,
                "updated": 0,
                "failed": 0,
                "error": error_msg
            }
        
        # 同步分类（已禁用，无需获取商品分类）
        # _sync_progress[shop_id].update({
        #     "progress": 90,
        #     "current_step": "正在同步分类数据...",
        # })
        # try:
        #     categories_result = await sync_service.sync_categories()
        #     _sync_progress[shop_id]["categories"] = categories_result
        # except Exception as e:
        #     _sync_progress[shop_id]["categories"] = {"error": str(e)}
        
        await sync_service.temu_service.close()
        
        # 完成
        _sync_progress[shop_id].update({
            "status": "completed",
            "progress": 100,
            "current_step": "同步完成",
            "end_time": datetime.now().isoformat(),
        })
        
    except Exception as e:
        _sync_progress[shop_id] = {
            "status": "error",
            "error": str(e),
            "end_time": datetime.now().isoformat(),
        }


@router.post("/shops/{shop_id}/all")
async def sync_shop_all_data(
    shop_id: int,
    full_sync: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步指定店铺的所有数据（订单+商品）
    支持实时进度查询
    
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
    
    # 检查是否已有同步任务在运行
    if shop_id in _sync_progress and _sync_progress[shop_id].get("status") == "running":
        return {
            "success": True,
            "message": "同步任务已在运行中",
            "data": {
                "shop_id": shop_id,
                "shop_name": shop.shop_name,
                "progress": _sync_progress[shop_id],
            }
        }
    
    # 在后台任务中执行同步
    background_tasks.add_task(_sync_shop_with_progress, shop_id, full_sync, db)
    
    return {
        "success": True,
        "message": "同步任务已启动",
        "data": {
            "shop_id": shop_id,
            "shop_name": shop.shop_name,
                "environment": shop.environment.value,
                "region": shop.region.value,
        }
    }


@router.get("/shops/{shop_id}/progress")
async def get_sync_progress(
    shop_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取店铺同步进度
    
    Returns:
        同步进度信息
    """
    try:
        if shop_id not in _sync_progress:
            return {
                "status": "not_started",
                "progress": 0,
            }
        
        progress = _sync_progress[shop_id].copy()
        
        # 确保所有值都是可序列化的
        # 转换datetime对象为字符串
        import json
        
        def make_serializable(obj):
            """递归地将对象转换为可序列化的格式"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return make_serializable(obj.__dict__)
            else:
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError):
                    return str(obj)
        
        return make_serializable(progress)
        
    except Exception as e:
        logger.error(f"获取同步进度失败 - 店铺ID: {shop_id}, 错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "progress": 0,
            "error": f"获取进度失败: {str(e)}",
        }


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
