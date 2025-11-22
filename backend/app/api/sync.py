"""数据同步API"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import asyncio
import traceback
import json
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.shop import Shop
from app.models.user import User
from app.services.sync_service import sync_shop_data, sync_all_shops, SyncService

router = APIRouter(prefix="/sync", tags=["sync"])

# Redis客户端（用于跨worker共享同步进度）
try:
    import redis
    from app.core.config import settings
    
    # 从REDIS_URL解析连接信息，如果没有则使用默认值
    redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
    if redis_url.startswith('redis://'):
        # 解析Redis URL，支持密码：redis://:password@host:port/db
        import urllib.parse
        parsed = urllib.parse.urlparse(redis_url)
        redis_password = parsed.password if parsed.password else None
        redis_host = parsed.hostname or 'redis'
        redis_port = parsed.port or 6379
        redis_db = int(parsed.path.lstrip('/')) if parsed.path else 0
        
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
            socket_timeout=5,  # 5秒超时，避免卡住
            socket_connect_timeout=5
        )
        # 测试连接
        _redis_client.ping()
        _use_redis = True
        logger.info(f"已连接到Redis ({redis_host}:{redis_port})，同步进度将使用Redis存储")
    else:
        # 兼容旧格式
        _redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True, socket_timeout=5, socket_connect_timeout=5)
        _redis_client.ping()
        _use_redis = True
        logger.info("已连接到Redis，同步进度将使用Redis存储")
except Exception as e:
    logger.warning(f"Redis连接失败，将使用内存存储（多worker环境下可能导致进度丢失）: {e}")
    _sync_progress: Dict[int, Dict[str, Any]] = {}
    _use_redis = False


def _get_sync_progress(shop_id: int) -> Dict[str, Any]:
    """从Redis或内存获取同步进度"""
    if _use_redis:
        try:
            data = _redis_client.get(f"sync_progress:{shop_id}")
            if data:
                return json.loads(data)
            return {"status": "not_started", "progress": 0}
        except Exception as e:
            logger.error(f"从Redis读取进度失败: {e}")
            return {"status": "not_started", "progress": 0}
    else:
        return _sync_progress.get(shop_id, {"status": "not_started", "progress": 0})


def _set_sync_progress(shop_id: int, progress_data: Dict[str, Any]):
    """将同步进度存储到Redis或内存"""
    if _use_redis:
        try:
            _redis_client.setex(
                f"sync_progress:{shop_id}",
                3600,  # 1小时过期
                json.dumps(progress_data, ensure_ascii=False, default=str)
            )
        except Exception as e:
            logger.error(f"将进度写入Redis失败: {e}")
    else:
        _sync_progress[shop_id] = progress_data


def _delete_sync_progress(shop_id: int):
    """删除同步进度"""
    if _use_redis:
        try:
            _redis_client.delete(f"sync_progress:{shop_id}")
        except Exception as e:
            logger.error(f"从Redis删除进度失败: {e}")
    else:
        if shop_id in _sync_progress:
            del _sync_progress[shop_id]


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
    
    sync_service = None
    try:
        sync_service = SyncService(db, shop)
        result = await sync_service.sync_orders(full_sync=full_sync)
        
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
        logger.error(f"订单同步失败 - 店铺ID: {shop_id}, 错误: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订单同步失败: {str(e)}"
        )
    finally:
        # 确保资源清理
        if sync_service and sync_service.temu_service:
            try:
                await sync_service.temu_service.close()
            except Exception as e:
                logger.warning(f"关闭Temu服务时出错: {e}")


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
    
    sync_service = None
    try:
        sync_service = SyncService(db, shop)
        result = await sync_service.sync_products(full_sync=full_sync)
        
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
        logger.error(f"商品同步失败 - 店铺ID: {shop_id}, 错误: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"商品同步失败: {str(e)}"
        )
    finally:
        # 确保资源清理
        if sync_service and sync_service.temu_service:
            try:
                await sync_service.temu_service.close()
            except Exception as e:
                logger.warning(f"关闭Temu服务时出错: {e}")


async def _sync_shop_with_progress(shop_id: int, full_sync: bool, db: Session):
    """执行同步并更新进度"""
    sync_service = None
    try:
        # 初始化进度
        _set_sync_progress(shop_id, {
            "status": "running",
            "progress": 0,
            "current_step": "准备同步...",
            "orders": None,
            "products": None,
            "error": None,
            "start_time": datetime.now().isoformat(),
        })
        
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            _set_sync_progress(shop_id, {
                "status": "error",
                "error": "店铺不存在",
            })
            return
        
        sync_service = SyncService(db, shop)
        
        # 定义进度回调函数
        def update_progress(progress_percent: int, step_desc: str):
            """更新同步进度"""
            current = _get_sync_progress(shop_id)
            current.update({
                "progress": progress_percent,
                "current_step": step_desc,
            })
            _set_sync_progress(shop_id, current)
        
        # 同步订单
        current = _get_sync_progress(shop_id)
        current.update({
            "progress": 10,
            "current_step": "开始同步订单...",
        })
        _set_sync_progress(shop_id, current)
        
        try:
            orders_result = await sync_service.sync_orders(
                full_sync=full_sync,
                progress_callback=update_progress
            )
            # 确保返回的结果包含统计信息
            current = _get_sync_progress(shop_id)
            if isinstance(orders_result, dict):
                current["orders"] = orders_result
            else:
                current["orders"] = {
                    "total": 0,
                    "new": 0,
                    "updated": 0,
                    "failed": 0,
                    "error": "返回格式异常"
                }
            _set_sync_progress(shop_id, current)
        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(f"订单同步失败 - 店铺ID: {shop_id}, 错误: {error_msg}\n{traceback.format_exc()}")
            current = _get_sync_progress(shop_id)
            current["orders"] = {
                "total": 0,
                "new": 0,
                "updated": 0,
                "failed": 0,
                "error": error_msg
            }
            _set_sync_progress(shop_id, current)
        
        # 同步商品
        current = _get_sync_progress(shop_id)
        current.update({
            "progress": 60,
            "current_step": "开始同步商品...",
        })
        _set_sync_progress(shop_id, current)
        
        try:
            products_result = await sync_service.sync_products(
                full_sync=full_sync,
                progress_callback=update_progress
            )
            # 确保返回的结果包含统计信息
            current = _get_sync_progress(shop_id)
            if isinstance(products_result, dict):
                current["products"] = products_result
            else:
                current["products"] = {
                    "total": 0,
                    "new": 0,
                    "updated": 0,
                    "failed": 0,
                    "error": "返回格式异常"
                }
            _set_sync_progress(shop_id, current)
        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(f"商品同步失败 - 店铺ID: {shop_id}, 错误: {error_msg}\n{traceback.format_exc()}")
            current = _get_sync_progress(shop_id)
            current["products"] = {
                "total": 0,
                "new": 0,
                "updated": 0,
                "failed": 0,
                "error": error_msg
            }
            _set_sync_progress(shop_id, current)
        
        # 同步分类（已禁用，无需获取商品分类）
        # current = _get_sync_progress(shop_id)
        # current.update({
        #     "progress": 90,
        #     "current_step": "正在同步分类数据...",
        # })
        # _set_sync_progress(shop_id, current)
        # try:
        #     categories_result = await sync_service.sync_categories()
        #     current = _get_sync_progress(shop_id)
        #     current["categories"] = categories_result
        #     _set_sync_progress(shop_id, current)
        # except Exception as e:
        #     current = _get_sync_progress(shop_id)
        #     current["categories"] = {"error": str(e)}
        #     _set_sync_progress(shop_id, current)
        
        # 完成
        current = _get_sync_progress(shop_id)
        current.update({
            "status": "completed",
            "progress": 100,
            "current_step": "同步完成",
            "end_time": datetime.now().isoformat(),
        })
        _set_sync_progress(shop_id, current)
        
    except Exception as e:
        logger.error(f"同步任务失败 - 店铺ID: {shop_id}, 错误: {e}")
        logger.error(traceback.format_exc())
        _set_sync_progress(shop_id, {
            "status": "error",
            "error": str(e),
            "end_time": datetime.now().isoformat(),
        })
    finally:
        # 确保资源清理
        if sync_service and sync_service.temu_service:
            try:
                await sync_service.temu_service.close()
            except Exception as e:
                logger.warning(f"关闭Temu服务时出错: {e}")


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
    current_progress = _get_sync_progress(shop_id)
    if current_progress.get("status") == "running":
        return {
            "success": True,
            "message": "同步任务已在运行中",
            "data": {
                "shop_id": shop_id,
                "shop_name": shop.shop_name,
                "progress": current_progress,
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
async def get_sync_progress_endpoint(
    shop_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取店铺同步进度
    
    Returns:
        同步进度信息
    """
    try:
        progress = _get_sync_progress(shop_id)
        return progress
        
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
