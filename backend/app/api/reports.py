"""报表API"""
from typing import Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["报表"])


@router.get("/daily")
def get_daily_report(
    shop_id: int = Query(..., description="店铺ID"),
    report_date: Optional[str] = Query(None, description="报表日期 (YYYY-MM-DD)，默认为昨天"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取日报
    
    如果报表不存在，返回空数据。
    """
    # 解析日期，默认为昨天
    if report_date:
        report_dt = date.fromisoformat(report_date)
    else:
        report_dt = date.today() - timedelta(days=1)
    
    service = ReportService(db)
    snapshot = service.get_daily_report(shop_id, report_dt)
    
    if not snapshot:
        return {
            "date": report_dt.isoformat(),
            "shop_id": shop_id,
            "metrics": None,
            "ai_summary": None,
            "exists": False
        }
    
    return {
        "date": snapshot.date.isoformat() if snapshot.date else None,
        "shop_id": snapshot.shop_id,
        "metrics": snapshot.metrics,
        "ai_summary": snapshot.ai_summary,
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
        "updated_at": snapshot.updated_at.isoformat() if snapshot.updated_at else None,
        "exists": True
    }


@router.post("/daily/generate")
def generate_daily_report(
    shop_id: int = Query(..., description="店铺ID"),
    report_date: Optional[str] = Query(None, description="报表日期 (YYYY-MM-DD)，默认为昨天"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    手动触发日报生成
    """
    # 解析日期，默认为昨天
    if report_date:
        report_dt = date.fromisoformat(report_date)
    else:
        report_dt = date.today() - timedelta(days=1)
    
    service = ReportService(db)
    
    # 生成指标
    metrics = service.generate_daily_metrics(shop_id, report_dt)
    
    # 保存报表快照（不含AI总结，AI总结后续添加）
    snapshot = service.save_daily_report(shop_id, report_dt, metrics)
    
    return {
        "date": snapshot.date.isoformat() if snapshot.date else None,
        "shop_id": snapshot.shop_id,
        "metrics": snapshot.metrics,
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
    }


@router.get("/history")
def get_report_history(
    shop_id: int = Query(..., description="店铺ID"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(30, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取历史报表
    """
    # 解析日期
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = date.fromisoformat(start_date)
    if end_date:
        end_dt = date.fromisoformat(end_date)
    
    service = ReportService(db)
    result = service.get_report_history(
        shop_id=shop_id,
        start_date=start_dt,
        end_date=end_dt,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": [
            {
                "id": s.id,
                "date": s.date.isoformat() if s.date else None,
                "shop_id": s.shop_id,
                "type": s.type,
                "metrics": s.metrics,
                "ai_summary": s.ai_summary,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in result['items']
        ],
        "total": result['total'],
        "page": result['page'],
        "page_size": result['page_size'],
        "total_pages": result['total_pages']
    }


@router.get("/compare")
def compare_reports(
    shop_id: int = Query(..., description="店铺ID"),
    date1: str = Query(..., description="日期1 (YYYY-MM-DD)"),
    date2: str = Query(..., description="日期2 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    对比两个日期的报表
    """
    date1_dt = date.fromisoformat(date1)
    date2_dt = date.fromisoformat(date2)
    
    service = ReportService(db)
    try:
        comparison = service.compare_reports(shop_id, date1_dt, date2_dt)
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

