"""备货计划API - 根据回款数据和销量数据生成备货计划"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text, case, or_
from decimal import Decimal
from loguru import logger
import traceback
from fastapi import HTTPException

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.shop import Shop
from app.models.user import User
from app.utils.currency import CurrencyConverter
from app.services.unified_statistics import UnifiedStatisticsService
import pytz
from app.core.config import settings

# 货币转换函数（与analytics.py保持一致）
def _convert_to_cny(price_column, usd_rate):
    """将价格转换为CNY"""
    return case(
        (Order.currency == 'USD', price_column * usd_rate),
        (Order.currency == 'CNY', price_column),
        else_=price_column * usd_rate
    )

# 北京时间时区
BEIJING_TIMEZONE = pytz.timezone(getattr(settings, 'TIMEZONE', 'Asia/Shanghai'))

router = APIRouter(prefix="/inventory-planning", tags=["inventory-planning"])


def get_beijing_now() -> datetime:
    """获取北京时区的当前时间"""
    return datetime.now(BEIJING_TIMEZONE)


@router.get("/stock-plan")
async def get_stock_plan(
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    past_days: int = Query(7, ge=1, le=30, description="过去N天的数据用于分析（默认7天）"),
    future_period: str = Query("week", regex="^(week|month)$", description="备货周期（week=一周，month=一个月）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取按SKU货号的备货计划
    
    根据过去N天的回款数据和销量数据，预测未来一周/月的备货需求
    
    注意：SKU货号对应原始数据中的 extCode 字段，已映射到 Order.product_sku
    
    Args:
        shop_ids: 店铺ID列表，None表示所有店铺
        past_days: 过去N天的数据用于分析（默认7天）
        future_period: 备货周期（week=一周，month=一个月）
    
    Returns:
        备货计划数据，包含每个SKU货号的：
        - 过去N天的销量
        - 过去N天的回款金额
        - 预测未来销量
        - 建议备货数量
    """
    try:
        # 计算日期范围
        end_date = get_beijing_now()
        start_date = end_date - timedelta(days=past_days)
        
        # 计算未来周期天数
        future_days = 7 if future_period == "week" else 30
        
        # 构建基础过滤条件（用于销量统计）
        filters = UnifiedStatisticsService.build_base_filters(
            db, start_date, end_date, shop_ids, None, None, None
        )
        
        # 1. 获取过去N天的SKU销量数据（按SKU货号统计）
        # 注意：Order.product_sku 存储的是原始数据中的 extCode 字段值（SKU货号，如LBB3-...）
        # 使用 Order.product_sku 作为分组键，确保按SKU货号统计，而不是按SKU ID
        parent_order_key = UnifiedStatisticsService.get_parent_order_key()
        
        sku_sales_query = db.query(
            Order.product_sku.label("sku"),  # extCode (SKU货号)
            func.max(Order.product_name).label("product_name"),
            func.max(Product.manager).label("manager"),
            func.sum(Order.quantity).label("total_quantity"),
            func.count(func.distinct(parent_order_key)).label("order_count"),
            func.sum(Order.total_price).label("total_gmv"),
            func.sum(Order.profit).label("total_profit"),
        ).outerjoin(
            Product, Order.product_id == Product.id
        ).filter(
            and_(*filters),
            Order.product_sku.isnot(None),
            Order.product_sku != ''
        ).group_by(
            Order.product_sku
        ).order_by(
            func.sum(Order.quantity).desc()
        ).limit(1000).all()
        
        # 转换为字典格式
        sku_sales = [
            {
                "sku": row.sku,
                "product_name": row.product_name or '未知商品',
                "manager": row.manager or '未分配',
                "total_quantity": int(row.total_quantity or 0),
                "order_count": int(row.order_count or 0),
                "total_gmv": float(row.total_gmv or 0),
                "total_profit": float(row.total_profit or 0),
            }
            for row in sku_sales_query
        ]
        
        # 2. 获取过去N天的回款数据（按SKU货号分组）
        # 注意：Order.product_sku 存储的是原始数据中的 extCode 字段值（SKU货号）
        # 回款日期 = delivery_time + 8天
        collection_date_expr = func.date(Order.delivery_time + text("INTERVAL '8 days'"))
        
        # 筛选已签收的订单，且回款日期在过去N天内
        collection_filters = [
            Order.status == OrderStatus.DELIVERED,
            Order.delivery_time.isnot(None),
            collection_date_expr >= start_date.date(),
            collection_date_expr <= end_date.date()
        ]
        
        if shop_ids:
            collection_filters.append(Order.shop_id.in_(shop_ids))
        
        # 按SKU货号（extCode）统计回款金额
        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
        sku_collections = db.query(
            Order.product_sku,  # extCode (SKU货号)
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_price * usd_rate),
                    (Order.currency == 'CNY', Order.total_price),
                    else_=Order.total_price * usd_rate
                )
            ).label("collection_amount"),
            func.sum(Order.quantity).label("collection_quantity"),
        ).filter(
            and_(*collection_filters),
            Order.product_sku.isnot(None)
        ).group_by(
            Order.product_sku
        ).all()
        
        # 构建SKU回款数据字典
        collection_by_sku = {
            row.product_sku: {
                "collection_amount": float(row.collection_amount or 0),
                "collection_quantity": int(row.collection_quantity or 0),
            }
            for row in sku_collections
        }
        
        # 3. 合并销量和回款数据，生成备货计划
        stock_plans = []
        for sku_stat in sku_sales:
            sku = sku_stat.get('sku')
            if not sku:
                continue
            
            # 过去N天的销量
            past_quantity = sku_stat.get('total_quantity', 0)
            past_orders = sku_stat.get('order_count', 0)
            past_gmv = sku_stat.get('total_gmv', 0)
            
            # 过去N天的回款数据
            collection_data = collection_by_sku.get(sku, {})
            past_collection_amount = collection_data.get('collection_amount', 0)
            past_collection_quantity = collection_data.get('collection_quantity', 0)
            
            # 计算日均销量
            daily_avg_quantity = past_quantity / past_days if past_days > 0 else 0
            
            # 预测未来销量（基于日均销量）
            predicted_quantity = daily_avg_quantity * future_days
            
            # 计算建议备货数量（考虑安全库存，建议备货量为预测销量的1.2-1.5倍）
            # 如果过去销量为0，不生成备货计划
            if past_quantity > 0:
                safety_factor = 1.3  # 安全系数
                suggested_stock = int(predicted_quantity * safety_factor)
                
                # 计算回款率（回款金额/GMV）
                collection_rate = (past_collection_amount / past_gmv * 100) if past_gmv > 0 else 0
                
                stock_plans.append({
                    "sku": sku,
                    "product_name": sku_stat.get('product_name', '未知商品'),
                    "manager": sku_stat.get('manager', '未分配'),
                    "past_period": {
                        "days": past_days,
                        "quantity": int(past_quantity),
                        "orders": int(past_orders),
                        "gmv": round(past_gmv, 2),
                        "collection_amount": round(past_collection_amount, 2),
                        "collection_quantity": int(past_collection_quantity),
                        "collection_rate": round(collection_rate, 2),
                    },
                    "prediction": {
                        "period": future_period,
                        "days": future_days,
                        "daily_avg_quantity": round(daily_avg_quantity, 2),
                        "predicted_quantity": int(predicted_quantity),
                    },
                    "suggestion": {
                        "suggested_stock": suggested_stock,
                        "safety_factor": safety_factor,
                        "priority": "high" if past_quantity > 100 else ("medium" if past_quantity > 50 else "low"),
                    }
                })
        
        # 按建议备货数量降序排序
        stock_plans.sort(key=lambda x: x['suggestion']['suggested_stock'], reverse=True)
        
        return {
            "analysis_period": {
                "past_days": past_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "future_period": {
                "type": future_period,
                "days": future_days,
            },
            "stock_plans": stock_plans,
            "summary": {
                "total_skus": len(stock_plans),
                "total_suggested_stock": sum(plan['suggestion']['suggested_stock'] for plan in stock_plans),
                "high_priority_count": sum(1 for plan in stock_plans if plan['suggestion']['priority'] == 'high'),
            }
        }
    except Exception as e:
        logger.error(f"生成备货计划失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"生成备货计划失败: {str(e)}")


@router.get("/stock-plan-by-sku")
async def get_stock_plan_by_sku(
    sku: str = Query(..., description="SKU货号"),
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    past_days: int = Query(7, ge=1, le=30, description="过去N天的数据用于分析（默认7天）"),
    future_period: str = Query("week", regex="^(week|month)$", description="备货周期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定SKU货号的详细备货计划
    
    注意：sku 参数应该是 SKU货号（原始数据中的 extCode 字段值，如LBB3-...）
    
    返回该SKU货号的详细销量、回款和备货建议
    """
    try:
        # 计算日期范围
        end_date = get_beijing_now()
        start_date = end_date - timedelta(days=past_days)
        future_days = 7 if future_period == "week" else 30
        
        # 构建基础过滤条件
        filters = UnifiedStatisticsService.build_base_filters(
            db, start_date, end_date, shop_ids, None, None, None
        )
        
        # 添加SKU货号过滤
        filters.append(Order.product_sku == sku)
        
        # 获取该SKU货号的销量统计
        # 注意：Order.product_sku 存储的是原始数据中的 extCode 字段值（SKU货号）
        parent_order_key = UnifiedStatisticsService.get_parent_order_key()
        
        sku_stat_query = db.query(
            Order.product_sku.label("sku"),  # extCode (SKU货号)
            func.max(Order.product_name).label("product_name"),
            func.max(Product.manager).label("manager"),
            func.sum(Order.quantity).label("total_quantity"),
            func.count(func.distinct(parent_order_key)).label("order_count"),
            func.sum(Order.total_price).label("total_gmv"),
            func.sum(Order.profit).label("total_profit"),
        ).outerjoin(
            Product, Order.product_id == Product.id
        ).filter(
            and_(*filters),
            Order.product_sku.isnot(None),
            Order.product_sku != ''
        ).group_by(
            Order.product_sku
        ).first()
        
        if not sku_stat_query:
            return {
                "sku": sku,
                "message": "未找到该SKU的销售数据",
                "stock_plan": None
            }
        
        # 转换为字典格式
        sku_stat = {
            "sku": sku_stat_query.sku,
            "product_name": sku_stat_query.product_name or '未知商品',
            "manager": sku_stat_query.manager or '未分配',
            "total_quantity": int(sku_stat_query.total_quantity or 0),
            "order_count": int(sku_stat_query.order_count or 0),
            "total_gmv": float(sku_stat_query.total_gmv or 0),
            "total_profit": float(sku_stat_query.total_profit or 0),
        }
        
        # 获取回款数据
        collection_date_expr = func.date(Order.delivery_time + text("INTERVAL '8 days'"))
        collection_filters = [
            Order.status == OrderStatus.DELIVERED,
            Order.delivery_time.isnot(None),
            Order.product_sku == sku,
            collection_date_expr >= start_date.date(),
            collection_date_expr <= end_date.date()
        ]
        
        if shop_ids:
            collection_filters.append(Order.shop_id.in_(shop_ids))
        
        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
        collection_result = db.query(
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_price * usd_rate),
                    (Order.currency == 'CNY', Order.total_price),
                    else_=Order.total_price * usd_rate
                )
            ).label("collection_amount"),
            func.sum(Order.quantity).label("collection_quantity"),
        ).filter(and_(*collection_filters)).first()
        
        past_quantity = sku_stat.get('total_quantity', 0)
        past_gmv = sku_stat.get('total_gmv', 0)
        past_collection_amount = float(collection_result.collection_amount or 0) if collection_result else 0
        past_collection_quantity = int(collection_result.collection_quantity or 0) if collection_result else 0
        
        daily_avg_quantity = past_quantity / past_days if past_days > 0 else 0
        predicted_quantity = daily_avg_quantity * future_days
        safety_factor = 1.3
        suggested_stock = int(predicted_quantity * safety_factor) if past_quantity > 0 else 0
        collection_rate = (past_collection_amount / past_gmv * 100) if past_gmv > 0 else 0
        
        return {
            "sku": sku,
            "product_name": sku_stat.get('product_name', '未知商品'),
            "manager": sku_stat.get('manager', '未分配'),
            "analysis_period": {
                "past_days": past_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "past_data": {
                "quantity": int(past_quantity),
                "orders": int(sku_stat.get('order_count', 0)),
                "gmv": round(past_gmv, 2),
                "collection_amount": round(past_collection_amount, 2),
                "collection_quantity": int(past_collection_quantity),
                "collection_rate": round(collection_rate, 2),
            },
            "prediction": {
                "period": future_period,
                "days": future_days,
                "daily_avg_quantity": round(daily_avg_quantity, 2),
                "predicted_quantity": int(predicted_quantity),
            },
            "stock_plan": {
                "suggested_stock": suggested_stock,
                "safety_factor": safety_factor,
                "priority": "high" if past_quantity > 100 else ("medium" if past_quantity > 50 else "low"),
            } if past_quantity > 0 else None
        }
    except Exception as e:
        logger.error(f"获取SKU备货计划失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取SKU备货计划失败: {str(e)}")

