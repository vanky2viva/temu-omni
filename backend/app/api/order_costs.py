"""订单成本计算API"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.order_cost_service import OrderCostCalculationService


router = APIRouter(prefix="/order-costs")


class CalculateCostRequest(BaseModel):
    """计算成本请求模型"""
    shop_id: Optional[int] = None
    order_ids: Optional[List[int]] = None
    force_recalculate: bool = False


class CalculateCostResponse(BaseModel):
    """计算成本响应模型"""
    total: int
    success: int
    failed: int
    skipped: int
    message: str


class DailyCollectionForecast(BaseModel):
    """每日预估回款模型"""
    date: str
    order_count: int
    total_amount: float
    total_cost: float
    total_profit: float
    profit_margin: float


@router.post("/calculate", response_model=CalculateCostResponse)
async def calculate_order_costs(
    request: CalculateCostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算订单成本和利润
    
    将商品列表中的供货价格、成本价格带入到订单列表中，计算每个订单的成本和利润
    """
    try:
        service = OrderCostCalculationService(db)
        result = service.calculate_order_costs(
            shop_id=request.shop_id,
            order_ids=request.order_ids,
            force_recalculate=request.force_recalculate
        )
        
        message = (
            f"订单成本计算完成 - "
            f"总计: {result['total']}, "
            f"成功: {result['success']}, "
            f"失败: {result['failed']}, "
            f"跳过: {result['skipped']}"
        )
        
        return CalculateCostResponse(
            total=result['total'],
            success=result['success'],
            failed=result['failed'],
            skipped=result['skipped'],
            message=message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算订单成本失败: {str(e)}"
        )


@router.get("/daily-forecast", response_model=List[DailyCollectionForecast])
async def get_daily_collection_forecast(
    shop_id: Optional[int] = Query(None, description="店铺ID"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取每日预估回款金额
    
    基于已计算成本的订单，统计每日的订单量、销售额、成本和利润
    """
    try:
        # 解析日期参数
        start_datetime = None
        end_datetime = None
        
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
        
        if end_date:
            end_datetime = datetime.fromisoformat(end_date)
        
        service = OrderCostCalculationService(db)
        result = service.get_daily_collection_forecast(
            shop_id=shop_id,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"日期格式错误: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取每日预估回款失败: {str(e)}"
        )

