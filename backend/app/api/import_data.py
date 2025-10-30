"""数据导入API"""
import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shop import Shop
from app.models.import_history import ImportHistory, ImportType
from app.services.excel_import_service import ExcelImportService
from app.services.feishu_sheets_service import FeishuSheetsService

router = APIRouter(prefix="/import", tags=["import"])

# 上传文件保存目录
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 请求模型
class OnlineSheetImportRequest(BaseModel):
    """在线表格导入请求"""
    url: str
    password: Optional[str] = None  # 表格访问密码（可选）
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://mcnkufobiqbi.feishu.cn/sheets/Xd3SsrVlEhNoBXtawvlcryWVnJc?sheet=HPLHTM",
                "password": "your_password_here"  # 可选
            }
        }


@router.post("/shops/{shop_id}/orders")
async def import_orders(
    shop_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入订单数据
    
    上传订单导出Excel文件
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只支持Excel文件(.xlsx, .xls)")
    
    file_path = os.path.join(UPLOAD_DIR, f"{shop_id}_{file.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        import_service = ExcelImportService(db, shop)
        result = await import_service.import_orders(file_path=file_path, file_name=file.filename, file_size=file_size)
        
        return {
            "success": True,
            "message": "订单数据导入完成",
            "data": {
                "import_id": result.id,
                "status": result.status.value,
                "total_rows": result.total_rows,
                "success_rows": result.success_rows,
                "failed_rows": result.failed_rows,
                "skipped_rows": result.skipped_rows
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"导入失败: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/shops/{shop_id}/activities")
async def import_activities(
    shop_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入活动数据
    
    上传活动商品明细Excel文件
    """
    # 验证店铺
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持Excel文件(.xlsx, .xls)"
        )
    
    # 保存上传文件
    file_path = os.path.join(UPLOAD_DIR, f"{shop_id}_{file.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        # 执行导入
        import_service = ExcelImportService(db, shop)
        result = await import_service.import_activities(
            file_path=file_path,
            file_name=file.filename,
            file_size=file_size
        )
        
        return {
            "success": True,
            "message": "活动数据导入完成",
            "data": {
                "import_id": result.id,
                "status": result.status.value,
                "total_rows": result.total_rows,
                "success_rows": result.success_rows,
                "failed_rows": result.failed_rows,
                "skipped_rows": result.skipped_rows
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/shops/{shop_id}/products")
async def import_products(
    shop_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    导入商品数据
    
    上传商品基础信息Excel文件
    """
    # 验证店铺
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持Excel文件(.xlsx, .xls)"
        )
    
    # 保存上传文件
    file_path = os.path.join(UPLOAD_DIR, f"{shop_id}_{file.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        # 执行导入
        import_service = ExcelImportService(db, shop)
        result = await import_service.import_products(
            file_path=file_path,
            file_name=file.filename,
            file_size=file_size
        )
        
        return {
            "success": True,
            "message": "商品数据导入完成",
            "data": {
                "import_id": result.id,
                "status": result.status.value,
                "total_rows": result.total_rows,
                "success_rows": result.success_rows,
                "failed_rows": result.failed_rows,
                "skipped_rows": result.skipped_rows
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)


@router.get("/shops/{shop_id}/history")
async def get_import_history(
    shop_id: int,
    skip: int = 0,
    limit: int = 20,
    import_type: str = None,
    db: Session = Depends(get_db)
):
    """
    获取导入历史记录
    
    Args:
        shop_id: 店铺ID
        skip: 跳过记录数
        limit: 返回记录数
        import_type: 导入类型筛选(orders/products/activities)
    """
    # 验证店铺
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    # 构建查询
    query = db.query(ImportHistory).filter(ImportHistory.shop_id == shop_id)
    
    if import_type:
        query = query.filter(ImportHistory.import_type == import_type)
    
    # 获取总数
    total = query.count()
    
    # 获取记录
    records = query.order_by(ImportHistory.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "records": [
            {
                "id": r.id,
                "import_type": r.import_type.value,
                "file_name": r.file_name,
                "file_size": r.file_size,
                "total_rows": r.total_rows,
                "success_rows": r.success_rows,
                "failed_rows": r.failed_rows,
                "skipped_rows": r.skipped_rows,
                "status": r.status.value,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    }


@router.get("/shops/{shop_id}/history/{import_id}")
async def get_import_detail(
    shop_id: int,
    import_id: int,
    db: Session = Depends(get_db)
):
    """
    获取导入详情（包括错误日志）
    """
    record = db.query(ImportHistory).filter(
        ImportHistory.id == import_id,
        ImportHistory.shop_id == shop_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入记录不存在"
        )
    
    import json
    
    return {
        "id": record.id,
        "import_type": record.import_type.value,
        "file_name": record.file_name,
        "file_size": record.file_size,
        "total_rows": record.total_rows,
        "success_rows": record.success_rows,
        "failed_rows": record.failed_rows,
        "skipped_rows": record.skipped_rows,
        "status": record.status.value,
        "error_log": json.loads(record.error_log) if record.error_log else [],
        "success_log": json.loads(record.success_log) if record.success_log else [],
        "started_at": record.started_at.isoformat() if record.started_at else None,
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
        "created_at": record.created_at.isoformat() if record.created_at else None
    }


@router.post("/shops/{shop_id}/orders/from-url")
async def import_orders_from_url(
    shop_id: int,
    request: OnlineSheetImportRequest,
    db: Session = Depends(get_db)
):
    """
    从在线表格导入订单数据
    
    支持飞书在线表格URL
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")
    
    feishu_service = FeishuSheetsService()
    if not feishu_service.validate_feishu_url(request.url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的飞书表格URL")
    
    try:
        import_service = ExcelImportService(db, shop)
        result = await import_service.import_orders_from_url(request.url, request.password)
        
        return {
            "success": True,
            "message": "订单数据导入完成",
            "data": {
                "import_id": result.id,
                "status": result.status.value,
                "total_rows": result.total_rows,
                "success_rows": result.success_rows,
                "failed_rows": result.failed_rows,
                "skipped_rows": result.skipped_rows
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"导入失败: {str(e)}")


@router.post("/shops/{shop_id}/activities/from-url")
async def import_activities_from_url(
    shop_id: int,
    request: OnlineSheetImportRequest,
    db: Session = Depends(get_db)
):
    """
    从在线表格导入活动数据
    
    支持飞书在线表格URL
    """
    # 验证店铺
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    # 验证URL格式
    feishu_service = FeishuSheetsService()
    if not feishu_service.validate_feishu_url(request.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的飞书表格URL，请确保URL格式正确"
        )
    
    try:
        # 执行导入
        import_service = ExcelImportService(db, shop)
        result = await import_service.import_activities_from_url(request.url, request.password)
        
        return {
            "success": True,
            "message": "活动数据导入完成",
            "data": {
                "import_id": result.id,
                "status": result.status.value,
                "total_rows": result.total_rows,
                "success_rows": result.success_rows,
                "failed_rows": result.failed_rows,
                "skipped_rows": result.skipped_rows
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.post("/shops/{shop_id}/products/from-url")
async def import_products_from_url(
    shop_id: int,
    request: OnlineSheetImportRequest,
    db: Session = Depends(get_db)
):
    """
    从在线表格导入商品数据
    
    支持飞书在线表格URL
    """
    # 验证店铺
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    # 验证URL格式
    feishu_service = FeishuSheetsService()
    if not feishu_service.validate_feishu_url(request.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的飞书表格URL，请确保URL格式正确"
        )
    
    try:
        # 执行导入
        import_service = ExcelImportService(db, shop)
        result = await import_service.import_products_from_url(request.url, request.password)
        
        return {
            "success": True,
            "message": "商品数据导入完成",
            "data": {
                "import_id": result.id,
                "status": result.status.value,
                "total_rows": result.total_rows,
                "success_rows": result.success_rows,
                "failed_rows": result.failed_rows,
                "skipped_rows": result.skipped_rows
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )

