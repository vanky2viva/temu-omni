"""数据同步API"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import asyncio
import traceback
import json
from datetime import datetime, timedelta
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
    _sync_logs: Dict[int, List[Dict[str, Any]]] = {}  # 内存回退：存储同步日志
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


def _add_sync_log(shop_id: int, log_message: str, log_level: str = "info"):
    """添加同步日志到Redis或内存（最新的在前）"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": log_level,
        "message": log_message
    }
    
    if _use_redis:
        try:
            # 使用列表存储日志，lpush将新日志添加到列表头部（最新的在前）
            log_key = f"sync_logs:{shop_id}"
            _redis_client.lpush(log_key, json.dumps(log_entry, ensure_ascii=False))
            _redis_client.ltrim(log_key, 0, 999)  # 只保留最近1000条
            _redis_client.expire(log_key, 3600)  # 1小时过期
        except Exception as e:
            logger.error(f"写入同步日志到Redis失败: {e}")
            # Redis失败时回退到内存存储
            if shop_id not in _sync_logs:
                _sync_logs[shop_id] = []
            _sync_logs[shop_id].insert(0, log_entry)  # 插入到列表头部（最新的在前）
            # 只保留最近1000条
            if len(_sync_logs[shop_id]) > 1000:
                _sync_logs[shop_id] = _sync_logs[shop_id][:1000]
    else:
        # 使用内存存储
        if shop_id not in _sync_logs:
            _sync_logs[shop_id] = []
        _sync_logs[shop_id].insert(0, log_entry)  # 插入到列表头部（最新的在前）
        # 只保留最近1000条
        if len(_sync_logs[shop_id]) > 1000:
            _sync_logs[shop_id] = _sync_logs[shop_id][:1000]


def _get_sync_logs(shop_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """获取同步日志（从Redis或内存）"""
    if _use_redis:
        try:
            log_key = f"sync_logs:{shop_id}"
            logs = _redis_client.lrange(log_key, 0, limit - 1)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"从Redis读取同步日志失败: {e}")
            # Redis失败时回退到内存存储
            if shop_id in _sync_logs:
                return _sync_logs[shop_id][:limit]
            return []
    else:
        # 使用内存存储
        if shop_id in _sync_logs:
            return _sync_logs[shop_id][:limit]
        return []


def _delete_sync_progress(shop_id: int):
    """删除同步进度和日志"""
    if _use_redis:
        try:
            _redis_client.delete(f"sync_progress:{shop_id}")
            # 同时删除同步日志
            _redis_client.delete(f"sync_logs:{shop_id}")
        except Exception as e:
            logger.error(f"从Redis删除进度失败: {e}")
    else:
        if shop_id in _sync_progress:
            del _sync_progress[shop_id]
        # 同时删除内存中的同步日志
        if shop_id in _sync_logs:
            del _sync_logs[shop_id]


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
    start_time = datetime.now()  # 定义开始时间
    try:
        # 初始化进度
        _set_sync_progress(shop_id, {
            "status": "running",
            "progress": 0,
            "current_step": "准备同步...",
            "orders": None,
            "products": None,
            "error": None,
            "start_time": start_time.isoformat(),
        })
        
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            _set_sync_progress(shop_id, {
                "status": "error",
                "error": "店铺不存在",
            })
            return
        
        sync_service = SyncService(db, shop)
        
        # 定义进度回调函数（支持时间信息和日志）
        def update_progress(progress_percent: int, step_desc: str, time_info: Optional[Dict[str, Any]] = None):
            """更新同步进度"""
            current = _get_sync_progress(shop_id)
            current.update({
                "progress": progress_percent,
                "current_step": step_desc,
            })
            if time_info:
                current["time_info"] = time_info
                # 计算预计完成时间戳（秒）
                # 使用 is not None 而不是直接判断值，以正确处理0秒的情况
                if time_info.get("estimated_remaining_seconds") is not None:
                    estimated_completion = datetime.now() + timedelta(seconds=int(time_info["estimated_remaining_seconds"]))
                    current["estimated_completion_timestamp"] = int(estimated_completion.timestamp())
            _set_sync_progress(shop_id, current)
            # 记录详细日志（每10%或关键步骤）
            if progress_percent % 10 == 0 or "完成" in step_desc or "失败" in step_desc or "开始" in step_desc:
                _add_sync_log(shop_id, f"[{progress_percent}%] {step_desc}", "info")
        
        # 为进度回调添加日志回调函数
        def log_callback(log_message: str):
            """日志回调函数"""
            _add_sync_log(shop_id, log_message, "info")
        
        update_progress._log_callback = log_callback
        
        # 同步订单
        current = _get_sync_progress(shop_id)
        current.update({
            "progress": 10,
            "current_step": "开始同步订单...",
        })
        _set_sync_progress(shop_id, current)
        _add_sync_log(shop_id, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        _add_sync_log(shop_id, "📦 开始同步订单数据...", "info")
        
        try:
            orders_result = await sync_service.sync_orders(
                full_sync=full_sync,
                progress_callback=update_progress
            )
            # 确保返回的结果包含统计信息
            current = _get_sync_progress(shop_id)
            if isinstance(orders_result, dict):
                current["orders"] = orders_result
                # 记录订单同步结果日志
                if orders_result.get("error"):
                    _add_sync_log(shop_id, f"❌ 订单同步失败: {orders_result['error']}", "error")
                else:
                    total = orders_result.get("total", 0)
                    new = orders_result.get("new", 0)
                    updated = orders_result.get("updated", 0)
                    failed = orders_result.get("failed", 0)
                    _add_sync_log(shop_id, f"✅ 订单同步完成", "success")
                    _add_sync_log(shop_id, f"   📊 统计：总数 {total}，新增 {new}，更新 {updated}，失败 {failed}", "info")
                    if total > 0:
                        success_rate = ((total - failed) / total * 100) if total > 0 else 0
                        _add_sync_log(shop_id, f"   📈 成功率：{success_rate:.1f}%", "info")
            else:
                current["orders"] = {
                    "total": 0,
                    "new": 0,
                    "updated": 0,
                    "failed": 0,
                    "error": "返回格式异常"
                }
                _add_sync_log(shop_id, "⚠️ 订单同步返回格式异常", "warning")
            _set_sync_progress(shop_id, current)
        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(f"订单同步失败 - 店铺ID: {shop_id}, 错误: {error_msg}\n{traceback.format_exc()}")
            _add_sync_log(shop_id, f"❌ 订单同步异常: {error_msg}", "error")
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
        _add_sync_log(shop_id, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        _add_sync_log(shop_id, "🛍️  开始同步商品数据...", "info")
        
        try:
            products_result = await sync_service.sync_products(
                full_sync=full_sync,
                progress_callback=update_progress
            )
            # 确保返回的结果包含统计信息
            current = _get_sync_progress(shop_id)
            if isinstance(products_result, dict):
                current["products"] = products_result
                # 记录商品同步结果日志
                if products_result.get("error"):
                    _add_sync_log(shop_id, f"❌ 商品同步失败: {products_result['error']}", "error")
                else:
                    total = products_result.get("total", 0)
                    new = products_result.get("new", 0)
                    updated = products_result.get("updated", 0)
                    failed = products_result.get("failed", 0)
                    _add_sync_log(shop_id, f"✅ 商品同步完成", "success")
                    _add_sync_log(shop_id, f"   📊 统计：总数 {total}，新增 {new}，更新 {updated}，失败 {failed}", "info")
                    if total > 0:
                        success_rate = ((total - failed) / total * 100) if total > 0 else 0
                        _add_sync_log(shop_id, f"   📈 成功率：{success_rate:.1f}%", "info")
            else:
                current["products"] = {
                    "total": 0,
                    "new": 0,
                    "updated": 0,
                    "failed": 0,
                    "error": "返回格式异常"
                }
                _add_sync_log(shop_id, "⚠️ 商品同步返回格式异常", "warning")
            _set_sync_progress(shop_id, current)
        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(f"商品同步失败 - 店铺ID: {shop_id}, 错误: {error_msg}\n{traceback.format_exc()}")
            _add_sync_log(shop_id, f"❌ 商品同步异常: {error_msg}", "error")
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
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        current = _get_sync_progress(shop_id)
        
        # 构建完成消息
        orders_info = current.get("orders", {})
        products_info = current.get("products", {})
        completion_msg = f"同步完成！耗时 {elapsed_time:.1f} 秒"
        if orders_info and not orders_info.get("error"):
            completion_msg += f"\n订单：总数 {orders_info.get('total', 0)}，新增 {orders_info.get('new', 0)}，更新 {orders_info.get('updated', 0)}"
        if products_info and not products_info.get("error"):
            completion_msg += f"\n商品：总数 {products_info.get('total', 0)}，新增 {products_info.get('new', 0)}，更新 {products_info.get('updated', 0)}"
        
        current.update({
            "status": "completed",
            "progress": 100,
            "current_step": completion_msg,
            "end_time": end_time.isoformat(),
            "elapsed_seconds": elapsed_time,
        })
        _set_sync_progress(shop_id, current)
        _add_sync_log(shop_id, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        _add_sync_log(shop_id, f"🎉 同步任务完成！", "success")
        _add_sync_log(shop_id, f"   ⏱️  总耗时：{elapsed_time:.1f} 秒 ({elapsed_time/60:.1f} 分钟)", "info")
        if orders_info and not orders_info.get("error"):
            _add_sync_log(shop_id, f"   📦 订单：总数 {orders_info.get('total', 0)}，新增 {orders_info.get('new', 0)}，更新 {orders_info.get('updated', 0)}", "info")
        if products_info and not products_info.get("error"):
            _add_sync_log(shop_id, f"   🛍️  商品：总数 {products_info.get('total', 0)}，新增 {products_info.get('new', 0)}，更新 {products_info.get('updated', 0)}", "info")
        _add_sync_log(shop_id, f"   ✅ 完成时间：{end_time.strftime('%Y-%m-%d %H:%M:%S')}", "info")
        
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
        同步进度信息（包含日志）
    """
    try:
        progress = _get_sync_progress(shop_id)
        # 添加最近的日志
        logs = _get_sync_logs(shop_id, limit=50)
        progress["logs"] = logs
        return progress
        
    except Exception as e:
        logger.error(f"获取同步进度失败 - 店铺ID: {shop_id}, 错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "progress": 0,
            "error": f"获取进度失败: {str(e)}",
            "logs": []
        }


@router.get("/shops/{shop_id}/logs")
async def get_sync_logs_endpoint(
    shop_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    获取店铺同步日志
    
    Args:
        shop_id: 店铺ID
        limit: 返回日志条数（最多1000）
    
    Returns:
        同步日志列表
    """
    try:
        logs = _get_sync_logs(shop_id, limit=min(limit, 1000))
        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"获取同步日志失败 - 店铺ID: {shop_id}, 错误: {e}")
        return {
            "success": False,
            "error": f"获取日志失败: {str(e)}",
            "data": []
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
