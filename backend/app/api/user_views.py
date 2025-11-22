"""用户视图管理API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user_view import UserView
from app.models.user import User
from app.schemas.user_view import UserViewCreate, UserViewUpdate, UserViewResponse

router = APIRouter(prefix="/user-views", tags=["user-views"])


@router.get("/", response_model=List[UserViewResponse])
def get_user_views(
    view_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的所有视图
    
    Args:
        view_type: 视图类型过滤（如 'order_list'）
    
    Returns:
        用户视图列表
    """
    query = db.query(UserView).filter(UserView.user_id == current_user.id)
    
    if view_type:
        query = query.filter(UserView.view_type == view_type)
    
    views = query.order_by(UserView.created_at.desc()).all()
    return views


@router.get("/{view_id}", response_model=UserViewResponse)
def get_user_view(
    view_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定的用户视图"""
    view = db.query(UserView).filter(
        and_(
            UserView.id == view_id,
            UserView.user_id == current_user.id
        )
    ).first()
    
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视图不存在"
        )
    
    return view


@router.post("/", response_model=UserViewResponse, status_code=status.HTTP_201_CREATED)
def create_user_view(
    view: UserViewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的用户视图
    
    如果设置为默认视图，会将其他同类型视图的默认标记移除
    """
    # 检查同名视图是否已存在
    existing = db.query(UserView).filter(
        and_(
            UserView.user_id == current_user.id,
            UserView.name == view.name,
            UserView.view_type == view.view_type
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"视图名称 '{view.name}' 已存在"
        )
    
    # 如果设置为默认视图，取消其他同类型视图的默认标记
    if view.is_default:
        db.query(UserView).filter(
            and_(
                UserView.user_id == current_user.id,
                UserView.view_type == view.view_type,
                UserView.is_default == True
            )
        ).update({"is_default": False})
    
    db_view = UserView(
        user_id=current_user.id,
        **view.model_dump()
    )
    
    db.add(db_view)
    db.commit()
    db.refresh(db_view)
    
    return db_view


@router.put("/{view_id}", response_model=UserViewResponse)
def update_user_view(
    view_id: int,
    view_update: UserViewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户视图"""
    view = db.query(UserView).filter(
        and_(
            UserView.id == view_id,
            UserView.user_id == current_user.id
        )
    ).first()
    
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视图不存在"
        )
    
    # 如果更新名称，检查新名称是否已被使用
    if view_update.name and view_update.name != view.name:
        existing = db.query(UserView).filter(
            and_(
                UserView.user_id == current_user.id,
                UserView.name == view_update.name,
                UserView.view_type == view.view_type,
                UserView.id != view_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"视图名称 '{view_update.name}' 已存在"
            )
    
    # 如果设置为默认视图，取消其他同类型视图的默认标记
    if view_update.is_default:
        db.query(UserView).filter(
            and_(
                UserView.user_id == current_user.id,
                UserView.view_type == view.view_type,
                UserView.is_default == True,
                UserView.id != view_id
            )
        ).update({"is_default": False})
    
    # 更新视图
    update_data = view_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(view, field, value)
    
    db.commit()
    db.refresh(view)
    
    return view


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_view(
    view_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户视图"""
    view = db.query(UserView).filter(
        and_(
            UserView.id == view_id,
            UserView.user_id == current_user.id
        )
    ).first()
    
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视图不存在"
        )
    
    db.delete(view)
    db.commit()
    
    return None


@router.get("/default/{view_type}", response_model=Optional[UserViewResponse])
def get_default_view(
    view_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定类型的默认视图"""
    view = db.query(UserView).filter(
        and_(
            UserView.user_id == current_user.id,
            UserView.view_type == view_type,
            UserView.is_default == True
        )
    ).first()
    
    return view

