"""统一统计API - 提供统一的数据获取端点，避免重复计算"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import hashlib
import json
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.redis_client import RedisClient
from app.services.unified_statistics import UnifiedStatisticsService
from app.models.user import User

router = APIRouter(prefix="/statistics/unified", tags=["statistics-unified"])


def generate_cache_key(endpoint: str, params: dict) -> str:
    """生成缓存键"""
    # 对参数进行排序和序列化，确保相同参数生成相同键
    sorted_params = json.dumps(params, sort_keys=True, default=str)
    params_hash = hashlib.md5(sorted_params.encode()).hexdigest()
    return f"stats:unified:{endpoint}:{params_hash}"


def get_cached_or_compute(
    cache_key: str,
    compute_func,
    ttl: int = 300,
    use_redis: bool = True
):
    """
    获取缓存或计算数据
    
    Args:
        cache_key: 缓存键
        compute_func: 计算函数
        ttl: 缓存过期时间（秒）
        use_redis: 是否使用Redis缓存
    
    Returns:
        数据结果
    """
    # 尝试从Redis获取
    if use_redis:
        cached = RedisClient.get(cache_key)
        if cached:
            logger.debug(f"从Redis缓存获取: {cache_key}")
            return cached
    
    # 计算数据
    result = compute_func()
    
    # 存入Redis缓存
    if use_redis and result:
        try:
            RedisClient.set(cache_key, result, ttl=ttl)
            logger.debug(f"数据已缓存: {cache_key}, TTL={ttl}秒")
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")
    
    return result


@router.get("/overview")
async def get_unified_overview(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: Optional[int] = Query(None, description="统计天数（如果未提供start_date和end_date则使用此参数）"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取统一订单总览统计
    
    返回订单总数、GMV、成本、利润、延误率等核心指标
    使用 UnifiedStatisticsService 确保数据一致性
    """
    # 构建参数字典用于缓存键
    params = {
        "shop_ids": sorted(shop_ids) if shop_ids else None,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
    }
    cache_key = generate_cache_key("overview", params)
    
    def compute():
        # 解析日期范围
        start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
            start_date, end_date, days
        )
        
        # 构建查询条件
        filters = UnifiedStatisticsService.build_base_filters(
            db, start_dt, end_dt, shop_ids, None, None, None
        )
        
        # 计算统计数据
        overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
        
        # 计算利润率
        profit_margin = (
            (overview['total_profit'] / overview['total_gmv'] * 100)
            if overview['total_gmv'] > 0 else 0
        )
        
        return {
            "order_count": overview['order_count'],
            "total_orders": overview['order_count'],  # 兼容字段
            "total_quantity": overview['total_quantity'],
            "total_gmv": round(overview['total_gmv'], 2),
            "total_cost": round(overview['total_cost'], 2),
            "total_profit": round(overview['total_profit'], 2),
            "profit_margin": round(profit_margin, 2),
            "delay_rate": round(overview.get('delay_rate', 0), 2),
            "delay_count": overview.get('delay_count', 0),
            "avg_order_value": round(
                (overview['total_gmv'] / overview['order_count'])
                if overview['order_count'] > 0 else 0, 2
            ),
        }
    
    return get_cached_or_compute(
        cache_key,
        compute,
        ttl=300 if use_cache else 0,  # 5分钟缓存
        use_redis=use_cache
    )


@router.get("/daily")
async def get_unified_daily(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: Optional[int] = Query(None, description="统计天数"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取统一每日统计数据
    
    返回每日订单数、GMV、利润、延误率等数据
    使用 UnifiedStatisticsService 确保数据一致性
    """
    from app.services.statistics import StatisticsService
    
    params = {
        "shop_ids": sorted(shop_ids) if shop_ids else None,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
    }
    cache_key = generate_cache_key("daily", params)
    
    def compute():
        # 解析日期范围
        start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
            start_date, end_date, days
        )
        
        # 使用 StatisticsService.get_daily_statistics，但传递None以获取全部数据
        return StatisticsService.get_daily_statistics(
            db=db,
            shop_ids=shop_ids,
            start_date=start_dt,
            end_date=end_dt,
            days=days if days is not None else None
        )
    
    return get_cached_or_compute(
        cache_key,
        compute,
        ttl=300 if use_cache else 0,  # 5分钟缓存
        use_redis=use_cache
    )


@router.get("/sku-ranking")
async def get_unified_sku_ranking(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: Optional[int] = Query(None, description="统计天数"),
    limit: int = Query(10, description="返回数量限制"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取统一SKU销售排行
    
    返回SKU销售排行数据
    使用 UnifiedStatisticsService 确保数据一致性
    """
    params = {
        "shop_ids": sorted(shop_ids) if shop_ids else None,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "limit": limit,
    }
    cache_key = generate_cache_key("sku-ranking", params)
    
    def compute():
        # 解析日期范围
        start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
            start_date, end_date, days
        )
        
        # 构建查询条件
        filters = UnifiedStatisticsService.build_base_filters(
            db, start_dt, end_dt, shop_ids, None, None, None
        )
        
        # 获取SKU统计
        sku_stats = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=limit)
        
        return {
            "ranking": sku_stats,
            "period": {
                "start_date": start_dt.isoformat() if start_dt else None,
                "end_date": end_dt.isoformat() if end_dt else None,
            }
        }
    
    return get_cached_or_compute(
        cache_key,
        compute,
        ttl=300 if use_cache else 0,  # 5分钟缓存
        use_redis=use_cache
    )


@router.get("/manager-ranking")
async def get_unified_manager_ranking(
    shop_ids: Optional[List[int]] = Query(None),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    days: Optional[int] = Query(None, description="统计天数"),
    limit: int = Query(10, description="返回数量限制"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取统一负责人业绩排行
    
    返回负责人业绩排行数据
    使用 UnifiedStatisticsService 确保数据一致性
    """
    params = {
        "shop_ids": sorted(shop_ids) if shop_ids else None,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "limit": limit,
    }
    cache_key = generate_cache_key("manager-ranking", params)
    
    def compute():
        # 解析日期范围
        start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
            start_date, end_date, days
        )
        
        # 构建查询条件
        filters = UnifiedStatisticsService.build_base_filters(
            db, start_dt, end_dt, shop_ids, None, None, None
        )
        
        # 获取负责人统计
        manager_stats = UnifiedStatisticsService.get_manager_statistics(db, filters)
        
        return {
            "managers": manager_stats[:limit] if limit else manager_stats,
            "period": {
                "start_date": start_dt.isoformat() if start_dt else None,
                "end_date": end_dt.isoformat() if end_dt else None,
            }
        }
    
    return get_cached_or_compute(
        cache_key,
        compute,
        ttl=300 if use_cache else 0,  # 5分钟缓存
        use_redis=use_cache
    )


@router.get("/summary")
async def get_unified_summary(
    shop_ids: Optional[List[int]] = Query(None),
    days: Optional[int] = Query(None, description="统计天数，如果为None则获取全部历史数据"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取统一数据摘要（综合数据）
    
    返回包含总览、SKU排行、负责人排行的综合数据
    用于FrogGPT等需要综合数据的场景
    """
    params = {
        "shop_ids": sorted(shop_ids) if shop_ids else None,
        "days": days,
    }
    cache_key = generate_cache_key("summary", params)
    
    def compute():
        # 解析日期范围
        start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
            None, None, days
        )
        
        # 构建查询条件
        filters = UnifiedStatisticsService.build_base_filters(
            db, start_dt, end_dt, shop_ids, None, None, None
        )
        
        # 计算总览统计
        overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
        
        # 计算利润率
        profit_margin = (
            (overview['total_profit'] / overview['total_gmv'] * 100)
            if overview['total_gmv'] > 0 else 0
        )
        
        # 获取Top SKU（前10）
        top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
        
        # 获取Top负责人（前10）
        top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
        
        return {
            "overview": {
                "total_orders": overview['order_count'],
                "total_quantity": overview['total_quantity'],
                "total_gmv": round(overview['total_gmv'], 2),
                "total_cost": round(overview['total_cost'], 2),
                "total_profit": round(overview['total_profit'], 2),
                "profit_margin": round(profit_margin, 2),
                "delay_rate": round(overview.get('delay_rate', 0), 2),
                "delay_count": overview.get('delay_count', 0),
            },
            "top_skus": top_skus,
            "top_managers": top_managers,
            "period": {
                "start_date": start_dt.isoformat() if start_dt else None,
                "end_date": end_dt.isoformat() if end_dt else None,
            }
        }
    
    return get_cached_or_compute(
        cache_key,
        compute,
        ttl=300 if use_cache else 0,  # 5分钟缓存
        use_redis=use_cache
    )

