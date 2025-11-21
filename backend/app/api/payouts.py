"""回款计划API"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.payout import PayoutStatus
from app.services.payout_service import PayoutService

router = APIRouter(prefix="/payouts", tags=["回款计划"])


class PayoutStatusUpdate(BaseModel):
    """回款状态更新请求"""
    status: PayoutStatus


@router.get("")
def get_payouts(
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    status: Optional[PayoutStatus] = Query(None, description="回款状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询回款计划列表
    """
    # 解析日期
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = date.fromisoformat(start_date)
    if end_date:
        end_dt = date.fromisoformat(end_date)
    
    service = PayoutService(db)
    result = service.get_payouts(
        shop_ids=shop_ids,
        start_date=start_dt,
        end_date=end_dt,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": [
            {
                "id": p.id,
                "shop_id": p.shop_id,
                "order_id": p.order_id,
                "external_payout_id": p.external_payout_id,
                "payout_date": p.payout_date.isoformat() if p.payout_date else None,
                "payout_amount": float(p.payout_amount),
                "currency": p.currency,
                "status": p.status.value if p.status else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in result['items']
        ],
        "total": result['total'],
        "page": result['page'],
        "page_size": result['page_size'],
        "total_pages": result['total_pages']
    }


@router.patch("/{payout_id}")
def update_payout_status(
    payout_id: int,
    update_data: PayoutStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新回款状态
    """
    service = PayoutService(db)
    try:
        payout = service.update_payout_status(payout_id, update_data.status)
        return {
            "id": payout.id,
            "status": payout.status.value,
            "updated_at": payout.updated_at.isoformat() if payout.updated_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/summary")
def get_payout_summary(
    shop_ids: Optional[List[int]] = Query(None, description="店铺ID列表"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取回款统计汇总
    """
    # 解析日期
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = date.fromisoformat(start_date)
    if end_date:
        end_dt = date.fromisoformat(end_date)
    
    service = PayoutService(db)
    summary = service.get_payout_summary(
        shop_ids=shop_ids,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return summary

